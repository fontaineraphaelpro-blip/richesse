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
<title>&#9889; Crypto Trading Bot Pro</title>
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
        <h1>&#9889; Crypto Trading Bot <span class="version">PRO v2.1</span></h1>
        <span style="font-size:0.8em;color:var(--text3)">Swing Trading &#8226; {{ timeframe|upper }} &#8226; Auto-buy &#8805; {{ min_score }}</span>
    </div>
    <div class="status">
        <div class="dot {% if is_scanning %}scanning{% endif %}"></div>
        {% if is_scanning %}Scanning...{% else %}Active{% endif %}
        <span style="margin-left:16px;color:var(--text3)">Scan #{{ scan_count }} &#8226; {{ last_update }}</span>
    </div>
</div>

<!-- TABS NAVIGATION -->
<div class="tabs">
    <button class="tab active" onclick="showTab('dashboard')">&#128200; Dashboard</button>
    <button class="tab" onclick="showTab('charts')">&#128202; Graphiques</button>
    <button class="tab" onclick="showTab('stats')">&#128201; Statistiques</button>
    <button class="tab" onclick="showTab('history')">&#128220; Historique</button>
</div>

<!-- ==================== TAB: DASHBOARD ==================== -->
<div id="tab-dashboard" class="tab-content active">

<!-- STATS PRINCIPAUX -->
<div class="stats">
    <div class="stat s-blue">
        <div class="stat-label">Capital Total</div>
        <div class="stat-value blue">${{ "%.2f"|format(total_capital) }}</div>
        <div class="stat-sub">Disponible: ${{ "%.2f"|format(balance) }}</div>
        <div class="stat-icon">&#128176;</div>
    </div>
    <div class="stat s-{% if total_unrealized_pnl >= 0 %}green{% else %}red{% endif %}">
        <div class="stat-label">PnL Latent</div>
        <div class="stat-value {% if total_unrealized_pnl >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(total_unrealized_pnl) }}$</div>
        <div class="stat-sub">{{ positions|length }} position(s) active(s)</div>
        <div class="stat-icon">&#128200;</div>
    </div>
    <div class="stat s-{% if perf.total_pnl >= 0 %}green{% else %}red{% endif %}">
        <div class="stat-label">PnL Realise</div>
        <div class="stat-value {% if perf.total_pnl >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(perf.total_pnl) }}$</div>
        <div class="stat-sub">{{ perf.winning_trades }}/{{ perf.total_trades }} gagnants</div>
        <div class="stat-icon">&#10004;</div>
    </div>
    <div class="stat s-purple">
        <div class="stat-label">Win Rate</div>
        <div class="stat-value purple">{{ perf.win_rate }}%</div>
        <div class="stat-sub">{{ perf.total_trades }} trades total</div>
        <div class="stat-icon">&#127919;</div>
    </div>
    <div class="stat s-cyan">
        <div class="stat-label">Profit Factor</div>
        <div class="stat-value" style="color:var(--cyan)">{{ "%.2f"|format(stats.profit_factor) }}</div>
        <div class="stat-sub">Gains / Pertes</div>
        <div class="stat-icon">&#128178;</div>
    </div>
    <div class="stat s-yellow">
        <div class="stat-label">Max Drawdown</div>
        <div class="stat-value yellow">{{ "%.1f"|format(stats.max_drawdown) }}%</div>
        <div class="stat-sub">Perte max depuis pic</div>
        <div class="stat-icon">&#128201;</div>
    </div>
</div>

