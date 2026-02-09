"""
Script principal du Crypto Signal Scanner Web.
Scanne les cryptos, calcule les scores et affiche les résultats dans une page web.
"""

import time
import os
from datetime import datetime
from flask import Flask

from fetch_pairs import get_top_usdt_pairs
from data_fetcher import fetch_multiple_pairs
from indicators import calculate_indicators
from support import find_swing_low, calculate_distance_to_support
from scorer import calculate_opportunity_score
from web_server import create_app


def run_scanner():
    """
    Exécute un scan complet et retourne les Top 10 opportunités.
    """
    print("\n" + "="*60)
    print("🚀 CRYPTO SIGNAL SCANNER - Démarrage du scan")
    print("="*60)
    print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    try:
        # 1. Récupérer les principales paires USDT
        print("📋 Étape 1: Récupération des paires USDT...")
        pairs = get_top_usdt_pairs(limit=50)
        
        if not pairs:
            print("❌ Aucune paire trouvée. Arrêt du scanner.")
            return []
        
        # 2. Générer les données OHLCV (données de démonstration)
        print("\n📊 Étape 2: Génération des données OHLCV (1H, 200 bougies)...")
        print("💡 Utilisation de données de démonstration (libres de droit)")
        data = fetch_multiple_pairs(pairs, interval='1h', limit=200)
        
        if not data:
            print("❌ Aucune donnée récupérée. Arrêt du scanner.")
            return []
        
        # 3. Calculer les indicateurs et scores pour chaque paire
        print("\n🔍 Étape 3: Calcul des indicateurs et scores...")
        opportunities = []
        total = len(data)
        
        for i, (symbol, df) in enumerate(data.items(), 1):
            print(f"📊 Analyse {symbol} ({i}/{total})...", end='\r')
            
            # Calculer les indicateurs techniques
            indicators = calculate_indicators(df)
            
            # Détecter le support
            support = find_swing_low(df, lookback=30)
            current_price = indicators.get('current_price')
            support_distance = None
            
            if current_price and support:
                support_distance = calculate_distance_to_support(current_price, support)
            
            # Calculer le score d'opportunité
            score_data = calculate_opportunity_score(indicators, support_distance)
            
            # Ajouter à la liste des opportunités
            opportunities.append({
                'pair': symbol,
                'score': score_data['score'],
                'trend': score_data['trend'],
                'rsi': indicators.get('rsi14'),
                'signal': score_data['signal'],
                'price': current_price
            })
        
        print(f"\n✅ {len(opportunities)} paires analysées")
        
        # 4. Trier par score décroissant et prendre le Top 10
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        top_10 = opportunities[:10]
        
        # Ajouter le rank
        for i, opp in enumerate(top_10, 1):
            opp['rank'] = i
        
        # 5. Afficher les résultats dans le terminal
        print("\n" + "="*60)
        print("🏆 TOP 10 OPPORTUNITÉS")
        print("="*60)
        print(f"{'Rank':<6} {'Pair':<15} {'Score':<8} {'Trend':<10} {'RSI':<8} {'Signal':<30}")
        print("-"*60)
        
        for opp in top_10:
            rsi_display = f"{opp['rsi']:.1f}" if opp['rsi'] else "N/A"
            print(f"#{opp['rank']:<5} {opp['pair']:<15} {opp['score']:<8} {opp['trend']:<10} {rsi_display:<8} {opp['signal']:<30}")
        
        print("="*60)
        
        return top_10
        
    except Exception as e:
        print(f"\n❌ Erreur lors du scan: {e}")
        import traceback
        traceback.print_exc()
        return []


