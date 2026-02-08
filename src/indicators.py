"""
Module pour calculer les indicateurs techniques.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """
    Calcule la Simple Moving Average (SMA).
    
    Args:
        series: Série de prix (typiquement 'close')
        period: Période de la moyenne mobile
    
    Returns:
        Série avec les valeurs SMA
    """
    return series.rolling(window=period, min_periods=1).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calcule le Relative Strength Index (RSI).
    
    Args:
        series: Série de prix (typiquement 'close')
        period: Période du RSI (défaut: 14)
    
    Returns:
        Série avec les valeurs RSI (0-100)
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.fillna(50)  # RSI neutre par défaut si pas assez de données


def calculate_volume_ma(volume: pd.Series, period: int = 20) -> pd.Series:
    """
    Calcule la moyenne mobile du volume.
    
    Args:
        volume: Série de volumes
        period: Période de la moyenne (défaut: 20)
    
    Returns:
        Série avec les valeurs de volume moyen
    """
    return volume.rolling(window=period, min_periods=1).mean()


def calculate_indicators(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calcule tous les indicateurs techniques pour un DataFrame OHLCV.
    
    Args:
        df: DataFrame avec colonnes open, high, low, close, volume
    
    Returns:
        Dictionnaire avec les valeurs des indicateurs (dernière bougie)
    """
    if df.empty or len(df) < 50:
        return {
            'sma20': None,
            'sma50': None,
            'rsi14': None,
            'volume_ma20': None,
            'current_price': None,
            'current_volume': None
        }
    
    # Calculer les indicateurs
    df['sma20'] = calculate_sma(df['close'], 20)
    df['sma50'] = calculate_sma(df['close'], 50)
    df['rsi14'] = calculate_rsi(df['close'], 14)
    df['volume_ma20'] = calculate_volume_ma(df['volume'], 20)
    
    # Récupérer les dernières valeurs
    last = df.iloc[-1]
    
    return {
        'sma20': float(last['sma20']) if pd.notna(last['sma20']) else None,
        'sma50': float(last['sma50']) if pd.notna(last['sma50']) else None,
        'rsi14': float(last['rsi14']) if pd.notna(last['rsi14']) else None,
        'volume_ma20': float(last['volume_ma20']) if pd.notna(last['volume_ma20']) else None,
        'current_price': float(last['close']),
        'current_volume': float(last['volume'])
    }