<!-- POSITIONS ACTIVES -->
<div class="card">
    <div class="card-header">
        <h2>&#128188; Positions Actives ({{ positions|length }})</h2>
        <span class="badge b-blue">PAPER TRADING</span>
    </div>
    {% if positions %}
    <div class="table-scroll">
        <table>
            <thead><tr>
                <th>Paire</th><th>Type</th><th>Entree</th><th>Actuel</th><th>Taille</th>
                <th>PnL</th><th>SL / TP</th><th>Progression</th><th>Duree</th><th>Action</th>
            </tr></thead>
            <tbody>
            {% for p in positions %}
            <tr>
                <td style="font-weight:700;color:var(--blue)">{{ p.symbol }}</td>
                <td><span class="badge {% if p.direction == 'LONG' %}b-green{% else %}b-red{% endif %}">{{ p.direction }}</span></td>
                <td>${{ "%.4f"|format(p.entry) }}</td>
                <td style="font-weight:600">${{ "%.4f"|format(p.current) }}</td>
                <td>${{ "%.0f"|format(p.amount) }}</td>
                <td class="{% if p.pnl_percent >= 0 %}green{% else %}red{% endif %}" style="font-weight:700">
                    {{ "%+.2f"|format(p.pnl_percent) }}% ({{ "%+.2f"|format(p.pnl_value) }}$)
                </td>
                <td style="font-size:0.85em;color:var(--text3)">
                    <span class="red">{{ "%.4f"|format(p.sl) }}</span> / 
                    <span class="green">{{ "%.4f"|format(p.tp) }}</span>
                </td>
                <td>
                    <div style="display:flex;align-items:center;gap:8px;">
                        <div class="progress"><div class="progress-fill" style="width:{{ [0,[100,p.progress]|min]|max }}%"></div></div>
                        <span style="font-size:0.8em;color:var(--text3)">{{ "%.0f"|format(p.progress) }}%</span>
                    </div>
                </td>
                <td style="font-size:0.85em;color:var(--text3)">{{ p.duration }}</td>
                <td><button class="btn btn-close" onclick="closePos('{{ p.symbol }}')">Fermer</button></td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    <!-- Mobile Cards View -->
    <div class="mobile-cards">
        {% for p in positions %}
        <div class="pos-card">
            <div class="pos-card-header">
                <span class="pos-card-symbol">{{ p.symbol }}</span>
                <span class="badge {% if p.direction == 'LONG' %}b-green{% else %}b-red{% endif %}">{{ p.direction }}</span>
            </div>
            <div class="pos-card-row">
                <span class="pos-card-label">PnL</span>
                <span class="pos-card-pnl {% if p.pnl_percent >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(p.pnl_percent) }}% ({{ "%+.2f"|format(p.pnl_value) }}$)</span>
            </div>
            <div class="pos-card-row">
                <span class="pos-card-label">Taille</span>
                <span class="pos-card-value">${{ "%.0f"|format(p.amount) }}</span>
            </div>
            <div class="pos-card-row">
                <span class="pos-card-label">Entree / Actuel</span>
                <span class="pos-card-value">${{ "%.4f"|format(p.entry) }} &#8594; ${{ "%.4f"|format(p.current) }}</span>
            </div>
            <div class="pos-card-row">
                <span class="pos-card-label">SL / TP</span>
                <span class="pos-card-value"><span class="red">${{ "%.4f"|format(p.sl) }}</span> / <span class="green">${{ "%.4f"|format(p.tp) }}</span></span>
            </div>
            <div class="pos-card-row">
                <span class="pos-card-label">Progression</span>
                <span class="pos-card-value">{{ "%.0f"|format(p.progress) }}%</span>
            </div>
            <div class="pos-card-actions">
                <button class="btn btn-close" style="flex:1" onclick="closePos('{{ p.symbol }}')">Fermer Position</button>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="empty">Aucune position ouverte</div>
    {% endif %}
</div>

