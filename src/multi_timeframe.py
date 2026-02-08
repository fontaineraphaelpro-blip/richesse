"""
Module pour l'analyse multi-timeframe (confirmation de tendance).
"""

from binance.client import Client
from data_fetcher import fetch_klines
from indicators import calculate_indicators
from typing import Optional, Dict


def analyze_timeframe(client: Client, symbol: str, interval: str, limit: int = 100) -> Optional[str]:
    """
    Analyse un timeframe spécifique pour déterminer la tendance.
    
    Args:
        client: Client Binance
        symbol: Symbole de la paire
        interval: Timeframe ('15m', '4h', '1d', etc.)
        limit: Nombre de bougies à récupérer
    
    Returns:
        'Bullish', 'Bearish', ou None si indéterminé
    """
    try:
        df = fetch_klines(client, symbol, interval=interval, limit=limit)
        
        if df is None or len(df) < 50:
            return None
        
        indicators = calculate_indicators(df)
        sma20 = indicators.get('sma20')
        sma50 = indicators.get('sma50')
        
        if sma20 is None or sma50 is None:
            return None
        
        if sma20 > sma50:
            return 'Bullish'
        else:
            return 'Bearish'
    
    except Exception as e:
        print(f"⚠️ Erreur analyse timeframe {interval} pour {symbol}: {e}")
        return None


def get_multi_timeframe_confirmation(client: Client, symbol: str) -> Optional[str]:
    """
    Analyse plusieurs timeframes pour confirmer la tendance.
    
    Analyse 4H et 15min pour confirmer la tendance principale (1H).
    
    Args:
        client: Client Binance
        symbol: Symbole de la paire
    
    Returns:
        'Bullish' si majorité bullish, 'Bearish' si majorité bearish, None sinon
    """
    try:
        # Analyser 4H et 15min
        tf_4h = analyze_timeframe(client, symbol, '4h', limit=100)
        tf_15m = analyze_timeframe(client, symbol, '15m', limit=100)
        
        # Compter les votes
        bullish_votes = 0
        bearish_votes = 0
        
        if tf_4h == 'Bullish':
            bullish_votes += 1
        elif tf_4h == 'Bearish':
            bearish_votes += 1
        
        if tf_15m == 'Bullish':
            bullish_votes += 1
        elif tf_15m == 'Bearish':
            bearish_votes += 1
        
        # Si au moins 2 timeframes sont d'accord
        if bullish_votes >= 1:
            return 'Bullish'
        elif bearish_votes >= 1:
            return 'Bearish'
        else:
            return None
    
    except Exception as e:
        print(f"⚠️ Erreur confirmation multi-timeframe pour {symbol}: {e}")
        return None