def main():
    """
    Fonction principale avec serveur web Flask intégré.
    """
    print("🚀 Crypto Signal Scanner Web - Démarrage")
    print("📌 Mode: Boucle continue (mise à jour toutes les heures)")
    print("🛑 Appuyez sur Ctrl+C pour arrêter\n")
    
    # Premier scan
    opportunities = run_scanner()
    
    # Variable partagée pour les opportunités
    opportunities_data = {'data': opportunities}
    
    # Créer l'application Flask avec fonction dynamique
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        """Page d'accueil avec le tableau des opportunités."""
        # Utiliser le template directement
        from flask import render_template_string
        from datetime import datetime
        
        HTML_TEMPLATE = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Crypto Signal Scanner</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                .container { max-width: 1200px; margin: 0 auto; }
                .header {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 30px;
                    margin-bottom: 20px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    text-align: center;
                }
                .header h1 {
                    font-size: 2.5em;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                }
                .last-update { color: #666; font-size: 0.9em; margin-top: 10px; }
                .main-content {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }
                table { width: 100%; border-collapse: collapse; font-size: 1em; }
                thead { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                th { padding: 15px; text-align: left; font-weight: 600; text-transform: uppercase; font-size: 0.9em; }
                td { padding: 15px; border-bottom: 1px solid #e9ecef; }
                tbody tr:hover { background: #f8f9fa; }
                tbody tr:nth-child(even) { background: #fafafa; }
                .rank { font-weight: bold; font-size: 1.2em; color: #667eea; }
                .score {
                    font-weight: bold;
                    padding: 5px 10px;
                    border-radius: 5px;
                    display: inline-block;
                }
                .score-high { background: #d4edda; color: #155724; }
                .score-medium { background: #fff3cd; color: #856404; }
                .score-low { background: #f8d7da; color: #721c24; }
                .trend-bullish { color: #28a745; font-weight: bold; }
                .trend-bearish { color: #dc3545; font-weight: bold; }
                .footer {
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    color: white;
                    font-size: 0.9em;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Crypto Signal Scanner</h1>
                    <p>Top 10 Opportunités Crypto</p>
                    <div class="last-update">
                        Dernière mise à jour: {{ last_update }}
                    </div>
                </div>
                <div class="main-content">
                    <table>
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Pair</th>
                                <th>Score</th>
                                <th>Trend</th>
                                <th>RSI</th>
                                <th>Signal</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for opp in opportunities %}
                            <tr>
                                <td class="rank">#{{ opp.rank }}</td>
                                <td><strong>{{ opp.pair }}</strong></td>
                                <td>
                                    <span class="score {% if opp.score >= 80 %}score-high{% elif opp.score >= 60 %}score-medium{% else %}score-low{% endif %}">
                                        {{ opp.score }}
                                    </span>
                                </td>
                                <td class="{% if opp.trend == 'Bullish' %}trend-bullish{% else %}trend-bearish{% endif %}">
                                    {{ opp.trend }}
                                </td>
                                <td>{{ "%.1f"|format(opp.rsi) if opp.rsi else "N/A" }}</td>
                                <td>{{ opp.signal }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                <div class="footer">
                    <p><strong>⚠️ Avertissement:</strong> Ce scanner fournit des indications statistiques, pas des conseils financiers.</p>
                    <p>Ne pas utiliser pour des ordres automatiques. Toujours faire vos propres recherches (DYOR).</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        last_update = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        return render_template_string(HTML_TEMPLATE, opportunities=opportunities_data['data'], last_update=last_update)
    
    @app.route('/health')
    def health():
        """Route de santé."""
        return {'status': 'ok', 'opportunities_count': len(opportunities_data['data'])}, 200
    
    # Fonction pour mettre à jour les opportunités en arrière-plan
    def update_opportunities():
        """Met à jour les opportunités toutes les heures."""
        while True:
            time.sleep(3600)  # Attendre 1 heure
            print("\n🔄 Mise à jour automatique...")
            new_opportunities = run_scanner()
            opportunities_data['data'] = new_opportunities
    
    # Lancer la mise à jour en arrière-plan
    import threading
    update_thread = threading.Thread(target=update_opportunities, daemon=True)
    update_thread.start()
    
    # Démarrer le serveur Flask
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🌐 Serveur web démarré sur http://0.0.0.0:{port}")
    print(f"📱 Dashboard accessible depuis votre navigateur\n")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du serveur...")
    except Exception as e:
        print(f"\n❌ Erreur serveur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
