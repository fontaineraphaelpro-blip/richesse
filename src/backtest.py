"""
Module pour le backtesting simple du système de scoring.
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from data_fetcher import fetch_klines
from indicators import calculate_indicators
from support import find_swing_low, calculate_distance_to_support
from scorer import calculate_opportunity_score
from breakout import get_breakout_signals


def calculate_historical_performance(client, symbol: str, days: int = 90) -> Dict:
    """
    Calcule la performance historique du scoring sur les 3 derniers mois.
    
    Args:
        client: Client Binance
        symbol: Symbole de la paire (ex: 'BTCUSDT')
        days: Nombre de jours à analyser (défaut: 90)
    
    Returns:
        Dictionnaire avec les métriques de performance
    """
    try:
        # Récupérer plus de données pour le backtest (1 bougie par heure sur 90 jours = ~2160 bougies)
        # On prend 1H timeframe pour avoir assez de données
        df = fetch_klines(client, symbol, interval='1h', limit=min(days * 24, 1000))
        
        if df is None or len(df) < 100:
            return None
        
        # Analyser chaque point dans le temps (toutes les 24 heures pour accélérer)
        results = []
        step = 24  # Analyser toutes les 24 heures
        
        for i in range(50, len(df), step):  # Commencer à 50 pour avoir assez de données pour SMA50
            # Prendre les données jusqu'à ce point
            historical_df = df.iloc[:i+1].copy()
            
            # Calculer les indicateurs
            indicators = calculate_indicators(historical_df)
            
            # Détecter le support
            support = find_swing_low(historical_df, lookback=30)
            current_price = indicators.get('current_price')
            support_distance = None
            
            if current_price and support:
                support_distance = calculate_distance_to_support(current_price, support)
            
            # Calculer le score
            score_data = calculate_opportunity_score(indicators, support_distance)
            score = score_data.get('score', 0)
            
            # Prix futur (24 heures plus tard)
            if i + 24 < len(df):
                future_price = float(df.iloc[i + 24]['close'])
                price_change = ((future_price - current_price) / current_price) * 100 if current_price else 0
                
                results.append({
                    'timestamp': historical_df.iloc[-1]['timestamp'],
                    'score': score,
                    'price': current_price,
                    'future_price': future_price,
                    'price_change_pct': price_change
                })
        
        if not results:
            return None
        
        # Analyser les résultats
        # Grouper par ranges de score
        high_scores = [r for r in results if r['score'] >= 70]
        medium_scores = [r for r in results if 40 <= r['score'] < 70]
        low_scores = [r for r in results if r['score'] < 40]
        
        def avg_price_change(group):
            if not group:
                return 0
            return sum(r['price_change_pct'] for r in group) / len(group)
        
        def win_rate(group):
            if not group:
                return 0
            wins = sum(1 for r in group if r['price_change_pct'] > 0)
            return (wins / len(group)) * 100
        
        return {
            'symbol': symbol,
            'total_signals': len(results),
            'high_score_count': len(high_scores),
            'medium_score_count': len(medium_scores),
            'low_score_count': len(low_scores),
            'high_score_avg_return': avg_price_change(high_scores),
            'medium_score_avg_return': avg_price_change(medium_scores),
            'low_score_avg_return': avg_price_change(low_scores),
            'high_score_win_rate': win_rate(high_scores),
            'medium_score_win_rate': win_rate(medium_scores),
            'low_score_win_rate': win_rate(low_scores),
            'overall_avg_return': avg_price_change(results),
            'overall_win_rate': win_rate(results)
        }
    
    except Exception as e:
        print(f"❌ Erreur backtest pour {symbol}: {e}")
        return None


def run_backtest(client, symbols: List[str], days: int = 90) -> pd.DataFrame:
    """
    Lance un backtest sur plusieurs symboles.
    
    Args:
        client: Client Binance
        symbols: Liste des symboles à tester
        days: Nombre de jours à analyser
    
    Returns:
        DataFrame avec les résultats du backtest
    """
    print(f"\n🔬 Démarrage du backtest sur {len(symbols)} paires ({days} jours)...")
    
    results = []
    
    for i, symbol in enumerate(symbols, 1):
        print(f"📊 Backtest {symbol} ({i}/{len(symbols)})...", end='\r')
        result = calculate_historical_performance(client, symbol, days)
        if result:
            results.append(result)
    
    print(f"\n✅ Backtest terminé: {len(results)}/{len(symbols)} paires analysées")
    
    if not results:
        return pd.DataFrame()
    
    # Créer un DataFrame avec les résultats
    df = pd.DataFrame(results)
    
    # Afficher un résumé
    print("\n" + "="*60)
    print("📊 RÉSULTATS DU BACKTEST")
    print("="*60)
    print(f"\nScore élevé (≥70):")
    print(f"  - Nombre de signaux: {df['high_score_count'].sum()}")
    print(f"  - Retour moyen: {df['high_score_avg_return'].mean():.2f}%")
    print(f"  - Taux de réussite: {df['high_score_win_rate'].mean():.2f}%")
    
    print(f"\nScore moyen (40-69):")
    print(f"  - Nombre de signaux: {df['medium_score_count'].sum()}")
    print(f"  - Retour moyen: {df['medium_score_avg_return'].mean():.2f}%")
    print(f"  - Taux de réussite: {df['medium_score_win_rate'].mean():.2f}%")
    
    print(f"\nScore faible (<40):")
    print(f"  - Nombre de signaux: {df['low_score_count'].sum()}")
    print(f"  - Retour moyen: {df['low_score_avg_return'].mean():.2f}%")
    print(f"  - Taux de réussite: {df['low_score_win_rate'].mean():.2f}%")
    
    print("="*60)
    
    return df

