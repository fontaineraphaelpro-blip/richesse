"""
Script principal: Crypto Swing Trader Bot & Dashboard.
Version: ULTIMATE (Swing Trading 1H + Gestion PnL + Dashboard Complet)
"""

import time
import os
import threading
import json
from datetime import datetime
try:
    from flask import Flask, render_template_string, jsonify
except Exception:
    Flask = None
    def render_template_string(template, **kwargs):
        raise RuntimeError('Flask not available in this environment')
    def jsonify(*args, **kwargs):
        raise RuntimeError('Flask not available in this environment')

# Import des modules internes
from trader import PaperTrader
from data_fetcher import fetch_multiple_pairs, fetch_klines
from indicators import calculate_indicators
from scorer import calculate_opportunity_score
from backtest import quick_backtest_from_df
from config import cfg
import argparse

# --- CONFIGURATION DU BOT (depuis config.py) ---
TIMEFRAME = cfg.TIMEFRAME
CANDLE_LIMIT = cfg.CANDLE_LIMIT
TRADE_AMOUNT = cfg.TRADE_AMOUNT
MIN_SCORE_TO_BUY = cfg.MIN_SCORE_TO_BUY
SCAN_INTERVAL = cfg.SCAN_INTERVAL
MAX_OPEN_POSITIONS = cfg.MAX_OPEN_POSITIONS

# Variable partagée entre le Scanner (Thread) et le Site Web (Flask)
shared_data = {
    'opportunities': [],
    'last_prices': {},     # Pour calculer le PnL en temps réel
    'is_scanning': False,
    'last_update': 'Jamais'
}

app = Flask(__name__) if Flask is not None else None

def run_scanner():
    """
    Cœur du système : Scanne le marché, gère les positions et trouve des opportunités.
    """
    print("\n" + "="*70)
    print(f"🦁 SWING BOT ACTIF - {datetime.now().strftime('%d/%m %H:%M:%S')}")
    print("Stratégie: Trend Following (SMA 200) + Breakout")
    print("="*70)
    
    try:
        # --- ÉTAPE 1 : Récupération des données ---
        print("📡 Récupération des données marché (Binance)...")
        data, real_prices = fetch_multiple_pairs(None, interval=TIMEFRAME, limit=CANDLE_LIMIT)
        
        if not data:
            print("❌ Erreur critique : Aucune donnée reçue.")
            return []
            
        # Mise à jour des prix en temps réel pour le dashboard
        shared_data['last_prices'] = real_prices

        # --- ÉTAPE 2 : Gestion des Positions Existantes (Stop Loss / Take Profit) ---
        print("💼 Vérification du portefeuille...")
        trader = PaperTrader()
        
        # Le trader vérifie s'il doit vendre des positions
        if real_prices:
            trader.check_positions(real_prices)
        
        # --- ÉTAPE 3 : Analyse Technique (Scan) ---
        print("🔍 Analyse des 150+ paires (Expanded Scanner)...")
        opportunities = []
        
        for symbol, df in data.items():
            # 1. Calcul des indicateurs (SMA, RSI, MACD, ATR...)
            indicators = calculate_indicators(df)
            
            # 2. Calcul du Score et Signaux
            # On passe le DataFrame complet pour la validation du volume
            score_data = calculate_opportunity_score(indicators, None, df)
            
            # 3. Filtrage : On ne garde que ce qui a un signal (même faible)
            if score_data['entry_signal'] != 'NEUTRAL':
                opportunities.append({
                    'pair': symbol,
                    'score': score_data['score'],
                    'trend': score_data['trend'],
                    'signal': score_data['signal'],
                    'price': indicators['current_price'],
                    'entry_signal': score_data['entry_signal'],
                    'stop_loss': score_data['stop_loss'],
                    'take_profit': score_data['take_profit_1'],
                    'details': score_data.get('details', ''),
                    'confidence': score_data.get('confidence', 0),
                    'atr_percent': score_data.get('atr_percent', 0)
                })

        # Tri par Score décroissant (Les meilleures opportunités en haut)
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        # On garde le Top 25 pour l'affichage (support plus de trades)
        top_picks = opportunities[:25]
        
        # Affichage Terminal propre
        print("\n" + "-"*95)
        print(f"{'Paire':<10} {'Score':<5} {'Signal':<6} {'Prix':<10} {'SL':<10} {'Détails'}")
        print("-"*95)
        for opp in top_picks:
            print(f"{opp['pair']:<10} {opp['score']:<5} {opp['entry_signal']:<6} ${opp['price']:.4f} ${opp['stop_loss']:.4f} {opp['details'][:35]}...")

        # --- ÉTAPE 4 : Exécution Automatique (Achat) ---
        print("\n🤖 Auto-Trading (Support Multi-Positions)...")
        my_positions = trader.get_open_positions() # Retourne un dictionnaire
        balance = trader.get_usdt_balance()
        
        # Vérification du nombre de positions ouvertes
        num_open = len(my_positions)
        max_new_positions = MAX_OPEN_POSITIONS - num_open
        
        if max_new_positions <= 0:
            print(f"⚠️ Position max atteinte ({MAX_OPEN_POSITIONS} positions). Aucun nouveau trade.")
        else:
            print(f"💰 Positions ouvertes: {num_open}/{MAX_OPEN_POSITIONS} | Nouvelles positions possibles: {max_new_positions}")
        
        new_trades_count = 0
        for opp in top_picks:
            # RÈGLES D'ACHAT STRICTES :
            # 1. Score >= MIN_SCORE_TO_BUY (Qualité améliorée)
            # 2. Signal LONG (On achète)
            # 3. Pas déjà en portefeuille
            # 4. Solde suffisant
            # 5. Position max non atteinte
            
            if (opp['score'] >= MIN_SCORE_TO_BUY and 
                opp['entry_signal'] == 'LONG' and 
                opp['pair'] not in my_positions and
                new_trades_count < max_new_positions):
                
                if balance >= TRADE_AMOUNT:
                    success = trader.place_buy_order(
                        symbol=opp['pair'],
                        amount_usdt=TRADE_AMOUNT,
                        current_price=opp['price'],
                        stop_loss_price=opp['stop_loss'],
                        take_profit_price=opp['take_profit']
                    )
                    if success:
                        balance -= TRADE_AMOUNT # Mise à jour locale pour la boucle
                        new_trades_count += 1
                        print(f"✅ Trade #{new_trades_count}: {opp['pair']} (Score: {opp['score']}, Prix: ${opp['price']:.4f})")
                else:
                    print("⚠️ Solde insuffisant pour nouveaux trades.")
                    break
        
        return top_picks
        
    except Exception as e:
        print(f"\n❌ Erreur Scan: {e}")
        import traceback
        traceback.print_exc()
        return []

