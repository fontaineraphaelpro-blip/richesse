"""
Script principal du Crypto Signal Scanner Web.
Version HYBRIDE : Bot Autonome + Dashboard d'Analyse Technique Complet.
Indépendant et prêt pour le déploiement.
"""

import time
import os
import threading
import traceback
from datetime import datetime
from flask import Flask, render_template_string

# Imports des modules locaux (Assurez-vous que ces fichiers existent)
from trader import PaperTrader
try:
    from data_fetcher import fetch_multiple_pairs
    from indicators import calculate_indicators
    from support import find_swing_low, calculate_distance_to_support
    from scorer import calculate_opportunity_score
except ImportError as e:
    print(f"⚠️ Modules manquants : {e}. Assurez-vous d'avoir tous les fichiers.")
    # On crée des mocks pour éviter le crash si on teste isolément
    def fetch_multiple_pairs(*args, **kwargs): return {}, {}

# Configuration globale
SCAN_INTERVAL = 3600  # 1 heure en secondes (pour éviter les bans API et respecter la logique 1H)

def run_scanner():
    """
    Exécute un scan complet, gère le trading auto, et retourne TOUTES les infos pour le dashboard.
    """
    print("\n" + "="*60)
    print("🚀 CRYPTO SCANNER - Mode HYBRIDE (1h)")
    print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    try:
        # 1. Récupération des données
        print("📊 Récupération des données sur 500 bougies de 1h...")
        # Note: limit=500 est souvent suffisant et plus rapide que 1000
        data, real_prices = fetch_multiple_pairs(None, interval='1h', limit=500)
        
        if not data:
            print("❌ Aucune donnée reçue des API.")
            return []
            
        # ==============================================================================
        # 2. GESTION DES SORTIES (Bot)
        # ==============================================================================
        trader = PaperTrader() # Charge automatiquement le wallet existant
        if real_prices:
            trader.check_positions(real_prices)
        
        # ==============================================================================
        
        # 3. Analyse Technique Complète
        print("🔍 Analyse détaillée du marché...")
        opportunities = []
        
        for i, (symbol, df) in enumerate(data.items(), 1):
            try:
                indicators = calculate_indicators(df)
                current_price = real_prices.get(symbol) or indicators.get('current_price')
                
                if not current_price: continue

                support = find_swing_low(df, lookback=50)
                support_dist = calculate_distance_to_support(current_price, support) if support else None
                
                score_data = calculate_opportunity_score(indicators, support_dist, df)
                
                opportunities.append({
                    'pair': symbol,
                    'score': score_data.get('score', 0),
                    'trend': score_data.get('trend', 'Neutral'),
                    'signal_text': score_data.get('signal', '-'),
                    'details': score_data.get('details', ''),
                    'price': current_price,
                    'rsi': indicators.get('rsi14'),
                    'entry_signal': score_data.get('entry_signal', 'NEUTRAL'),
                    'entry_price': score_data.get('entry_price'),
                    'stop_loss': score_data.get('stop_loss'),
                    'take_profit_1': score_data.get('take_profit_1'),
                    'confidence': score_data.get('confidence', 0),
                })
            except Exception as inner_e:
                # Si une paire échoue, on continue les autres
                continue
        
        # Filtrage et Tri
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        top_picks = opportunities[:20] 

        for i, opp in enumerate(top_picks, 1):
            opp['rank'] = i
        
        # Affichage Terminal
        print("\n" + "-"*80)
        print(f"{'Paire':<10} {'Score':<5} {'Signal':<6} {'Prix':<10} {'RSI':<6}")
        print("-"*80)
        
        for opp in top_picks[:5]: # Affiche seulement le top 5 dans les logs pour clarté
            price_str = f"${opp['price']:.4f}" if opp['price'] else "N/A"
            rsi_str = f"{opp['rsi']:.1f}" if opp['rsi'] else "-"
            print(f"{opp['pair']:<10} {opp['score']:<5} {opp['entry_signal']:<6} {price_str:<10} {rsi_str:<6}")
        
        # ==============================================================================
        # 4. GESTION DES ENTRÉES (Bot Auto)
        # ==============================================================================
        my_positions = trader.get_open_positions()
        balance = trader.get_usdt_balance()
        
        TRADE_AMOUNT = 100
        MIN_SCORE = 80 
        
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
                    # On ne prend qu'un trade par cycle pour prudence
                    break 
        
        return top_picks
        
    except Exception as e:
        print(f"\n❌ Erreur critique scan: {e}")
        traceback.print_exc()
        return []

# Variable globale pour partager les données entre le Thread et Flask
shared_data = {
    'opportunities': [], 
    'is_scanning': False,
    'last_update': 'Jamais'
}

