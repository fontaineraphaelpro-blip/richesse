require('dotenv').config();

const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const CACHE_TTL_MS = 60_000;
const CACHE_LONG_MS = 300_000;
const ANTHROPIC_MODEL = 'claude-sonnet-4-20250514';
const WATCHLIST = ['BTC', 'ETH', 'SOL', 'XRP', 'AAVE'];

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
  '1m': 120, '5m': 72, '15m': 72, '1h': 72, '4h': 72, '1d': 60,
};

const MACRO_SYMBOLS = [
  { label: 'DXY', yahoo: 'DX-Y.NYB' },
  { label: 'Nasdaq', yahoo: '^IXIC' },
  { label: 'Gold', yahoo: 'GC=F' },
  { label: 'VIX', yahoo: '^VIX' },
  { label: '10Y Yield', yahoo: '^TNX' },
  { label: 'S&P 500', yahoo: '^GSPC' },
];

const cache = {
  market: { data: null, expiresAt: 0 },
  coins: new Map(),
  correlation: { data: null, expiresAt: 0 },
  news: { data: null, expiresAt: 0 },
  macro: { data: null, expiresAt: 0 },
  regime: { data: null, expiresAt: 0 },
  why: new Map(),
  scenarios: new Map(),
  timeline: { data: null, expiresAt: 0 },
};

app.use(cors());
app.use(express.json({ limit: '256kb' }));
app.use(express.static(path.join(__dirname, 'public')));

function getCached(key, map) {
  const entry = map.get(key);
  if (entry && Date.now() < entry.expiresAt) return entry.data;
  return null;
}

function setCached(key, map, data, ttl = CACHE_TTL_MS) {
  map.set(key, { data, expiresAt: Date.now() + ttl });
}

function getSimpleCache(bucket) {
  if (bucket.data && Date.now() < bucket.expiresAt) return bucket.data;
  return null;
}

function setSimpleCache(bucket, data, ttl = CACHE_TTL_MS) {
  bucket.data = data;
  bucket.expiresAt = Date.now() + ttl;
}

async function fetchJson(url, config = {}) {
  const { data } = await axios.get(url, {
    timeout: 15_000,
    headers: { 'User-Agent': 'CryptoContextRadar/1.0' },
    ...config,
  });
  return data;
}

function calcRSI(prices, period = 14) {
  if (prices.length < period + 1) return null;
  let gains = 0, losses = 0;
  for (let i = 1; i <= period; i++) {
    const d = prices[i] - prices[i - 1];
    if (d > 0) gains += d; else losses -= d;
  }
  let avgG = gains / period, avgL = losses / period;
  for (let i = period + 1; i < prices.length; i++) {
    const d = prices[i] - prices[i - 1];
    avgG = (avgG * (period - 1) + (d > 0 ? d : 0)) / period;
    avgL = (avgL * (period - 1) + (d < 0 ? -d : 0)) / period;
  }
  if (avgL === 0) return 100;
  return 100 - 100 / (1 + avgG / avgL);
}

function calcVolatility(prices) {
  if (prices.length < 2) return { index: 0, level: 'LOW' };
  const changes = prices.slice(1).map((p, i) => Math.abs(p - prices[i]) / prices[i] * 100);
  const slice = changes.slice(-Math.min(24, changes.length));
  const avgVol = slice.reduce((a, b) => a + b, 0) / slice.length;
  const level = avgVol > 2 ? 'HIGH' : avgVol > 1 ? 'MEDIUM' : 'LOW';
  return { index: avgVol, level };
}

function returnsFromPrices(prices) {
  return prices.slice(1).map((p, i) => (p - prices[i]) / prices[i]);
}

function pearson(x, y) {
  const n = Math.min(x.length, y.length);
  if (n < 3) return 0;
  const mx = x.slice(0, n).reduce((a, b) => a + b, 0) / n;
  const my = y.slice(0, n).reduce((a, b) => a + b, 0) / n;
  let num = 0, dx = 0, dy = 0;
  for (let i = 0; i < n; i++) {
    const vx = x[i] - mx, vy = y[i] - my;
    num += vx * vy; dx += vx * vx; dy += vy * vy;
  }
  const den = Math.sqrt(dx * dy);
  return den ? num / den : 0;
}

