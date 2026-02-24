# -*- coding: utf-8 -*-
"""
Dashboard Template - Version Avancee avec Graphiques et Statistiques
"""

def get_enhanced_dashboard():
    """Retourne le template HTML du dashboard avance."""
    return r'''
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Scanner Crypto — Bot Trading & Arbitrage</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html { overflow-x: hidden; }
:root {
    --bg: #0a0e17; --bg2: #111827; --bg3: #1a2332; --border: #1f2937;
    --text: #f3f4f6; --text2: #9ca3af; --text3: #6b7280;
    --green: #10b981; --red: #ef4444; --blue: #3b82f6; --yellow: #f59e0b;
    --purple: #8b5cf6; --cyan: #06b6d4;
}
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; overflow-x: hidden; width: 100%; }
.app { max-width: 1600px; margin: 0 auto; padding: 20px; width: 100%; overflow-x: hidden; }

/* Tabs Navigation */
.tabs { display: flex; gap: 4px; margin-bottom: 20px; background: var(--bg2); padding: 6px; border-radius: 12px; border: 1px solid var(--border); }
.tab { padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 0.9em; color: var(--text2); transition: all 0.2s; border: none; background: transparent; }
.tab:hover { color: var(--text); background: var(--bg3); }
.tab.active { background: var(--blue); color: white; }
.tab-content { display: none; }
.tab-content.active { display: block; }

/* Header */
.header { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; background: var(--bg2); border-radius: 12px; margin-bottom: 20px; border: 1px solid var(--border); }
.header h1 { font-size: 1.5em; color: var(--blue); display: flex; align-items: center; gap: 10px; }
.header .status { display: flex; align-items: center; gap: 8px; font-size: 0.9em; color: var(--text2); }
.dot { width: 10px; height: 10px; border-radius: 50%; background: var(--green); }
.dot.scanning { background: var(--yellow); animation: pulse 1s infinite; }
@keyframes pulse { 50% { opacity: 0.5; } }
.version { background: var(--purple); color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.7em; font-weight: 700; }

/* Stats Grid */
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 20px; }
.stat { background: var(--bg2); padding: 20px; border-radius: 12px; border: 1px solid var(--border); position: relative; overflow: hidden; }
.stat::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.stat.s-blue::before { background: var(--blue); }
.stat.s-green::before { background: var(--green); }
.stat.s-red::before { background: var(--red); }
.stat.s-yellow::before { background: var(--yellow); }
.stat.s-purple::before { background: var(--purple); }
.stat.s-cyan::before { background: var(--cyan); }
.stat-label { font-size: 0.75em; color: var(--text3); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.stat-value { font-size: 1.8em; font-weight: 700; }
.stat-sub { font-size: 0.8em; color: var(--text3); margin-top: 4px; }
.stat-icon { position: absolute; right: 16px; top: 50%; transform: translateY(-50%); font-size: 2.5em; opacity: 0.1; }
.green { color: var(--green); }
.red { color: var(--red); }
.blue { color: var(--blue); }
.yellow { color: var(--yellow); }
.purple { color: var(--purple); }

/* Cards */
.card { background: var(--bg2); border-radius: 12px; border: 1px solid var(--border); margin-bottom: 20px; overflow: hidden; }
.card-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border); background: rgba(0,0,0,0.2); }
.card-header h2 { font-size: 1em; font-weight: 600; color: var(--text2); }
.badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: 600; }
.b-green { background: rgba(16,185,129,0.1); color: var(--green); }
.b-red { background: rgba(239,68,68,0.1); color: var(--red); }
.b-blue { background: rgba(59,130,246,0.1); color: var(--blue); }
.b-yellow { background: rgba(245,158,11,0.1); color: var(--yellow); }
.b-purple { background: rgba(139,92,246,0.1); color: var(--purple); }

/* Charts */
.chart-container { padding: 20px; height: 300px; position: relative; }
.chart-row { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 20px; }
.chart-row-equal { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
@media (max-width: 1000px) { .chart-row, .chart-row-equal { grid-template-columns: 1fr; } }

/* Tables */
table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
th { padding: 12px 16px; text-align: left; font-size: 0.7em; text-transform: uppercase; letter-spacing: 1px; color: var(--text3); border-bottom: 1px solid var(--border); background: rgba(0,0,0,0.2); cursor: pointer; user-select: none; }
th:hover { color: var(--blue); }
th.sorted::after { content: ' &#9660;'; }
th.sorted-asc::after { content: ' &#9650;'; }
td { padding: 12px 16px; border-bottom: 1px solid rgba(31,41,55,0.5); }
tr:hover td { background: rgba(59,130,246,0.03); }
.empty { text-align: center; padding: 40px; color: var(--text3); }

/* Table scroll wrapper */
.table-scroll { overflow-x: auto; max-width: 100%; -webkit-overflow-scrolling: touch; }

/* Mobile cards - hidden on desktop, shown on mobile */
.mobile-cards { display: none; padding: 12px; }
.pos-card { background: var(--bg3); border-radius: 10px; padding: 14px; margin-bottom: 12px; border: 1px solid var(--border); }
.pos-card:last-child { margin-bottom: 0; }
.pos-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.pos-card-symbol { font-weight: 700; font-size: 1.1em; color: var(--blue); }
.pos-card-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.85em; }
.pos-card-row:last-child { border-bottom: none; }
.pos-card-label { color: var(--text3); }
.pos-card-value { font-weight: 600; }
.pos-card-actions { margin-top: 12px; display: flex; gap: 8px; }
.pos-card-pnl { font-size: 1.2em; font-weight: 700; }

/* Progress */
.progress { width: 80px; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--red), var(--yellow), var(--green)); border-radius: 3px; }

/* Buttons */
.btn { padding: 6px 14px; border-radius: 6px; font-size: 0.8em; font-weight: 600; cursor: pointer; border: none; transition: all 0.2s; }
.btn-close { background: rgba(239,68,68,0.1); color: var(--red); border: 1px solid rgba(239,68,68,0.3); }
.btn-close:hover { background: rgba(239,68,68,0.2); }
.btn-primary { background: var(--blue); color: white; }
.btn-primary:hover { background: #2563eb; }

/* Filters */
.filters { display: flex; gap: 12px; padding: 16px 20px; background: rgba(0,0,0,0.2); border-bottom: 1px solid var(--border); flex-wrap: wrap; }
.filter-group { display: flex; align-items: center; gap: 8px; }
.filter-group label { font-size: 0.8em; color: var(--text3); }
.filter-group select, .filter-group input { background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 6px 12px; border-radius: 6px; font-size: 0.85em; }

/* Log */
.log { max-height: 300px; overflow-y: auto; }
.log-line { display: flex; gap: 12px; padding: 8px 16px; border-bottom: 1px solid rgba(31,41,55,0.3); font-size: 0.8em; }
.log-time { color: var(--text3); width: 60px; flex-shrink: 0; }
.log-level { width: 50px; flex-shrink: 0; font-weight: 600; text-align: center; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }
.l-INFO { background: rgba(59,130,246,0.1); color: var(--blue); }
.l-TRADE { background: rgba(16,185,129,0.1); color: var(--green); }
.l-WARN { background: rgba(245,158,11,0.1); color: var(--yellow); }
.l-ERROR { background: rgba(239,68,68,0.1); color: var(--red); }
.log-msg { color: var(--text2); flex: 1; }

/* Grid layouts */
.grid-2 { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
@media (max-width: 1000px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } }

/* Stats Detail Cards */
.stats-detail { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; padding: 20px; }
.detail-item { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--border); }
.detail-item:last-child { border-bottom: none; }
.detail-label { color: var(--text3); font-size: 0.9em; }
.detail-value { font-weight: 600; }

/* Quick indicators */
.indicators { display: flex; gap: 16px; padding: 12px 20px; background: rgba(0,0,0,0.2); border-top: 1px solid var(--border); font-size: 0.8em; flex-wrap: wrap; }
.ind { display: flex; align-items: center; gap: 6px; }
.ind-label { color: var(--text3); }
.ind-value { font-weight: 600; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* Animations */
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.card { animation: fadeIn 0.3s ease-out; }

/* Tooltips */
[data-tooltip] { position: relative; cursor: help; }
[data-tooltip]:hover::after { content: attr(data-tooltip); position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%); background: var(--bg3); color: var(--text); padding: 6px 12px; border-radius: 6px; font-size: 0.8em; white-space: nowrap; z-index: 100; }

/* ==================== RESPONSIVE MOBILE ==================== */
@media (max-width: 768px) {
    .app { padding: 10px; overflow-x: hidden; }
    html, body { overflow-x: hidden; width: 100%; }
    
    /* Header mobile */
    .header { flex-direction: column; align-items: flex-start; gap: 12px; padding: 12px 16px; }
    .header h1 { font-size: 1.2em; word-break: break-word; }
    .header .status { width: 100%; justify-content: space-between; flex-wrap: wrap; }
    
    /* Tabs mobile - scrollable */
    .tabs { overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; -ms-overflow-style: none; }
    .tabs::-webkit-scrollbar { display: none; }
    .tab { padding: 10px 16px; font-size: 0.8em; white-space: nowrap; flex-shrink: 0; }
    
    /* Stats mobile */
    .stats { grid-template-columns: repeat(2, 1fr); gap: 10px; }
    .stat { padding: 14px; }
    .stat-value { font-size: 1.4em; word-break: break-all; }
    .stat-icon { display: none; }
    .stat-label { font-size: 0.65em; }
    
    /* Cards mobile */
    .card { overflow: hidden; }
    .card-header { padding: 12px 14px; flex-wrap: wrap; gap: 8px; }
    .card-header h2 { font-size: 0.9em; word-break: break-word; }
    
    /* Charts mobile */
    .chart-container { padding: 12px; height: 250px; }
    .chart-row, .chart-row-equal { grid-template-columns: 1fr; gap: 16px; }
    
    /* Tables mobile - scroll horizontal */
    .table-wrapper, .card > div[style*="overflow"] { overflow-x: auto; -webkit-overflow-scrolling: touch; max-width: 100%; }
    table { min-width: 500px; font-size: 0.75em; table-layout: auto; }
    th, td { padding: 8px 10px; white-space: nowrap; }
    
    /* Filters mobile */
    .filters { flex-direction: column; gap: 10px; padding: 12px 14px; }
    .filter-group { width: 100%; justify-content: space-between; }
    .filter-group select, .filter-group input { flex: 1; }
    
    /* Progress mobile */
    .progress { width: 60px; }
    
    /* Log mobile */
    .log { max-height: 200px; }
    .log-line { padding: 6px 12px; font-size: 0.75em; }
    .log-time { width: 50px; }
    .log-level { width: 40px; font-size: 0.75em; }
    
    /* Stats detail mobile */
    .stats-detail { grid-template-columns: 1fr; padding: 14px; gap: 10px; }
    .detail-item { padding: 10px 0; font-size: 0.9em; }
    
    /* Indicators mobile */
    .indicators { padding: 10px 14px; gap: 10px; font-size: 0.75em; }
    
    /* Grid mobile */
    .grid-2, .grid-3 { grid-template-columns: 1fr; gap: 16px; }
    
    /* Badges mobile */
    .badge { padding: 3px 8px; font-size: 0.7em; }
    
    /* Buttons mobile */
    .btn { padding: 8px 12px; font-size: 0.75em; }
    
    /* Hide table on mobile, show mobile cards */
    .table-scroll { display: none; }
    .mobile-cards { display: block; }
}

@media (max-width: 480px) {
    .app { padding: 8px; }
    
    /* Stats extra small */
    .stats { grid-template-columns: 1fr 1fr; gap: 8px; }
    .stat { padding: 12px; }
    .stat-value { font-size: 1.2em; }
    .stat-sub { font-size: 0.7em; }
    
    /* Header extra small */
    .header h1 { font-size: 1em; }
    .version { font-size: 0.6em; padding: 3px 8px; }
    
    /* Tabs extra small */
    .tab { padding: 8px 12px; font-size: 0.75em; }
    
    /* Charts extra small */
    .chart-container { height: 200px; padding: 10px; }
    
    /* Log extra small */
    .log-line { flex-wrap: wrap; gap: 6px; }
    .log-time { width: auto; }
    
    /* Mobile cards extra small */
    .pos-card { padding: 12px; }
    .pos-card-header { font-size: 0.9em; }
}

/* Touch improvements */
@media (hover: none) and (pointer: coarse) {
    .tab, .btn, th { min-height: 44px; display: flex; align-items: center; justify-content: center; }
    .filter-group select, .filter-group input { min-height: 40px; }
}
</style>
</head>
<body>
<div class="app">

<!-- HEADER -->
<div class="header">
    <div>
        <h1>Scanner Crypto</h1>
        <span style="font-size:0.8em;color:var(--text3)">SHORT grandes baisses &#8226; {{ timeframe|upper }} &#8226; Paper trading &#8226; Scan #{{ scan_count }}</span>
    </div>
    <div class="status">
        <div class="dot {% if is_scanning %}scanning{% endif %}"></div>
        {% if is_scanning %}Scan en cours...{% elif bot_status == 'ACTIF' %}Actif{% elif bot_status == 'POSITION_OUVERTE' %}Position ouverte{% else %}Pause{% endif %}
        <span style="margin-left:16px;color:var(--text3)">Derniere MAJ: {{ last_update }}</span>
        <span style="margin-left:8px;color:var(--text3)">&#8226; Prochain scan ~{{ scan_interval_display|default('15 min') }}</span>
    </div>
</div>

<!-- 2 ONGLETS: Bot de trading | Bot d'arbitrage -->
<div class="tabs">
    <button class="tab active" onclick="showTab('trading')">Bot de trading</button>
    <button class="tab" onclick="showTab('arbitrage')">Bot d'arbitrage</button>
</div>

<!-- ==================== ONGLET 1: BOT DE TRADING ==================== -->
<div id="tab-trading" class="tab-content active">

<div class="card" style="margin-bottom:16px;">
    <div class="card-header">
        <h2>Etat du bot &amp; config</h2>
        <span class="badge {% if bot_status == 'ACTIF' or bot_status == 'SCAN_EN_COURS' %}b-green{% elif bot_status == 'POSITION_OUVERTE' %}b-blue{% else %}b-yellow{% endif %}">
            {% if bot_status == 'ACTIF' %}Pret a trader{% elif bot_status == 'SCAN_EN_COURS' %}Scan...{% elif bot_status == 'POSITION_OUVERTE' %}Position ouverte{% elif bot_status == 'PAUSE_DRAWDOWN' %}Pause (drawdown){% elif bot_status == 'PAUSE_3_PERTES' %}Pause (3 pertes){% else %}Pause{% endif %}
        </span>
    </div>
    <div style="padding:16px 20px;">
        <p style="color:var(--text2);margin-bottom:16px;font-size:0.9em;">{{ bot_status_reason|default('') }}</p>
        <div class="stats-detail" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;">
            <div class="detail-item"><span class="detail-label">Timeframe</span><span class="detail-value">{{ timeframe|upper }}</span></div>
            <div class="detail-item"><span class="detail-label">Stop loss</span><span class="detail-value red">+{{ stop_loss_pct|default(1) }}%</span></div>
            <div class="detail-item"><span class="detail-label">Take profit</span><span class="detail-value green">-{{ take_profit_pct|default(2) }}%</span></div>
            <div class="detail-item"><span class="detail-label">R:R</span><span class="detail-value blue">{{ rr_ratio|default(2)|round(1) }}x</span></div>
            <div class="detail-item"><span class="detail-label">Levier SHORT</span><span class="detail-value">{{ levier_display|default(10) }}x</span></div>
            <div class="detail-item"><span class="detail-label">Risque max / trade</span><span class="detail-value">{{ risk_pct_capital|default(1)|int }}% capital</span></div>
            <div class="detail-item"><span class="detail-label">Max drawdown jour</span><span class="detail-value">{{ max_daily_drawdown_pct|default(5) }}%</span></div>
            <div class="detail-item"><span class="detail-label">Intervalle scan</span><span class="detail-value">{{ scan_interval_display|default('15 min') }}</span></div>
            <div class="detail-item"><span class="detail-label">Paires scannees</span><span class="detail-value">{{ scan_pairs_display|default('20 paires') }}</span></div>
            <div class="detail-item"><span class="detail-label">Frais simules</span><span class="detail-value">0,05% / cote</span></div>
            <div class="detail-item"><span class="detail-label">Score min pour ouvrir</span><span class="detail-value">{{ min_score_to_open|default(75) }} pts</span></div>
            <div class="detail-item"><span class="detail-label">Filtre sentiment (Extreme Fear)</span><span class="detail-value">{% if sentiment_filter_enabled %}Oui{% else %}Non{% endif %}</span></div>
        </div>
    </div>
</div>

<!-- Sentiment du marché & réseaux -->
<div class="card" style="margin-bottom:16px;">
    <div class="card-header">
        <h2>Sentiment du marché & réseaux</h2>
        <span style="font-size:0.8em;color:var(--text3)">Fear & Greed, Reddit, trending, news — MAJ {{ sentiment_display.updated|default('--:--') }}</span>
    </div>
    <div style="padding:16px 20px;">
        {% if sentiment_display and (sentiment_display.fear_greed or sentiment_display.reddit or sentiment_display.trending) %}
        <div class="stats-detail" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;">
            {% if sentiment_display.fear_greed %}
            <div style="background:var(--bg3);border-radius:10px;padding:14px;border:1px solid var(--border);">
                <div style="font-size:0.7em;text-transform:uppercase;letter-spacing:1px;color:var(--text3);margin-bottom:8px;">Fear & Greed (Alternative.me)</div>
                <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
                    <span style="font-size:2em;font-weight:700;color:{% if sentiment_display.fear_greed.value <= 25 %}var(--green){% elif sentiment_display.fear_greed.value >= 75 %}var(--red){% else %}var(--yellow){% endif %}">{{ sentiment_display.fear_greed.value }}</span>
                    <span style="color:var(--text2);">{{ sentiment_display.fear_greed.classification }}</span>
                    <span class="badge {% if sentiment_display.fear_greed.signal == 'strong_buy' %}b-green{% elif sentiment_display.fear_greed.signal == 'buy' %}b-green{% elif sentiment_display.fear_greed.signal == 'strong_sell' %}b-red{% elif sentiment_display.fear_greed.signal == 'caution' %}b-yellow{% else %}b-blue{% endif %}">{{ sentiment_display.fear_greed.signal }}</span>
                </div>
                {% if sentiment_display.fear_greed.avg_7d is not none %}<div style="font-size:0.8em;color:var(--text3);margin-top:6px;">Moy. 7j: {{ "%.0f"|format(sentiment_display.fear_greed.avg_7d) }} — Tendance: {{ sentiment_display.fear_greed.trend_direction }}</div>{% endif %}
            </div>
            {% endif %}
            {% if sentiment_display.reddit %}
            <div style="background:var(--bg3);border-radius:10px;padding:14px;border:1px solid var(--border);">
                <div style="font-size:0.7em;text-transform:uppercase;letter-spacing:1px;color:var(--text3);margin-bottom:8px;">Reddit (r/cryptocurrency, r/bitcoin…)</div>
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                    <span style="font-size:1.5em;font-weight:700;color:{% if sentiment_display.reddit.sentiment_score > 20 %}var(--green){% elif sentiment_display.reddit.sentiment_score < -20 %}var(--red){% else %}var(--text2){% endif %}">{{ sentiment_display.reddit.sentiment_score }}%</span>
                    <span class="badge {% if sentiment_display.reddit.signal == 'bullish' %}b-green{% elif sentiment_display.reddit.signal == 'bearish' %}b-red{% else %}b-blue{% endif %}">{{ sentiment_display.reddit.signal }}</span>
                </div>
                <div style="font-size:0.8em;color:var(--text3);margin-top:6px;">Hausse {{ sentiment_display.reddit.bullish_percent|default(0)|round(1) }}% / Baisse {{ sentiment_display.reddit.bearish_percent|default(0)|round(1) }}% — {{ sentiment_display.reddit.total_posts|default(0) }} posts</div>
                {% if sentiment_display.reddit.top_mentions %}
                <div style="font-size:0.75em;color:var(--text3);margin-top:8px;">Mentions: {% for sym, cnt in sentiment_display.reddit.top_mentions.items() %}{% if loop.index <= 5 %}{% if loop.index > 1 %} · {% endif %}{{ sym }} ({{ cnt }}){% endif %}{% endfor %}</div>
                {% endif %}
            </div>
            {% endif %}
            {% if sentiment_display.trending %}
            <div style="background:var(--bg3);border-radius:10px;padding:14px;border:1px solid var(--border);">
                <div style="font-size:0.7em;text-transform:uppercase;letter-spacing:1px;color:var(--text3);margin-bottom:8px;">Trending (CoinGecko)</div>
                <div style="display:flex;flex-wrap:wrap;gap:8px;">
                    {% for c in sentiment_display.trending[:6] %}
                    <span class="badge b-purple" title="{{ c.name|default('') }}">{{ c.symbol|default('-') }}{% if c.rank %}#{{ c.rank }}{% endif %}</span>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            {% if sentiment_display.news %}
            <div style="background:var(--bg3);border-radius:10px;padding:14px;border:1px solid var(--border);">
                <div style="font-size:0.7em;text-transform:uppercase;letter-spacing:1px;color:var(--text3);margin-bottom:8px;">News (CryptoPanic)</div>
                <div style="font-size:0.9em;">Score {{ sentiment_display.news.score }} — 🟢 {{ sentiment_display.news.bullish }} / 🔴 {{ sentiment_display.news.bearish }} / ⚪ {{ sentiment_display.news.neutral }}</div>
            </div>
            {% endif %}
        </div>
        {% else %}
        <p style="color:var(--text3);font-size:0.9em;">Chargement du sentiment au prochain scan (Fear & Greed, Reddit, trending).</p>
        {% endif %}
    </div>
</div>

<div class="stats">
    <div class="stat s-blue">
        <div class="stat-label">Capital (paper)</div>
        <div class="stat-value blue">${{ "%.2f"|format(total_capital) }}</div>
        <div class="stat-sub">Dispo: ${{ "%.2f"|format(balance) }} — Capital de test: 100 €</div>
    </div>
    <div class="stat s-{% if total_unrealized_pnl >= 0 %}green{% else %}red{% endif %}">
        <div class="stat-label">PnL latent</div>
        <div class="stat-value {% if total_unrealized_pnl >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(total_unrealized_pnl) }}$</div>
        <div class="stat-sub">{{ positions|length }} position(s)</div>
    </div>
    <div class="stat s-{% if perf.total_pnl >= 0 %}green{% else %}red{% endif %}">
        <div class="stat-label">PnL realise</div>
        <div class="stat-value {% if perf.total_pnl >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(perf.total_pnl) }}$</div>
        <div class="stat-sub">{{ perf.winning_trades }}/{{ perf.total_trades }} gagnants</div>
    </div>
    <div class="stat s-purple">
        <div class="stat-label">Win rate</div>
        <div class="stat-value purple">{{ perf.win_rate }}%</div>
        <div class="stat-sub">{{ perf.total_trades }} trades</div>
    </div>
</div>
<div class="stats" style="margin-bottom:16px;">
    <div class="stat s-yellow">
        <div class="stat-label">Frais cumules (simules)</div>
        <div class="stat-value">{{ "%.2f"|format(total_fees_usdt|default(0)) }}$</div>
        <div class="stat-sub">0,05% par cote (open/close)</div>
    </div>
    <div class="stat s-{% if (daily_drawdown_pct|default(0)) >= 5 %}red{% else %}cyan{% endif %}">
        <div class="stat-label">Drawdown jour</div>
        <div class="stat-value">{{ "%.1f"|format(daily_drawdown_pct|default(0)) }}%</div>
        <div class="stat-sub">Pause si &gt; 5%</div>
    </div>
    <div class="stat s-blue">
        <div class="stat-label">Risque / trade</div>
        <div class="stat-value">{{ risk_pct_capital|default(1)|int }}%</div>
        <div class="stat-sub">Du capital max par position</div>
    </div>
</div>

<div class="card">
    <div class="card-header">
        <h2>Meilleures opportunites SHORT (ranking par pts)</h2>
        <span style="font-size:0.8em;color:var(--text3)">{{ opportunities|length }} signaux — meilleur en tete, le bot ouvre la #1 si dispo</span>
    </div>
    {% if opportunities %}
    <div class="table-scroll">
        <table>
            <thead><tr>
                <th>#</th><th>Paire</th><th>Score</th><th>RSI</th><th>Vol</th><th>15m</th><th>1h</th>
                <th>Prix</th><th>SL</th><th>TP</th><th>R:R</th><th>Spread%</th><th>ATR%</th>
            </tr></thead>
            <tbody>
            {% for opp in opportunities[:20] %}
            <tr>
                <td style="font-weight:700;color:var(--text3)">{{ loop.index }}</td>
                <td style="font-weight:700;color:var(--blue)">{{ opp.symbol|default(opp.pair) }}</td>
                <td style="font-weight:700;color:{% if opp.score >= 80 %}var(--green){% elif opp.score >= 60 %}var(--yellow){% else %}var(--text2){% endif %}">{{ opp.score|default(0) }} pts</td>
                <td>{{ opp.rsi|default('-') }}</td>
                <td>{{ opp.volume_ratio|default('-') }}x</td>
                <td><span class="badge {% if opp.momentum_15m == 'BEARISH' %}b-red{% else %}b-yellow{% endif %}">{{ opp.momentum_15m|default('-') }}</span></td>
                <td><span class="badge {% if opp.momentum_1h == 'BEARISH' %}b-red{% else %}b-yellow{% endif %}">{{ opp.momentum_1h|default('-') }}</span></td>
                <td>${{ "%.4f"|format(opp.price|default(0)) }}</td>
                <td style="font-size:0.85em;color:var(--red)">${{ "%.4f"|format(opp.stop_loss|default(0)) }}</td>
                <td style="font-size:0.85em;color:var(--green)">${{ "%.4f"|format(opp.take_profit|default(0)) }}</td>
                <td style="color:var(--blue)">{{ opp.rr_ratio|default('-') }}x</td>
                <td style="font-size:0.85em">{{ opp.spread_pct|default('-') }}%</td>
                <td style="font-size:0.85em">{{ opp.atr_pct|default('-') }}%</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    <div style="padding:12px 20px;background:rgba(0,0,0,0.2);border-top:1px solid var(--border);font-size:0.8em;color:var(--text3)">
        <strong>Score:</strong> RSI bas + volume eleve + 15m/1h baissiers + spread faible + ATR modere (max 100 pts). Le bot ouvre un SHORT sur la 1re opportunite si aucune position ouverte.
    </div>
    {% else %}
    <div class="empty">Aucune opportunite SHORT pour l'instant. Prochain scan dans {{ scan_interval_display|default('15 min') }}.</div>
    {% endif %}
</div>

<div class="card">
        <span class="badge b-blue">PAPER</span>
    </div>
    {% if positions %}
    <div class="table-scroll">
        <table>
            <thead><tr>
                <th>Paire</th><th>Type</th><th>Entree</th><th>Actuel</th><th>Marge</th>
                <th>PnL</th><th>SL / TP</th><th>Progression</th><th>Action</th>
            </tr></thead>
            <tbody>
            {% for p in positions %}
            <tr>
                <td style="font-weight:700;color:var(--blue)">{{ p.symbol }}</td>
                <td><span class="badge {% if p.direction == 'LONG' %}b-green{% else %}b-red{% endif %}">{{ p.direction }}{% if p.leverage and p.leverage != 1 %} {{ p.leverage|int }}x{% endif %}</span></td>
                <td>${{ "%.4f"|format(p.entry) }}</td>
                <td style="font-weight:600">${{ "%.4f"|format(p.current) }}</td>
                <td>${{ "%.0f"|format(p.amount) }}</td>
                <td class="{% if p.pnl_percent >= 0 %}green{% else %}red{% endif %}" style="font-weight:700">
                    {{ "%+.2f"|format(p.pnl_percent) }}% ({{ "%+.2f"|format(p.pnl_value) }}$)
                </td>
                <td style="font-size:0.85em;color:var(--text3)">
                    <span class="red">{{ "%.4f"|format(p.sl) }}</span> / <span class="green">{{ "%.4f"|format(p.tp) }}</span>
                </td>
                <td>
                    <div style="display:flex;align-items:center;gap:8px;">
                        <div class="progress"><div class="progress-fill" style="width:{{ [0,[100,p.progress]|min]|max }}%"></div></div>
                        <span style="font-size:0.8em;color:var(--text3)">{{ "%.0f"|format(p.progress) }}%</span>
                    </div>
                </td>
                <td><button class="btn btn-close" onclick="closePos('{{ p.symbol }}')">Fermer</button></td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="empty">Aucune position ouverte</div>
    {% endif %}
</div>

<div class="card">
    <div class="card-header">
        <h2>Historique du bot trading</h2>
        <span style="font-size:0.8em;color:var(--text3)">Scans, signaux, ouvertures/fermetures — {{ bot_log|length }} evenements</span>
    </div>
    <div class="log">
        {% if bot_log %}
        {% for entry in bot_log %}
        <div class="log-line">
            <span class="log-time">{{ entry.time }}</span>
            <span class="log-level l-{{ entry.level }}">{{ entry.level }}</span>
            <span class="log-msg">{{ entry.msg }}</span>
        </div>
        {% endfor %}
        {% else %}
        <div class="empty">En attente du premier scan...</div>
        {% endif %}
    </div>
</div>

<div class="card">
    <div class="card-header">
        <h2>Historique des trades fermes (bot trading)</h2>
        <span style="font-size:0.8em;color:var(--text3)">{{ history|length }} trades</span>
    </div>
    {% if history %}
    <div class="table-scroll">
        <table>
            <thead><tr>
                <th>Date / Heure</th><th>Paire</th><th>Type</th><th>Entree</th><th>Sortie</th>
                <th>Montant</th><th>PnL</th><th>Duree</th><th>Raison</th>
            </tr></thead>
            <tbody>
            {% for h in history[:30] %}
            <tr>
                <td style="color:var(--text3);font-size:0.85em">{{ h.time }}</td>
                <td style="font-weight:600;color:var(--blue)">{{ h.symbol }}</td>
                <td><span class="badge {% if h.direction == 'LONG' %}b-green{% else %}b-red{% endif %}">{{ h.direction }}</span></td>
                <td>${{ "%.4f"|format(h.entry_price) }}</td>
                <td>${{ "%.4f"|format(h.exit_price) }}</td>
                <td>${{ "%.0f"|format(h.amount) }}</td>
                <td class="{% if h.pnl >= 0 %}green{% else %}red{% endif %}" style="font-weight:600">{{ "%+.2f"|format(h.pnl) }}$</td>
                <td style="font-size:0.85em;color:var(--text3)">{{ h.duration }}</td>
                <td style="font-size:0.85em;color:var(--text3)">{{ h.exit_reason }}</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="empty">Aucun trade ferme pour l'instant.</div>
    {% endif %}
</div>

</div>

<!-- ==================== ONGLET 2: BOT D'ARBITRAGE ==================== -->
<div id="tab-arbitrage" class="tab-content" style="display:none">
    <div class="stats" style="margin-bottom:20px;">
        <div class="stat s-cyan">
            <div class="stat-label">Capital paper (bot arbitrage)</div>
            <div class="stat-value">{{ "%.2f"|format(arbitrage_paper_balance|default(100)) }} €</div>
            <div class="stat-sub">Initial: 100 € — gains simulés sur chaque opportunité</div>
        </div>
        <div class="stat s-blue">
            <div class="stat-label">Trades paper simulés</div>
            <div class="stat-value">{{ arbitrage_paper_trades|default([])|length }}</div>
            <div class="stat-sub">Dernières opérations d'arbitrage simulées</div>
        </div>
    </div>
    <div class="card" style="margin-bottom:20px;">
        <div class="card-header">
            <h2>Config &amp; état du bot arbitrage</h2>
            <span class="badge b-cyan">PAPER</span>
        </div>
        <div style="padding:16px 20px;">
            <div class="stats-detail" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;">
                <div class="detail-item"><span class="detail-label">Symbole surveillé</span><span class="detail-value">{{ arbitrage_symbol|default('BTC/USDT') }}</span></div>
                <div class="detail-item"><span class="detail-label">Seuil spread (min)</span><span class="detail-value">{{ arbitrage_threshold_pct|default('0.3') }}%</span></div>
                <div class="detail-item"><span class="detail-label">Intervalle scan</span><span class="detail-value">{{ arbitrage_poll_sec|default('45') }} s</span></div>
                <div class="detail-item"><span class="detail-label">Exchanges</span><span class="detail-value">Binance, KuCoin, Bybit</span></div>
                <div class="detail-item"><span class="detail-label">Mode</span><span class="detail-value">Paper (simulation)</span></div>
            </div>
            <p style="margin-top:12px;font-size:0.85em;color:var(--text3);">Les logs ci-dessous indiquent chaque scan et les opportunités détectées. En paper, chaque opportunité ajoute un gain simulé au capital ci-dessus.</p>
        </div>
    </div>
    <div class="card" style="margin-bottom:20px;">
        <div style="padding:20px;color:var(--text2);line-height:1.6;">
            <p><strong>Principe :</strong> le bot compare les prix d'un meme actif (ex. ETH/USDT) sur plusieurs exchanges (Binance, KuCoin, etc.). Quand l'ecart de prix (spread) depasse un seuil (ex. 0,5 %), il y a une opportunite d'arbitrage : <em>acheter la ou c'est le moins cher, vendre la ou c'est le plus cher</em>.</p>
            <p><strong>Rentabilite :</strong> le seuil doit etre superieur aux frais des deux cotes pour degager un gain net. En mode paper trading, le bot simule ces operations avec un capital de <strong>100 €</strong> (fichier <code>paper_arbitrage_wallet.json</code>).</p>
            <p><strong>Lancement :</strong> le bot d'arbitrage tourne avec l'app (<code>python run.py</code>). Les logs ci-dessous s'affichent en temps reel.</p>
        </div>
    </div>
    {% if arbitrage_paper_trades %}
    <div class="card" style="margin-bottom:20px;">
        <div class="card-header">
            <h2>Historique des trades paper (bot arbitrage)</h2>
            <span style="font-size:0.8em;color:var(--text3)">{{ arbitrage_paper_trades|length }} operations</span>
        </div>
        <div style="padding:16px;overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:0.85em;">
                <thead>
                    <tr style="color:var(--text3);border-bottom:1px solid var(--border);">
                        <th style="text-align:left;padding:8px;">Heure</th>
                        <th style="text-align:left;padding:8px;">Achat</th>
                        <th style="text-align:left;padding:8px;">Vente</th>
                        <th style="text-align:right;padding:8px;">Spread %</th>
                        <th style="text-align:right;padding:8px;">Profit €</th>
                        <th style="text-align:right;padding:8px;">Solde</th>
                    </tr>
                </thead>
                <tbody>
                {% for t in (arbitrage_paper_trades|default([]))[-15:]|reverse %}
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:8px;">{{ t.time }}</td>
                        <td style="padding:8px;">{{ t.buy_ex }}</td>
                        <td style="padding:8px;">{{ t.sell_ex }}</td>
                        <td style="text-align:right;padding:8px;">{{ t.spread_pct }}%</td>
                        <td style="text-align:right;padding:8px;color:var(--green);">+{{ t.profit_usdt }}</td>
                        <td style="text-align:right;padding:8px;">{{ t.balance_after }} €</td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}
    <div class="card">
        <div class="card-header">
            <h2>Historique du bot arbitrage</h2>
            <span style="font-size:0.8em;color:var(--text3)">Scans, opportunites, gains paper — {{ arbitrage_logs|length }} evenements</span>
        </div>
        <div class="log">
            {% if arbitrage_logs %}
                {% for log in arbitrage_logs|reverse %}
                <div class="log-line">
                    <span class="log-time">{{ log.time }}</span>
                    <span class="log-level l-{{ log.level|upper }}">{{ log.level }}</span>
                    <span class="log-msg">{{ log.msg }}</span>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty">En attente du premier scan arbitrage...</div>
            {% endif %}
        </div>
    </div>
</div>

<!-- FOOTER -->
<div style="text-align:center;padding:20px;color:var(--text3);font-size:0.8em;">
    Bot SHORT grandes baisses + Bot arbitrage &#8226; Paper trading &#8226; Rafraichir la page pour mettre a jour
</div>

</div>

<script>
function showTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(tc => {
        tc.classList.remove('active');
        tc.style.display = 'none';
    });
    var btn = document.querySelector('[onclick="showTab(\'' + tabId + '\')"]');
    if (btn) btn.classList.add('active');
    var tabContent = document.getElementById('tab-' + tabId);
    if (tabContent) {
        tabContent.classList.add('active');
        tabContent.style.display = 'block';
    }
}

function closePos(symbol) {
    if (confirm('Fermer la position ' + symbol + ' ?')) {
        fetch('/api/close/' + symbol, {method: 'POST'})
            .then(r => r.json())
            .then(d => {
                if(d.success) { alert('Position fermee.'); location.reload(); }
                else { alert('Erreur: ' + (d.error || 'Echec')); }
            })
            .catch(err => alert('Erreur reseau: ' + err));
    }
}
</script>
</body>
</html>
'''
