"""
Module pour calculer les indicateurs techniques.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """
    Calcule la moyenne mobile simple (SMA).
    
    Args:
        data: Série de prix (généralement 'close')
        period: Période de la moyenne mobile
    
    Returns:
        Série avec les valeurs SMA
    """
    return data.rolling(window=period).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calcule l'indicateur RSI (Relative Strength Index).
    
    Args:
        data: Série de prix (généralement 'close')
        period: Période du RSI (défaut: 14)
    
    Returns:
        Série avec les valeurs RSI (0-100)
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_indicators(df: pd.DataFrame) -> Dict:
    """
    Calcule tous les indicateurs techniques pour un DataFrame OHLCV.
    
    Args:
        df: DataFrame avec colonnes: timestamp, open, high, low, close, volume
    
    Returns:
        Dictionnaire avec tous les indicateurs calculés
    """
    if df is None or len(df) == 0:
        return {}
    
    close = df['close']
    volume = df['volume']
    
    # Calculer les indicateurs
    sma20 = calculate_sma(close, 20)
    sma50 = calculate_sma(close, 50)
    rsi14 = calculate_rsi(close, 14)
    volume_ma20 = calculate_sma(volume, 20)
    
    # Récupérer les dernières valeurs
    indicators = {
        'sma20': sma20.iloc[-1] if len(sma20) > 0 and not pd.isna(sma20.iloc[-1]) else None,
        'sma50': sma50.iloc[-1] if len(sma50) > 0 and not pd.isna(sma50.iloc[-1]) else None,
        'rsi14': rsi14.iloc[-1] if len(rsi14) > 0 and not pd.isna(rsi14.iloc[-1]) else None,
        'volume_ma20': volume_ma20.iloc[-1] if len(volume_ma20) > 0 and not pd.isna(volume_ma20.iloc[-1]) else None,
        'current_price': close.iloc[-1] if len(close) > 0 else None,
        'current_volume': volume.iloc[-1] if len(volume) > 0 else None
    }
    
    return indicators