<div class="grid-2">
    <!-- OPPORTUNITES -->
    <div class="card">
        <div class="card-header">
            <h2>&#127919; Meilleures Opportunites ({{ opportunities|length }})</h2>
            <span style="font-size:0.8em;color:var(--text3)">Score &#8805; {{ min_score }} = Auto-achat</span>
        </div>
        {% if opportunities %}
        <div class="table-scroll">
            <table>
                <thead><tr><th>Paire</th><th>Prix</th><th>Signal</th><th>Score</th><th>R/R</th><th>Volume 24h</th></tr></thead>
                <tbody>
                {% for opp in opportunities[:10] %}
                <tr>
                    <td style="font-weight:700">{{ opp.pair }}</td>
                    <td>${{ "%.4f"|format(opp.price|default(0)) }}</td>
                    <td><span class="badge {% if opp.entry_signal == 'LONG' %}b-green{% elif opp.entry_signal == 'SHORT' %}b-red{% else %}b-yellow{% endif %}">{{ opp.entry_signal|default('N/A') }}</span></td>
                    <td style="font-weight:700;color:{% if opp.score >= 80 %}var(--green){% elif opp.score >= 60 %}var(--yellow){% else %}var(--text3){% endif %}">{{ opp.score|default(0) }}</td>
                    <td style="color:var(--blue)">{{ opp.rr_ratio|default('N/A') }}{% if opp.rr_ratio %}x{% endif %}</td>
                    <td style="color:var(--text3)">${{ "%.0f"|format((opp.volume_24h|default(0)) / 1000000) }}M</td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
        <!-- Mobile Cards View -->
        <div class="mobile-cards">
            {% for opp in opportunities[:10] %}
            <div class="pos-card">
                <div class="pos-card-header">
                    <span class="pos-card-symbol">{{ opp.pair }}</span>
                    <span class="badge {% if opp.entry_signal == 'LONG' %}b-green{% elif opp.entry_signal == 'SHORT' %}b-red{% else %}b-yellow{% endif %}">{{ opp.entry_signal|default('N/A') }}</span>
                </div>
                <div class="pos-card-row">
                    <span class="pos-card-label">Score</span>
                    <span class="pos-card-value" style="color:{% if opp.score >= 80 %}var(--green){% elif opp.score >= 60 %}var(--yellow){% else %}var(--text3){% endif %};font-weight:700;font-size:1.1em">{{ opp.score|default(0) }}</span>
                </div>
                <div class="pos-card-row">
                    <span class="pos-card-label">Prix</span>
                    <span class="pos-card-value">${{ "%.4f"|format(opp.price|default(0)) }}</span>
                </div>
                <div class="pos-card-row">
                    <span class="pos-card-label">R/R</span>
                    <span class="pos-card-value" style="color:var(--blue)">{{ opp.rr_ratio|default('N/A') }}{% if opp.rr_ratio %}x{% endif %}</span>
                </div>
                <div class="pos-card-row">
                    <span class="pos-card-label">Volume 24h</span>
                    <span class="pos-card-value">${{ "%.0f"|format((opp.volume_24h|default(0)) / 1000000) }}M</span>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="empty">Aucune opportunite detectee</div>
        {% endif %}
    </div>

    <!-- MINI CHART PnL -->
    <div class="card">
        <div class="card-header">
            <h2>&#128200; Evolution PnL</h2>
            <span class="badge b-{% if perf.total_pnl >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(perf.total_pnl) }}$</span>
        </div>
        <div class="chart-container" style="height:200px;">
            <canvas id="miniPnlChart"></canvas>
        </div>
    </div>
</div>

<!-- BOT LOG -->
<div class="card">
    <div class="card-header">
        <h2>&#129302; Journal du Bot</h2>
        <span style="font-size:0.8em;color:var(--text3)">{{ bot_log|length }} evenements</span>
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
        <div class="empty">En attente d'activite...</div>
        {% endif %}
    </div>
    <!-- Quick Indicators -->
    <div class="indicators">
        <div class="ind"><span class="ind-label">Sentiment:</span><span class="ind-value">{{ mkt.sentiment }}</span></div>
        <div class="ind"><span class="ind-label">RSI moy:</span><span class="ind-value">{{ mkt.avg_rsi }}</span></div>
        <div class="ind"><span class="ind-label">Bullish:</span><span class="ind-value green">{{ mkt.total_bullish }}</span></div>
        <div class="ind"><span class="ind-label">Bearish:</span><span class="ind-value red">{{ mkt.total_bearish }}</span></div>
        <div class="ind" id="fear-greed-display"><span class="ind-label">Fear/Greed:</span><span class="ind-value" id="fg-val">--</span></div>
        <div class="ind"><span class="ind-label">Crash Protection:</span><span class="ind-value {% if crash.trading_allowed %}green{% else %}red{% endif %}">{% if crash.trading_allowed %}OK{% else %}ACTIF{% endif %}</span></div>
    </div>
</div>

</div>

<!-- ==================== TAB: CHARTS ==================== -->
<div id="tab-charts" class="tab-content">

<div class="chart-row">
    <div class="card">
        <div class="card-header">
            <h2>&#128200; Courbe d'Equite (PnL Cumule)</h2>
        </div>
        <div class="chart-container" style="height:350px;">
            <canvas id="equityChart"></canvas>
        </div>
    </div>
    <div class="card">
        <div class="card-header">
            <h2>&#127919; Repartition Win/Loss</h2>
        </div>
        <div class="chart-container" style="height:350px;">
            <canvas id="winLossChart"></canvas>
        </div>
    </div>
</div>

