# -*- coding: utf-8 -*-
"""Interface Setup Sniper — claire, compréhensible, temps réel."""

def get_minimal_dashboard_html():
    return r"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Setup Sniper — Bot Day Trading</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #0a0e14;
  --bg-card: #12171f;
  --bg-hover: #1a2029;
  --border: #1e2633;
  --text: #e6edf3;
  --text-muted: #8b949e;
  --accent: #58a6ff;
  --accent-dim: #388bfd66;
  --green: #3fb950;
  --green-dim: #3fb95044;
  --red: #f85149;
  --red-dim: #f8514944;
  --yellow: #d29922;
  --purple: #a371f7;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 16px;
  background: var(--bg);
  color: var(--text);
  font-family: 'Outfit', system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}
h1, h2, h3 { font-family: 'Outfit', sans-serif; margin: 0; font-weight: 600; }
h1 { font-size: 1.5rem; letter-spacing: -0.02em; }
h2 { font-size: 0.95rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px; }
.mono { font-family: 'JetBrains Mono', monospace; }

/* Layout */
.container { max-width: 1200px; margin: 0 auto; }
.grid { display: grid; gap: 16px; }
@media (min-width: 900px) {
  .grid-main { grid-template-columns: 1fr 340px; }
  .grid-stats { grid-template-columns: repeat(4, 1fr); }
}

/* Header */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}
.header-left { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
}
.status-badge.scanning { background: var(--yellow); color: #000; }
.status-badge.idle { background: var(--green-dim); color: var(--green); }
.status-badge .pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}
.status-badge.scanning .pulse { animation: pulse 1s infinite; }
@keyframes pulse { 50% { opacity: 0.4; } }
.header-meta { font-size: 0.85rem; color: var(--text-muted); }
.header-meta span { margin-right: 12px; }

/* Cards */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  overflow: hidden;
}
.card-title { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 8px; }
.card-value { font-size: 1.25rem; font-weight: 600; }
.card-value.green { color: var(--green); }
.card-value.red { color: var(--red); }

/* Strategy banner */
.strategy-banner {
  background: linear-gradient(135deg, var(--accent-dim) 0%, transparent 100%);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 20px;
  font-size: 0.9rem;
  color: var(--text-muted);
}
.strategy-banner strong { color: var(--text); }

/* Activity feed */
.activity-feed {
  max-height: 280px;
  overflow-y: auto;
  font-size: 0.85rem;
}
.activity-line {
  display: flex;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  margin-bottom: 2px;
  align-items: flex-start;
}
.activity-line:hover { background: var(--bg-hover); }
.activity-time { color: var(--text-muted); font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; min-width: 64px; }
.activity-msg { flex: 1; word-break: break-word; }
.activity-line.level-INFO .activity-msg { color: var(--text); }
.activity-line.level-TRADE .activity-msg { color: var(--green); }
.activity-line.level-WARN .activity-msg { color: var(--yellow); }
.activity-line.level-ERROR .activity-msg { color: var(--red); }

/* Sniper stats */
.sniper-stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.sniper-stat {
  background: var(--bg-hover);
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
}
.sniper-stat .num { font-weight: 600; color: var(--accent); }
.sniper-stat .label { color: var(--text-muted); margin-left: 4px; }

/* Tables */
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); }
th { color: var(--text-muted); font-weight: 500; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--bg-hover); }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.badge-long { background: var(--green-dim); color: var(--green); }
.badge-short { background: var(--red-dim); color: var(--red); }
.score { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--accent); }
.progress-bar {
  height: 6px;
  background: var(--bg-hover);
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}
.progress-fill.green { background: var(--green); }
.progress-fill.red { background: var(--red); }

/* Buttons */
button {
  background: var(--accent);
  color: #fff;
  border: none;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
}
button:hover { opacity: 0.9; }
button:active { opacity: 0.8; }
button.secondary { background: var(--bg-hover); color: var(--text); }

/* Empty state */
.empty { color: var(--text-muted); padding: 16px; text-align: center; font-size: 0.9rem; }
.block-reason { margin-bottom: 12px; padding: 10px; background: var(--red-dim); border-radius: 8px; color: var(--red); font-size: 0.85rem; }

