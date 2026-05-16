/* Live data layer — overrides static panels with API-backed data */

window._fearGreed = null;

async function fetchWhyMoving(sym) {
  const container = el('whyReasons');
  if (!container) return;
  container.textContent = 'Loading live drivers...';
  container.style.cssText = 'padding:12px 16px;color:var(--text-dim);font-size:12px';
  try {
    const res = await fetch('/api/why/' + sym);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    container.style.cssText = '';
    container.innerHTML = '';
    (data.reasons || []).forEach((r) => {
      const row = document.createElement('div');
      row.className = 'why-row';
      row.innerHTML =
        '<div class="why-label"></div><div class="why-bar-bg"><div class="why-bar-fill"></div></div><div class="why-pct"></div>';
      row.querySelector('.why-label').textContent = r.label;
      row.querySelector('.why-bar-fill').style.cssText = 'width:' + r.pct + '%;background:' + r.col;
      row.querySelector('.why-pct').textContent = r.pct + '%';
      row.querySelector('.why-pct').style.color = r.col;
      container.appendChild(row);
    });
  } catch (e) {
    container.textContent = 'Unable to load drivers';
    container.style.color = 'var(--red)';
  }
}

async function fetchCorrelation() {
  const matrix = el('corrMatrix');
  if (!matrix) return;
  try {
    const res = await fetch('/api/correlation');
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    matrix.innerHTML = '';
    (data.coins || []).forEach((c, i) => {
      (data.coins || []).forEach((c2, j) => {
        const v = data.matrix[i][j];
        const intensity = Math.abs(v);
        const r = Math.round(255 * (1 - intensity) * 0.3);
        const g = Math.round(v >= 0 ? 212 * intensity : 80 * intensity);
        const b = Math.round(v >= 0 ? 255 * intensity : 107 * intensity);
        const cell = document.createElement('div');
        cell.className = 'hm-cell';
        cell.style.background = 'rgba(' + r + ',' + g + ',' + b + ',' + (0.15 + intensity * 0.35) + ')';
        cell.title = c + ' vs ' + c2 + ': ' + v.toFixed(2);
        cell.textContent = i === j ? c : v.toFixed(2);
        matrix.appendChild(cell);
      });
    });
    if (el('corrInsight')) el('corrInsight').textContent = data.insight || '';
  } catch (e) {
    matrix.textContent = 'Correlation unavailable';
  }
}

async function fetchRegime() {
  try {
    const res = await fetch('/api/regime');
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    if (el('regimeBadge')) el('regimeBadge').textContent = data.name;
    if (el('regimeMain')) el('regimeMain').textContent = data.name;
    if (el('regimeDesc')) el('regimeDesc').textContent = data.description;
    setText('regimeConf', data.confidence + '%');
    const c = el('regimeSignals');
    if (c) {
      c.innerHTML = '';
      (data.signals || []).forEach((s) => {
        const row = document.createElement('div');
        row.className = 'signal-row';
        row.innerHTML =
          '<div class="signal-dot"></div><div class="sig-l"></div><div class="sig-v"></div>';
        row.querySelector('.signal-dot').style.background = s.col;
        row.querySelector('.sig-l').textContent = s.label;
        row.querySelector('.sig-l').style.cssText = 'flex:1;font-size:11px;color:var(--text-muted)';
        row.querySelector('.sig-v').textContent = s.val;
        row.querySelector('.sig-v').style.cssText = 'font-size:11px;font-family:var(--mono);color:' + s.col;
        c.appendChild(row);
      });
    }
  } catch (e) {
    console.warn('regime', e);
  }
}

async function fetchScenarios(sym) {
  const c = el('scenariosList');
  if (!c) return;
  try {
    const res = await fetch('/api/scenarios/' + sym);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    c.innerHTML = '';
    (data.scenarios || []).forEach((s) => {
      const row = document.createElement('div');
      row.className = 'scenario-item';
      row.innerHTML =
        '<div class="sc-icon"></div><div class="sc-label"></div><div class="scenario-pct"></div>';
      row.querySelector('.sc-icon').textContent = s.icon;
      row.querySelector('.sc-icon').style.color = s.col;
      row.querySelector('.sc-label').textContent = s.label;
      row.querySelector('.scenario-pct').textContent = s.pct + '%';
      row.querySelector('.scenario-pct').style.color = s.col;
      c.appendChild(row);
    });
  } catch (e) {
    c.textContent = 'Scenarios unavailable';
  }
}