<div class="chart-row-equal">
    <div class="card">
        <div class="card-header">
            <h2>&#128202; PnL par Jour</h2>
        </div>
        <div class="chart-container" style="height:300px;">
            <canvas id="dailyPnlChart"></canvas>
        </div>
    </div>
    <div class="card">
        <div class="card-header">
            <h2>&#128178; Performance par Paire</h2>
        </div>
        <div class="chart-container" style="height:300px;">
            <canvas id="pairPerfChart"></canvas>
        </div>
    </div>
</div>

<div class="chart-row-equal">
    <div class="card">
        <div class="card-header">
            <h2>&#128197; Distribution des Trades par Heure</h2>
        </div>
        <div class="chart-container" style="height:250px;">
            <canvas id="hourlyChart"></canvas>
        </div>
    </div>
    <div class="card">
        <div class="card-header">
            <h2>&#127919; Performance LONG vs SHORT</h2>
        </div>
        <div class="chart-container" style="height:250px;">
            <canvas id="directionChart"></canvas>
        </div>
    </div>
</div>

</div>

<!-- ==================== TAB: STATISTICS ==================== -->
<div id="tab-stats" class="tab-content">

<div class="stats">
    <div class="stat s-green">
        <div class="stat-label">Total Gains</div>
        <div class="stat-value green">${{ "%.2f"|format(stats.total_gains) }}</div>
        <div class="stat-sub">{{ stats.winning_count }} trades</div>
    </div>
    <div class="stat s-red">
        <div class="stat-label">Total Pertes</div>
        <div class="stat-value red">${{ "%.2f"|format(stats.total_losses) }}</div>
        <div class="stat-sub">{{ stats.losing_count }} trades</div>
    </div>
    <div class="stat s-blue">
        <div class="stat-label">Gain Moyen</div>
        <div class="stat-value blue">${{ "%.2f"|format(stats.avg_win) }}</div>
        <div class="stat-sub">Par trade gagnant</div>
    </div>
    <div class="stat s-yellow">
        <div class="stat-label">Perte Moyenne</div>
        <div class="stat-value yellow">${{ "%.2f"|format(stats.avg_loss) }}</div>
        <div class="stat-sub">Par trade perdant</div>
    </div>
    <div class="stat s-purple">
        <div class="stat-label">Meilleur Trade</div>
        <div class="stat-value green">${{ "%.2f"|format(stats.best_trade) }}</div>
        <div class="stat-sub">{{ stats.best_trade_pair }}</div>
    </div>
    <div class="stat s-cyan">
        <div class="stat-label">Pire Trade</div>
        <div class="stat-value red">${{ "%.2f"|format(stats.worst_trade) }}</div>
        <div class="stat-sub">{{ stats.worst_trade_pair }}</div>
    </div>
</div>

<div class="grid-3">
    <div class="card">
        <div class="card-header"><h2>&#128201; Metriques de Risque</h2></div>
        <div class="stats-detail">
            <div class="detail-item">
                <span class="detail-label">Max Drawdown</span>
                <span class="detail-value red">{{ "%.2f"|format(stats.max_drawdown) }}%</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Profit Factor</span>
                <span class="detail-value {% if stats.profit_factor >= 1.5 %}green{% elif stats.profit_factor >= 1 %}yellow{% else %}red{% endif %}">{{ "%.2f"|format(stats.profit_factor) }}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Ratio Reward/Risk</span>
                <span class="detail-value blue">{{ "%.2f"|format(stats.avg_rr) }}x</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Expectancy</span>
                <span class="detail-value {% if stats.expectancy >= 0 %}green{% else %}red{% endif %}">${{ "%.2f"|format(stats.expectancy) }}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Consecutive Wins Max</span>
                <span class="detail-value green">{{ stats.max_consecutive_wins }}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Consecutive Losses Max</span>
                <span class="detail-value red">{{ stats.max_consecutive_losses }}</span>
            </div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header"><h2>&#128336; Metriques Temporelles</h2></div>
        <div class="stats-detail">
            <div class="detail-item">
                <span class="detail-label">Duree Moyenne Trade</span>
                <span class="detail-value">{{ stats.avg_duration }}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Trade le plus court</span>
                <span class="detail-value">{{ stats.min_duration }}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Trade le plus long</span>
                <span class="detail-value">{{ stats.max_duration }}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Trades par jour (moy)</span>
                <span class="detail-value">{{ "%.1f"|format(stats.trades_per_day) }}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Meilleure heure</span>
                <span class="detail-value green">{{ stats.best_hour }}h</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Pire heure</span>
                <span class="detail-value red">{{ stats.worst_hour }}h</span>
            </div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header"><h2>&#128176; Performance par Direction</h2></div>
        <div class="stats-detail">
            <div class="detail-item">
                <span class="detail-label">LONG - Win Rate</span>
                <span class="detail-value green">{{ "%.1f"|format(stats.long_winrate) }}%</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">LONG - PnL Total</span>
                <span class="detail-value {% if stats.long_pnl >= 0 %}green{% else %}red{% endif %}">${{ "%.2f"|format(stats.long_pnl) }}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">LONG - Trades</span>
                <span class="detail-value">{{ stats.long_count }}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">SHORT - Win Rate</span>
                <span class="detail-value red">{{ "%.1f"|format(stats.short_winrate) }}%</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">SHORT - PnL Total</span>
                <span class="detail-value {% if stats.short_pnl >= 0 %}green{% else %}red{% endif %}">${{ "%.2f"|format(stats.short_pnl) }}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">SHORT - Trades</span>
                <span class="detail-value">{{ stats.short_count }}</span>
            </div>
        </div>
    </div>