function normalizeWeights(items) {
  const sum = items.reduce((s, i) => s + i.weight, 0) || 1;
  return items.map((i) => ({
    ...i,
    pct: Math.max(1, Math.round((i.weight / sum) * 100)),
  }));
}

async function fetchRssNews() {
  const feeds = [
    'https://www.coindesk.com/arc/outboundfeeds/rss/',
    'https://cointelegraph.com/rss',
  ];
  const items = [];
  for (const feedUrl of feeds) {
    if (items.length >= 12) break;
    try {
      const { data: xml } = await axios.get(feedUrl, {
        timeout: 12_000,
        responseType: 'text',
        headers: { 'User-Agent': 'CryptoContextRadar/1.0' },
      });
      const re = /<item[\s\S]*?<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>[\s\S]*?(?:<link>([^<]+)<\/link>|<link\/>)[\s\S]*?<pubDate>([^<]+)<\/pubDate/gi;
      let m;
      while ((m = re.exec(xml)) && items.length < 12) {
        const title = m[1].replace(/<[^>]+>/g, '').trim();
        const url = (m[2] || '').trim();
        const time = new Date(m[3]).toISOString();
        if (title) items.push({ title, url, time, coins: [], sent: 'neu' });
      }
    } catch (e) {
      console.warn('RSS feed failed:', feedUrl, e.message);
    }
  }
  return items;
}

async function fetchYahooQuote(yahooSymbol) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(yahooSymbol)}?interval=1d&range=5d`;
  const data = await fetchJson(url);
  const result = data?.chart?.result?.[0];
  if (!result) return null;
  const meta = result.meta;
  const closes = (result.indicators?.quote?.[0]?.close || []).filter((c) => c != null);
  const last = meta.regularMarketPrice ?? closes[closes.length - 1];
  const prev = closes.length >= 2 ? closes[closes.length - 2] : last;
  const changePct = prev ? ((last - prev) / prev) * 100 : 0;
  return {
    value: last,
    change24h: changePct,
    currency: meta.currency || 'USD',
  };
}

async function getMarketPayload() {
  const cached = getSimpleCache(cache.market);
  if (cached) return cached;

  const [globalRes, fgRes, btcRes] = await Promise.allSettled([
    fetchJson('https://api.coingecko.com/api/v3/global'),
    fetchJson('https://api.alternative.me/fng/?limit=1'),
    fetchJson('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true'),
  ]);

  const payload = { global: null, fearGreed: null, btc: null };
  if (globalRes.status === 'fulfilled') payload.global = globalRes.value.data;
  if (fgRes.status === 'fulfilled' && fgRes.value?.data?.[0]) {
    const fg = fgRes.value.data[0];
    payload.fearGreed = { value: parseInt(fg.value, 10), classification: fg.value_classification };
  }
  if (btcRes.status === 'fulfilled' && btcRes.value?.bitcoin) {
    payload.btc = { price: btcRes.value.bitcoin.usd, change24h: btcRes.value.bitcoin.usd_24h_change };
  }
  setSimpleCache(cache.market, payload);
  return payload;
}

async function fetchBinanceMetrics(binanceSymbol) {
  const [premium, oi, lsr, forceOrders, ticker24h] = await Promise.allSettled([
    fetchJson(`https://fapi.binance.com/fapi/v1/premiumIndex?symbol=${binanceSymbol}`),
    fetchJson(`https://fapi.binance.com/fapi/v1/openInterest?symbol=${binanceSymbol}`),
    fetchJson(`https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=${binanceSymbol}&period=1h&limit=1`),
    fetchJson(`https://fapi.binance.com/fapi/v1/allForceOrders?symbol=${binanceSymbol}&limit=100`),
    fetchJson(`https://api.binance.com/api/v3/ticker/24hr?symbol=${binanceSymbol}`),
  ]);

  let fundingRate = null, openInterestUsd = null, longShortRatio = null, liquidations1hUsd = 0;
  let volume24h = null, priceChange24h = null, lastPrice = null;

  if (premium.status === 'fulfilled') fundingRate = parseFloat(premium.value.lastFundingRate);
  if (oi.status === 'fulfilled') {
    const oiVal = parseFloat(oi.value.openInterest);
    const mark = premium.status === 'fulfilled' ? parseFloat(premium.value.markPrice) : null;
    openInterestUsd = mark ? oiVal * mark : oiVal;
  }
  if (lsr.status === 'fulfilled' && Array.isArray(lsr.value) && lsr.value.length) {
    longShortRatio = parseFloat(lsr.value[0].longShortRatio);
  }
  if (forceOrders.status === 'fulfilled' && Array.isArray(forceOrders.value)) {
    const oneHourAgo = Date.now() - 3600000;
    liquidations1hUsd = forceOrders.value
      .filter((o) => o.time >= oneHourAgo)
      .reduce((s, o) => s + parseFloat(o.origQty || 0) * parseFloat(o.price || o.avgPrice || 0), 0);
  }
  if (ticker24h.status === 'fulfilled') {
    const t = ticker24h.value;
    volume24h = parseFloat(t.quoteVolume);
    priceChange24h = parseFloat(t.priceChangePercent);
    lastPrice = parseFloat(t.lastPrice);
  }

  return { fundingRate, openInterestUsd, longShortRatio, liquidations1hUsd, volume24h, priceChange24h, lastPrice };
}