# --- PARTIE WEB (FLASK DASHBOARD) ---

@app.route('/')
def dashboard():
    try:
        trader = PaperTrader()
        balance = trader.get_usdt_balance()
        all_trades = trader.get_trades_history()
        open_positions = trader.get_open_positions() # Dict: {'BTCUSDT': {...}}
        
        # 1. Séparer les trades terminés (Ventes)
        history = [t for t in all_trades if 'VENTE' in t['type']]
    except Exception as e:
        print(f"❌ Erreur Dashboard: {e}")
        return f"Erreur serveur: {str(e)}", 500
    
    # 2. Calculer le PnL en temps réel des positions ouvertes
    positions_view = []
    total_unrealized_pnl = 0
    
    for symbol, pos_data in open_positions.items():
        entry = pos_data['entry_price']
        # Prix actuel (soit du dernier scan, soit l'entrée si scan pas encore fait)
        current = shared_data['last_prices'].get(symbol, entry)
        
        # Calcul PnL non réalisé
        pnl_value = (current - entry) * pos_data['quantity']
        pnl_percent = ((current - entry) / entry) * 100
        
        total_unrealized_pnl += pnl_value
        
        positions_view.append({
            'symbol': symbol,
            'entry': entry,
            'current': current,
            'amount': pos_data['amount_usdt'],
            'quantity': pos_data['quantity'],
            'pnl_value': pnl_value,
            'pnl_percent': pnl_percent,
            'sl': pos_data['stop_loss'],
            'tp': pos_data['take_profit']
        })

    # Template HTML/CSS Complet
    HTML = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🦁 Swing Bot Master</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            :root { --bg: #0f172a; --card: #1e293b; --text: #f1f5f9; --accent: #3b82f6; --green: #10b981; --red: #ef4444; }
            body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }
            .container { max-width: 1400px; margin: 0 auto; }
            
            /* Header */
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 1px solid #334155; padding-bottom: 20px; }
            .status { background: rgba(59, 130, 246, 0.1); color: var(--accent); padding: 8px 16px; border-radius: 20px; font-weight: 600; font-size: 0.9em; border: 1px solid rgba(59, 130, 246, 0.2); }
            .scanning { animation: pulse 2s infinite; color: #fbbf24; border-color: #fbbf24; }
            
            /* Stats Cards */
            .grid-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .card { background: var(--card); padding: 25px; border-radius: 16px; border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
            .stat-label { color: #94a3b8; font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
            .stat-value { font-size: 2em; font-weight: 800; }
            .positive { color: var(--green); }
            .negative { color: var(--red); }
            
            /* Tables */
            h2 { font-size: 1.2em; margin-bottom: 15px; color: #e2e8f0; display: flex; align-items: center; gap: 10px; }
            .table-container { overflow-x: auto; }
            table { width: 100%; border-collapse: collapse; font-size: 0.95em; }
            th { text-align: left; padding: 15px; color: #94a3b8; font-weight: 600; border-bottom: 1px solid #334155; }
            td { padding: 15px; border-bottom: 1px solid #334155; vertical-align: middle; }
            tr:last-child td { border-bottom: none; }
            
            /* Badges */
            .badge { padding: 4px 10px; border-radius: 6px; font-size: 0.8em; font-weight: 700; }
            .b-green { background: rgba(16, 185, 129, 0.2); color: var(--green); }
            .b-red { background: rgba(239, 68, 68, 0.2); color: var(--red); }
            .score { font-weight: 800; }
            .s-high { color: var(--green); }
            .s-med { color: #fbbf24; }
            .s-low { color: #f87171; }
            
            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
            
            .refresh-btn { background: var(--accent); color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; }
            .refresh-btn:hover { opacity: 0.9; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1 style="margin:0">🦁 Swing Bot Dashboard</h1>
                    <div style="color:#94a3b8; font-size:0.9em; margin-top:5px">Mise à jour: <span id="last-update">{{ last_update }}</span></div>
                </div>
                <div class="status {% if is_scanning %}scanning{% endif %}" id="status-badge">
                    {% if is_scanning %}🔄 SCAN EN COURS...{% else %}✅ SYSTÈME PRÊT{% endif %}
                </div>
            </div>

            <div class="grid-stats">
                <div class="card">
                    <div class="stat-label">Solde Disponible</div>
                    <div class="stat-value" id="balance-value">${{ "%.2f"|format(balance) }}</div>
                </div>
                <div class="card">
                    <div class="stat-label">PnL Latent (Positions)</div>
                    <div class="stat-value {% if total_unrealized_pnl >= 0 %}positive{% else %}negative{% endif %}" id="pnl-value">
                        {{ "%+.2f"|format(total_unrealized_pnl) }} $
                    </div>
                </div>
                <div class="card">
                    <div class="stat-label">Positions Actives</div>
                    <div class="stat-value" id="positions-count">{{ positions|length }} / 10</div>
                </div>
                <div class="card">
                    <div class="stat-label">Levier Appliqué</div>
                    <div class="stat-value" style="color:#fbbf24">10x</div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                
                <div class="card">
                    <h2>💼 Portefeuille Actif</h2>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Paire</th>
                                    <th>Quantité</th>
                                    <th>Entrée</th>
                                    <th>Actuel</th>
                                    <th>Montant</th>
                                    <th>PnL Value</th>
                                    <th>PnL %</th>
                                    <th>SL / TP</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% if not positions %}
                                <tr><td colspan="8" style="text-align:center; padding:30px; color:#64748b">Aucune position ouverte</td></tr>
                                {% else %}
                                {% for pos in positions %}
                                <tr>
                                    <td style="font-weight:bold">{{ pos.symbol }}</td>
                                    <td style="font-size:0.9em">{{ "%.4f"|format(pos.quantity|default(0)) }}</td>
                                    <td>${{ "%.2f"|format(pos.entry) }}</td>
                                    <td>${{ "%.2f"|format(pos.current) }}</td>
                                    <td>${{ "%.0f"|format(pos.amount) }}</td>
                                    <td><span class="{% if pos.pnl_value >= 0 %}positive{% else %}negative{% endif %}" style="font-weight:bold">${{ "%+.2f"|format(pos.pnl_value) }}</span></td>
                                    <td>
                                        <span class="badge {% if pos.pnl_value >= 0 %}b-green{% else %}b-red{% endif %}">
                                            {{ "%+.2f"|format(pos.pnl_percent) }}%
                                        </span>
                                    </td>
                                    <td style="font-size:0.85em">
                                        <span style="color:#ef4444">SL: {{ "%.2f"|format(pos.sl) }}</span><br>
                                        <span style="color:#10b981">TP: {{ "%.2f"|format(pos.tp) }}</span>
                                    </td>
                                </tr>
                                {% endfor %}
                                {% endif %}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="card">
                    <h2>📜 Dernières Clôtures</h2>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Paire</th>
                                    <th>Résultat</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% if not history %}
                                <tr><td colspan="2" style="text-align:center; color:#64748b">Aucun historique</td></tr>
                                {% else %}
                                {% for trade in history[:8] %}
                                <tr>
                                    <td>
                                        <div><strong>{{ trade.symbol }}</strong></div>
                                        <div style="font-size:0.8em; color:#64748b">{{ trade.time }}</div>
                                    </td>
                                    <td style="text-align:right">
                                        <span class="{% if trade.pnl > 0 %}positive{% else %}negative{% endif %}" style="font-weight:bold">
                                            {{ "%+.2f"|format(trade.pnl) }}$
                                        </span>
                                    </td>
                                </tr>
                                {% endfor %}
                                {% endif %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="card" style="margin-top: 20px;">
                <h2>📡 Scanner Opportunités (Top 15)</h2>
                <div style="margin-bottom: 15px; padding: 15px; background: rgba(59, 130, 246, 0.1); border-radius: 8px; font-size: 0.9em;">
                    <strong>Configuration:</strong> Score Min: {{ min_score }} | Levier: 10x | Capital: $1000 | Par Position: ${{ trade_amount }}
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Paire</th>
                                <th>Score</th>
                                <th>Trend</th>
                                <th>Signal</th>
                                <th>Prix</th>
                                <th>SL / TP</th>
                                <th>Confiance</th>
                                <th>ATR%</th>
                                <th>Détails</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% if not opportunities %}
                            <tr><td colspan="10" style="text-align:center; padding:30px; color:#64748b">En attente du prochain scan...</td></tr>
                            {% else %}
                            {% for opp in opportunities %}
                            <tr>
                                <td>{{ loop.index }}</td>
                                <td style="font-weight:bold; color:var(--accent)">{{ opp.pair }}</td>
                                <td class="score {% if opp.score >= 70 %}s-high{% elif opp.score >= 60 %}s-med{% else %}s-low{% endif %}">{{ opp.score }}</td>
                                <td>
                                    <span class="badge {% if 'UP' in opp.trend|upper %}b-green{% else %}b-red{% endif %}">
                                        {{ opp.trend }}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge {% if opp.entry_signal == 'LONG' %}b-green{% else %}b-red{% endif %}">
                                        {{ opp.entry_signal }}
                                    </span>
                                </td>
                                <td>${{ "%.4f"|format(opp.price) }}</td>
                                <td style="font-size:0.8em">
                                    <div style="color:#ef4444">SL: ${{ "%.4f"|format(opp.stop_loss) }}</div>
                                    <div style="color:#10b981">TP: ${{ "%.4f"|format(opp.take_profit) }}</div>
                                </td>
                                <td>
                                    <span class="badge {% if opp.confidence|default(0) >= 80 %}b-green{% else %}b-red{% endif %}">
                                        {{ "%.0f"|format(opp.confidence|default(0)) }}%
                                    </span>
                                </td>
                                <td style="color:#fbbf24; font-weight:600">{{ "%.2f"|format(opp.atr_percent|default(0)) }}%</td>
                                <td style="font-size:0.85em; max-width:150px; white-space:normal">{{ opp.details }}</td>
                            </tr>
                            {% endfor %}
                            {% endif %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        <script>
            // Auto-refresh temps réel - Rafraîchit les données toutes les 5 secondes
            async function refreshData() {
                try {
                    const response = await fetch('/api/data');
                    const data = await response.json();
                    
                    // Mise à jour du solde
                    document.getElementById('balance-value').textContent = '$' + data.balance.toFixed(2);
                    
                    // Mise à jour du PnL
                    const pnlElement = document.getElementById('pnl-value');
                    pnlElement.textContent = (data.total_unrealized_pnl >= 0 ? '+' : '') + data.total_unrealized_pnl.toFixed(2) + ' $';
                    pnlElement.className = 'stat-value ' + (data.total_unrealized_pnl >= 0 ? 'positive' : 'negative');
                    
                    // Mise à jour du nombre de positions
                    document.getElementById('positions-count').textContent = data.positions.length + ' / 10';
                    
                    // Mise à jour du timestamp
                    document.getElementById('last-update').textContent = data.last_update;
                    
                    // Mise à jour du statut scanning
                    const statusElement = document.getElementById('status-badge');
                    if (data.is_scanning) {
                        statusElement.innerHTML = '🔄 SCAN EN COURS...';
                        statusElement.classList.add('scanning');
                    } else {
                        statusElement.innerHTML = '✅ SYSTÈME PRÊT';
                        statusElement.classList.remove('scanning');
                    }
                    
                    console.log('Dashboard refresh:', new Date().toLocaleTimeString());
                } catch (error) {
                    console.error('Erreur refresh:', error);
                }
            }
            
            // Refresh initial et toutes les 5 secondes
            refreshData();
            setInterval(refreshData, 5000);
        </script>
    </body>
    </html>
    """
    
    return render_template_string(HTML, 
                                 balance=balance,
                                 positions=positions_view,
                                 total_unrealized_pnl=total_unrealized_pnl,
                                 history=history,
                                 opportunities=shared_data['opportunities'],
                                 is_scanning=shared_data['is_scanning'],
                                 last_update=shared_data['last_update'],
                                 min_score=MIN_SCORE_TO_BUY,
                                 trade_amount=TRADE_AMOUNT)

# --- API TEMPS RÉEL ---

@app.route('/api/data')
def api_data():
    """Endpoint API pour obtenir les données temps réel en JSON."""
    try:
        trader = PaperTrader()
        balance = trader.get_usdt_balance()
        all_trades = trader.get_trades_history()
        open_positions = trader.get_open_positions()
        
        # Séparer les trades terminés
        history = [t for t in all_trades if 'VENTE' in t['type']]
        
        # Calculer les positions avec PnL
        positions_view = []
        total_unrealized_pnl = 0
        
        for symbol, pos_data in open_positions.items():
            entry = pos_data['entry_price']
            current = shared_data['last_prices'].get(symbol, entry)
            
            pnl_value = (current - entry) * pos_data['quantity']
            pnl_percent = ((current - entry) / entry) * 100
            
            total_unrealized_pnl += pnl_value
            
            positions_view.append({
                'symbol': symbol,
                'entry': entry,
                'current': current,
                'amount': pos_data['amount_usdt'],
                'quantity': pos_data['quantity'],
                'pnl_value': pnl_value,
                'pnl_percent': pnl_percent,
                'sl': pos_data['stop_loss'],
                'tp': pos_data['take_profit']
            })
        
        return jsonify({
            'balance': balance,
            'total_unrealized_pnl': total_unrealized_pnl,
            'positions': positions_view,
            'history': history[:20],
            'opportunities': shared_data['opportunities'][:15],
            'is_scanning': shared_data['is_scanning'],
            'last_update': shared_data['last_update'],
            'min_score': MIN_SCORE_TO_BUY,
            'trade_amount': TRADE_AMOUNT,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ Erreur API: {e}")
        return jsonify({'error': str(e)}), 500

# --- BOUCLE PRINCIPALE (THREAD) ---

def run_loop():
    """Boucle infinie qui lance le scanner périodiquement."""
    print("⏳ Démarrage de la boucle de scan...")
    while True:
        shared_data['is_scanning'] = True
        try:
            shared_data['opportunities'] = run_scanner()
            shared_data['last_update'] = datetime.now().strftime('%H:%M:%S')
        except Exception as e:
            print(f"❌ Erreur Loop: {e}")
        finally:
            shared_data['is_scanning'] = False
        
        print(f"💤 Pause de {SCAN_INTERVAL/60} minutes...")
        time.sleep(SCAN_INTERVAL)

# --- LANCEMENT ---

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Richesse Bot Runner')
    parser.add_argument('--backtest', help='Run quick backtest for SYMBOL (ex: BTCUSDT)')
    parser.add_argument('--bt-amount', type=float, default=1000.0, help='Initial balance for backtest')
    parser.add_argument('--bt-risk', type=float, default=0.01, help='Risk per trade for backtest (fraction)')
    args = parser.parse_args()

    # If backtest requested, run it and exit
    if args.backtest:
        symbol = args.backtest.upper()
        print(f"🔁 Running quick backtest for {symbol}...")
        df, price = fetch_klines(symbol, interval='15m', limit=1000)
        if df is None or df.empty:
            print(f"❌ Could not fetch data for {symbol}. Aborting backtest.")
        else:
            result = quick_backtest_from_df(df, initial_balance=args.bt_amount, risk_per_trade=args.bt_risk)
            print("\n--- Backtest Summary ---")
            print(f"Initial Balance: ${result.get('initial_balance')}")
            print(f"Final Balance:   ${result.get('final_balance')}")
            print(f"Trades: {result.get('trades_count')} | Wins: {result.get('wins')} | Losses: {result.get('losses')} | WinRate: {result.get('win_rate')}%")
        raise SystemExit(0)
    # 1. Lancer le scanner dans un thread séparé (background)
    scanner_thread = threading.Thread(target=run_loop, daemon=True)
    scanner_thread.start()
    
    # 2. Lancer le serveur Web Flask (bloquant)
    print("🌍 Dashboard accessible sur http://localhost:8080")
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