</div>

<!-- Top Pairs -->
<div class="card">
    <div class="card-header">
        <h2>&#127942; Top 10 Paires les Plus Rentables</h2>
    </div>
    <div class="table-scroll">
        <table>
            <thead><tr><th>Paire</th><th>Trades</th><th>Win Rate</th><th>PnL Total</th><th>PnL Moyen</th><th>Meilleur</th><th>Pire</th></tr></thead>
            <tbody>
            {% for pair in stats.top_pairs[:10] %}
            <tr>
                <td style="font-weight:700">{{ pair.symbol }}</td>
                <td>{{ pair.count }}</td>
                <td class="{% if pair.winrate >= 60 %}green{% elif pair.winrate >= 40 %}yellow{% else %}red{% endif %}">{{ "%.1f"|format(pair.winrate) }}%</td>
                <td class="{% if pair.pnl >= 0 %}green{% else %}red{% endif %}" style="font-weight:700">{{ "%+.2f"|format(pair.pnl) }}$</td>
                <td>{{ "%+.2f"|format(pair.avg_pnl) }}$</td>
                <td class="green">+{{ "%.2f"|format(pair.best) }}$</td>
                <td class="red">{{ "%.2f"|format(pair.worst) }}$</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
</div>

</div>

<!-- ==================== TAB: HISTORY ==================== -->
<div id="tab-history" class="tab-content">

