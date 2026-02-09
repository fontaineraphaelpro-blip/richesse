"""
Point d'entrée WSGI pour Gunicorn (production).
"""

import sys
import os
import threading
import time
from flask import Flask, render_template_string
from datetime import datetime

# Ajouter src au path
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Importer les modules nécessaires
from fetch_pairs import get_top_usdt_pairs
from data_fetcher import fetch_multiple_pairs
from indicators import calculate_indicators
from support import find_swing_low, calculate_distance_to_support
from scorer import calculate_opportunity_score

# Variable globale pour les opportunités
opportunities_data = {'data': []}

# Fonction pour exécuter un scan
def run_scanner():
    """Exécute un scan complet et retourne les Top 10 opportunités."""
    from datetime import datetime
    
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
            current_price = real_prices.get(symbol)
            if not current_price:
                # Fallback: utiliser le prix du DataFrame si pas de prix réel
                current_price = indicators.get('current_price')
            
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
        
        print("\n✅ Scan terminé avec succès!")
        return top_10
        
    except Exception as e:
        print(f"\n❌ Erreur lors du scan: {e}")
        import traceback
        traceback.print_exc()
        return []

# Créer l'app Flask
app = Flask(__name__)

# Template HTML
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

@app.route('/')
def home():
    """Page d'accueil avec le tableau des opportunités."""
    last_update = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    return render_template_string(HTML_TEMPLATE, opportunities=opportunities_data['data'], last_update=last_update)

@app.route('/health')
def health():
    """Route de santé."""
    return {'status': 'ok', 'opportunities_count': len(opportunities_data['data'])}, 200

# Fonction pour exécuter le scanner en arrière-plan
def run_scanner_background():
    """Exécute le scanner en arrière-plan."""
    try:
        print("🚀 Démarrage du scan initial en arrière-plan...")
        new_opportunities = run_scanner()
        opportunities_data['data'] = new_opportunities
        print("✅ Scan initial terminé!")
    except Exception as e:
        print(f"❌ Erreur lors du scan: {e}")
        import traceback
        traceback.print_exc()

# Fonction pour mettre à jour les opportunités toutes les heures
def update_opportunities():
    """Met à jour les opportunités toutes les heures."""
    while True:
        time.sleep(3600)  # Attendre 1 heure
        try:
            print("\n🔄 Mise à jour automatique...")
            new_opportunities = run_scanner()
            opportunities_data['data'] = new_opportunities
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour: {e}")

# Lancer le scanner initial en arrière-plan (non-bloquant)
scanner_thread = threading.Thread(target=run_scanner_background, daemon=True)
scanner_thread.start()

# Lancer la mise à jour périodique en arrière-plan
update_thread = threading.Thread(target=update_opportunities, daemon=True)
update_thread.start()

print("✅ Serveur web prêt - Scanner en cours d'initialisation en arrière-plan...")

# Exporter pour Gunicorn
application = app
