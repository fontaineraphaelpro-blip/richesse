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
        # Réduire à 30 paires pour accélérer le scan initial
        pairs = get_top_usdt_pairs(limit=30)
        
        if not pairs:
            print("❌ Aucune paire trouvée. Arrêt du scanner.")
            return []
        
        # 2. Récupérer les prix réels et générer les données OHLCV pour scalping (15min)
        print("\n📊 Étape 2: Récupération des prix réels et génération OHLCV (15min, 200 bougies)...")
        print("💡 Mode SCALPING - Récupération des prix réels depuis CryptoCompare API publique")
        data, real_prices = fetch_multiple_pairs(pairs, interval='15m', limit=200)
        
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
            
            # UTILISER LE PRIX RÉEL RÉCUPÉRÉ, pas le prix généré
            # Le prix réel est toujours le plus à jour
            current_price = real_prices.get(symbol)
            if not current_price or current_price <= 0:
                # Fallback: utiliser le prix du DataFrame si pas de prix réel
                current_price = indicators.get('current_price')
                if current_price:
                    print(f"⚠️ {symbol}: Prix réel non disponible, utilisation prix généré ${current_price:.4f}")
            
            # Détecter le support
            support = find_swing_low(df, lookback=30)
            support_distance = None
            
            if current_price and support:
                support_distance = calculate_distance_to_support(current_price, support)
            
            # Calculer le score d'opportunité (avec DataFrame pour résistance)
            score_data = calculate_opportunity_score(indicators, support_distance, df)
            
            # Ajouter à la liste des opportunités avec toutes les infos scalping
            opportunities.append({
                'pair': symbol,
                'score': score_data['score'],
                'trend': score_data['trend'],
                'rsi': indicators.get('rsi14'),
                'signal': score_data['signal'],
                'price': current_price,  # PRIX RÉEL récupéré depuis CoinGecko
                # Signaux scalping
                'entry_signal': score_data.get('entry_signal', 'NEUTRAL'),
                'entry_price': score_data.get('entry_price'),
                'stop_loss': score_data.get('stop_loss'),
                'take_profit_1': score_data.get('take_profit_1'),
                'take_profit_2': score_data.get('take_profit_2'),
                'risk_reward_ratio': score_data.get('risk_reward_ratio'),
                'exit_signal': score_data.get('exit_signal', 'HOLD'),
                'confidence': score_data.get('confidence', 0),
                # Indicateurs supplémentaires
                'ema9': indicators.get('ema9'),
                'ema21': indicators.get('ema21'),
                'macd': indicators.get('macd'),
                'atr_percent': indicators.get('atr_percent'),
                'momentum_percent': indicators.get('momentum_percent'),
                'volume_ratio': (indicators.get('current_volume') / indicators.get('volume_ma20')) if (indicators.get('current_volume') and indicators.get('volume_ma20') and indicators.get('volume_ma20') > 0) else None
            })
        
        print(f"\n✅ {len(opportunities)} paires analysées")
        
        # 4. Filtrer UNIQUEMENT les opportunités SHORT de qualité
        # Score >= 60, signal SHORT uniquement, confiance >= 70 (avec toutes les données)
        quality_opportunities = [
            opp for opp in opportunities 
            if opp['score'] >= 60 
            and opp.get('entry_signal') == 'SHORT'  # UNIQUEMENT SHORT
            and opp.get('confidence', 0) >= 70  # Confiance élevée avec toutes les données
        ]
        
        print(f"📊 {len(quality_opportunities)} opportunités SHORT de qualité trouvées (score >= 60, confiance >= 70, 8+ confirmations)")
        
        # Trier par score décroissant et prendre le Top 10
        quality_opportunities.sort(key=lambda x: x['score'], reverse=True)
        top_10 = quality_opportunities[:10]
        
        # Si moins de 10 opportunités de qualité, compléter avec les meilleures autres
        if len(top_10) < 10:
            remaining = [opp for opp in opportunities if opp not in quality_opportunities]
            remaining.sort(key=lambda x: x['score'], reverse=True)
            top_10.extend(remaining[:10 - len(top_10)])
        
        # Ajouter le rank
        for i, opp in enumerate(top_10, 1):
            opp['rank'] = i
        
        # 5. Afficher les résultats dans le terminal
        print("\n" + "="*80)
        print("🏆 TOP 10 OPPORTUNITÉS SCALPING")
        print("="*80)
        print(f"{'Rank':<6} {'Pair':<12} {'Score':<7} {'Entry':<8} {'Entry $':<10} {'Stop $':<10} {'TP1 $':<10} {'R/R':<6}")
        print("-"*80)
        
        for opp in top_10:
            entry_signal = opp.get('entry_signal', 'N/A')
            entry_price = f"${opp['entry_price']:.4f}" if opp.get('entry_price') else "N/A"
            stop_loss = f"${opp['stop_loss']:.4f}" if opp.get('stop_loss') else "N/A"
            tp1 = f"${opp['take_profit_1']:.4f}" if opp.get('take_profit_1') else "N/A"
            rr = f"{opp['risk_reward_ratio']:.2f}" if opp.get('risk_reward_ratio') else "N/A"
            print(f"#{opp['rank']:<5} {opp['pair']:<12} {opp['score']:<7} {entry_signal:<8} {entry_price:<10} {stop_loss:<10} {tp1:<10} {rr:<6}")
        
        print("="*80)
        
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
    print("⚡ Scalping Crypto Scanner Web - Démarrage")
    print("📌 Mode SCALPING (15min) - Boucle continue (mise à jour toutes les heures)")
    print("🛑 Appuyez sur Ctrl+C pour arrêter\n")
    
    # Variable partagée pour les opportunités (vide au départ)
    opportunities_data = {'data': []}
    scanning_status = {'is_scanning': False}
    
    # Créer l'application Flask avec fonction dynamique
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        """Page d'accueil avec le tableau des opportunités."""
        # Utiliser le template directement
        from flask import render_template_string
        from datetime import datetime
        
        # Vérifier si le scan est en cours ou si les données sont disponibles
        is_scanning = scanning_status.get('is_scanning', False)
        opportunities = opportunities_data.get('data', [])
        
        HTML_TEMPLATE = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Scalping Crypto Scanner</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                .container { max-width: 1600px; margin: 0 auto; }
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
                .header .subtitle {
                    color: #666;
                    font-size: 1.1em;
                    margin-top: 5px;
                }
                .last-update { color: #666; font-size: 0.9em; margin-top: 10px; }
                .main-content {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    overflow-x: auto;
                }
                table { width: 100%; border-collapse: collapse; font-size: 0.9em; min-width: 1400px; }
                thead { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                th { padding: 12px 8px; text-align: left; font-weight: 600; text-transform: uppercase; font-size: 0.85em; white-space: nowrap; }
                td { padding: 12px 8px; border-bottom: 1px solid #e9ecef; font-size: 0.9em; }
                tbody tr:hover { background: #f8f9fa; }
                tbody tr:nth-child(even) { background: #fafafa; }
                .rank { font-weight: bold; font-size: 1.1em; color: #667eea; }
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
                .entry-long { color: #28a745; font-weight: bold; }
                .entry-short { color: #dc3545; font-weight: bold; }
                .entry-neutral { color: #6c757d; }
                .price-info { font-family: 'Courier New', monospace; font-size: 0.9em; }
                .rr-ratio {
                    font-weight: bold;
                    padding: 3px 8px;
                    border-radius: 4px;
                    display: inline-block;
                }
                .rr-good { background: #d4edda; color: #155724; }
                .rr-medium { background: #fff3cd; color: #856404; }
                .rr-bad { background: #f8d7da; color: #721c24; }
                .confidence {
                    font-size: 0.85em;
                    color: #666;
                }
                .footer {
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    color: white;
                    font-size: 0.9em;
                }
                .info-badge {
                    display: inline-block;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 0.8em;
                    margin: 2px;
                }
                .badge-green { background: #d4edda; color: #155724; }
                .badge-yellow { background: #fff3cd; color: #856404; }
                .badge-red { background: #f8d7da; color: #721c24; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚡ Scalping Crypto Scanner</h1>
                    <p class="subtitle">Signaux d'entrée et de sortie pour trading à court terme (15min)</p>
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
                                <th>Prix</th>
                                <th>Entry</th>
                                <th>Entry $</th>
                                <th>Stop $</th>
                                <th>TP1 $</th>
                                <th>TP2 $</th>
                                <th>R/R</th>
                                <th>RSI</th>
                                <th>Trend</th>
                                <th>Conf.</th>
                                <th>Exit</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% if not opportunities %}
                            <tr>
                                <td colspan="14" style="text-align: center; padding: 50px;">
                                    <h2>⏳ Scan en cours...</h2>
                                    <p>Récupération des prix réels et analyse des cryptomonnaies en cours.</p>
                                    <p>Veuillez patienter, les données seront disponibles dans quelques instants.</p>
                                    <p style="margin-top: 20px;"><small>Cette page se rafraîchira automatiquement dans 10 secondes.</small></p>
                                    <script>
                                        setTimeout(function(){ location.reload(); }, 10000);
                                    </script>
                                </td>
                            </tr>
                            {% else %}
                            {% for opp in opportunities %}
                            <tr>
                                <td class="rank">#{{ opp.rank }}</td>
                                <td><strong>{{ opp.pair }}</strong></td>
                                <td>
                                    <span class="score {% if opp.score >= 80 %}score-high{% elif opp.score >= 60 %}score-medium{% else %}score-low{% endif %}">
                                        {{ opp.score }}
                                    </span>
                                </td>
                                <td class="price-info">${{ "%.4f"|format(opp.price) if opp.price else "N/A" }}</td>
                                <td>
                                    <span class="{% if opp.entry_signal == 'LONG' %}entry-long{% elif opp.entry_signal == 'SHORT' %}entry-short{% else %}entry-neutral{% endif %}">
                                        {{ opp.entry_signal if opp.entry_signal else 'N/A' }}
                                    </span>
                                </td>
                                <td class="price-info">${{ "%.4f"|format(opp.entry_price) if opp.entry_price else "N/A" }}</td>
                                <td class="price-info">${{ "%.4f"|format(opp.stop_loss) if opp.stop_loss else "N/A" }}</td>
                                <td class="price-info">${{ "%.4f"|format(opp.take_profit_1) if opp.take_profit_1 else "N/A" }}</td>
                                <td class="price-info">${{ "%.4f"|format(opp.take_profit_2) if opp.take_profit_2 else "N/A" }}</td>
                                <td>
                                    {% if opp.risk_reward_ratio %}
                                        <span class="rr-ratio {% if opp.risk_reward_ratio >= 2 %}rr-good{% elif opp.risk_reward_ratio >= 1.5 %}rr-medium{% else %}rr-bad{% endif %}">
                                            {{ "%.2f"|format(opp.risk_reward_ratio) }}
                                        </span>
                                    {% else %}
                                        N/A
                                    {% endif %}
                                </td>
                                <td>{{ "%.1f"|format(opp.rsi) if opp.rsi else "N/A" }}</td>
                                <td class="{% if opp.trend == 'Bullish' %}trend-bullish{% else %}trend-bearish{% endif %}">
                                    {{ opp.trend }}
                                </td>
                                <td>
                                    <span class="confidence">
                                        {{ opp.confidence if opp.confidence else 0 }}%
                                    </span>
                                </td>
                                <td style="font-size: 0.85em;">{{ opp.exit_signal if opp.exit_signal else 'HOLD' }}</td>
                            </tr>
                            {% endfor %}
                            {% endif %}
                        </tbody>
                    </table>
                </div>
                <div class="footer">
                    <p><strong>⚠️ Avertissement:</strong> Ce scanner fournit des indications statistiques pour le scalping, pas des conseils financiers.</p>
                    <p>Ne pas utiliser pour des ordres automatiques. Toujours faire vos propres recherches (DYOR). Risques élevés en scalping.</p>
                    <p style="margin-top: 10px;"><strong>Légende:</strong> Entry = Signal d'entrée | TP1/TP2 = Take Profit 1/2 | R/R = Ratio Risque/Récompense | Conf. = Confiance</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        last_update = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        return render_template_string(HTML_TEMPLATE, 
                                     opportunities=opportunities, 
                                     last_update=last_update,
                                     is_scanning=is_scanning)
    
    @app.route('/health')
    def health():
        """Route de santé."""
        return {'status': 'ok', 'opportunities_count': len(opportunities_data['data'])}, 200
    
    # Fonction pour exécuter le scanner en arrière-plan
    def run_scanner_background():
        """Exécute le scanner en arrière-plan."""
        scanning_status['is_scanning'] = True
        try:
            print("🚀 Démarrage du scan initial en arrière-plan...")
            new_opportunities = run_scanner()
            opportunities_data['data'] = new_opportunities
            print("✅ Scan initial terminé!")
        except Exception as e:
            print(f"❌ Erreur lors du scan: {e}")
        finally:
            scanning_status['is_scanning'] = False
    
    # Fonction pour mettre à jour les opportunités toutes les heures
    def update_opportunities():
        """Met à jour les opportunités toutes les heures."""
        while True:
            time.sleep(3600)  # Attendre 1 heure
            scanning_status['is_scanning'] = True
            try:
                print("\n🔄 Mise à jour automatique...")
                new_opportunities = run_scanner()
                opportunities_data['data'] = new_opportunities
            except Exception as e:
                print(f"❌ Erreur lors de la mise à jour: {e}")
            finally:
                scanning_status['is_scanning'] = False
    
    # Lancer le scanner initial en arrière-plan
    import threading
    scanner_thread = threading.Thread(target=run_scanner_background, daemon=True)
    scanner_thread.start()
    
    # Lancer la mise à jour périodique en arrière-plan
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