<div class="card">
    <div class="card-header">
        <h2>&#128220; Historique Complet des Trades</h2>
        <span class="badge b-blue">{{ history|length }} trades</span>
    </div>
    
    <!-- Filters -->
    <div class="filters">
        <div class="filter-group">
            <label>Direction:</label>
            <select id="filter-direction" onchange="filterHistory()">
                <option value="">Toutes</option>
                <option value="LONG">LONG</option>
                <option value="SHORT">SHORT</option>
            </select>
        </div>
        <div class="filter-group">
            <label>Resultat:</label>
            <select id="filter-result" onchange="filterHistory()">
                <option value="">Tous</option>
                <option value="win">Gagnants</option>
                <option value="loss">Perdants</option>
            </select>
        </div>
        <div class="filter-group">
            <label>Paire:</label>
            <select id="filter-pair" onchange="filterHistory()">
                <option value="">Toutes</option>
                {% for pair in all_pairs %}
                <option value="{{ pair }}">{{ pair }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="filter-group">
            <label>Periode:</label>
            <select id="filter-period" onchange="filterHistory()">
                <option value="">Tout</option>
                <option value="today">Aujourd'hui</option>
                <option value="week">Cette semaine</option>
                <option value="month">Ce mois</option>
            </select>
        </div>
    </div>
    
    {% if history %}
    <div class="table-scroll">
        <table id="history-table">
            <thead><tr>
                <th onclick="sortTable(0)">Date</th>
                <th onclick="sortTable(1)">Paire</th>
                <th onclick="sortTable(2)">Direction</th>
                <th onclick="sortTable(3)">Entree</th>
                <th onclick="sortTable(4)">Sortie</th>
                <th onclick="sortTable(5)">Taille</th>
                <th onclick="sortTable(6)">PnL $</th>
                <th onclick="sortTable(7)">PnL %</th>
                <th onclick="sortTable(8)">Duree</th>
                <th>Raison</th>
            </tr></thead>
            <tbody>
            {% for t in history %}
            <tr data-direction="{{ t.direction|default('LONG') }}" data-result="{% if t.pnl|default(0) >= 0 %}win{% else %}loss{% endif %}" data-pair="{{ t.symbol|default('') }}" data-date="{{ t.date|default('') }}">
                <td style="color:var(--text3);font-size:0.85em">{{ t.time|default('N/A') }}</td>
                <td style="font-weight:700">{{ t.symbol|default('N/A') }}</td>
                <td><span class="badge {% if t.direction == 'LONG' %}b-green{% else %}b-red{% endif %}">{{ t.direction|default('N/A') }}</span></td>
                <td>${{ "%.4f"|format(t.entry_price|default(0)) }}</td>
                <td>${{ "%.4f"|format(t.exit_price|default(0)) }}</td>
                <td>${{ "%.0f"|format(t.amount|default(0)) }}</td>
                <td class="{% if t.pnl|default(0) >= 0 %}green{% else %}red{% endif %}" style="font-weight:700">{{ "%+.2f"|format(t.pnl|default(0)) }}$</td>
                <td class="{% if t.pnl_percent|default(0) >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(t.pnl_percent|default(0)) }}%</td>
                <td style="color:var(--text3)">{{ t.duration|default('N/A') }}</td>
                <td style="font-size:0.85em;color:var(--text3)">{{ t.exit_reason|default('N/A') }}</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="empty">Aucun trade dans l'historique</div>
    {% endif %}
</div>

</div>

<!-- FOOTER -->
<div style="text-align:center;padding:20px;color:var(--text3);font-size:0.8em;">
    Crypto Trading Bot PRO v2.1 &#8226; Tous modules actifs (ML, On-Chain, Kelly, Macro, Social, Journal AI)
</div>

</div>

<script>
// Tab switching
function showTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelector(`[onclick="showTab('${tabId}')"]`).classList.add('active');
    document.getElementById(`tab-${tabId}`).classList.add('active');
    
    // Initialize charts when switching to charts tab
    if (tabId === 'charts') initCharts();
}

// Close position
function closePos(symbol) {
    if (confirm('Fermer la position ' + symbol + ' ?')) {
        fetch('/close/' + symbol).then(r => r.json()).then(d => {
            if(d.success) location.reload();
            else alert('Erreur: ' + (d.error || 'Echec'));
        });
    }
}

// History filtering
function filterHistory() {
    const direction = document.getElementById('filter-direction').value;
    const result = document.getElementById('filter-result').value;
    const pair = document.getElementById('filter-pair').value;
    const period = document.getElementById('filter-period').value;
    
    const rows = document.querySelectorAll('#history-table tbody tr');
    rows.forEach(row => {
        let show = true;
        if (direction && row.dataset.direction !== direction) show = false;
        if (result && row.dataset.result !== result) show = false;
        if (pair && row.dataset.pair !== pair) show = false;
        // Period filtering would need date comparison
        row.style.display = show ? '' : 'none';
    });
}

// Table sorting
let sortDir = 1;
function sortTable(col) {
    const table = document.getElementById('history-table');
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    
    rows.sort((a, b) => {
        let aVal = a.cells[col].textContent;
        let bVal = b.cells[col].textContent;
        
        // Try numeric sort
        const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
        const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return (aNum - bNum) * sortDir;
        }
        return aVal.localeCompare(bVal) * sortDir;
    });
    
    sortDir *= -1;
    const tbody = table.querySelector('tbody');
    rows.forEach(row => tbody.appendChild(row));
}

// Chart colors
const chartColors = {
    green: 'rgba(16, 185, 129, 1)',
    greenBg: 'rgba(16, 185, 129, 0.2)',
    red: 'rgba(239, 68, 68, 1)',
    redBg: 'rgba(239, 68, 68, 0.2)',
    blue: 'rgba(59, 130, 246, 1)',
    blueBg: 'rgba(59, 130, 246, 0.2)',
    yellow: 'rgba(245, 158, 11, 1)',
    purple: 'rgba(139, 92, 246, 1)',
    cyan: 'rgba(6, 182, 212, 1)',
    gray: 'rgba(107, 114, 128, 1)'
};

// Charts data from server
const chartData = {{ chart_data | safe }};

