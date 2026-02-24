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
<title>Richesse Crypto — Trading & Arbitrage</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html { overflow-x: hidden; }
:root {
    --bg: #0f1419; --bg2: #1a2332; --bg3: #243044; --border: #2d3a4d;
    --text: #e6edf3; --text2: #8b949e; --text3: #6e7681;
    --green: #3fb950; --red: #f85149; --blue: #58a6ff; --yellow: #d29922;
    --purple: #a371f7; --cyan: #39c5cf;
}
body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; line-height: 1.5; }
.app { max-width: 1200px; margin: 0 auto; padding: 24px; }

/* Tabs Navigation */
.tabs { display: flex; gap: 4px; margin-bottom: 20px; background: var(--bg2); padding: 6px; border-radius: 12px; border: 1px solid var(--border); }
.tab { padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 0.9em; color: var(--text2); transition: all 0.2s; border: none; background: transparent; }
.tab:hover { color: var(--text); background: var(--bg3); }
.tab.active { background: var(--blue); color: white; }
.tab-content { display: none; }
.tab-content.active { display: block; }

/* Header simple */
.header { padding: 20px 0 24px; border-bottom: 1px solid var(--border); margin-bottom: 24px; }
.header h1 { font-size: 1.75rem; font-weight: 700; color: var(--text); margin-bottom: 6px; }
.header .status { display: flex; align-items: center; gap: 10px; font-size: 0.9rem; color: var(--text2); }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); }
.dot.scanning { background: var(--yellow); animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%,100%{ opacity:1 } 50%{ opacity:0.4 } }
.header .meta { color: var(--text3); font-size: 0.85rem; margin-top: 4px; }