async function fetchCoinSnapshot(symbol) {
  const sym = symbol.toUpperCase();
  const coin = COIN_MAP[sym];
  if (!coin) return null;

  const cacheKey = `${sym}:snapshot`;
  const cached = getCached(cacheKey, cache.coins);
  if (cached) return cached;

  const [cgRes, klineRes, binanceMetrics] = await Promise.allSettled([
    fetchJson(`https://api.coingecko.com/api/v3/coins/${coin.gecko}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false`),
    fetchJson(`https://api.binance.com/api/v3/klines?symbol=${coin.binance}&interval=1h&limit=72`),
    fetchBinanceMetrics(coin.binance),
  ]);

  const result = {
    symbol: sym, name: sym, price: null, change24h: null, vol24h: null,
    rsi: null, volatility: { index: 0, level: 'LOW' },
    metrics: { fundingRate: null, openInterestUsd: null, volume24h: null, longShortRatio: null, liquidations1hUsd: null },
  };

  if (cgRes.status === 'fulfilled') {
    const md = cgRes.value.market_data;
    if (md) {
      result.name = cgRes.value.name || sym;
      result.price = md.current_price?.usd ?? null;
      result.change24h = md.price_change_percentage_24h ?? null;
      result.vol24h = md.total_volume?.usd ?? null;
    }
  }
  if (klineRes.status === 'fulfilled' && Array.isArray(klineRes.value) && klineRes.value.length) {
    const prices = klineRes.value.map((k) => parseFloat(k[4]));
    result.rsi = calcRSI(prices);
    result.volatility = calcVolatility(prices);
  }
  if (binanceMetrics.status === 'fulfilled') {
    const b = binanceMetrics.value;
    result.metrics = { fundingRate: b.fundingRate, openInterestUsd: b.openInterestUsd, volume24h: b.volume24h, longShortRatio: b.longShortRatio, liquidations1hUsd: b.liquidations1hUsd };
    if (b.lastPrice && !result.price) result.price = b.lastPrice;
    if (b.priceChange24h != null && result.change24h == null) result.change24h = b.priceChange24h;
  }

  setCached(cacheKey, cache.coins, result);
  return result;
}

// ─── ROUTES ───────────────────────────────────────────────────

app.get('/api/market', async (req, res) => {
  try {
    const payload = await getMarketPayload();
    res.json({ ...payload, cached: Date.now() < cache.market.expiresAt });
  } catch (err) {
    console.error('GET /api/market:', err.message);
    res.status(502).json({ error: 'Failed to fetch market data' });
  }
});