// Initialize all charts
function initCharts() {
    // Equity Chart
    const equityCtx = document.getElementById('equityChart');
    if (equityCtx && !equityCtx.chart) {
        equityCtx.chart = new Chart(equityCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: chartData.equity.labels,
                datasets: [{
                    label: 'PnL Cumule',
                    data: chartData.equity.data,
                    borderColor: chartColors.blue,
                    backgroundColor: chartColors.blueBg,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#6b7280' } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#6b7280' } }
                }
            }
        });
    }
    
    // Win/Loss Donut
    const winLossCtx = document.getElementById('winLossChart');
    if (winLossCtx && !winLossCtx.chart) {
        winLossCtx.chart = new Chart(winLossCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Gagnants', 'Perdants'],
                datasets: [{
                    data: [chartData.winLoss.wins, chartData.winLoss.losses],
                    backgroundColor: [chartColors.green, chartColors.red],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#9ca3af' } }
                },
                cutout: '60%'
            }
        });
    }
    
    // Daily PnL Bar Chart
    const dailyCtx = document.getElementById('dailyPnlChart');
    if (dailyCtx && !dailyCtx.chart) {
        dailyCtx.chart = new Chart(dailyCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: chartData.daily.labels,
                datasets: [{
                    label: 'PnL Journalier',
                    data: chartData.daily.data,
                    backgroundColor: chartData.daily.data.map(v => v >= 0 ? chartColors.green : chartColors.red)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#6b7280' } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#6b7280' } }
                }
            }
        });
    }
    
    // Pair Performance
    const pairCtx = document.getElementById('pairPerfChart');
    if (pairCtx && !pairCtx.chart) {
        pairCtx.chart = new Chart(pairCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: chartData.pairs.labels,
                datasets: [{
                    label: 'PnL',
                    data: chartData.pairs.data,
                    backgroundColor: chartData.pairs.data.map(v => v >= 0 ? chartColors.green : chartColors.red)
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#6b7280' } },
                    y: { grid: { display: false }, ticks: { color: '#6b7280' } }
                }
            }
        });
    }
    
    // Hourly Distribution
    const hourlyCtx = document.getElementById('hourlyChart');
    if (hourlyCtx && !hourlyCtx.chart) {
        hourlyCtx.chart = new Chart(hourlyCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: chartData.hourly.labels,
                datasets: [{
                    label: 'Trades',
                    data: chartData.hourly.data,
                    backgroundColor: chartColors.blueBg,
                    borderColor: chartColors.blue,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#6b7280' } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#6b7280' } }
                }
            }
        });
    }
    
    // Direction Performance
    const dirCtx = document.getElementById('directionChart');
    if (dirCtx && !dirCtx.chart) {
        dirCtx.chart = new Chart(dirCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['LONG', 'SHORT'],
                datasets: [
                    {
                        label: 'Gagnants',
                        data: chartData.direction.wins,
                        backgroundColor: chartColors.green
                    },
                    {
                        label: 'Perdants',
                        data: chartData.direction.losses,
                        backgroundColor: chartColors.red
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { color: '#9ca3af' } } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#6b7280' } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#6b7280' } }
                }
            }
        });
    }
}

// Mini PnL Chart on dashboard
const miniPnlCtx = document.getElementById('miniPnlChart');
if (miniPnlCtx) {
    new Chart(miniPnlCtx.getContext('2d'), {
        type: 'line',
        data: {
            labels: chartData.equity.labels.slice(-20),
            datasets: [{
                data: chartData.equity.data.slice(-20),
                borderColor: chartData.equity.data[chartData.equity.data.length-1] >= 0 ? chartColors.green : chartColors.red,
                backgroundColor: chartData.equity.data[chartData.equity.data.length-1] >= 0 ? chartColors.greenBg : chartColors.redBg,
                fill: true,
                tension: 0.3,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: { display: false }
            }
        }
    });
}

// Fetch Fear & Greed
fetch('/api/social/fear_greed')
    .then(r => r.json())
    .then(data => {
        if(data.value) {
            const el = document.getElementById('fg-val');
            el.textContent = data.value + ' (' + data.classification + ')';
            el.style.color = data.value <= 30 ? 'var(--red)' : (data.value >= 70 ? 'var(--green)' : 'var(--yellow)');
        }
    })
    .catch(() => {});
</script>
</body>
</html>
'''
