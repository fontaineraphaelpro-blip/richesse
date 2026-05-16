require('dotenv').config();

const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const CACHE_TTL_MS = 60_000;
const ANTHROPIC_MODEL = 'claude-sonnet-4-20250514';

const COIN_MAP = {
  BTC: { gecko: 'bitcoin', binance: 'BTCUSDT' },
  ETH: { gecko: 'ethereum', binance: 'ETHUSDT' },
  SOL: { gecko: 'solana', binance: 'SOLUSDT' },
  XRP: { gecko: 'ripple', binance: 'XRPUSDT' },
  AAVE: { gecko: 'aave', binance: 'AAVEUSDT' },
  AVAX: { gecko: 'avalanche-2', binance: 'AVAXUSDT' },
  LINK: { gecko: 'chainlink', binance: 'LINKUSDT' },
  DOT: { gecko: 'polkadot', binance: 'DOTUSDT' },
};

const TF_LIMITS = {
  '1m': 120,
  '5m': 72,
  '15m': 72,
  '1h': 72,
  '4h': 72,
  '1d': 60,
};

const cache = {
  market: { data: null, expiresAt: 0 },
  coins: new Map(),
};

app.use(cors());
app.use(express.json({ limit: '256kb' }));
app.use(express.static(path.join(__dirname, 'public')));

function getCached(key, map) {
  const entry = map.get(key);
  if (entry && Date.now() < entry.expiresAt) return entry.data;
  return null;
}

function setCached(key, map, data) {
  map.set(key, { data, expiresAt: Date.now() + CACHE_TTL_MS });
}

async function fetchJson(url, config = {}) {
  const { data } = await axios.get(url, {
    timeout: 15_000,
    ...config,
  });
  return data;
}

function calcRSI(prices, period = 14) {
  if (prices.length < period + 1) return null;
  let gains = 0;
  let losses = 0;
  for (let i = 1; i <= period; i++) {
    const d = prices[i] - prices[i - 1];
    if (d > 0) gains += d;
    else losses -= d;
  }
  let avgG = gains / period;
  let avgL = losses / period;
  for (let i = period + 1; i < prices.length; i++) {
    const d = prices[i] - prices[i - 1];
    avgG = (avgG * (period - 1) + (d > 0 ? d : 0)) / period;
    avgL = (avgL * (period - 1) + (d < 0 ? -d : 0)) / period;
  }
  if (avgL === 0) return 100;
  const rs = avgG / avgL;
  return 100 - 100 / (1 + rs);
}

function calcVolatility(prices) {
  if (prices.length < 2) return { index: 0, level: 'LOW' };
  const changes = prices.slice(1).map((p, i) => Math.abs(p - prices[i]) / prices[i] * 100);
  const slice = changes.slice(-Math.min(24, changes.length));
  const avgVol = slice.reduce((a, b) => a + b, 0) / slice.length;
  const level = avgVol > 2 ? 'HIGH' : avgVol > 1 ? 'MEDIUM' : 'LOW';
  return { index: avgVol, level };
}

function computeStress(fearGreed, fundingRate, volatilityIndex) {
  const fg = Number(fearGreed) || 50;
  const funding = Math.abs(Number(fundingRate) || 0) * 100;
  const vol = Number(volatilityIndex) || 1;

  const fgStress = fg > 75 ? 70 : fg > 50 ? 40 : fg > 25 ? 30 : 80;
  const fundingStress = Math.min(95, 20 + funding * 800);
  const volStress = Math.min(95, vol * 25);
  const liqStress = 25;

  const stress = Math.round((fundingStress + liqStress + volStress + fgStress) / 4 * 1.5);
  const clamped = Math.min(Math.max(stress, 10), 95);
  const tag = clamped >= 75 ? 'EXTREME' : clamped >= 55 ? 'HIGH' : clamped >= 35 ? 'MEDIUM' : 'LOW';

  return {
    score: clamped,
    tag,
    components: {
      funding: Math.round(fundingStress),
      oi: Math.round(35 + vol * 5),
      fearGreed: Math.round(fgStress),
    },
  };
}