app.get('/api/coin/:symbol', async (req, res) => {
  const symbol = String(req.params.symbol || '').toUpperCase();
  const interval = TF_LIMITS[req.query.interval] ? req.query.interval : '1h';
  const limit = TF_LIMITS[interval] || 72;
  const coin = COIN_MAP[symbol];
  if (!coin) return res.status(404).json({ error: `Unknown symbol: ${symbol}` });

  const cacheKey = `${symbol}:${interval}`;
  const cached = getCached(cacheKey, cache.coins);
  if (cached) return res.json({ ...cached, cached: true });

  try {
    const [cgRes, klineRes, binanceMetrics] = await Promise.allSettled([
      fetchJson(`https://api.coingecko.com/api/v3/coins/${coin.gecko}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false`),
      fetchJson(`https://api.binance.com/api/v3/klines?symbol=${coin.binance}&interval=${interval}&limit=${limit}`),
      fetchBinanceMetrics(coin.binance),
    ]);

    const result = {
      symbol, name: symbol, price: null, change24h: null, vol24h: null, mcap: null,
      high24h: null, low24h: null,
      chart: { labels: [], prices: [], open: null },
      rsi: null, volatility: { index: 0, level: 'LOW' },
      metrics: { fundingRate: null, openInterestUsd: null, volume24h: null, longShortRatio: null, liquidations1hUsd: null },
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
      result.chart = {
        labels: klines.map((k) => {
          const d = new Date(k[0]);
          return interval === '1d' ? `${d.getMonth() + 1}/${d.getDate()}` : `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
        }),
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
      result.metrics = { fundingRate: b.fundingRate, openInterestUsd: b.openInterestUsd, volume24h: b.volume24h ?? result.vol24h, longShortRatio: b.longShortRatio, liquidations1hUsd: b.liquidations1hUsd };
      if (b.lastPrice && !result.price) result.price = b.lastPrice;
      if (b.priceChange24h != null && result.change24h == null) result.change24h = b.priceChange24h;
    }

    setCached(cacheKey, cache.coins, result);
    res.json(result);
  } catch (err) {
    console.error(`GET /api/coin/${symbol}:`, err.message);
    res.status(502).json({ error: 'Failed to fetch coin data' });
  }
});

app.get('/api/correlation', async (req, res) => {
  try {
    const cached = getSimpleCache(cache.correlation);
    if (cached) return res.json({ ...cached, cached: true });

    const series = await Promise.all(
      WATCHLIST.map(async (sym) => {
        const coin = COIN_MAP[sym];
        const klines = await fetchJson(`https://api.binance.com/api/v3/klines?symbol=${coin.binance}&interval=1h&limit=48`);
        const prices = klines.map((k) => parseFloat(k[4]));
        return { sym, returns: returnsFromPrices(prices) };
      })
    );

    const n = series.length;
    const matrix = Array.from({ length: n }, () => Array(n).fill(0));
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        matrix[i][j] = i === j ? 1 : pearson(series[i].returns, series[j].returns);
      }
    }

    const payload = { coins: WATCHLIST, matrix, insight: buildCorrelationInsight(WATCHLIST, matrix) };
    setSimpleCache(cache.correlation, payload, CACHE_LONG_MS);
    res.json({ ...payload, cached: false });
  } catch (err) {
    console.error('GET /api/correlation:', err.message);
    res.status(502).json({ error: 'Failed to compute correlation' });
  }
});

async function getBtcCorrelation(symbol) {
  if (symbol === 'BTC') return 1;
  const coin = COIN_MAP[symbol];
  if (!coin) return 0.85;
  try {
    const [btcK, symK] = await Promise.all([
      fetchJson('https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=48'),
      fetchJson(`https://api.binance.com/api/v3/klines?symbol=${coin.binance}&interval=1h&limit=48`),
    ]);
    return pearson(returnsFromPrices(btcK.map((k) => parseFloat(k[4]))), returnsFromPrices(symK.map((k) => parseFloat(k[4]))));
  } catch {
    return 0.85;
  }
}