async function fetchMacro() {
  const c = el('macroGrid');
  if (!c) return;
  try {
    const res = await fetch('/api/macro');
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    c.innerHTML = '';
    (data.items || []).forEach((it) => {
      const col = it.change >= 0 ? 'var(--green)' : 'var(--red)';
      const ch = (it.change >= 0 ? '+' : '') + it.change.toFixed(2) + '%';
      const card = document.createElement('div');
      card.style.cssText = 'background:var(--bg-panel);border:1px solid var(--border);border-radius:8px;padding:10px';
      card.innerHTML = '<div class="m-l"></div><div class="m-v"></div><div class="m-c"></div>';
      card.querySelector('.m-l').textContent = it.label;
      card.querySelector('.m-l').style.cssText = 'font-size:9px;font-family:var(--mono);color:var(--text-muted);text-transform:uppercase;margin-bottom:4px';
      card.querySelector('.m-v').textContent = it.val;
      card.querySelector('.m-v').style.cssText = 'font-family:var(--mono);font-size:14px;font-weight:600';
      card.querySelector('.m-c').textContent = ch;
      card.querySelector('.m-c').style.cssText = 'font-family:var(--mono);font-size:10px;color:' + col;
      c.appendChild(card);
    });
  } catch (e) {
    c.textContent = 'Macro unavailable (Yahoo Finance)';
  }
}

async function fetchNews() {
  const c = el('newsFeed');
  if (!c) return;
  try {
    const res = await fetch('/api/news');
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    c.innerHTML = '';
    (data.items || []).forEach((n) => {
      const m = Math.floor((Date.now() - new Date(n.time)) / 60000);
      const ago = (m < 60 ? m + 'm' : Math.floor(m / 60) + 'h') + ' ago';
      const item = document.createElement('div');
      item.className = 'news-item';
      const title = n.url
        ? '<a href="' + n.url + '" target="_blank" rel="noopener" style="color:inherit">' + n.title + '</a>'
        : n.title;
      item.innerHTML =
        '<div class="news-time">' +
        ago +
        '</div><div class="news-title">' +
        title +
        '</div><div class="news-tags"></div>';
      const tags = item.querySelector('.news-tags');
      (n.coins || []).forEach((co) => {
        const t = document.createElement('span');
        t.className = 'news-tag tag-neu';
        t.textContent = co;
        tags.appendChild(t);
      });
      const st = document.createElement('span');
      st.className = 'news-tag ' + (n.sent === 'pos' ? 'tag-pos' : n.sent === 'neg' ? 'tag-neg' : 'tag-neu');
      st.textContent = n.sent === 'pos' ? 'Bullish' : n.sent === 'neg' ? 'Bearish' : 'Neutral';
      tags.appendChild(st);
      c.appendChild(item);
    });
  } catch (e) {
    c.textContent = 'News unavailable';
  }
}

async function fetchTimeline(sym) {
  try {
    const res = await fetch('/api/timeline?symbol=' + sym);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    timelineEvents = data.events || [];
    const c = el('causalTimeline');
    if (!c) return;
    c.innerHTML = '';
    timelineEvents.forEach((e) => {
      const item = document.createElement('div');
      item.className = 'tl-item';
      item.innerHTML = '<div class="tl-time"></div><div class="tl-icon"></div><div class="tl-text"></div>';
      item.querySelector('.tl-time').textContent = e.time;
      item.querySelector('.tl-icon').textContent = e.icon;
      item.querySelector('.tl-icon').style.cssText = 'background:' + e.col + '22;color:' + e.col;
      item.querySelector('.tl-text').textContent = e.text;
      c.appendChild(item);
    });
  } catch (e) {
    console.warn('timeline', e);
  }
}

