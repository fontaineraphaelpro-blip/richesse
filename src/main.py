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
        
        # 2. Récupérer les données OHLCV
        print("\n📊 Étape 2: Récupération des données OHLCV (1H, 200 bougies)...")
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
    
    # Créer l'application Flask
    app = create_app(opportunities)
    
    # Fonction pour mettre à jour les opportunités en arrière-plan
    def update_opportunities():
        """Met à jour les opportunités toutes les heures."""
        while True:
            time.sleep(3600)  # Attendre 1 heure
            print("\n🔄 Mise à jour automatique...")
            new_opportunities = run_scanner()
            # Mettre à jour l'app avec les nouvelles opportunités
            app.config['opportunities'] = new_opportunities
            # Recréer les routes avec les nouvelles données
            app.view_functions['home'] = lambda: create_app(new_opportunities).view_functions['home']()
    
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