function buildCorrelationInsight(coins, matrix) {
  let maxPair = { i: 0, j: 1, v: 0 };
  for (let i = 0; i < coins.length; i++) {
    for (let j = i + 1; j < coins.length; j++) {
      if (matrix[i][j] > maxPair.v) maxPair = { i, j, v: matrix[i][j] };
    }
  }
  let minIndep = { sym: coins[0], avg: 1 };
  coins.forEach((c, i) => {
    const others = matrix[i].filter((_, j) => i !== j);
    const avg = others.reduce((a, b) => a + Math.abs(b), 0) / others.length;
    if (avg < minIndep.avg) minIndep = { sym: c, avg };
  });
  return `${coins[maxPair.i]} and ${coins[maxPair.j]} show the highest 24h co-movement (${maxPair.v.toFixed(2)}). ${minIndep.sym} is the most decorrelated from the cluster (avg |ρ| ${minIndep.avg.toFixed(2)}). Values computed from Binance 1h returns (48 candles).`;
}

app.get('/api/news', async (req, res) => {
  try {
    const cached = getSimpleCache(cache.news);
    if (cached) return res.json({ ...cached, cached: true });

    let items = [];
    const cpToken = process.env.CRYPTOPANIC_TOKEN;
    if (cpToken) {
      const cp = await fetchJson(`https://cryptopanic.com/api/v1/posts/?auth_token=${cpToken}&public=true&filter=hot`);
      items = (cp.results || []).slice(0, 12).map((p) => ({
        title: p.title,
        time: p.published_at,
        url: p.url,
        coins: (p.currencies || []).map((c) => c.code?.toUpperCase()).filter(Boolean),
        sent: p.votes?.positive > p.votes?.negative ? 'pos' : p.votes?.negative > p.votes?.positive ? 'neg' : 'neu',
      }));
    } else {
      items = await fetchRssNews();
    }

    setSimpleCache(cache.news, { items }, 180_000);
    res.json({ items, cached: false });
  } catch (err) {
    console.error('GET /api/news:', err.message);
    res.status(502).json({ error: 'Failed to fetch news' });
  }
});

app.get('/api/macro', async (req, res) => {
  try {
    const cached = getSimpleCache(cache.macro);
    if (cached) return res.json({ ...cached, cached: true });

    const results = await Promise.allSettled(
      MACRO_SYMBOLS.map(async (m) => {
        const q = await fetchYahooQuote(m.yahoo);
        if (!q) return null;
        let displayVal = q.value;
        if (m.label === '10Y Yield') displayVal = q.value.toFixed(2) + '%';
        else if (m.label === 'VIX') displayVal = q.value.toFixed(1);
        else if (q.value > 1000) displayVal = q.value.toLocaleString('en-US', { maximumFractionDigits: 0 });
        else displayVal = q.value.toFixed(2);
        return { label: m.label, val: displayVal, change: q.change24h, raw: q.value };
      })
    );

    const items = results.filter((r) => r.status === 'fulfilled' && r.value).map((r) => ({
      label: r.value.label,
      val: r.value.val,
      change: r.value.change,
    }));

    setSimpleCache(cache.macro, { items }, CACHE_LONG_MS);
    res.json({ items, cached: false });
  } catch (err) {
    console.error('GET /api/macro:', err.message);
    res.status(502).json({ error: 'Failed to fetch macro data' });
  }
});