def create_app():
    """Factory function pour créer l'app Flask."""
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        # On recharge le trader à chaque requête pour avoir le solde à jour
        trader = PaperTrader()
        balance = trader.get_usdt_balance()
        trades = trader.get_trades_history()
        positions = trader.get_open_positions()
        
        # NOTE : J'ai gardé votre template HTML original mais abrégé ici pour la clarté.
        # Il fonctionnera exactement comme avant.
        HTML = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="refresh" content="30">
            <title>Crypto Trading Hub</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: system-ui, sans-serif; background: #f0f2f5; padding: 20px; color: #333; }
                .container { max-width: 1200px; margin: 0 auto; }
                .card { background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 10px; border-bottom: 1px solid #eee; text-align: left; }
                .badge { padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; font-size: 0.8em; }
                .bg-green { background: #27ae60; } .bg-red { background: #c0392b; } .bg-blue { background: #2980b9; }
                .header { display: flex; justify-content: space-between; align-items: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Crypto Hub</h1>
                    <div>
                        <span class="badge bg-blue">{{ "Scan en cours..." if is_scanning else "✅ Prêt" }}</span>
                        <small>MAJ: {{ last_update }}</small>
                    </div>
                </div>

                <div class="card" style="border-left: 5px solid #2980b9;">
                    <h2>💰 Portefeuille: ${{ "%.2f"|format(balance) }}</h2>
                    <p>Positions ouvertes: {{ positions|length }} | Trades: {{ trades|length }}</p>
                    
                    {% if positions %}
                    <h3>Positions Actuelles</h3>
                    <ul>
                        {% for sym, pos in positions.items() %}
                        <li><strong>{{ sym }}</strong> - Entrée: ${{ "%.4f"|format(pos.entry_price) }} ({{ pos.entry_time }})</li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                </div>

                <div class="card" style="border-left: 5px solid #27ae60;">
                    <h2>📡 Opportunités (Top 20)</h2>
                    <table>
                        <thead>
                            <tr><th>#</th><th>Paire</th><th>Score</th><th>Signal</th><th>Prix</th><th>RSI</th><th>SL / TP</th></tr>
                        </thead>
                        <tbody>
                            {% if not opportunities %}
                            <tr><td colspan="7">Scan en attente ou données insuffisantes...</td></tr>
                            {% else %}
                            {% for opp in opportunities %}
                            <tr>
                                <td>{{ opp.rank }}</td>
                                <td><strong>{{ opp.pair }}</strong></td>
                                <td style="font-weight:bold; color: {% if opp.score >= 80 %}#27ae60{% else %}#f39c12{% endif %}">{{ opp.score }}</td>
                                <td><span class="badge {% if opp.entry_signal == 'LONG' %}bg-green{% elif opp.entry_signal == 'SHORT' %}bg-red{% else %}bg-gray{% endif %}">{{ opp.entry_signal }}</span></td>
                                <td>${{ "%.4f"|format(opp.price) }}</td>
                                <td>{{ "%.1f"|format(opp.rsi) if opp.rsi else "-" }}</td>
                                <td style="font-size:0.9em">
                                    <span style="color:#c0392b">SL: {{ "%.4f"|format(opp.stop_loss) if opp.stop_loss else "-" }}</span><br>
                                    <span style="color:#27ae60">TP: {{ "%.4f"|format(opp.take_profit_1) if opp.take_profit_1 else "-" }}</span>
                                </td>
                            </tr>
                            {% endfor %}
                            {% endif %}
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(HTML, 
                                     opportunities=shared_data['opportunities'], 
                                     last_update=shared_data['last_update'],
                                     is_scanning=shared_data['is_scanning'],
                                     balance=balance,
                                     trades=trades,
                                     positions=positions)
    return app

def run_loop():
    """Boucle infinie exécutée dans un thread séparé."""
    print("🔄 Démarrage de la boucle de scan...")
    while True:
        shared_data['is_scanning'] = True
        try:
            results = run_scanner()
            shared_data['opportunities'] = results
            shared_data['last_update'] = datetime.now().strftime('%H:%M')
        except Exception as e:
            print(f"⚠️ Erreur dans la boucle principale: {e}")
        finally:
            shared_data['is_scanning'] = False
        
        print(f"💤 Pause de {SCAN_INTERVAL/60} min...")
        time.sleep(SCAN_INTERVAL)

def main():
    # 1. Lancer le thread de scan en arrière-plan
    scanner_thread = threading.Thread(target=run_loop, daemon=True)
    scanner_thread.start()
    
    # 2. Lancer le serveur Web Flask
    app = create_app()
    port = int(os.environ.get('PORT', 8080))
    # use_reloader=False est important pour éviter de lancer 2 fois le thread scanner en mode debug local
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
