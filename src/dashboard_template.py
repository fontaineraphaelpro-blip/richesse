# -*- coding: utf-8 -*-
"""
Dashboard Template - Version Pro avec Graphiques et Statistiques
"""

def get_enhanced_dashboard():
    """Retourne le template HTML du dashboard avance."""
    return r'''
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0b0e13">
<link rel="manifest" crossorigin="use-credentials">
<title>Richesse Crypto — Trading Bot</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html { overflow-x: hidden; scroll-behavior: smooth; -webkit-text-size-adjust: 100%; }
:root {
    --bg: #0b0e13; --bg2: #141a23; --bg3: #1c2736; --border: #242f3f;
    --text: #e6edf3; --text2: #8b949e; --text3: #6e7681;
    --green: #3fb950; --red: #f85149; --blue: #58a6ff; --yellow: #d29922;
    --purple: #a371f7; --cyan: #39c5cf; --accent: #2563eb;
    --safe-top: env(safe-area-inset-top, 0px);
    --safe-bottom: env(safe-area-inset-bottom, 0px);
    --safe-left: env(safe-area-inset-left, 0px);
    --safe-right: env(safe-area-inset-right, 0px);
}
body { font-family: -apple-system, 'Inter', 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; min-height: 100dvh; line-height: 1.5; -webkit-font-smoothing: antialiased; }
.app { max-width: 1280px; margin: 0 auto; padding: 20px 24px; padding-top: calc(20px + var(--safe-top)); padding-bottom: calc(20px + var(--safe-bottom)); }

/* Header */
.header { display: flex; justify-content: space-between; align-items: center; padding: 16px 0 20px; border-bottom: 1px solid var(--border); margin-bottom: 20px; }
.header-left h1 { font-size: 1.5rem; font-weight: 700; color: var(--text); display: flex; align-items: center; gap: 10px; }
.header-left .subtitle { color: var(--text3); font-size: 0.82rem; margin-top: 2px; }
.header-right { display: flex; align-items: center; gap: 16px; font-size: 0.85rem; color: var(--text2); }
.status-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--green); display: inline-block; flex-shrink: 0; }
.status-dot.scanning { background: var(--yellow); animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%,100%{ opacity:1 } 50%{ opacity:0.4 } }

/* Tabs */
.tabs { display: flex; gap: 2px; margin-bottom: 24px; background: var(--bg2); padding: 4px; border-radius: 12px; border: 1px solid var(--border); overflow-x: auto; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
.tabs::-webkit-scrollbar { display: none; }
.tab { padding: 12px 24px; border-radius: 10px; cursor: pointer; font-weight: 600; font-size: 0.85em; color: var(--text2); transition: all 0.2s; border: none; background: transparent; flex: 1; text-align: center; white-space: nowrap; min-height: 44px; display: flex; align-items: center; justify-content: center; -webkit-tap-highlight-color: transparent; }
.tab:hover { color: var(--text); background: var(--bg3); }
.tab.active { background: var(--accent); color: white; box-shadow: 0 2px 8px rgba(37,99,235,0.3); }
.tab-content { display: none; }
.tab-content.active { display: block; }

/* Stats */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.stat { background: var(--bg2); padding: 18px 20px; border-radius: 12px; border: 1px solid var(--border); transition: border-color 0.2s; }
.stat:hover { border-color: var(--bg3); }
.stat-label { font-size: 0.75rem; color: var(--text3); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.stat-value { font-size: 1.6rem; font-weight: 700; }
.stat-sub { font-size: 0.78rem; color: var(--text3); margin-top: 4px; }
.stat.s-blue .stat-value { color: var(--blue); }
.stat.s-green .stat-value { color: var(--green); }
.stat.s-red .stat-value { color: var(--red); }
.stat.s-purple .stat-value { color: var(--purple); }
.stat.s-yellow .stat-value { color: var(--yellow); }
.stat.s-cyan .stat-value { color: var(--cyan); }
.green { color: var(--green); }
.red { color: var(--red); }
.blue { color: var(--blue); }

/* Cards */
.card { background: var(--bg2); border-radius: 12px; border: 1px solid var(--border); margin-bottom: 16px; overflow: hidden; animation: fadeIn 0.25s ease-out; }
.card-header { padding: 14px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }
.card-header h2 { font-size: 0.95rem; font-weight: 600; color: var(--text); }
.badge { padding: 3px 10px; border-radius: 6px; font-size: 0.72rem; font-weight: 600; white-space: nowrap; }
.b-green { background: rgba(63,185,80,0.12); color: var(--green); }
.b-red { background: rgba(248,81,73,0.12); color: var(--red); }
.b-blue { background: rgba(88,166,255,0.12); color: var(--blue); }
.b-yellow { background: rgba(210,153,34,0.12); color: var(--yellow); }
.b-purple { background: rgba(163,113,247,0.12); color: var(--purple); }
.b-cyan { background: rgba(57,197,207,0.12); color: var(--cyan); }

/* Two-column layout */
.grid-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.grid-2-1 { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }

/* Charts */
.chart-container { padding: 16px; height: 280px; position: relative; }

/* Tables */
table { width: 100%; border-collapse: collapse; font-size: 0.85em; }
th { padding: 10px 14px; text-align: left; font-size: 0.68em; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text3); border-bottom: 1px solid var(--border); background: rgba(0,0,0,0.15); position: sticky; top: 0; z-index: 2; }
td { padding: 10px 14px; border-bottom: 1px solid rgba(36,47,63,0.5); }
tr:hover td { background: rgba(37,99,235,0.03); }
.empty { text-align: center; padding: 32px; color: var(--text3); font-size: 0.9em; }
.table-scroll { overflow-x: auto; max-width: 100%; -webkit-overflow-scrolling: touch; overscroll-behavior-x: contain; }

/* Progress */
.progress { width: 72px; height: 5px; background: var(--border); border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--red), var(--yellow), var(--green)); border-radius: 3px; }

/* Buttons */
.btn { padding: 8px 16px; border-radius: 8px; font-size: 0.8em; font-weight: 600; cursor: pointer; border: none; transition: all 0.2s; min-height: 36px; -webkit-tap-highlight-color: transparent; touch-action: manipulation; }
.btn-close { background: rgba(248,81,73,0.1); color: var(--red); border: 1px solid rgba(248,81,73,0.25); }
.btn-close:hover, .btn-close:active { background: rgba(248,81,73,0.25); }
.btn-primary { background: var(--accent); color: white; }
.btn-primary:hover, .btn-primary:active { background: #1d4ed8; }

/* Log */
.log { max-height: 280px; overflow-y: auto; -webkit-overflow-scrolling: touch; }
.log-line { display: flex; gap: 8px; padding: 7px 16px; border-bottom: 1px solid rgba(36,47,63,0.3); font-size: 0.78em; align-items: flex-start; }
.log-time { color: var(--text3); width: 50px; flex-shrink: 0; font-variant-numeric: tabular-nums; }
.log-level { width: 48px; flex-shrink: 0; font-weight: 600; text-align: center; padding: 2px 4px; border-radius: 4px; font-size: 0.82em; }
.l-INFO { background: rgba(59,130,246,0.1); color: var(--blue); }
.l-TRADE { background: rgba(16,185,129,0.1); color: var(--green); }
.l-WARN { background: rgba(245,158,11,0.1); color: var(--yellow); }
.l-ERROR { background: rgba(239,68,68,0.1); color: var(--red); }
.log-msg { color: var(--text2); flex: 1; word-break: break-word; }
.log-scan-summary { background: rgba(99,102,241,0.06); border-left: 3px solid var(--blue); font-weight: 500; }

/* Detail items */
.params-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 8px; padding: 16px 20px; }
.param { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--border); }
.param:last-child { border-bottom: none; }
.param-label { color: var(--text3); font-size: 0.85em; }
.param-value { font-weight: 600; font-size: 0.9em; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* Animations */
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

/* Tooltips - disabled on touch */
@media (hover: hover) {
    [data-tooltip] { position: relative; cursor: help; }
    [data-tooltip]:hover::after { content: attr(data-tooltip); position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%); background: var(--bg3); color: var(--text); padding: 5px 10px; border-radius: 6px; font-size: 0.78em; white-space: nowrap; z-index: 100; }
}

/* Mobile position card */
.pos-card { padding: 14px 16px; border-bottom: 1px solid var(--border); }
.pos-card:last-child { border-bottom: none; }
.pos-card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.pos-card-mid { display: flex; justify-content: space-between; font-size: 0.82em; margin-bottom: 6px; }
.pos-card-progress { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.pos-card-bottom { display: flex; justify-content: space-between; align-items: center; }

/* Pull-to-refresh indicator */
.refresh-bar { position: fixed; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--accent), var(--cyan), var(--accent)); background-size: 200% 100%; animation: shimmer 1.5s ease-in-out infinite; z-index: 999; display: none; }
.refresh-bar.active { display: block; }
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }

/* ==================== TABLET (< 900px) ==================== */
@media (max-width: 900px) {
    .stats { grid-template-columns: repeat(2, 1fr); }
    .grid-2col, .grid-2-1 { grid-template-columns: 1fr; }
}

/* ==================== MOBILE (< 768px) ==================== */
@media (max-width: 768px) {
    .app { padding: 12px 12px; padding-top: calc(12px + var(--safe-top)); padding-bottom: calc(12px + var(--safe-bottom)); }
    .header { flex-direction: column; align-items: flex-start; gap: 6px; padding: 12px 0 14px; margin-bottom: 14px; }
    .header-left h1 { font-size: 1.25rem; }
    .header-right { gap: 10px; font-size: 0.78rem; flex-wrap: wrap; }
    .stats { grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 14px; }
    .stat { padding: 14px 12px; border-radius: 10px; }
    .stat-value { font-size: 1.3rem; }
    .stat-sub { font-size: 0.72rem; }
    .stat-label { font-size: 0.68rem; margin-bottom: 4px; }
    .card { border-radius: 10px; margin-bottom: 12px; }
    .card-header { padding: 12px 14px; }
    .card-header h2 { font-size: 0.88rem; }
    .chart-container { height: 200px; padding: 10px 8px; }
    table { font-size: 0.75em; }
    th { padding: 8px 10px; font-size: 0.62em; }
    td { padding: 8px 10px; white-space: nowrap; }
    .log { max-height: 220px; }
    .log-line { padding: 6px 12px; font-size: 0.72em; gap: 6px; }
    .log-time { width: 42px; font-size: 0.92em; }
    .log-level { width: 40px; font-size: 0.78em; }
    .badge { font-size: 0.68rem; padding: 2px 7px; }
    .params-grid { grid-template-columns: 1fr; padding: 12px 14px; }
    .btn { min-height: 40px; padding: 8px 14px; }
    .pos-card-bottom .btn { min-height: 36px; padding: 6px 12px; }
}

/* ==================== SMALL PHONE (< 400px) ==================== */
@media (max-width: 400px) {
    .app { padding: 8px; padding-top: calc(8px + var(--safe-top)); }
    .header-left h1 { font-size: 1.1rem; gap: 6px; }
    .header-left .subtitle { font-size: 0.72rem; }
    .header-right { font-size: 0.72rem; gap: 6px; }
    .stats { gap: 6px; }
    .stat { padding: 10px; }
    .stat-value { font-size: 1.15rem; }
    .stat-label { font-size: 0.62rem; }
    .tab { padding: 10px 14px; font-size: 0.75em; }
    .card-header { padding: 10px 12px; }
    .chart-container { height: 160px; padding: 8px 4px; }
    .pos-card { padding: 10px 12px; }
}
</style>
</head>
<body>
<div class="refresh-bar" id="refreshBar"></div>
<div class="app">

<!-- HEADER -->
<div class="header">
    <div class="header-left">
        <h1>
            <span class="status-dot {% if is_scanning %}scanning{% endif %}"></span>
            Richesse Crypto
        </h1>
        <div class="subtitle">Paper Trading · {{ scan_pairs_display|default('200 paires') }} · {{ timeframe|default('15m') }} · Sniper Mode</div>
    </div>
    <div class="header-right">
        <span>MAJ {{ last_update }}</span>
        <span>·</span>
        <span>{{ scan_interval_display|default('5 min') }}</span>
        <span>·</span>
        <span>#{{ scan_count|default(0) }}</span>
    </div>
</div>

<!-- ONGLETS -->
<div class="tabs">
    <button class="tab active" onclick="showTab('trading')">Bot Trading</button>
    <button class="tab" onclick="showTab('manual')">Trader moi-même</button>
</div>

<!-- ==================== ONGLET 1: BOT DE TRADING ==================== -->
<div id="tab-trading" class="tab-content active">

<!-- Statut + Sentiment en side by side -->
<div class="grid-2col" style="margin-bottom:16px;">
    <div class="card" style="margin-bottom:0;">
        <div class="card-header">
            <h2>État du bot</h2>
            <span class="badge {% if bot_status == 'ACTIF' or bot_status == 'SCAN_EN_COURS' %}b-green{% elif bot_status == 'POSITION_OUVERTE' %}b-blue{% else %}b-yellow{% endif %}">
                {% if bot_status == 'ACTIF' %}Prêt{% elif bot_status == 'SCAN_EN_COURS' %}Scan...{% elif bot_status == 'POSITION_OUVERTE' %}En position{% elif bot_status == 'PAUSE_DRAWDOWN' %}Pause DD{% elif bot_status == 'PAUSE_3_PERTES' %}Pause 3L{% else %}Pause{% endif %}
            </span>
        </div>
        <div style="padding:12px 16px;">
            <p style="color:var(--text2);font-size:0.85rem;margin-bottom:10px;">{{ bot_status_reason|default('') }}</p>
            <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(120px, 1fr));gap:8px;font-size:0.82rem;">
                <span><span style="color:var(--text3)">SL/TP</span> <span class="red">{{ stop_loss_pct|default(1) }}%</span>/<span class="green">{{ take_profit_pct|default(2) }}%</span></span>
                <span><span style="color:var(--text3)">Score</span> {{ min_score_to_open|default(75) }}pts</span>
                <span><span style="color:var(--text3)">Levier</span> {{ levier_display|default(10) }}x</span>
                <span><span style="color:var(--text3)">Risque</span> {{ risk_pct_capital|default(1.5) }}%</span>
                <span><span style="color:var(--text3)">DD max</span> {{ max_daily_drawdown_pct|default(5) }}%</span>
            </div>
        </div>
    </div>
    <div class="card" style="margin-bottom:0;">
        <div class="card-header">
            <h2>Sentiment</h2>
            <span style="font-size:0.78rem;color:var(--text3)">{{ (sentiment_display or {}).get('updated', '--:--') }}</span>
        </div>
        <div style="padding:12px 16px;">
            {% if sentiment_display and ((sentiment_display or {}).get('fear_greed') or (sentiment_display or {}).get('reddit') or (sentiment_display or {}).get('trending')) %}
            <div style="display:flex;flex-wrap:wrap;gap:16px;align-items:center;">
                {% if (sentiment_display or {}).get('fear_greed') %}
                <div>
                    <span style="font-size:2rem;font-weight:700;color:{% if sentiment_display.fear_greed.value <= 25 %}var(--green){% elif sentiment_display.fear_greed.value >= 75 %}var(--red){% else %}var(--yellow){% endif %}">{{ sentiment_display.fear_greed.value }}</span>
                    <div style="color:var(--text3);font-size:0.78rem;">Fear & Greed</div>
                </div>
                {% endif %}
                {% if (sentiment_display or {}).get('reddit') %}
                <div>
                    <span style="font-size:1.3rem;font-weight:700;">{{ sentiment_display.reddit.sentiment_score }}%</span>
                    <div style="color:var(--text3);font-size:0.78rem;">Reddit</div>
                </div>
                {% endif %}
                {% if (sentiment_display or {}).get('trending') %}
                <div style="display:flex;gap:4px;flex-wrap:wrap;">{% for c in sentiment_display.trending[:5] %}<span class="badge b-purple">{{ c.symbol|default('-') }}</span>{% endfor %}</div>
                {% endif %}
            </div>
            {% else %}
            <p style="color:var(--text3);font-size:0.85rem;">Chargement au prochain scan.</p>
            {% endif %}
        </div>
    </div>
</div>

<!-- KPIs -->
<div class="stats">
    <div class="stat s-blue">
        <div class="stat-label">Capital</div>
        <div class="stat-value">${{ "%.2f"|format(total_capital) }}</div>
        <div class="stat-sub">Dispo ${{ "%.2f"|format(balance) }}</div>
    </div>
    <div class="stat s-{% if perf.total_pnl >= 0 %}green{% else %}red{% endif %}">
        <div class="stat-label">PnL réalisé</div>
        <div class="stat-value">{{ "%+.2f"|format(perf.total_pnl) }}$</div>
        <div class="stat-sub">{{ perf.winning_trades }}/{{ perf.total_trades }} gagnants</div>
    </div>
    <div class="stat s-{% if total_unrealized_pnl >= 0 %}green{% else %}red{% endif %}">
        <div class="stat-label">PnL latent</div>
        <div class="stat-value">{{ "%+.2f"|format(total_unrealized_pnl) }}$</div>
        <div class="stat-sub">{{ positions|length }} position(s)</div>
    </div>
    <div class="stat s-purple">
        <div class="stat-label">Win rate</div>
        <div class="stat-value">{{ perf.win_rate }}%</div>
        <div class="stat-sub">Frais ${{ "%.2f"|format(total_fees_usdt|default(0)) }} · DD {{ "%.1f"|format(daily_drawdown_pct|default(0)) }}%</div>
    </div>
</div>

<!-- Equity + Positions side by side -->
<div class="grid-2-1">
    <div class="card" style="margin-bottom:0;">
        <div class="card-header">
            <h2>Courbe d'équité</h2>
            <span style="font-size:0.78rem;color:var(--text3)">PnL cumulé</span>
        </div>
        <div class="chart-container">
            <canvas id="equityChart"></canvas>
        </div>
    </div>
    <div class="card" style="margin-bottom:0;">
        <div class="card-header">
            <h2>Positions</h2>
            <span class="badge b-blue">{{ positions|length }}</span>
        </div>
        {% if positions %}
        <div>
            {% for p in positions %}
            <div class="pos-card">
                <div class="pos-card-top">
                    <span style="font-weight:700;color:var(--blue);font-size:1rem;">{{ p.symbol }}</span>
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span style="font-weight:700;font-size:1.1rem;" class="{% if p.pnl_percent >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(p.pnl_percent) }}%</span>
                        <span class="badge {% if p.direction == 'LONG' %}b-green{% else %}b-red{% endif %}">{{ p.direction }}{% if p.leverage and p.leverage != 1 %} {{ p.leverage|int }}x{% endif %}</span>
                    </div>
                </div>
                <div class="pos-card-mid">
                    <span style="color:var(--text3)">Entree ${{ "%.4f"|format(p.entry) }}</span>
                    <span style="color:var(--text2)">${{ "%.2f"|format(p.amount) }}</span>
                </div>
                <div class="pos-card-progress">
                    <div class="progress" style="flex:1;height:6px;"><div class="progress-fill" style="width:{{ [0,[100,p.progress]|min]|max }}%"></div></div>
                    <span style="font-size:0.75em;color:var(--text3);min-width:30px;text-align:right;">{{ "%.0f"|format(p.progress) }}%</span>
                </div>
                <div class="pos-card-bottom">
                    <span style="font-size:0.75em;color:var(--text3)"><span class="red">SL {{ "%.4f"|format(p.sl) }}</span> · <span class="green">TP {{ "%.4f"|format(p.tp) }}</span></span>
                    <button class="btn btn-close" onclick="closePos('{{ p.symbol }}')">Fermer</button>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="empty" style="padding:24px;">Aucune position ouverte</div>
        {% endif %}
    </div>
</div>

<!-- Opportunités -->
<div class="card" style="margin-top:16px;">
    <div class="card-header">
        <h2>Opportunités ({{ opportunities|length }})</h2>
        <div style="display:flex;gap:8px;align-items:center;">
            <span style="font-size:0.78rem;color:var(--text3)">Score ≥ {{ min_score_to_open|default(68) }} pour ouverture auto</span>
            <a href="/api/export/trades" class="btn btn-primary" style="text-decoration:none;font-size:0.72em;padding:4px 10px;">CSV</a>
        </div>
    </div>
    {% if opportunities %}
    <div class="table-scroll">
        <table>
            <thead><tr>
                <th>#</th><th>Dir</th><th>Type</th><th>Paire</th><th>Score</th><th>RSI</th><th>Vol</th><th>15m</th><th>1h</th>
                <th>Prix</th><th>SL</th><th>TP</th><th>R:R</th><th>Spread</th><th>ATR</th>
            </tr></thead>
            <tbody>
            {% for opp in opportunities[:20] %}
            <tr>
                <td style="font-weight:700;color:var(--text3)">{{ loop.index }}</td>
                <td><span class="badge {% if opp.entry_signal == 'LONG' %}b-green{% else %}b-red{% endif %}">{{ opp.entry_signal|default('SHORT') }}</span></td>
                <td><span class="badge {% if opp.is_signal|default(True) %}b-blue{% else %}b-yellow{% endif %}" title="{% if opp.is_signal|default(True) %}Le bot peut ouvrir{% else %}Info seulement{% endif %}">{% if opp.is_signal|default(True) %}Signal{% else %}Potentiel{% endif %}</span></td>
                <td style="font-weight:700;color:var(--blue)">{{ opp.symbol|default(opp.pair) }}</td>
                <td style="font-weight:700;color:{% if opp.score >= 80 %}var(--green){% elif opp.score >= 60 %}var(--yellow){% else %}var(--text2){% endif %}">{{ opp.score|default(0) }}</td>
                <td>{{ opp.rsi|default('-') }}</td>
                <td>{{ opp.volume_ratio|default('-') }}x</td>
                <td><span class="badge {% if opp.momentum_15m == 'BEARISH' %}b-red{% elif opp.momentum_15m == 'BULLISH' %}b-green{% else %}b-yellow{% endif %}">{{ opp.momentum_15m|default('-') }}</span></td>
                <td><span class="badge {% if opp.momentum_1h == 'BEARISH' %}b-red{% elif opp.momentum_1h == 'BULLISH' %}b-green{% else %}b-yellow{% endif %}">{{ opp.momentum_1h|default('-') }}</span></td>
                <td>${{ "%.4f"|format(opp.price|default(0)) }}</td>
                <td style="font-size:0.82em;color:var(--red)">${{ "%.4f"|format(opp.stop_loss|default(0)) }}</td>
                <td style="font-size:0.82em;color:var(--green)">${{ "%.4f"|format(opp.take_profit|default(0)) }}</td>
                <td style="color:var(--blue);font-weight:600">{{ opp.rr_ratio|default('-') }}x</td>
                <td style="font-size:0.82em">{{ opp.spread_pct|default('-') }}%</td>
                <td style="font-size:0.82em">{{ opp.atr_pct|default('-') }}%</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="empty">Aucune opportunité. Prochain scan dans {{ scan_interval_display|default('10 min') }}.</div>
    {% endif %}
</div>

<!-- Historique trades + Logs side by side -->
<div class="grid-2col">
    <div class="card" style="margin-bottom:0;">
        <div class="card-header">
            <h2>Trades fermés</h2>
            <span style="font-size:0.78rem;color:var(--text3)">{{ history|length }} trades</span>
        </div>
        {% if history %}
        <div class="table-scroll">
            <table>
                <thead><tr>
                    <th>Date</th><th>Paire</th><th>Dir</th><th>Entrée</th><th>Sortie</th>
                    <th>PnL</th><th>Raison</th>
                </tr></thead>
                <tbody>
                {% for h in history[:20] %}
                <tr>
                    <td style="color:var(--text3);font-size:0.82em">{{ h.time }}</td>
                    <td style="font-weight:600;color:var(--blue)">{{ h.symbol }}</td>
                    <td><span class="badge {% if h.direction == 'LONG' %}b-green{% else %}b-red{% endif %}">{{ h.direction }}</span></td>
                    <td>${{ "%.4f"|format(h.entry_price) }}</td>
                    <td>${{ "%.4f"|format(h.exit_price) }}</td>
                    <td class="{% if h.pnl >= 0 %}green{% else %}red{% endif %}" style="font-weight:600">{{ "%+.2f"|format(h.pnl) }}$</td>
                    <td style="font-size:0.82em;color:var(--text3)">{{ h.exit_reason }}</td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
        <div class="empty">Aucun trade fermé.</div>
        {% endif %}
    </div>
    <div class="card" style="margin-bottom:0;">
        <div class="card-header">
            <h2>Logs bot</h2>
        </div>
        <div class="log">
            {% if bot_log %}
            {% for entry in bot_log %}
            <div class="log-line{% if 'Scan #' in entry.msg %} log-scan-summary{% endif %}">
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
</div>

</div>

<!-- ==================== ONGLET 2: TRADER MOI-MÊME ==================== -->
<div id="tab-manual" class="tab-content" style="display:none">

<div class="stats" style="margin-bottom:16px;">
    <div class="stat s-blue">
        <div class="stat-label">Capital / Équité</div>
        <div class="stat-value">${{ "%.2f"|format(total_capital|default(0)) }}</div>
        <div class="stat-sub">Dispo ${{ "%.2f"|format(balance|default(0)) }}</div>
    </div>
    <div class="stat s-{% if total_unrealized_pnl >= 0 %}green{% else %}red{% endif %}">
        <div class="stat-label">PnL latent</div>
        <div class="stat-value">{{ "%+.2f"|format(total_unrealized_pnl|default(0)) }}$</div>
    </div>
    <div class="stat s-{% if perf.total_pnl >= 0 %}green{% else %}red{% endif %}">
        <div class="stat-label">PnL réalisé</div>
        <div class="stat-value">{{ "%+.2f"|format(perf.total_pnl|default(0)) }}$</div>
        <div class="stat-sub">Win rate {{ perf.win_rate|default(0) }}% · {{ perf.total_trades|default(0) }} trades</div>
    </div>
    <div class="stat s-purple">
        <div class="stat-label">Sentiment F&G</div>
        <div class="stat-value">{{ (sentiment_display or {}).get('fear_greed', {}).get('value') or '—' }}</div>
        <div class="stat-sub">{{ (sentiment_display or {}).get('fear_greed', {}).get('label') or 'Fear & Greed' }}</div>
    </div>
</div>

<div class="card" style="margin-bottom:16px;">
    <div class="card-header">
        <h2>Paramètres bot (référence)</h2>
    </div>
    <div class="params-grid">
        <div class="param"><span class="param-label">SHORT SL / TP</span><span class="param-value"><span class="red">+{{ stop_loss_pct|default(1) }}%</span> / <span class="green">-{{ take_profit_pct|default(2) }}%</span></span></div>
        <div class="param"><span class="param-label">LONG SL / TP</span><span class="param-value"><span class="red">-{{ long_stop_loss_pct|default(1) }}%</span> / <span class="green">+{{ long_take_profit_pct|default(2) }}%</span></span></div>
        <div class="param"><span class="param-label">Score min</span><span class="param-value">{{ min_score_to_open|default(68) }} pts</span></div>
        <div class="param"><span class="param-label">Scan interval</span><span class="param-value">{{ scan_interval_display|default('10 min') }}</span></div>
        <div class="param"><span class="param-label">R:R minimum</span><span class="param-value">{{ rr_ratio|default(2) }}x</span></div>
        <div class="param"><span class="param-label">Levier SHORT</span><span class="param-value">{{ levier_display|default(10) }}x</span></div>
    </div>
</div>

<div class="card">
    <div class="card-header">
        <h2>Top 10 opportunités</h2>
        <a href="/api/export/trades" class="btn btn-primary" style="text-decoration:none;font-size:0.72em;padding:4px 10px;">Export CSV</a>
    </div>
    {% if opportunities %}
    <div class="table-scroll">
        <table>
            <thead><tr>
                <th>#</th><th>Dir</th><th>Type</th><th>Paire</th><th>Score</th><th>RSI</th><th>Vol</th><th>15m</th><th>1h</th>
                <th>Prix</th><th>SL</th><th>TP</th><th>R:R</th><th>Spread</th><th>ATR</th>
            </tr></thead>
            <tbody>
            {% for opp in opportunities[:10] %}
            <tr>
                <td style="font-weight:700;color:var(--text3)">{{ loop.index }}</td>
                <td><span class="badge {% if opp.entry_signal == 'LONG' %}b-green{% else %}b-red{% endif %}">{{ opp.entry_signal|default('SHORT') }}</span></td>
                <td><span class="badge {% if opp.is_signal|default(True) %}b-blue{% else %}b-yellow{% endif %}">{% if opp.is_signal|default(True) %}Signal{% else %}Potentiel{% endif %}</span></td>
                <td style="font-weight:700;color:var(--blue)">{{ opp.symbol|default(opp.pair) }}</td>
                <td style="font-weight:700;color:{% if opp.score >= 80 %}var(--green){% elif opp.score >= 60 %}var(--yellow){% else %}var(--text2){% endif %}">{{ opp.score|default(0) }}</td>
                <td>{{ opp.rsi|default('-') }}</td>
                <td>{{ opp.volume_ratio|default('-') }}x</td>
                <td><span class="badge {% if opp.momentum_15m == 'BEARISH' %}b-red{% elif opp.momentum_15m == 'BULLISH' %}b-green{% else %}b-yellow{% endif %}">{{ opp.momentum_15m|default('-') }}</span></td>
                <td><span class="badge {% if opp.momentum_1h == 'BEARISH' %}b-red{% elif opp.momentum_1h == 'BULLISH' %}b-green{% else %}b-yellow{% endif %}">{{ opp.momentum_1h|default('-') }}</span></td>
                <td>${{ "%.4f"|format(opp.price|default(0)) }}</td>
                <td style="font-size:0.82em;color:var(--red)">${{ "%.4f"|format(opp.stop_loss|default(0)) }}</td>
                <td style="font-size:0.82em;color:var(--green)">${{ "%.4f"|format(opp.take_profit|default(0)) }}</td>
                <td style="color:var(--blue);font-weight:600">{{ opp.rr_ratio|default('-') }}x</td>
                <td style="font-size:0.82em">{{ opp.spread_pct|default('-') }}%</td>
                <td style="font-size:0.82em">{{ opp.atr_pct|default('-') }}%</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="empty">Aucune opportunité. Prochain scan dans {{ scan_interval_display|default('10 min') }}.</div>
    {% endif %}
</div>

{% if positions %}
<div class="card">
    <div class="card-header">
        <h2>Positions ouvertes</h2>
    </div>
    <div class="table-scroll">
        <table>
            <thead><tr>
                <th>Paire</th><th>Dir</th><th>Entrée</th><th>Actuel</th><th>Marge</th><th>PnL</th><th>SL / TP</th><th>Action</th>
            </tr></thead>
            <tbody>
            {% for p in positions %}
            <tr>
                <td style="font-weight:700;color:var(--blue)">{{ p.symbol }}</td>
                <td><span class="badge {% if p.direction == 'LONG' %}b-green{% else %}b-red{% endif %}">{{ p.direction }}</span></td>
                <td>${{ "%.4f"|format(p.entry) }}</td>
                <td>${{ "%.4f"|format(p.current) }}</td>
                <td>${{ "%.0f"|format(p.amount) }}</td>
                <td class="{% if p.pnl_percent >= 0 %}green{% else %}red{% endif %}" style="font-weight:700">{{ "%+.2f"|format(p.pnl_percent) }}%</td>
                <td style="font-size:0.82em"><span class="red">{{ "%.4f"|format(p.sl) }}</span> / <span class="green">{{ "%.4f"|format(p.tp) }}</span></td>
                <td><button class="btn btn-close" onclick="closePos('{{ p.symbol }}')">Fermer</button></td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endif %}

{% if history %}
<div class="card">
    <div class="card-header">
        <h2>Derniers trades fermés</h2>
        <span style="font-size:0.78rem;color:var(--text3)">{{ history|length }}</span>
    </div>
    <div class="table-scroll">
        <table>
            <thead><tr>
                <th>Date</th><th>Paire</th><th>Dir</th><th>Entrée</th><th>Sortie</th><th>PnL</th><th>Raison</th>
            </tr></thead>
            <tbody>
            {% for h in history[:15] %}
            <tr>
                <td style="font-size:0.82em;color:var(--text3)">{{ h.time }}</td>
                <td style="font-weight:600;color:var(--blue)">{{ h.symbol }}</td>
                <td><span class="badge {% if h.direction == 'LONG' %}b-green{% else %}b-red{% endif %}">{{ h.direction }}</span></td>
                <td>${{ "%.4f"|format(h.entry_price) }}</td>
                <td>${{ "%.4f"|format(h.exit_price) }}</td>
                <td class="{% if h.pnl >= 0 %}green{% else %}red{% endif %}" style="font-weight:600">{{ "%+.2f"|format(h.pnl) }}$</td>
                <td style="font-size:0.82em;color:var(--text3)">{{ h.exit_reason }}</td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endif %}

<div class="card">
    <div class="card-header">
        <h2>Dernier scan</h2>
    </div>
    <div class="log" style="max-height:120px;">
        {% if bot_log %}
        {% for entry in bot_log[-5:]|reverse %}
        <div class="log-line">
            <span class="log-time">{{ entry.time }}</span>
            <span class="log-level l-{{ entry.level }}">{{ entry.level }}</span>
            <span class="log-msg">{{ entry.msg }}</span>
        </div>
        {% endfor %}
        {% else %}
        <div class="empty">En attente du premier scan.</div>
        {% endif %}
    </div>
</div>

</div>

<div style="text-align:center;padding:20px;color:var(--text3);font-size:0.75rem;">
    Richesse Crypto · Paper Trading
</div>

</div>

<script>
function showTab(tabId) {
    document.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
    document.querySelectorAll('.tab-content').forEach(function(tc) {
        tc.classList.remove('active');
        tc.style.display = 'none';
    });
    var btn = document.querySelector('[onclick="showTab(\'' + tabId + '\')"]');
    if (btn) btn.classList.add('active');
    var el = document.getElementById('tab-' + tabId);
    if (el) { el.classList.add('active'); el.style.display = 'block'; }
    try { localStorage.setItem('activeTab', tabId); } catch(e) {}
}

(function() {
    try {
        var saved = localStorage.getItem('activeTab');
        if (saved) showTab(saved);
    } catch(e) {}
})();

function closePos(symbol) {
    if (confirm('Fermer la position ' + symbol + ' ?')) {
        fetch('/api/close/' + symbol, {method: 'POST'})
            .then(function(r) { return r.json(); })
            .then(function(d) {
                if(d.success) { location.reload(); }
                else { alert('Erreur: ' + (d.error || 'Echec')); }
            })
            .catch(function(err) { alert('Erreur: ' + err); });
    }
}

(function() {
    var chartData = {{ chart_data|safe }};
    var el = document.getElementById('equityChart');
    if (el && chartData && chartData.equity) {
        var isMobile = window.innerWidth < 768;
        new Chart(el, {
            type: 'line',
            data: {
                labels: chartData.equity.labels,
                datasets: [{
                    label: 'Equite ($)',
                    data: chartData.equity.data,
                    borderColor: '#58a6ff',
                    backgroundColor: 'rgba(88,166,255,0.08)',
                    fill: true,
                    tension: 0.3,
                    borderWidth: isMobile ? 1.5 : 2,
                    pointRadius: 0,
                    pointHitRadius: isMobile ? 20 : 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'nearest', intersect: false },
                plugins: { legend: { display: false },
                    tooltip: { titleFont: { size: isMobile ? 11 : 13 }, bodyFont: { size: isMobile ? 11 : 13 }, padding: isMobile ? 8 : 6 }
                },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#6e7681', maxTicksLimit: isMobile ? 5 : 10, font: { size: isMobile ? 9 : 11 } } },
                    y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#6e7681', font: { size: isMobile ? 9 : 11 }, maxTicksLimit: isMobile ? 5 : 8 } }
                }
            }
        });
    }
})();

var refreshInterval = 60000;
function doRefresh() {
    var bar = document.getElementById('refreshBar');
    if (bar) bar.classList.add('active');
    setTimeout(function() { location.reload(); }, 300);
}
setInterval(doRefresh, refreshInterval);

if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        var scrollY = 0;
        window.addEventListener('scroll', function() { scrollY = window.scrollY; });
    });
}
</script>
</body>
</html>
'''