app.get('/api/regime', async (req, res) => {
  try {
    const cached = getSimpleCache(cache.regime);
    if (cached) return res.json({ ...cached, cached: true });

    const market = await getMarketPayload();
    const btc = await fetchCoinSnapshot('BTC');
    const fg = market.fearGreed?.value ?? 50;
    const btcChange = btc?.change24h ?? market.btc?.change24h ?? 0;
    const mcapCh = market.global?.market_cap_change_percentage_24h_usd ?? 0;
    const btcDom = market.global?.market_cap_percentage?.btc ?? 50;
    const funding = btc?.metrics?.fundingRate ?? 0;
    const rsi = btc?.rsi ?? 50;
    const vol = btc?.volatility?.level ?? 'LOW';

    const trendBull = btcChange > 1;
    const trendBear = btcChange < -1;
    const regimeName = trendBull && fg >= 45 ? 'Risk-On Trend' : trendBear && fg < 40 ? 'Risk-Off / Defensive' : fg < 30 ? 'Fear / Capitulation' : fg > 70 ? 'Euphoria / Overheated' : 'Range / Neutral';
    const regimeClass = trendBull ? 'regime-trending' : trendBear ? 'regime-risk-off' : 'regime-trending';

    const signals = [
      { label: 'Trend Direction', val: trendBull ? 'Bullish' : trendBear ? 'Bearish' : 'Neutral', col: trendBull ? 'var(--green)' : trendBear ? 'var(--red)' : 'var(--amber)' },
      { label: 'BTC 24h', val: `${btcChange >= 0 ? '+' : ''}${btcChange.toFixed(2)}%`, col: colorForChange(btcChange) },
      { label: 'Fear & Greed', val: `${fg} (${market.fearGreed?.classification || '—'})`, col: fg >= 55 ? 'var(--green)' : fg >= 40 ? 'var(--amber)' : 'var(--red)' },
      { label: 'Funding (BTC)', val: funding != null ? `${(funding * 100).toFixed(4)}%` : '—', col: funding > 0.0003 ? 'var(--red)' : funding < 0 ? 'var(--green)' : 'var(--amber)' },
      { label: 'Volatility', val: vol, col: vol === 'HIGH' ? 'var(--red)' : vol === 'MEDIUM' ? 'var(--amber)' : 'var(--cyan)' },
      { label: 'BTC Dominance', val: `${btcDom.toFixed(1)}%`, col: mcapCh < 0 && btcChange > 0 ? 'var(--violet)' : 'var(--text-muted)' },
    ];

    const confidence = Math.min(95, Math.round(55 + Math.abs(btcChange) * 2 + (rsi > 40 && rsi < 65 ? 10 : 0)));

    const payload = {
      name: regimeName,
      class: regimeClass,
      description: buildRegimeDescription(regimeName, btcChange, fg, mcapCh),
      confidence,
      signals,
    };
    setSimpleCache(cache.regime, payload);
    res.json({ ...payload, cached: false });
  } catch (err) {
    console.error('GET /api/regime:', err.message);
    res.status(502).json({ error: 'Failed to compute regime' });
  }
});

function colorForChange(v) {
  return v >= 0 ? 'var(--green)' : 'var(--red)';
}

function buildRegimeDescription(name, btcCh, fg, mcapCh) {
  return `${name}: BTC ${btcCh >= 0 ? '+' : ''}${btcCh.toFixed(2)}% (24h), Fear & Greed ${fg}, total market cap ${mcapCh >= 0 ? '+' : ''}${mcapCh.toFixed(2)}% (24h). Derived from live CoinGecko, Alternative.me and Binance data.`;
}

app.get('/api/why/:symbol', async (req, res) => {
  const symbol = String(req.params.symbol || 'BTC').toUpperCase();
  try {
    const cached = getCached(symbol, cache.why);
    if (cached) return res.json({ ...cached, cached: true });

    const [coin, market, btcCorrLive] = await Promise.all([
      fetchCoinSnapshot(symbol),
      getMarketPayload(),
      getBtcCorrelation(symbol),
    ]);

    if (!coin) return res.status(404).json({ error: 'Unknown symbol' });

    const btcCorr = btcCorrLive;

    const btcChange = market.btc?.change24h ?? 0;
    const change = coin.change24h ?? 0;
    const funding = coin.metrics?.fundingRate ?? 0;
    const liq = coin.metrics?.liquidations1hUsd ?? 0;
    const lsr = coin.metrics?.longShortRatio ?? 1;
    const fg = market.fearGreed?.value ?? 50;

    const raw = normalizeWeights([
      { label: `BTC beta driver (ρ=${btcCorr.toFixed(2)})`, weight: Math.abs(btcChange) * 4 + btcCorr * 35, col: 'var(--cyan)' },
      { label: 'Spot momentum (24h)', weight: Math.abs(change) * 5, col: 'var(--blue)' },
      { label: 'Derivatives (funding & L/S)', weight: Math.abs(funding) * 8000 + Math.abs(lsr - 1) * 25, col: 'var(--violet)' },
      { label: 'Liquidations (1h, Binance)', weight: Math.min(liq / 500000, 40), col: 'var(--amber)' },
      { label: 'Macro sentiment (F&G)', weight: Math.abs(fg - 50) * 0.8, col: fg >= 50 ? 'var(--green)' : 'var(--red)' },
    ]);

    const reasons = raw.map((r) => ({ label: r.label, pct: r.pct, col: r.col }));
    setCached(symbol, cache.why, { reasons });
    res.json({ reasons, cached: false });
  } catch (err) {
    console.error(`GET /api/why/${symbol}:`, err.message);
    res.status(502).json({ error: 'Failed to compute why moving' });
  }
});