async function fetchBinanceMetrics(binanceSymbol) {
  const [premium, oi, lsr, forceOrders, ticker24h] = await Promise.allSettled([
    fetchJson(`https://fapi.binance.com/fapi/v1/premiumIndex?symbol=${binanceSymbol}`),
    fetchJson(`https://fapi.binance.com/fapi/v1/openInterest?symbol=${binanceSymbol}`),
    fetchJson(
      `https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=${binanceSymbol}&period=1h&limit=1`
    ),
    fetchJson(`https://fapi.binance.com/fapi/v1/allForceOrders?symbol=${binanceSymbol}&limit=100`),
    fetchJson(`https://api.binance.com/api/v3/ticker/24hr?symbol=${binanceSymbol}`),
  ]);

  let fundingRate = null;
  if (premium.status === 'fulfilled') {
    fundingRate = parseFloat(premium.value.lastFundingRate);
  }

  let openInterestUsd = null;
  if (oi.status === 'fulfilled') {
    const oiVal = parseFloat(oi.value.openInterest);
    const mark =
      premium.status === 'fulfilled' ? parseFloat(premium.value.markPrice) : null;
    openInterestUsd = mark ? oiVal * mark : oiVal;
  }

  let longShortRatio = null;
  if (lsr.status === 'fulfilled' && Array.isArray(lsr.value) && lsr.value.length) {
    longShortRatio = parseFloat(lsr.value[0].longShortRatio);
  }

  let liquidations1hUsd = 0;
  if (forceOrders.status === 'fulfilled' && Array.isArray(forceOrders.value)) {
    const oneHourAgo = Date.now() - 60 * 60 * 1000;
    liquidations1hUsd = forceOrders.value
      .filter((o) => o.time >= oneHourAgo)
      .reduce((sum, o) => {
        const qty = parseFloat(o.origQty || 0);
        const price = parseFloat(o.price || o.avgPrice || 0);
        return sum + qty * price;
      }, 0);
  }

  let volume24h = null;
  let priceChange24h = null;
  let lastPrice = null;
  if (ticker24h.status === 'fulfilled') {
    const t = ticker24h.value;
    volume24h = parseFloat(t.quoteVolume);
    priceChange24h = parseFloat(t.priceChangePercent);
    lastPrice = parseFloat(t.lastPrice);
  }

  return {
    fundingRate,
    openInterestUsd,
    longShortRatio,
    liquidations1hUsd,
    volume24h,
    priceChange24h,
    lastPrice,
  };
}

// GET /api/market — global CoinGecko + Fear & Greed (60s cache)
app.get('/api/market', async (req, res) => {
  try {
    if (cache.market.data && Date.now() < cache.market.expiresAt) {
      return res.json({ ...cache.market.data, cached: true });
    }

    const [globalRes, fgRes, btcRes] = await Promise.allSettled([
      fetchJson('https://api.coingecko.com/api/v3/global'),
      fetchJson('https://api.alternative.me/fng/?limit=1'),
      fetchJson(
        'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true'
      ),
    ]);

    const payload = { global: null, fearGreed: null, btc: null, cached: false };

    if (globalRes.status === 'fulfilled') {
      payload.global = globalRes.value.data;
    }

    if (fgRes.status === 'fulfilled' && fgRes.value?.data?.[0]) {
      const fg = fgRes.value.data[0];
      payload.fearGreed = {
        value: parseInt(fg.value, 10),
        classification: fg.value_classification,
      };
    }

    if (btcRes.status === 'fulfilled' && btcRes.value?.bitcoin) {
      payload.btc = {
        price: btcRes.value.bitcoin.usd,
        change24h: btcRes.value.bitcoin.usd_24h_change,
      };
    }

    cache.market = { data: payload, expiresAt: Date.now() + CACHE_TTL_MS };
    res.json(payload);
  } catch (err) {
    console.error('GET /api/market error:', err.message);
    res.status(502).json({ error: 'Failed to fetch market data' });
  }
});

