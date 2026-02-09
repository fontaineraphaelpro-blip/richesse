"""
Script principal du Crypto Signal Scanner Web.
Version HYBRIDE : Bot Autonome + Dashboard d'Analyse Technique Complet.
"""

import time
import os
from datetime import datetime
from flask import Flask, render_template_string
import threading

from trader import PaperTrader
from data_fetcher import fetch_multiple_pairs
from indicators import calculate_indicators
from support import find_swing_low, calculate_distance_to_support
from scorer import calculate_opportunity_score

def run_scanner():
    """
    Exécute un scan complet, gère le trading auto, et retourne TOUTES les infos pour le dashboard.
    """
    print("\n" + "="*60)
    print("🚀 CRYPTO SCANNER - Mode HYBRIDE (1h)")
    print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    try:
        # 1. Récupération des données
        print("📊 Récupération des données sur 1000 bougies de 1h...")
        data, real_prices = fetch_multiple_pairs(None, interval='1h', limit=1000)
        
        if not data:
            print("❌ Aucune donnée.")
            return []
            
        # ==============================================================================
        # 2. GESTION DES SORTIES (Bot)
        # ==============================================================================
        trader = PaperTrader()
        if real_prices:
            trader.check_positions(real_prices)
        
        # ==============================================================================
        
        # 3. Analyse Technique Complète
        print("🔍 Analyse détaillée du marché...")
        opportunities = []
        
        for i, (symbol, df) in enumerate(data.items(), 1):
            indicators = calculate_indicators(df)
            current_price = real_prices.get(symbol) or indicators.get('current_price')
            
            support = find_swing_low(df, lookback=50)
            support_dist = calculate_distance_to_support(current_price, support) if support else None
            
            score_data = calculate_opportunity_score(indicators, support_dist, df)
            
            # On stocke TOUTES les données pour l'affichage manuel
            opportunities.append({
                'pair': symbol,
                'score': score_data['score'],
                'trend': score_data['trend'],          # Tendance (Bullish/Bearish)
                'signal_text': score_data['signal'],   # Texte "Opportunité Forte"
                'details': score_data['details'],      # Détails (ex: "RSI Achat, MACD Cross")
                'price': current_price,
                'rsi': indicators.get('rsi14'),        # RSI (Crucial pour manuel)
                'entry_signal': score_data.get('entry_signal', 'NEUTRAL'), # LONG/SHORT
                'entry_price': score_data.get('entry_price'),
                'stop_loss': score_data.get('stop_loss'),
                'take_profit_1': score_data.get('take_profit_1'),
                'confidence': score_data.get('confidence', 0), # Confiance %
            })
        
        # Filtrage
        quality_opportunities = [opp for opp in opportunities if opp['score'] >= 50]
        quality_opportunities.sort(key=lambda x: x['score'], reverse=True)
        top_picks = quality_opportunities[:20] # On affiche le Top 20 pour avoir du choix manuel
        
        if len(top_picks) < 5:
            remaining = [opp for opp in opportunities if opp not in quality_opportunities]
            remaining.sort(key=lambda x: x['score'], reverse=True)
            top_picks.extend(remaining[:10 - len(top_picks)])

        for i, opp in enumerate(top_picks, 1):
            opp['rank'] = i
        
        # Affichage Terminal Simplifié
        print("\n" + "-"*80)
        print(f"{'Paire':<10} {'Score':<5} {'Signal':<6} {'Prix':<10} {'RSI':<6} {'Tendance':<10}")
        print("-"*80)
        
        for opp in top_picks:
            price_str = f"${opp['price']:.4f}" if opp['price'] else "N/A"
            rsi_str = f"{opp['rsi']:.1f}" if opp['rsi'] else "-"
            print(f"{opp['pair']:<10} {opp['score']:<5} {opp['entry_signal']:<6} {price_str:<10} {rsi_str:<6} {opp['trend']:<10}")
        
        # ==============================================================================
        # 4. GESTION DES ENTRÉES (Bot Auto)
        # ==============================================================================
        my_positions = trader.get_open_positions()
        balance = trader.get_usdt_balance()
        
        TRADE_AMOUNT = 100
        MIN_SCORE = 80 # Le bot est strict (80), vous pouvez être plus souple manuellement
        
        if balance >= TRADE_AMOUNT:
            for opp in top_picks:
                if (opp['score'] >= MIN_SCORE and 
                    opp['entry_signal'] == 'LONG' and 
                    opp['pair'] not in my_positions and
                    opp['stop_loss'] is not None):
                    
                    trader.place_buy_order(
                        symbol=opp['pair'],
                        amount_usdt=TRADE_AMOUNT,
                        current_price=opp['price'], 
                        stop_loss_price=opp['stop_loss'],
                        take_profit_price=opp['take_profit_1']
                    )
                    break 
        
        return top_picks
        
    except Exception as e:
        print(f"\n❌ Erreur scan: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    print("⚡ Scanner Hybride Actif")
    
    shared_data = {'opportunities': [], 'is_scanning': False}
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        trader = PaperTrader()
        balance = trader.get_usdt_balance()
        trades = trader.get_trades_history()
        positions = trader.get_open_positions()
        
        # Template HTML complet (Bot + Analyse Technique)
        HTML = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Crypto Trading Hub</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f0f2f5; padding: 20px; color: #333; margin:0; font-size: 14px; }
                .container { max-width: 1600px; margin: 0 auto; } /* Largeur augmentée pour le tableau complet */
                
                .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
                
                /* Header */
                .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
                .status-badge { background: #e8f5e9; color: #2e7d32; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.9em; }
                .scanning { color: #f57c00; background: #fff3e0; animation: pulse 1.5s infinite; }
                
                /* Wallet */
                .wallet-info { display: flex; gap: 20px; margin-bottom: 10px; }
                .wallet-item { background: #f8f9fa; padding: 15px; border-radius: 8px; flex: 1; text-align: center; border: 1px solid #eee; }
                .wallet-value { font-size: 1.8em; font-weight: bold; color: #2c3e50; }
                .wallet-label { color: #666; font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px; }
                
                /* Tables */
                h2 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; }
                table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9em; }
                th { background-color: #f8f9fa; color: #666; padding: 12px; text-align: left; font-weight: 600; text-transform: uppercase; font-size: 0.8em; }
                td { padding: 10px 12px; border-bottom: 1px solid #eee; vertical-align: middle; }
                tr:hover { background-color: #f1f3f5; }
                
                /* Badges */
                .badge { padding: 4px 8px; border-radius: 4px; color: white; font-weight: 600; font-size: 0.85em; display: inline-block; }
                .bg-green { background-color: #27ae60; }
                .bg-red { background-color: #c0392b; }
                .bg-blue { background-color: #2980b9; }
                .bg-gray { background-color: #95a5a6; }
                
                /* Text Colors */
                .trend-bullish { color: #27ae60; font-weight: bold; }
                .trend-bearish { color: #c0392b; font-weight: bold; }
                .score-high { color: #27ae60; font-weight: 800; }
                .score-med { color: #f39c12; font-weight: 800; }
                .profit { color: #27ae60; font-weight: bold; }
                .loss { color: #c0392b; font-weight: bold; }
                
                /* Details Column */
                .details-text { font-size: 0.85em; color: #555; max-width: 250px; line-height: 1.2; }
                
                @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Crypto Hub : Bot Auto & Analyse</h1>
                    <span class="status-badge {% if is_scanning %}scanning{% endif %}">
                        {% if is_scanning %}🔄 Scan en cours...{% else %}✅ Système Prêt{% endif %}
                    </span>
                </div>

                <div class="card" style="border-left: 5px solid #2980b9;">
                    <h2>🤖 Activité du Bot (Paper Trading)</h2>
                    <div class="wallet-info">
                        <div class="wallet-item">
                            <div class="wallet-value">${{ "%.2f"|format(balance) }}</div>
                            <div class="wallet-label">Solde Total</div>
                        </div>
                        <div class="wallet-item">
                            <div class="wallet-value">{{ positions|length }}</div>
                            <div class="wallet-label">Positions Ouvertes</div>
                        </div>
                        <div class="wallet-item">
                            <div class="wallet-value">{{ trades|length }}</div>
                            <div class="wallet-label">Trades Effectués</div>
                        </div>
                    </div>
                    
                    {% if trades %}
                    <div style="max-height: 200px; overflow-y: auto; margin-top: 15px;">
                        <table>
                            <thead>
                                <tr>
                                    <th>Heure</th>
                                    <th>Type</th>
                                    <th>Paire</th>
                                    <th>Montant</th>
                                    <th>PnL (Résultat)</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for trade in trades[:10] %}
                                <tr>
                                    <td>{{ trade.time }}</td>
                                    <td><span class="badge {% if 'VENTE' in trade.type %}bg-red{% else %}bg-blue{% endif %}">{{ trade.type }}</span></td>
                                    <td><strong>{{ trade.symbol }}</strong></td>
                                    <td>${{ "%.2f"|format(trade.amount_usdt) }}</td>
                                    <td>
                                        {% if trade.pnl is defined and trade.pnl != 0 %}
                                            <span class="{% if trade.pnl > 0 %}profit{% else %}loss{% endif %}">{{ "+$" if trade.pnl > 0 else "-$" }}{{ "%.2f"|format(trade.pnl|abs) }}</span>
                                        {% else %}-{% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    {% endif %}
                </div>

                <div class="card" style="border-left: 5px solid #27ae60;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h2>📡 Scanner d'Opportunités (1H) - Pour Trading Manuel</h2>
                        <span style="font-size:0.9em; color:#666;">MAJ: {{ last_update }}</span>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Paire</th>
                                <th>Score</th>
                                <th>Tendance</th>
                                <th>Signal</th>
                                <th>Confiance</th>
                                <th>Prix</th>
                                <th>SL / TP</th>
                                <th>RSI</th>
                                <th>Détails Techniques</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% if not opportunities %}
                            <tr><td colspan="10" style="text-align:center; padding:30px">Chargement des données...</td></tr>
                            {% else %}
                            {% for opp in opportunities %}
                            <tr>
                                <td>{{ opp.rank }}</td>
                                <td><strong>{{ opp.pair }}</strong></td>
                                
                                <td class="{% if opp.score > 80 %}score-high{% else %}score-med{% endif %}" style="font-size: 1.2em;">
                                    {{ opp.score }}
                                </td>
                                
                                <td class="{% if opp.trend == 'Bullish' %}trend-bullish{% elif opp.trend == 'Bearish' %}trend-bearish{% else %}trend-neutral{% endif %}">
                                    {{ opp.trend }}
                                </td>
                                
                                <td>
                                    <span class="badge {% if opp.entry_signal == 'LONG' %}bg-green{% elif opp.entry_signal == 'SHORT' %}bg-red{% else %}bg-gray{% endif %}">
                                        {{ opp.entry_signal }}
                                    </span>
                                </td>
                                
                                <td>{{ opp.confidence }}%</td>
                                
                                <td style="font-family: monospace;">${{ "%.4f"|format(opp.price) if opp.price else "N/A" }}</td>
                                
                                <td style="font-family: monospace; font-size: 0.9em;">
                                    <span style="color:#c0392b">SL: {{ "%.4f"|format(opp.stop_loss) if opp.stop_loss else "-" }}</span><br>
                                    <span style="color:#27ae60">TP: {{ "%.4f"|format(opp.take_profit_1) if opp.take_profit_1 else "-" }}</span>
                                </td>
                                
                                <td style="font-weight: bold; color: {% if opp.rsi and opp.rsi < 30 %}#27ae60{% elif opp.rsi and opp.rsi > 70 %}#c0392b{% else %}#333{% endif %}">
                                    {{ "%.1f"|format(opp.rsi) if opp.rsi else "-" }}
                                </td>
                                
                                <td class="details-text">
                                    {{ opp.details }}
                                </td>
                            </tr>
                            {% endfor %}
                            {% endif %}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <script>
                setTimeout(function(){ location.reload(); }, 30000); // Auto-refresh 30s
            </script>
        </body>
        </html>
        """
        
        return render_template_string(HTML, 
                                     opportunities=shared_data['opportunities'], 
                                     last_update=datetime.now().strftime('%H:%M'),
                                     is_scanning=shared_data['is_scanning'],
                                     balance=balance,
                                     trades=trades,
                                     positions=positions)

    def run_loop():
        while True:
            shared_data['is_scanning'] = True
            try:
                shared_data['opportunities'] = run_scanner()
            except Exception as e:
                print(f"Erreur loop: {e}")
            finally:
                shared_data['is_scanning'] = False
            
            print("💤 Pause de 15 min...")
            time.sleep(900)

    scanner_thread = threading.Thread(target=run_loop, daemon=True)
    scanner_thread.start()
    
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()