app.get('/api/scenarios/:symbol', async (req, res) => {
  const symbol = String(req.params.symbol || 'BTC').toUpperCase();
  try {
    const cached = getCached(symbol, cache.scenarios);
    if (cached) return res.json({ ...cached, cached: true });

    const [coin, market] = await Promise.all([fetchCoinSnapshot(symbol), getMarketPayload()]);
    if (!coin) return res.status(404).json({ error: 'Unknown symbol' });

    const change = coin.change24h ?? 0;
    const rsi = coin.rsi ?? 50;
    const vol = coin.volatility?.level ?? 'LOW';
    const funding = Math.abs(coin.metrics?.fundingRate ?? 0);
    const liq = coin.metrics?.liquidations1hUsd ?? 0;
    const fg = market.fearGreed?.value ?? 50;

    const raw = [
      { label: 'Trend continuation (24h direction)', weight: 20 + Math.max(0, change) * 3 + (rsi > 45 && rsi < 72 ? 18 : 5), col: 'var(--green)', icon: '▲' },
      { label: 'Range / chop (low directional edge)', weight: vol === 'LOW' ? 38 : vol === 'MEDIUM' ? 22 : 10, col: 'var(--amber)', icon: '◆' },
      { label: 'Risk-off shock (macro fear)', weight: 12 + (fg < 35 ? 22 : 0) + (change < -3 ? 18 : 0), col: 'var(--red)', icon: '▼' },
      { label: 'Squeeze / volatility spike', weight: 8 + funding * 12000 + Math.min(liq / 1e6, 20), col: 'var(--violet)', icon: '⚡' },
    ];
    const scenarios = normalizeWeights(raw).map((s) => ({
      label: s.label, pct: s.pct, col: s.col, icon: s.icon,
    }));

    setCached(symbol, cache.scenarios, { scenarios });
    res.json({ scenarios, cached: false });
  } catch (err) {
    console.error(`GET /api/scenarios/${symbol}:`, err.message);
    res.status(502).json({ error: 'Failed to compute scenarios' });
  }
});

app.get('/api/timeline', async (req, res) => {
  try {
    const symbol = String(req.query.symbol || 'BTC').toUpperCase();
    const cached = getSimpleCache(cache.timeline);
    if (cached && cached.symbol === symbol) return res.json({ ...cached, cached: true });

    const [coin, market, newsRes] = await Promise.all([
      fetchCoinSnapshot(symbol),
      getMarketPayload(),
      getSimpleCache(cache.news),
    ]);

    const events = [];
    const now = new Date();
    const t = (d) => `${d.getUTCHours().toString().padStart(2, '0')}:${d.getUTCMinutes().toString().padStart(2, '0')}`;

    if (coin?.change24h != null && Math.abs(coin.change24h) >= 2) {
      events.push({
        time: t(now), col: coin.change24h >= 0 ? 'var(--green)' : 'var(--red)', icon: coin.change24h >= 0 ? '▲' : '▼',
        text: `${symbol} ${coin.change24h >= 0 ? 'up' : 'down'} ${coin.change24h.toFixed(2)}% over 24h (live)`,
      });
    }
    if (coin?.metrics?.liquidations1hUsd > 500000) {
      events.push({
        time: t(now), col: 'var(--red)', icon: '⚡',
        text: `$${(coin.metrics.liquidations1hUsd / 1e6).toFixed(2)}M liquidations on ${symbol} in the last hour (Binance)`,
      });
    }
    if (coin?.metrics?.fundingRate != null && Math.abs(coin.metrics.fundingRate) > 0.0004) {
      events.push({
        time: t(now), col: 'var(--amber)', icon: '⚠',
        text: `Funding rate ${(coin.metrics.fundingRate * 100).toFixed(3)}% on ${symbol} (elevated)`,
      });
    }
    if (market?.btc?.change24h != null && Math.abs(market.btc.change24h) >= 1.5) {
      events.push({
        time: t(now), col: 'var(--cyan)', icon: '◈',
        text: `BTC ${market.btc.change24h >= 0 ? '+' : ''}${market.btc.change24h.toFixed(2)}% — macro driver for alts`,
      });
    }
    if (newsRes?.items?.[0]) {
      const n = newsRes.items[0];
      events.push({
        time: t(new Date(n.time)), col: 'var(--violet)', icon: '●',
        text: n.title,
      });
    }

    const payload = { symbol, events: events.slice(0, 8) };
    setSimpleCache(cache.timeline, payload, 90_000);
    res.json({ ...payload, cached: false });
  } catch (err) {
    console.error('GET /api/timeline:', err.message);
    res.status(502).json({ error: 'Failed to build timeline' });
  }
});