/* Refresh indicator */
.refresh-indicator {
  position: fixed;
  bottom: 12px;
  right: 12px;
  font-size: 0.75rem;
  color: var(--text-muted);
}
</style>
</head>
<body>
<div class="container">
  <header class="header">
    <div class="header-left">
      <h1>Setup Sniper</h1>
      <div class="status-badge {% if is_scanning %}scanning{% else %}idle{% endif %}" id="scanStatus">
        <span class="pulse"></span>
        {% if is_scanning %}Scan en cours...{% else %}Actif{% endif %}
      </div>
      <div class="header-meta">
        <span>Scan #<span id="scanCount">{{ scan_count }}</span></span>
        <span>Dernière MAJ: <span id="lastUpdate">{{ last_update or '-' }}</span></span>
      </div>
    </div>
    <button onclick="resetWallet()" class="secondary" style="font-size:0.8rem;padding:6px 10px">Réinitialiser (100 USDT)</button>
  </header>

  <div class="strategy-banner">
    <strong>Stratégie:</strong> Multi-filtre (trend, pullback, volatility, momentum, volume, anti-fake, force relative, BTC). 
    Score &ge; {{ min_score }}/10 pour passer. Top 3 setups (LONG + SHORT). Exécution auto si conditions remplies.
  </div>

  <div class="grid grid-main">
    <div>
      <!-- Stats principales -->
      <div class="grid grid-stats" style="grid-template-columns: repeat(2, 1fr); margin-bottom: 16px;">
        <div class="card">
          <div class="card-title">Capital total</div>
          <div class="card-value mono">{{ "%.2f"|format(total_capital) }} USDT</div>
        </div>
        <div class="card">
          <div class="card-title">Disponible</div>
          <div class="card-value mono">{{ "%.2f"|format(balance) }} USDT</div>
        </div>
        <div class="card">
          <div class="card-title">PnL latent</div>
          <div class="card-value mono {% if total_unrealized_pnl >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(total_unrealized_pnl) }} USDT</div>
        </div>
        <div class="card">
          <div class="card-title">PnL réalisé</div>
          <div class="card-value mono {% if perf.total_pnl >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(perf.total_pnl) }} USDT</div>
          <div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px">{{ perf.win_rate }}% WR, {{ perf.total_trades }} trades</div>
        </div>
      </div>

      <div class="card" style="margin-bottom: 16px;" id="sniperStatsCard">
        <h2>Dernier scan</h2>
        <div class="sniper-stats" id="sniperStatsBox">
          <div class="sniper-stat"><span class="num">{{ sniper_stats.candidates|default(0) if sniper_stats else 0 }}</span><span class="label">candidats</span></div>
          <div class="sniper-stat"><span class="num">{{ sniper_stats.passed|default(0) if sniper_stats else 0 }}</span><span class="label">passés (score &ge;{{ min_score }})</span></div>
          <div class="sniper-stat"><span class="num">{{ sniper_stats.executed|default(0) if sniper_stats else 0 }}</span><span class="label">exécutés</span></div>
        </div>
        {% if sniper_stats and sniper_stats.errors %}
        <div style="font-size:0.8rem;color:var(--red);margin-top:8px" id="sniperErrors">{{ sniper_stats.errors|join('; ') }}</div>
        {% endif %}
      </div>

      <!-- Positions -->
      <div class="card" style="margin-bottom: 16px;">
        <h2>Positions ({{ positions|length }})</h2>
        {% if positions %}
        <table>
          <thead><tr><th>Paire</th><th>Type</th><th>Marge</th><th>PnL</th><th>Progression SL→TP</th><th></th></tr></thead>
          <tbody>
          {% for p in positions %}
          <tr>
            <td><strong>{{ p.symbol }}</strong></td>
            <td><span class="badge badge-{{ p.direction|lower }}">{{ p.direction }}</span></td>
            <td class="mono">{{ "%.2f"|format(p.amount|default(0)) }} USDT</td>
            <td class="mono {% if p.pnl_percent >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(p.pnl_value) }} ({{ "%+.2f"|format(p.pnl_percent) }}%)</td>
            <td style="width:120px">
              <div class="progress-bar"><div class="progress-fill {% if p.pnl_percent >= 0 %}green{% else %}red{% endif %}" style="width:{{ p.progress|default(0) }}%"></div></div>
            </td>
            <td><button onclick="closePos('{{ p.symbol }}')">Fermer</button></td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
        {% else %}
        <p class="empty">Aucune position ouverte</p>
        {% endif %}
      </div>

      <!-- Top setups -->
      <div class="card" style="margin-bottom: 16px;">
        <h2>Top setups ({{ opportunities|length }})</h2>
        {% if last_block_reason %}
        <div class="block-reason">Pas rentré: {{ last_block_reason }}</div>
        {% endif %}
        {% if opportunities %}
        <table>
          <thead><tr><th>Paire</th><th>Direction</th><th>Score</th><th>Prix</th><th>R:R</th></tr></thead>
          <tbody>
          {% for o in opportunities[:8] %}
          <tr>
            <td><strong>{{ o.pair }}</strong></td>
            <td><span class="badge badge-{{ (o.entry_signal|default('LONG'))|lower }}">{{ o.entry_signal|default('LONG') }}</span></td>
            <td><span class="score">{{ o.score }}/10</span></td>
            <td class="mono">{{ "%.2f"|format(o.price|default(0)) }}</td>
            <td>{{ o.rr_ratio|default(2) }}:1</td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
        {% else %}
        <p class="empty">Aucun setup qualifié pour le moment</p>
        {% endif %}
      </div>

      <!-- Historique -->
      <div class="card" style="margin-bottom: 16px;">
        <h2>Historique des trades ({{ (trades_history|default([]))|length }})</h2>
        {% if trades_history|default([]) %}
        <div style="max-height:200px;overflow-y:auto">
        <table>
          <thead><tr><th>Entrée</th><th>Sortie</th><th>Paire</th><th>Type</th><th>PnL</th></tr></thead>
          <tbody>
          {% for t in (trades_history|default([])) %}
          <tr>
            <td style="font-size:0.8rem;color:var(--text-muted)">{{ t.entry_time|default('-') }}</td>
            <td style="font-size:0.8rem;color:var(--text-muted)">{{ t.time }}</td>
            <td><strong>{{ t.symbol }}</strong></td>
            <td><span class="badge badge-{{ (t.direction|default('LONG'))|lower }}">{{ t.direction|default('LONG') }}</span></td>
            <td class="mono {% if t.pnl >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(t.pnl|default(0)) }} USDT</td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
        </div>
        <p style="font-size:0.75rem;color:var(--text-muted);margin-top:8px"><a href="/api/export/trades" style="color:var(--accent)">Exporter CSV</a></p>
        {% else %}
        <p class="empty">Aucun trade fermé</p>
        {% endif %}
      </div>
    </div>

    <!-- Colonne droite: activité temps réel -->
    <div>
      <div class="card" style="height:100%;min-height:400px;">
        <h2>Activité en temps réel</h2>
        <div class="activity-feed" id="activityFeed">
          {% if bot_log %}
          {% for e in bot_log %}
          <div class="activity-line level-{{ e.level|default('INFO') }}">
            <span class="activity-time">{{ e.time }}</span>
            <span class="activity-msg">{{ e.msg }}</span>
          </div>
          {% endfor %}
          {% else %}
          <p class="empty">En attente...</p>
          {% endif %}
        </div>
      </div>
    </div>
  </div>
