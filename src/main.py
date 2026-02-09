"""
Script principal du Crypto Signal Scanner Web.
Version DAY TRADING (1h) - Analyse de tendance sur longue période.
"""

import time
import os
from datetime import datetime
from flask import Flask, render_template_string
import threading

# Importations des modules locaux
from data_fetcher import fetch_multiple_pairs
from indicators import calculate_indicators
from support import find_swing_low, calculate_distance_to_support
from scorer import calculate_opportunity_score

def run_scanner():
    """
    Exécute un scan complet sur 1H et retourne les opportunités de Day Trading.
    """
    print("\n" + "="*60)
    print("🚀 CRYPTO SCANNER - Mode DAY TRADING (1h)")
    print("="*60)
    print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    try:
        # 1. CONFIGURATION 1H (Longue plage)
        # interval='1h' : Analyse chaque bougie d'une heure pour filtrer le bruit du 15m
        # limit=1000 : Récupère 1000 heures (~41 jours) d'historique pour une tendance de fond fiable
        print("📊 Récupération des données sur 1000 bougies de 1h (Analyse de fond)...")
        
        # On passe None pour utiliser la liste par défaut définie dans data_fetcher
        data, real_prices = fetch_multiple_pairs(None, interval='1h', limit=1000)
        
        if not data:
            print("❌ Aucune donnée récupérée. Vérifiez votre connexion.")
            return []
        
        # 2. Analyse Technique
        print("\n🔍 Analyse de la tendance et recherche de signaux...")
        opportunities = []
        
        for i, (symbol, df) in enumerate(data.items(), 1):
            # Calcul des indicateurs sur l'historique long
            indicators = calculate_indicators(df)
            
            current_price = real_prices.get(symbol)
            if not current_price: 
                current_price = indicators.get('current_price')

            # Détection de support sur une période plus large (50h = ~2 jours)
            support = find_swing_low(df, lookback=50)
            support_distance = None
            if current_price and support:
                support_distance = calculate_distance_to_support(current_price, support)
            
            # Calcul du score (La fonction detect_trend dans scorer utilisera automatiquement les données 1h)
            score_data = calculate_opportunity_score(indicators, support_distance, df)
            
            # On ne garde que les données pertinentes pour le Day Trading
            opportunities.append({
                'pair': symbol,
                'score': score_data['score'],
                'trend': score_data['trend'], # Tendance calculée sur 1h
                'signal': score_data['signal'],
                'price': current_price,
                'rsi': indicators.get('rsi14'),
                'entry_signal': score_data.get('entry_signal', 'NEUTRAL'),
                'entry_price': score_data.get('entry_price'),
                'stop_loss': score_data.get('stop_loss'),
                'take_profit_1': score_data.get('take_profit_1'),
                'take_profit_2': score_data.get('take_profit_2'),
                'risk_reward_ratio': score_data.get('risk_reward_ratio'),
                'confidence': score_data.get('confidence', 0),
                'atr_percent': indicators.get('atr_percent'),
            })
        
        # 3. Filtrage & Tri Intelligent
        # On privilégie les scores > 50 qui indiquent une vraie opportunité
        quality_opportunities = [opp for opp in opportunities if opp['score'] >= 50]
        
        # Tri par Score décroissant
        quality_opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        # Sélection du Top 15 (ou moins si pas assez d'opportunités)
        top_picks = quality_opportunities[:15]
        
        # Si le marché est calme et qu'on a peu de bons signaux, on complète avec le reste trié
        if len(top_picks) < 5:
            remaining = [opp for opp in opportunities if opp not in quality_opportunities]
            remaining.sort(key=lambda x: x['score'], reverse=True)
            top_picks.extend(remaining[:10 - len(top_picks)])

        # Ajout du classement (Rank)
        for i, opp in enumerate(top_picks, 1):
            opp['rank'] = i
        
        # 4. Affichage Terminal (Résumé)
        print("\n" + "="*80)
        print("🏆 TOP OPPORTUNITÉS DAY TRADING (Timeframe: 1H)")
        print("="*80)
        print(f"{'Paire':<12} {'Score':<7} {'Trend':<10} {'Signal':<8} {'Prix':<10} {'Stop Loss':<10}")
        print("-"*80)
        
        for opp in top_picks:
            entry_sig = opp.get('entry_signal', '-')
            print(f"{opp['pair']:<12} {opp['score']:<7} {opp['trend']:<10} {entry_sig:<8} ${opp['price']:.4f} ${opp['stop_loss']:.4f}")
        
        return top_picks
        
    except Exception as e:
        print(f"\n❌ Erreur critique lors du scan: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    print("⚡ Crypto Scanner - Mode DAY TRADING (1h)")
    print("📌 Analyse sur 1000 bougies (41 jours) pour déterminer la tendance de fond.")
    print("🛑 Ctrl+C pour arrêter")
    
    opportunities_data = {'data': []}
    scanning_status = {'is_scanning': False}
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        is_scanning = scanning_status.get('is_scanning', False)
        opportunities = opportunities_data.get('data', [])
        last_update = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Template HTML simplifié et épuré pour le Day Trading
        HTML = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Day Trading Scanner (1h)</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: 'Segoe UI', sans-serif; background: #f4f6f9; padding: 20px; color: #333; }
                .container { max-width: 1400px; margin: 0 auto; }
                .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px; }
                h1 { margin: 0 0 10px 0; color: #2c3e50; }
                .subtitle { color: #666; font-size: 0.9em; }
                
                table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                th { background-color: #f8f9fa; text-transform: uppercase; font-size: 0.8em; color: #666; padding: 15px; text-align: left; }
                td { padding: 15px; border-bottom: 1px solid #eee; vertical-align: middle; }
                tr:hover { background-color: #f8f9fa; }
                
                .trend-bullish { color: #27ae60; font-weight: bold; background: #eafaf1; padding: 4px 8px; border-radius: 4px; }
                .trend-bearish { color: #c0392b; font-weight: bold; background: #fdedec; padding: 4px 8px; border-radius: 4px; }
                .trend-neutral { color: #7f8c8d; background: #f2f3f4; padding: 4px 8px; border-radius: 4px; }
                
                .badge { padding: 6px 10px; border-radius: 6px; color: white; font-weight: 600; font-size: 0.85em; }
                .bg-green { background-color: #27ae60; }
                .bg-red { background-color: #c0392b; }
                .bg-gray { background-color: #95a5a6; }
                
                .score-val { font-weight: bold; font-size: 1.1em; }
                .price-val { font-family: 'Consolas', monospace; }
                
                .scan-loader { color: #e67e22; font-weight: bold; animation: blink 1.5s infinite; }
                @keyframes blink { 50% { opacity: 0.5; } }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h1>📈 Day Trading Scanner</h1>
                    <div class="subtitle">
                        Timeframe: <strong>1 Heure</strong> | Historique analysé: <strong>1000 bougies</strong> | 
                        Dernière MAJ: {{ last_update }}
                        {% if is_scanning %} <span class="scan-loader"> (Scan en cours...)</span>{% endif %}
                    </div>
                </div>
                
                <div class="card">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Paire</th>
                                <th>Score / 100</th>
                                <th>Tendance (Fond)</th>
                                <th>Signal</th>
                                <th>Confiance</th>
                                <th>Prix Actuel</th>
                                <th>Stop Loss</th>
                                <th>Objectif (TP1)</th>
                                <th>RSI</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% if not opportunities %}
                            <tr><td colspan="10" style="text-align:center; padding:30px">Initialisation ou aucun signal fort trouvé...</td></tr>
                            {% else %}
                            {% for opp in opportunities %}
                            <tr>
                                <td><strong>{{ opp.rank }}</strong></td>
                                <td><strong>{{ opp.pair }}</strong></td>
                                <td class="score-val" style="color: {% if opp.score > 70 %}#27ae60{% elif opp.score > 50 %}#f39c12{% else %}#7f8c8d{% endif %}">
                                    {{ opp.score }}
                                </td>
                                <td>
                                    <span class="{% if opp.trend == 'Bullish' %}trend-bullish{% elif opp.trend == 'Bearish' %}trend-bearish{% else %}trend-neutral{% endif %}">
                                        {{ opp.trend }}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge {% if opp.entry_signal == 'LONG' %}bg-green{% elif opp.entry_signal == 'SHORT' %}bg-red{% else %}bg-gray{% endif %}">
                                        {{ opp.entry_signal }}
                                    </span>
                                </td>
                                <td>{{ opp.confidence }}%</td>
                                <td class="price-val">${{ "%.4f"|format(opp.price) }}</td>
                                <td class="price-val" style="color: #c0392b;">${{ "%.4f"|format(opp.stop_loss) if opp.stop_loss else '-' }}</td>
                                <td class="price-val" style="color: #27ae60;">${{ "%.4f"|format(opp.take_profit_1) if opp.take_profit_1 else '-' }}</td>
                                <td>{{ "%.1f"|format(opp.rsi) if opp.rsi else '-' }}</td>
                            </tr>
                            {% endfor %}
                            {% endif %}
                        </tbody>
                    </table>
                </div>
            </div>
            <script>
                // Rafraîchir la page toutes les 60 secondes pour voir les mises à jour
                setTimeout(function(){ location.reload(); }, 60000);
            </script>
        </body>
        </html>
        """
        return render_template_string(HTML, opportunities=opportunities, last_update=last_update, is_scanning=is_scanning)

    def run_loop():
        while True:
            scanning_status['is_scanning'] = True
            try:
                opportunities_data['data'] = run_scanner()
            except Exception as e:
                print(f"Erreur loop: {e}")
            finally:
                scanning_status['is_scanning'] = False
            
            # Pause de 15 minutes (900 secondes)
            # En 1H, pas besoin de scanner chaque minute. 15min permet de voir l'évolution intra-bougie.
            print("💤 Pause de 15 minutes avant le prochain scan...")
            time.sleep(900)

    # Lancement du thread de scan
    scanner_thread = threading.Thread(target=run_loop, daemon=True)
    scanner_thread.start()
    
    # Lancement du serveur Web
    port = int(os.environ.get('PORT', 8080))
    print(f"\n🌐 Dashboard accessible sur http://0.0.0.0:{port}")
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"Erreur serveur: {e}")

if __name__ == '__main__':
    main()