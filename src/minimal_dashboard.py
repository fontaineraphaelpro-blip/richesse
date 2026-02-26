# -*- coding: utf-8 -*-
"""Interface HTML minimal noir/blanc, mobile friendly."""

def get_minimal_dashboard_html():
    return r"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Day Trader Bot</title>
<style>
* { box-sizing: border-box; }
body { margin: 0; padding: 12px; background: #000; color: #fff; font-family: system-ui, sans-serif; font-size: 15px; -webkit-text-size-adjust: 100%; }
h1 { font-size: 1.25rem; margin: 0 0 8px 0; }
h2 { font-size: 1rem; margin: 0 0 8px 0; font-weight: 600; }
section { margin-bottom: 20px; }
.status { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: #666; }
.dot.on { background: #fff; }
.dot.scan { background: #fff; animation: pulse 1s infinite; }
@keyframes pulse { 50% { opacity: 0.5; } }
.row { display: flex; justify-content: space-between; margin: 6px 0; }
.label { color: #999; }
.green { color: #fff; }
.red { color: #fff; }
.green .val { color: #0f0; }
.red .val { color: #f44; }
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th, td { padding: 8px; text-align: left; border-bottom: 1px solid #333; }
th { color: #999; font-weight: 500; }
.log { background: #111; padding: 10px; border-radius: 6px; max-height: 180px; overflow-y: auto; font-size: 0.8rem; font-family: monospace; }
.log-line { margin: 4px 0; word-break: break-word; }
.log-time { color: #666; margin-right: 8px; }
button { background: #fff; color: #000; border: none; padding: 8px 14px; border-radius: 6px; font-size: 0.9rem; cursor: pointer; }
button:active { opacity: 0.8; }
.empty { color: #666; padding: 12px; }
</style>
</head>
<body>
<section>
  <h1>Day Trader Bot</h1>
  <div class="status">
    <span class="dot {% if is_scanning %}scan{% else %}on{% endif %}"></span>
    <span>{% if is_scanning %}Scan...{% else %}Actif{% endif %} &middot; #{{ scan_count }} &middot; {{ last_update or '-' }}</span>
    <button onclick="resetWallet()" style="margin-left:auto;font-size:0.8rem;padding:6px 10px">Reinitialiser (100 EUR)</button>
  </div>
</section>
<section>
  <div class="row"><span class="label">Capital</span><span>{{ "%.2f"|format(total_capital * (usd_to_eur|default(0.92))) }} €</span></div>
  <div class="row"><span class="label">Dispo</span><span>{{ "%.2f"|format(balance * (usd_to_eur|default(0.92))) }} €</span></div>
  <div class="row"><span class="label">PnL latent</span><span class="{% if total_unrealized_pnl >= 0 %}green{% else %}red{% endif %}"><span class="val">{{ "%+.2f"|format(total_unrealized_pnl * (usd_to_eur|default(0.92))) }} €</span></span></div>
  <div class="row"><span class="label">PnL réalisé</span><span class="{% if perf.total_pnl >= 0 %}green{% else %}red{% endif %}"><span class="val">{{ "%+.2f"|format(perf.total_pnl * (usd_to_eur|default(0.92))) }} €</span> ({{ perf.win_rate }}% WR, {{ perf.total_trades }} trades)</span></div>
</section>
<section>
  <h2>Positions ({{ positions|length }})</h2>
  {% if positions %}
  <table>
    <thead><tr><th>Paire</th><th>Type</th><th>Marge</th><th>PnL</th><th></th></tr></thead>
    <tbody>
    {% for p in positions %}
    <tr>
      <td><strong>{{ p.symbol }}</strong></td>
      <td>{{ p.direction }}</td>
      <td>{{ "%.2f"|format((p.amount|default(0)) * (usd_to_eur|default(0.92))) }} €</td>
      <td class="{% if p.pnl_percent >= 0 %}green{% else %}red{% endif %}"><span class="val">{{ "%+.2f"|format(p.pnl_value * (usd_to_eur|default(0.92))) }} € ({{ "%+.2f"|format(p.pnl_percent) }}%)</span></td>
      <td><button onclick="closePos('{{ p.symbol }}')">Fermer</button></td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="empty">Aucune position</p>
  {% endif %}
</section>
<section>
  <h2>Opportunités ({{ opportunities|length }})</h2>
  {% if opportunities %}
  <table>
    <thead><tr><th>Paire</th><th>Signal</th><th>Score</th></tr></thead>
    <tbody>
    {% for o in opportunities[:8] %}
    <tr>
      <td>{{ o.pair }}</td>
      <td>{{ o.entry_signal }}</td>
      <td>{{ o.score }}</td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="empty">Aucune</p>
  {% endif %}
</section>
<section>
  <h2>Historique des trades ({{ (trades_history|default([]))|length }})</h2>
  {% if trades_history|default([]) %}
  <div style="max-height:220px;overflow-y:auto">
  <table>
    <thead><tr><th>Date</th><th>Paire</th><th>Type</th><th>PnL</th><th>Raison</th></tr></thead>
    <tbody>
    {% for t in (trades_history|default([])) %}
    <tr>
      <td style="font-size:0.8rem;color:#999">{{ t.time }}</td>
      <td><strong>{{ t.symbol }}</strong></td>
      <td>{{ t.direction }}</td>
      <td class="{% if t.pnl >= 0 %}green{% else %}red{% endif %}"><span class="val">{{ "%+.2f"|format((t.pnl|default(0)) * (usd_to_eur|default(0.92))) }} € ({{ "%+.1f"|format(t.pnl_percent|default(0)) }}%)</span></td>
      <td style="font-size:0.8rem">{{ (t.reason|default('-'))[:20] }}</td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  </div>
  <p style="font-size:0.75rem;color:#666;margin-top:6px"><a href="/api/export/trades" style="color:#888">Exporter CSV</a></p>
  {% else %}
  <p class="empty">Aucun trade ferme</p>
  {% endif %}
</section>
<section>
  <h2>Journal bot</h2>
  <div class="log">
  {% if bot_log %}
  {% for e in bot_log %}
  <div class="log-line"><span class="log-time">{{ e.time }}</span> {{ e.msg }}</div>
  {% endfor %}
  {% else %}
  <p class="empty">—</p>
  {% endif %}
  </div>
</section>
<script>
function resetWallet() {
  if (!confirm('Réinitialiser à 100€ ? Toutes les positions et l\'historique seront supprimés.')) return;
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
setTimeout(function() { location.reload(); }, 60000);
</script>
</body>
</html>
"""