// GET /api/coin/:symbol — coin + Binance metrics (60s cache per symbol+interval)
app.get('/api/coin/:symbol', async (req, res) => {
  const symbol = String(req.params.symbol || '').toUpperCase();
  const interval = TF_LIMITS[req.query.interval] ? req.query.interval : '1h';
  const limit = TF_LIMITS[interval] || 72;
  const coin = COIN_MAP[symbol];

  if (!coin) {
    return res.status(404).json({ error: `Unknown symbol: ${symbol}` });
  }

  const cacheKey = `${symbol}:${interval}`;
  const cached = getCached(cacheKey, cache.coins);
  if (cached) {
    return res.json({ ...cached, cached: true });
  }

  try {
    const [cgRes, klineRes, binanceMetrics] = await Promise.allSettled([
      fetchJson(
        `https://api.coingecko.com/api/v3/coins/${coin.gecko}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false`
      ),
      fetchJson(
        `https://api.binance.com/api/v3/klines?symbol=${coin.binance}&interval=${interval}&limit=${limit}`
      ),
      fetchBinanceMetrics(coin.binance),
    ]);

    const result = {
      symbol,
      name: symbol,
      price: null,
      change24h: null,
      vol24h: null,
      mcap: null,
      high24h: null,
      low24h: null,
      chart: { labels: [], prices: [], open: null },
      rsi: null,
      volatility: { index: 0, level: 'LOW' },
      metrics: {
        fundingRate: null,
        openInterestUsd: null,
        volume24h: null,
        longShortRatio: null,
        liquidations1hUsd: null,
      },
      cached: false,
    };

    if (cgRes.status === 'fulfilled') {
      const md = cgRes.value.market_data;
      if (md) {
        result.name = cgRes.value.name || symbol;
        result.price = md.current_price?.usd ?? null;
        result.change24h = md.price_change_percentage_24h ?? null;
        result.vol24h = md.total_volume?.usd ?? null;
        result.mcap = md.market_cap?.usd ?? null;
        result.high24h = md.high_24h?.usd ?? null;
        result.low24h = md.low_24h?.usd ?? null;
      }
    }

    if (klineRes.status === 'fulfilled' && Array.isArray(klineRes.value) && klineRes.value.length) {
      const klines = klineRes.value;
      const prices = klines.map((k) => parseFloat(k[4]));
      const labels = klines.map((k) => {
        const d = new Date(k[0]);
        if (interval === '1d') return `${d.getMonth() + 1}/${d.getDate()}`;
        return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
      });
      result.chart = {
        labels,
        prices,
        open: parseFloat(klines[0][1]),
        high: Math.max(...klines.map((k) => parseFloat(k[2]))),
        low: Math.min(...klines.map((k) => parseFloat(k[3]))),
        volume: klines.reduce((s, k) => s + parseFloat(k[5]), 0),
      };
      result.rsi = calcRSI(prices);
      result.volatility = calcVolatility(prices);
    }

    if (binanceMetrics.status === 'fulfilled') {
      const b = binanceMetrics.value;
      result.metrics = {
        fundingRate: b.fundingRate,
        openInterestUsd: b.openInterestUsd,
        volume24h: b.volume24h ?? result.vol24h,
        longShortRatio: b.longShortRatio,
        liquidations1hUsd: b.liquidations1hUsd,
      };
      if (b.lastPrice && !result.price) result.price = b.lastPrice;
      if (b.priceChange24h != null && result.change24h == null) {
        result.change24h = b.priceChange24h;
      }
      if (b.volume24h && !result.vol24h) result.vol24h = b.volume24h;
    }

    setCached(cacheKey, cache.coins, result);
    res.json(result);
  } catch (err) {
    console.error(`GET /api/coin/${symbol} error:`, err.message);
    res.status(502).json({ error: 'Failed to fetch coin data' });
  }
});

function parseConfidence(text) {
  const match = text.match(/(\d{1,3})\s*%/g);
  if (!match) return 68;
  const nums = match.map((m) => parseInt(m, 10)).filter((n) => n >= 0 && n <= 100);
  return nums.length ? nums[nums.length - 1] : 68;
}

