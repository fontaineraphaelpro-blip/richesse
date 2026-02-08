"""
Script pour lancer le backtesting du système de scoring.
Utilise l'API publique Binance (pas besoin de clé).
"""

from fetch_pairs import get_top_usdt_pairs
from backtest import run_backtest

if __name__ == '__main__':
    print("🔬 Crypto Signal Scanner - Backtesting")
    print("="*60)
    
    # Récupérer quelques paires pour le test (limiter à 10 pour le backtest)
    print("\n📋 Récupération des paires (API publique)...")
    pairs = get_top_usdt_pairs(limit=10)
    
    if not pairs:
        print("❌ Aucune paire trouvée.")
        exit(1)
    
    # Lancer le backtest sur 90 jours
    print(f"\n🚀 Lancement du backtest sur {len(pairs)} paires (90 jours)...")
    results_df = run_backtest(pairs, days=90)
    
    if not results_df.empty:
        # Sauvegarder les résultats
        output_file = 'backtest_results.csv'
        results_df.to_csv(output_file, index=False)
        print(f"\n💾 Résultats sauvegardés dans: {output_file}")
    else:
        print("\n⚠️ Aucun résultat de backtest généré.")