/* Stats : 4 blocs principaux */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
@media (max-width: 900px) { .stats { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 500px) { .stats { grid-template-columns: 1fr; } }
.stat { background: var(--bg2); padding: 20px; border-radius: 12px; border: 1px solid var(--border); }
.stat-label { font-size: 0.8rem; color: var(--text3); margin-bottom: 6px; }
.stat-value { font-size: 1.75rem; font-weight: 700; }
.stat-sub { font-size: 0.8rem; color: var(--text3); margin-top: 4px; }
.stat.s-blue .stat-value { color: var(--blue); }
.stat.s-green .stat-value { color: var(--green); }
.stat.s-red .stat-value { color: var(--red); }
.stat.s-purple .stat-value { color: var(--purple); }
.stat.s-yellow .stat-value { color: var(--yellow); }
.stat.s-cyan .stat-value { color: var(--cyan); }
.green { color: var(--green); }
.red { color: var(--red); }
.blue { color: var(--blue); }
.yellow { color: var(--yellow); }
.purple { color: var(--purple); }

/* Cards */
.card { background: var(--bg2); border-radius: 12px; border: 1px solid var(--border); margin-bottom: 20px; }
.card-header { padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.card-header h2 { font-size: 1rem; font-weight: 600; color: var(--text); }
.badge { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
.b-green { background: rgba(63,185,80,0.15); color: var(--green); }
.b-red { background: rgba(248,81,73,0.15); color: var(--red); }
.b-blue { background: rgba(88,166,255,0.15); color: var(--blue); }
.b-yellow { background: rgba(210,153,34,0.15); color: var(--yellow); }
.b-purple { background: rgba(163,113,247,0.15); color: var(--purple); }
.b-cyan { background: rgba(57,197,207,0.15); color: var(--cyan); }

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
    <h1>Richesse Crypto</h1>
    <div class="status">
        <div class="dot {% if is_scanning %}scanning{% endif %}"></div>
        {% if is_scanning %}Scan en cours{% elif bot_status == 'ACTIF' %}Bot actif{% elif bot_status == 'POSITION_OUVERTE' %}Position ouverte{% else %}Pause{% endif %}
        <span>·</span>
        <span>MAJ {{ last_update }}</span>
        <span>·</span>
        <span>Prochain scan {{ scan_interval_display|default('15 min') }}</span>
    </div>
    <div class="meta">Bot SHORT 15m · Paper · {{ scan_pairs_display|default('toutes paires') }}</div>
</div>

<!-- ONGLETS -->
<div class="tabs">
    <button class="tab active" onclick="showTab('trading')">Trading SHORT</button>
    <button class="tab" onclick="showTab('arbitrage')">Arbitrage</button>
</div>

<!-- ==================== ONGLET 1: BOT DE TRADING ==================== -->
<div id="tab-trading" class="tab-content active">

<div class="card" style="margin-bottom:16px;">
    <div class="card-header">
        <h2>État du bot</h2>
        <span class="badge {% if bot_status == 'ACTIF' or bot_status == 'SCAN_EN_COURS' %}b-green{% elif bot_status == 'POSITION_OUVERTE' %}b-blue{% else %}b-yellow{% endif %}">
            {% if bot_status == 'ACTIF' %}Prêt{% elif bot_status == 'SCAN_EN_COURS' %}Scan...{% elif bot_status == 'POSITION_OUVERTE' %}En position{% elif bot_status == 'PAUSE_DRAWDOWN' %}Pause DD{% elif bot_status == 'PAUSE_3_PERTES' %}Pause 3 pertes{% else %}Pause{% endif %}
        </span>
    </div>
    <div style="padding:16px 20px;">
        <p style="color:var(--text2);font-size:0.9rem;margin-bottom:12px;">{{ bot_status_reason|default('') }}</p>
        <div class="stats-detail" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;">
            <div class="detail-item"><span class="detail-label">SL / TP</span><span class="detail-value"><span class="red">+{{ stop_loss_pct|default(1) }}%</span> / <span class="green">-{{ take_profit_pct|default(2) }}%</span></span></div>
            <div class="detail-item"><span class="detail-label">Score min</span><span class="detail-value">{{ min_score_to_open|default(75) }} pts</span></div>
            <div class="detail-item"><span class="detail-label">Levier</span><span class="detail-value">{{ levier_display|default(10) }}x</span></div>
            <div class="detail-item"><span class="detail-label">Scan</span><span class="detail-value">{{ scan_interval_display|default('15 min') }}</span></div>
            <div class="detail-item"><span class="detail-label">Paires</span><span class="detail-value">{{ scan_pairs_display|default('toutes') }}</span></div>
        </div>
    </div>
</div>

<!-- Sentiment (résumé compact) -->
<div class="card" style="margin-bottom:16px;">
    <div class="card-header">
        <h2>Sentiment marché</h2>
        <span style="font-size:0.8rem;color:var(--text3)">{{ sentiment_display.updated|default('--:--') }}</span>
    </div>
    <div style="padding:16px 20px;">
        {% if sentiment_display and (sentiment_display.fear_greed or sentiment_display.reddit or sentiment_display.trending) %}
        <div style="display:flex;flex-wrap:wrap;gap:24px;align-items:center;">
            {% if sentiment_display.fear_greed %}
            <div><span style="font-size:1.5rem;font-weight:700;color:{% if sentiment_display.fear_greed.value <= 25 %}var(--green){% elif sentiment_display.fear_greed.value >= 75 %}var(--red){% else %}var(--yellow){% endif %}">{{ sentiment_display.fear_greed.value }}</span> <span style="color:var(--text2);margin-left:6px;">Fear & Greed</span></div>
            {% endif %}
            {% if sentiment_display.reddit %}
            <div><span style="font-weight:700;">{{ sentiment_display.reddit.sentiment_score }}%</span> <span style="color:var(--text2);margin-left:4px;">Reddit</span></div>
            {% endif %}
            {% if sentiment_display.trending %}
            <div style="display:flex;gap:6px;flex-wrap:wrap;">{% for c in sentiment_display.trending[:5] %}<span class="badge b-purple">{{ c.symbol|default('-') }}</span>{% endfor %}</div>
            {% endif %}
        </div>
        {% else %}
        <p style="color:var(--text3);font-size:0.9rem;">Chargement au prochain scan.</p>
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
<div class="stats" style="margin-bottom:20px;">
    <div class="stat s-yellow">
        <div class="stat-label">Frais · Drawdown · Risque</div>
        <div class="stat-value" style="font-size:1rem;">{{ "%.2f"|format(total_fees_usdt|default(0)) }} $ · {{ "%.1f"|format(daily_drawdown_pct|default(0)) }}% · {{ risk_pct_capital|default(1)|int }}%</div>
    </div>
</div>

<div class="card">
    <div class="card-header">
        <h2>Opportunités SHORT</h2>
        <span style="font-size:0.85rem;color:var(--text3)">{{ opportunities|length }} signaux</span>
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
    <div style="padding:10px 20px;border-top:1px solid var(--border);font-size:0.8rem;color:var(--text3)">Le bot ouvre un SHORT sur la 1re opportunité (score ≥ {{ min_score_to_open|default(75) }} pts) si aucune position.</div>
    {% else %}
    <div class="empty">Aucune opportunité. Prochain scan {{ scan_interval_display|default('15 min') }}.</div>
    {% endif %}
</div>

<div class="card">
    <div class="card-header">
        <h2>Positions ouvertes</h2>
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
        <h2>Journal (logs)</h2>
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
        <h2>Trades fermés</h2>
        <span style="font-size:0.85rem;color:var(--text3)">{{ history|length }} trades</span>
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
    <div class="empty">Aucun trade fermé.</div>
    {% endif %}
</div>

</div>

<!-- ONGLET ARBITRAGE -->
<div id="tab-arbitrage" class="tab-content" style="display:none">
    <div class="stats" style="margin-bottom:20px;">
        <div class="stat s-cyan">
            <div class="stat-label">Capital paper (arbitrage)</div>
            <div class="stat-value">{{ "%.2f"|format(arbitrage_paper_balance|default(100)) }} €</div>
            <div class="stat-sub">Initial 100 € · gains simulés</div>
        </div>
        <div class="stat s-blue">
            <div class="stat-label">Trades simulés</div>
            <div class="stat-value">{{ arbitrage_paper_trades|default([])|length }}</div>
        </div>
    </div>
    <div class="card" style="margin-bottom:20px;">
        <div class="card-header">
            <h2>Config arbitrage</h2>
            <span class="badge b-cyan">PAPER</span>
        </div>
        <div style="padding:16px 20px;font-size:0.9rem;color:var(--text2);">
            {{ arbitrage_symbol|default('BTC/USDT') }} · Seuil {{ arbitrage_threshold_pct|default('0.3') }}% · Scan {{ arbitrage_poll_sec|default('45') }} s · Binance, KuCoin, Bybit
        </div>
    </div>
    {% if arbitrage_paper_trades %}
    <div class="card" style="margin-bottom:20px;">
        <div class="card-header">
            <h2>Trades paper arbitrage</h2>
            <span style="font-size:0.85rem;color:var(--text3)">{{ arbitrage_paper_trades|length }} ops</span>
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
            <h2>Logs arbitrage</h2>
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
                <div class="empty">En attente du premier scan.</div>
            {% endif %}
        </div>
    </div>
</div>

<div style="text-align:center;padding:24px;color:var(--text3);font-size:0.8rem;">
    Richesse Crypto · Paper trading · Rafraîchir pour mettre à jour
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