fetchGlobalData = async function () {
  try {
    const res = await fetch('/api/market');
    if (!res.ok) throw new Error('market failed');
    const payload = await res.json();
    globalData = payload.global || {};
    window._fearGreed = payload.fearGreed;
    const g = globalData;
    if (g.total_market_cap?.usd) {
      const mcap = g.total_market_cap.usd;
      const mcapChange = g.market_cap_change_percentage_24h_usd;
      const btcDom = g.market_cap_percentage?.btc;
      const ethDom = g.market_cap_percentage?.eth;
      setText('total-mcap', mcap >= 1e12 ? '$' + (mcap / 1e12).toFixed(2) + 'T' : '$' + (mcap / 1e9).toFixed(0) + 'B');
      const mc = el('mcap-change');
      if (mc) {
        mc.textContent = fmtPct(mcapChange);
        mc.style.color = colorFor(mcapChange);
      }
      setText('btc-dom', btcDom ? btcDom.toFixed(1) + '%' : '—');
      const altStr = 100 - btcDom - ethDom;
      setText('alt-str', altStr.toFixed(1) + '%');
      const altEl = el('alt-trend');
      if (altEl) {
        altEl.textContent = altStr > 35 ? '▲ Strong' : altStr > 25 ? '~ Moderate' : '▼ Weak';
        altEl.style.color = altStr > 35 ? 'var(--green)' : altStr > 25 ? 'var(--amber)' : 'var(--red)';
      }
    }
    if (payload.btc?.price) {
      if (el('btc-price')) el('btc-price').textContent = '$' + payload.btc.price.toLocaleString('en-US', { maximumFractionDigits: 0 });
      const btcCh = el('btc-change');
      if (btcCh && payload.btc.change24h != null) {
        btcCh.textContent = fmtPct(payload.btc.change24h);
        btcCh.style.color = colorFor(payload.btc.change24h);
      }
    }
    if (payload.fearGreed) {
      const fgEl = el('fg-val');
      if (fgEl) {
        fgEl.textContent = payload.fearGreed.value;
        fgEl.style.color = payload.fearGreed.value >= 60 ? 'var(--green)' : payload.fearGreed.value >= 40 ? 'var(--amber)' : 'var(--red)';
      }
      setText('fg-label', payload.fearGreed.classification);
      computeMarketStress(payload.fearGreed.value);
    }
    el('lastUpdate').textContent = 'Updated ' + new Date().toLocaleTimeString();
    fetchRegime();
  } catch (e) {
    console.warn('market', e);
  }
};

const _selectCoin = selectCoin;
selectCoin = function (sym) {
  _selectCoin(sym);
  fetchScenarios(sym);
  fetchTimeline(sym);
};

generateAIAnalysis = async function (sym) {
  const bodyEl = el('aiAnalysis');
  if (bodyEl) bodyEl.textContent = 'Analyzing from live data...';
  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'analysis',
        symbol: sym,
        coinData: { ...(marketData[sym] || {}), name: COINS[sym]?.name || sym },
        marketContext: { fearGreed: window._fearGreed, btcDom: globalData.market_cap_percentage?.btc },
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    renderAnalysisText(data.text, bodyEl);
    if (data.confidence) {
      setText('confPct', data.confidence + '%');
      if (el('confFill')) el('confFill').style.width = data.confidence + '%';
    }
  } catch (e) {
    if (bodyEl) bodyEl.textContent = 'AI unavailable — configure ANTHROPIC_API_KEY on Railway.';
  }
};

generateDebate = async function (sym) {
  const bullEl = el('bullCase');
  const bearEl = el('bearCase');
  const concEl = el('debateConclusion');
  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'debate', symbol: sym, coinData: marketData[sym] || {}, marketContext: { fearGreed: window._fearGreed } }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    const t = data.text || '';
    if (bullEl) bullEl.textContent = t.match(/BULL:\s*(.+?)(?=BEAR:|$)/s)?.[1]?.trim() || '—';
    if (bearEl) bearEl.textContent = t.match(/BEAR:\s*(.+?)(?=VERDICT:|$)/s)?.[1]?.trim() || '—';
    if (concEl) concEl.innerHTML = '<span style="color:var(--cyan);font-weight:600">Verdict: </span>' + (t.match(/VERDICT:\s*(.+?)$/s)?.[1]?.trim() || '—');
  } catch (e) {
    if (bullEl) bullEl.textContent = 'Configure ANTHROPIC_API_KEY.';
    if (bearEl) bearEl.textContent = '—';
    if (concEl) concEl.textContent = 'Verdict: —';
  }
};

init = async function () {
  initChart();
  await fetchGlobalData();
  await Promise.all(['BTC', 'ETH', 'SOL', 'XRP', 'AAVE'].map((s) => fetchCoinData(s)));
  await Promise.all([fetchCorrelation(), fetchMacro(), fetchNews()]);
  fetchWhyMoving(selectedCoin);
  fetchScenarios(selectedCoin);
  fetchTimeline(selectedCoin);
  generateAIAnalysis(selectedCoin);
  generateDebate(selectedCoin);
  ['BTC', 'ETH', 'SOL', 'XRP', 'AAVE'].forEach((s) => checkMetricAlerts(s));
  renderAlerts();
  setInterval(fetchGlobalData, 60000);
  setInterval(() => fetchCoinData(selectedCoin), 15000);
  setInterval(() => {
    ['BTC', 'ETH', 'SOL', 'XRP', 'AAVE'].forEach((s) => {
      if (s !== selectedCoin) fetchCoinData(s);
    });
  }, 45000);
  setInterval(() => {
    checkMetricAlerts(selectedCoin);
    fetchTimeline(selectedCoin);
  }, 30000);
  setInterval(fetchNews, 300000);
  setInterval(fetchCorrelation, 300000);
  setInterval(fetchMacro, 300000);
};
