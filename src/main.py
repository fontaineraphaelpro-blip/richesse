"""
Script principal du Crypto Signal Scanner.
Scanne les cryptos sur Binance, calcule les opportunités et génère un rapport.
"""

import time
import os
from binance.client import Client
from datetime import datetime

from fetch_pairs import get_top_usdt_pairs
from data_fetcher import fetch_multiple_pairs
from indicators import calculate_indicators
from support import find_swing_low, calculate_distance_to_support
from scorer import calculate_opportunity_score
from html_report import generate_html_report


def run_scanner():
    """
    Fonction principale qui exécute un scan complet.
    """
    print("\n" + "="*60)
    print("🚀 CRYPTO SIGNAL SCANNER - Démarrage du scan")
    print("="*60)
    print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    try:
        # Initialiser le client Binance (pas besoin d'API key pour les données publiques)
        # Si vous avez des limites de rate, vous pouvez ajouter vos clés API
        client = Client()
        
        # 1. Récupérer les principales paires USDT
        print("📋 Étape 1: Récupération des paires USDT...")
        pairs = get_top_usdt_pairs(client, limit=50)
        
        if not pairs:
            print("❌ Aucune paire trouvée. Arrêt du scanner.")
            return
        
        # 2. Récupérer les données OHLCV
        print("\n📊 Étape 2: Récupération des données OHLCV (1H, 200 bougies)...")
        data = fetch_multiple_pairs(client, pairs, interval='1h', limit=200)
        
        if not data:
            print("❌ Aucune donnée récupérée. Arrêt du scanner.")
            return
        
        # 3. Calculer les indicateurs et scores pour chaque paire
        print("\n🔍 Étape 3: Calcul des indicateurs et scores...")
        opportunities = []
        
        for symbol, df in data.items():
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
                'details': score_data['details'],
                'price': current_price,
                'support': support,
                'support_distance': support_distance
            })
        
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
        
        # 6. Générer le rapport HTML
        print("\n📄 Étape 4: Génération du rapport HTML...")
        generate_html_report(top_10, output_file='report.html')
        
        print("\n✅ Scan terminé avec succès!")
        print(f"📊 {len(data)} paires analysées")
        print(f"🏆 Top 10 opportunités identifiées")
        print(f"📄 Rapport HTML: report.html\n")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du scan: {e}")
        import traceback
        traceback.print_exc()


def main():
    """
    Fonction main avec boucle continue pour Railway.
    """
    print("🚀 Crypto Signal Scanner - Démarrage")
    print("📌 Mode: Boucle continue (mise à jour toutes les heures)")
    print("🛑 Appuyez sur Ctrl+C pour arrêter\n")
    
    try:
        while True:
            run_scanner()
            
            # Attendre 1 heure avant le prochain scan
            print(f"⏳ Prochain scan dans 1 heure...")
            print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            time.sleep(3600)  # 3600 secondes = 1 heure
    
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du scanner demandé par l'utilisateur.")
        print("👋 Au revoir!")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

