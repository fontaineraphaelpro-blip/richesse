"""
Script principal du Crypto Signal Scanner Web.
Scanne les cryptos, calcule les scores et affiche les résultats dans une page web.
Version adaptée pour Binance (Données réelles) et critères assouplis.
"""

import time
import os
from datetime import datetime
from flask import Flask, render_template_string
import threading

# On n'importe plus fetch_pairs car la liste est dans data_fetcher
from data_fetcher import fetch_multiple_pairs
from indicators import calculate_indicators
from support import find_swing_low, calculate_distance_to_support
from scorer import calculate_opportunity_score

def run_scanner():
    """
    Exécute un scan complet et retourne les Top 10 opportunités.
    """
    print("\n" + "="*60)
    print("🚀 CRYPTO SIGNAL SCANNER - Démarrage du scan (Données Réelles Binance)")
    print("="*60)
    print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    try:
        # 1. Récupération des données (La liste est maintenant gérée par data_fetcher)
        print("📊 Étape 1 & 2: Récupération des prix réels et génération OHLCV...")
        # On passe None pour utiliser la liste par défaut (TOP_USDT_PAIRS) définie dans data_fetcher
        # On utilise limit=200 pour avoir assez d'historique pour les indicateurs
        data, real_prices = fetch_multiple_pairs(None, interval='15m', limit=200)
        
        if not data:
            print("❌ Aucune donnée récupérée. Arrêt du scanner.")
            return []
        
        # 2. Calculer les indicateurs et scores pour chaque paire
        print("\n🔍 Étape 3: Analyse technique et calcul des scores...")
        opportunities = []
        total = len(data)
        
        for i, (symbol, df) in enumerate(data.items(), 1):
            # Calculer les indicateurs techniques
            indicators = calculate_indicators(df)
            
            # Le prix réel est dans le dictionnaire real_prices
            current_price = real_prices.get(symbol)
            if not current_price:
                 current_price = indicators.get('current_price')

            # Détecter le support
            support = find_swing_low(df, lookback=30)
            support_distance = None
            
            if current_price and support:
                support_distance = calculate_distance_to_support(current_price, support)
            
            # Calculer le score d'opportunité
            score_data = calculate_opportunity_score(indicators, support_distance, df)
            
            # Ajouter à la liste des opportunités
            opportunities.append({
                'pair': symbol,
                'score': score_data['score'],
                'trend': score_data['trend'],
                'rsi': indicators.get('rsi14'),
                'signal': score_data['signal'],
                'price': current_price,
                # Signaux scalping
                'entry_signal': score_data.get('entry_signal', 'NEUTRAL'),
                'entry_price': score_data.get('entry_price'),
                'stop_loss': score_data.get('stop_loss'),
                'take_profit_1': score_data.get('take_profit_1'),
                'take_profit_2': score_data.get('take_profit_2'),
                'risk_reward_ratio': score_data.get('risk_reward_ratio'),
                'exit_signal': score_data.get('exit_signal', 'HOLD'),
                'confidence': score_data.get('confidence', 0),
                # Indicateurs supplémentaires pour le frontend
                'ema9': indicators.get('ema9'),
                'ema21': indicators.get('ema21'),
                'macd': indicators.get('macd'),
                'atr_percent': indicators.get('atr_percent'),
                'momentum_percent': indicators.get('momentum_percent'),
                'volume_ratio': (indicators.get('current_volume') / indicators.get('volume_ma20')) if (indicators.get('current_volume') and indicators.get('volume_ma20') and indicators.get('volume_ma20') > 0) else None
            })
        
        print(f"\n✅ {len(opportunities)} paires analysées")
        
        # 3. Filtrage ADAPTÉ AUX DONNÉES RÉELLES (Moins strict)
        # On accepte les scores >= 50 et confiance >= 50 pour capturer plus d'opportunités
        quality_opportunities = []
        for opp in opportunities:
            if (opp.get('entry_signal') in ['SHORT', 'LONG'] and 
                opp.get('score', 0) >= 50 and 
                opp.get('confidence', 0) >= 50):
                
                quality_opportunities.append(opp)
        
        print(f"📊 {len(quality_opportunities)} opportunités potentielles trouvées (Score >= 50, Conf >= 50).")
        
        # Trier par score décroissant
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        # Si on a trouvé des opportunités de qualité, on les met en premier, sinon on prend le top global
        if quality_opportunities:
             quality_opportunities.sort(key=lambda x: x['score'], reverse=True)
             top_10 = quality_opportunities[:10]
             # Si moins de 10, on complète avec les meilleures du reste
             if len(top_10) < 10:
                 remaining = [opp for opp in opportunities if opp not in quality_opportunities]
                 top_10.extend(remaining[:10 - len(top_10)])
        else:
             top_10 = opportunities[:10]

        # Ajouter le rank
        for i, opp in enumerate(top_10, 1):
            opp['rank'] = i
        
        # 4. Afficher les résultats dans le terminal
        print("\n" + "="*80)
        print("🏆 TOP 10 OPPORTUNITÉS SCALPING (Données Réelles)")
        print("="*80)
        print(f"{'Rank':<6} {'Pair':<12} {'Score':<7} {'Signal':<8} {'Entry $':<10} {'Stop $':<10} {'TP1 $':<10} {'R/R':<6}")
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
    print("📌 Mode SCALPING (15min) - Données Réelles Binance")
    print("🛑 Appuyez sur Ctrl+C pour arrêter\n")
    
    # Variable partagée pour les opportunités
    opportunities_data = {'data': []}
    scanning_status = {'is_scanning': False}
    
    # Créer l'application Flask
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        """Page d'accueil avec le tableau des opportunités."""
        is_scanning = scanning_status.get('is_scanning', False)
        opportunities = opportunities_data.get('data', [])
        
        # Template HTML intégré (Version améliorée)
        HTML_TEMPLATE = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Scalping Crypto Scanner (Binance Data)</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #2c3e50 0%, #4ca1af 100%);
                    min-height: 100vh;
                    padding: 20px;
                    color: #333;
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
                    color: #2c3e50;
                    margin-bottom: 10px;
                }
                .header .subtitle {
                    color: #666;
                    font-size: 1.1em;
                    margin-top: 5px;
                }
                .last-update { color: #666; font-size: 0.9em; margin-top: 10px; }
                .main-content {
                    background: rgba(255, 255, 255, 0.98);
                    border-radius: 15px;
                    padding: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    overflow-x: auto;
                }
                table { width: 100%; border-collapse: collapse; font-size: 0.9em; min-width: 1400px; }
                thead { background: #34495e; color: white; }
                th { padding: 15px 10px; text-align: left; font-weight: 600; text-transform: uppercase; font-size: 0.85em; white-space: nowrap; }
                td { padding: 12px 10px; border-bottom: 1px solid #e9ecef; font-size: 0.95em; vertical-align: middle; }
                tbody tr:hover { background: #f1f2f6; }
                .rank { font-weight: bold; font-size: 1.1em; color: #2c3e50; }
                .score {
                    font-weight: bold;
                    padding: 5px 10px;
                    border-radius: 5px;
                    display: inline-block;
                }
                .score-high { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .score-medium { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
                .score-low { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                
                .signal-badge {
                    font-weight: bold;
                    padding: 5px 10px;
                    border-radius: 5px;
                    text-transform: uppercase;
                    font-size: 0.85em;
                }
                .signal-long { background-color: #28a745; color: white; }
                .signal-short { background-color: #dc3545; color: white; }
                .signal-neutral { background-color: #6c757d; color: white; }
                
                .price-val { font-family: 'Consolas', 'Monaco', monospace; font-weight: 500; }
                
                .rr-ratio { font-weight: bold; }
                .rr-good { color: #28a745; }
                .rr-bad { color: #dc3545; }
                
                .footer {
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    color: rgba(255,255,255,0.9);
                    font-size: 0.9em;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚡ Scalping Crypto Scanner</h1>
                    <p class="subtitle">Données Réelles Binance | Timeframe: 15m | Stratégie: Scalping</p>
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
                                <th>Signal</th>
                                <th>Prix</th>
                                <th>Entry</th>
                                <th>Stop Loss</th>
                                <th>TP1</th>
                                <th>TP2</th>
                                <th>R/R</th>
                                <th>RSI</th>
                                <th>Trend</th>
                                <th>Conf.</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% if not opportunities %}
                            <tr>
                                <td colspan="13" style="text-align: center; padding: 50px;">
                                    {% if is_scanning %}
                                        <h2>🔄 Scan en cours...</h2>
                                        <p>Récupération des données réelles depuis Binance.</p>
                                    {% else %}
                                        <h2>⏳ Initialisation...</h2>
                                        <p>Le premier scan va démarrer dans quelques instants.</p>
                                    {% endif %}
                                    <p>La page se rafraîchira automatiquement.</p>
                                    <script>setTimeout(function(){ location.reload(); }, 5000);</script>
                                </td>
                            </tr>
                            {% else %}
                            {% for opp in opportunities %}
                            <tr>
                                <td class="rank">#{{ opp.rank }}</td>
                                <td><strong>{{ opp.pair }}</strong></td>
                                <td>
                                    <span class="score {% if opp.score >= 70 %}score-high{% elif opp.score >= 50 %}score-medium{% else %}score-low{% endif %}">
                                        {{ opp.score }}
                                    </span>
                                </td>
                                <td>
                                    <span class="signal-badge {% if opp.entry_signal == 'LONG' %}signal-long{% elif opp.entry_signal == 'SHORT' %}signal-short{% else %}signal-neutral{% endif %}">
                                        {{ opp.entry_signal }}
                                    </span>
                                </td>
                                <td class="price-val">${{ "%.4f"|format(opp.price) if opp.price else "N/A" }}</td>
                                <td class="price-val">${{ "%.4f"|format(opp.entry_price) if opp.entry_price else "N/A" }}</td>
                                <td class="price-val" style="color: #dc3545;">${{ "%.4f"|format(opp.stop_loss) if opp.stop_loss else "N/A" }}</td>
                                <td class="price-val" style="color: #28a745;">${{ "%.4f"|format(opp.take_profit_1) if opp.take_profit_1 else "N/A" }}</td>
                                <td class="price-val" style="color: #28a745;">${{ "%.4f"|format(opp.take_profit_2) if opp.take_profit_2 else "N/A" }}</td>
                                <td>
                                    {% if opp.risk_reward_ratio %}
                                        <span class="rr-ratio {% if opp.risk_reward_ratio >= 2 %}rr-good{% else %}rr-bad{% endif %}">
                                            {{ "%.2f"|format(opp.risk_reward_ratio) }}
                                        </span>
                                    {% else %}
                                        -
                                    {% endif %}
                                </td>
                                <td>{{ "%.1f"|format(opp.rsi) if opp.rsi else "-" }}</td>
                                <td style="font-weight:bold; color: {% if opp.trend == 'Bullish' %}#28a745{% elif opp.trend == 'Bearish' %}#dc3545{% else %}#6c757d{% endif %}">
                                    {{ opp.trend }}
                                </td>
                                <td>{{ opp.confidence }}%</td>
                            </tr>
                            {% endfor %}
                            {% endif %}
                        </tbody>
                    </table>
                </div>
                <div class="footer">
                    <p>⚠️ Trading à haut risque. Données à titre indicatif uniquement.</p>
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
        return {'status': 'ok', 'opportunities_count': len(opportunities_data['data'])}, 200
    
    # Threads de gestion du scan
    def run_scanner_loop():
        """Boucle infinie de scan"""
        while True:
            scanning_status['is_scanning'] = True
            try:
                print("🔄 Démarrage du scan périodique...")
                new_opportunities = run_scanner()
                opportunities_data['data'] = new_opportunities
                print("✅ Scan terminé et données mises à jour.")
            except Exception as e:
                print(f"❌ Erreur dans la boucle de scan: {e}")
            finally:
                scanning_status['is_scanning'] = False
            
            # Attendre 5 minutes pour être plus réactif
            time.sleep(300) 

    # Lancer le scanner en arrière-plan
    scanner_thread = threading.Thread(target=run_scanner_loop, daemon=True)
    scanner_thread.start()
    
    # Démarrer le serveur Web
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🌐 Dashboard accessible sur http://0.0.0.0:{port}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"Erreur serveur: {e}")

if __name__ == '__main__':
    main()