async function callAnthropic(userPrompt) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY is not configured');
  }

  const { data } = await axios.post(
    'https://api.anthropic.com/v1/messages',
    {
      model: ANTHROPIC_MODEL,
      max_tokens: 1000,
      messages: [{ role: 'user', content: userPrompt }],
    },
    {
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      timeout: 60_000,
    }
  );

  return data.content?.map((b) => b.text || '').join('') || '';
}

// POST /api/analyze — Anthropic proxy (key stays server-side)
app.post('/api/analyze', async (req, res) => {
  try {
    const { type = 'analysis', symbol, coinData, marketContext, prompt } = req.body || {};

    if (!symbol && !prompt) {
      return res.status(400).json({ error: 'symbol or prompt is required' });
    }

    let userPrompt = prompt;

    if (!userPrompt) {
      const sym = String(symbol).toUpperCase();
      const cd = coinData || {};
      const mc = marketContext || {};
      const price =
        cd.price != null
          ? cd.price > 1000
            ? `$${cd.price.toLocaleString('en-US', { maximumFractionDigits: 2 })}`
            : `$${Number(cd.price).toFixed(4)}`
          : 'unknown';
      const change =
        cd.change24h != null
          ? `${cd.change24h >= 0 ? '+' : ''}${Number(cd.change24h).toFixed(2)}%`
          : 'unknown';

      if (type === 'debate') {
        userPrompt = `You are running an AI debate system for ${sym} crypto analysis. Generate:

BULL: 2-3 sentences arguing bullish case for ${sym}
BEAR: 2-3 sentences arguing bearish case for ${sym}
VERDICT: One sentence probabilistic conclusion with % (e.g. "55% bullish")

Live data:
- Price: ${price}
- 24h change: ${change}
- Funding rate: ${cd.metrics?.fundingRate ?? 'n/a'}
- Long/short ratio: ${cd.metrics?.longShortRatio ?? 'n/a'}
- RSI: ${cd.rsi ?? 'n/a'}
- Market: ${JSON.stringify(mc)}

Format EXACTLY as:
BULL: [text]
BEAR: [text]
VERDICT: [text]

Be specific, use market terminology.`;
      } else {
        userPrompt = `You are an elite crypto market analyst at an institutional trading desk. Analyze ${cd.name || sym} (${sym}) with these live data points:
- Current price: ${price}
- 24h change: ${change}
- Funding rate: ${cd.metrics?.fundingRate ?? 'n/a'}
- Open interest (USD): ${cd.metrics?.openInterestUsd ?? 'n/a'}
- Long/short ratio: ${cd.metrics?.longShortRatio ?? 'n/a'}
- RSI: ${cd.rsi ?? 'n/a'}
- Volatility: ${cd.volatility?.level ?? 'n/a'}
- Market context: ${JSON.stringify(mc)}

Generate a concise, sharp institutional-grade market analysis in 3-4 sentences. Include:
1. Current price action interpretation
2. Key driver or catalyst
3. Risk factor or concern
4. Probability assessment (bullish/bearish continuation)

Use terms like OI, funding, CVD, structure, liquidity, squeeze. Be precise, data-driven, and direct. End with a one-line verdict including confidence %.

Format as plain text, no markdown, no bullets.`;
      }
    }

    const text = await callAnthropic(userPrompt);
    const confidence = parseConfidence(text);

    res.json({ text, confidence, type });
  } catch (err) {
    console.error('POST /api/analyze error:', err.response?.data || err.message);
    const status = err.message?.includes('ANTHROPIC_API_KEY') ? 503 : 502;
    res.status(status).json({
      error: err.response?.data?.error?.message || err.message || 'Analysis failed',
    });
  }
});

app.get('*', (req, res) => {
  if (req.path.startsWith('/api/')) {
    return res.status(404).json({ error: 'Not found' });
  }
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Crypto Context Radar listening on port ${PORT}`);
});