</div>

<div class="refresh-indicator" id="refreshIndicator">MAJ auto: <span id="countdown">15</span>s</div>

<script>
  const REFRESH_INTERVAL = 15;
  let countdown = REFRESH_INTERVAL;

  function resetWallet() {
    if (!confirm('Réinitialiser à 100 USDT ? Toutes les positions et l\'historique seront supprimés.')) return;
    fetch('/api/reset', { method: 'POST' })
      .then(r => r.json())
      .then(d => { if (d.success) location.reload(); else alert(d.error || 'Erreur'); })
      .catch(function() { alert('Erreur réseau'); });
  }
  function closePos(sym) {
    if (!confirm('Fermer ' + sym + ' ?')) return;
    fetch('/api/close/' + sym, { method: 'POST' })
      .then(r => r.json())
      .then(d => { if (d.success) location.reload(); else alert(d.error || 'Erreur'); })
      .catch(function() { alert('Erreur réseau'); });
  }

  function renderActivityFeed(log) {
    const el = document.getElementById('activityFeed');
    if (!el || !log || !log.length) return;
    el.innerHTML = log.map(function(e) {
      const level = (e.level || 'INFO');
      return '<div class="activity-line level-' + level + '"><span class="activity-time">' + (e.time || '') + '</span><span class="activity-msg">' + (e.msg || '').replace(/</g, '&lt;') + '</span></div>';
    }).join('');
  }

  function renderSniperStats(stats) {
    const container = document.getElementById('sniperStatsBox');
    if (!container || !stats) return;
    const c = stats.candidates || 0, p = stats.passed || 0, e = stats.executed || 0;
    container.innerHTML = '<div class="sniper-stat"><span class="num">' + c + '</span><span class="label">candidats</span></div>' +
      '<div class="sniper-stat"><span class="num">' + p + '</span><span class="label">passés</span></div>' +
      '<div class="sniper-stat"><span class="num">' + e + '</span><span class="label">exécutés</span></div>';
  }

  function refreshData() {
    fetch('/api/data')
      .then(r => r.json())
      .then(function(d) {
        if (d.error) return;
        renderActivityFeed(d.bot_log || []);
        renderSniperStats(d.sniper_stats);
        var status = document.getElementById('scanStatus');
        if (status) {
          status.innerHTML = '<span class="pulse"></span>' + (d.is_scanning ? 'Scan en cours...' : 'Actif');
          status.className = 'status-badge ' + (d.is_scanning ? 'scanning' : 'idle');
        }
        var lu = document.getElementById('lastUpdate');
        if (lu) lu.textContent = d.last_update || '-';
        var sc = document.getElementById('scanCount');
        if (sc) sc.textContent = d.scan_count;
        countdown = REFRESH_INTERVAL;
      })
      .catch(function() { countdown = REFRESH_INTERVAL; });
  }

  function updateCountdown() {
    countdown--;
    var el = document.getElementById('countdown');
    if (el) el.textContent = countdown;
    if (countdown <= 0) {
      refreshData();
    }
  }
  setInterval(updateCountdown, 1000);
</script>
</body>
</html>
"""