function parseConfidence(text) {
  const match = text.match(/(\d{1,3})\s*%/g);
  if (!match) return null;
  const nums = match.map((m) => parseInt(m, 10)).filter((n) => n >= 0 && n <= 100);
  return nums.length ? nums[nums.length - 1] : null;
}

async function callAnthropic(userPrompt) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY is not configured');

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

app.post('/api/analyze', async (req, res) => {
  try {
    const { type = 'analysis', symbol, coinData, marketContext, prompt } = req.body || {};
    if (!symbol && !prompt) return res.status(400).json({ error: 'symbol or prompt is required' });

    let userPrompt = prompt;
    if (!userPrompt) {
      const sym = String(symbol).toUpperCase();
      const cd = coinData || (await fetchCoinSnapshot(sym)) || {};
      const mc = marketContext || (await getMarketPayload());
      const price = cd.price != null ? (cd.price > 1000 ? `$${cd.price.toLocaleString('en-US', { maximumFractionDigits: 2 })}` : `$${Number(cd.price).toFixed(4)}`) : 'unknown';
      const change = cd.change24h != null ? `${cd.change24h >= 0 ? '+' : ''}${Number(cd.change24h).toFixed(2)}%` : 'unknown';
      const dataBlock = JSON.stringify({ coin: cd, market: { btcDom: mc.global?.market_cap_percentage?.btc, fearGreed: mc.fearGreed, btc: mc.btc } }, null, 0);

      const rules = 'CRITICAL: Use ONLY the numeric data provided below. Do not invent prices, percentages, or events. If a metric is missing, say "data unavailable".';

      if (type === 'debate') {
        userPrompt = `${rules}\n\nAI debate for ${sym}.\nLive JSON: ${dataBlock}\n\nFormat EXACTLY:\nBULL: [2-3 sentences using only provided data]\nBEAR: [2-3 sentences using only provided data]\nVERDICT: [one sentence with % probability]`;
      } else if (type === 'why') {
        userPrompt = `${rules}\n\nExplain why ${sym} is moving using ONLY this JSON: ${dataBlock}\n\nReturn 4-5 drivers as lines: "Driver | estimated weight%". Weights must sum to ~100. No markdown.`;
      } else {
        userPrompt = `${rules}\n\nInstitutional analysis for ${sym} (${cd.name || sym}).\nPrice: ${price}, 24h: ${change}\nFull JSON: ${dataBlock}\n\n3-4 sentences: price action, key driver from data, risk, verdict with confidence %. Plain text, no bullets.`;
      }
    }

    const text = await callAnthropic(userPrompt);
    res.json({ text, confidence: parseConfidence(text), type });
  } catch (err) {
    console.error('POST /api/analyze:', err.response?.data || err.message);
    const status = err.message?.includes('ANTHROPIC_API_KEY') ? 503 : 502;
    res.status(status).json({ error: err.response?.data?.error?.message || err.message || 'Analysis failed' });
  }
});

app.get('*', (req, res) => {
  if (req.path.startsWith('/api/')) return res.status(404).json({ error: 'Not found' });
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Crypto Context Radar listening on port ${PORT}`);
});
