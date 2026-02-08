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


def detect_rsi_divergence(df: pd.DataFrame, period: int = 14, lookback: int = 20) -> Dict:
    """
    Détecte une divergence RSI (RSI monte/baisse vs prix).
    
    Divergence haussière: Prix fait des plus bas plus bas, RSI fait des plus bas plus hauts
    Divergence baissière: Prix fait des plus hauts plus hauts, RSI fait des plus hauts plus bas
    
    Args:
        df: DataFrame OHLCV
        period: Période du RSI (défaut: 14)
        lookback: Nombre de bougies à analyser (défaut: 20)
    
    Returns:
        Dictionnaire avec les informations de divergence
    """
    if df.empty or len(df) < lookback + period:
        return {'divergence_detected': False, 'divergence_type': None}
    
    # Calculer RSI
    df['rsi'] = calculate_rsi(df['close'], period)
    
    # Prendre les N dernières bougies
    recent = df.tail(lookback).copy()
    
    if len(recent) < 10:
        return {'divergence_detected': False, 'divergence_type': None}
    
    # Trouver les minima et maxima locaux pour le prix
    prices = recent['close'].values
    rsis = recent['rsi'].values
    
    # Trouver les 2 derniers minima et maxima
    price_lows = []
    price_highs = []
    rsi_lows = []
    rsi_highs = []
    
    for i in range(1, len(prices) - 1):
        # Minima locaux
        if prices[i] < prices[i-1] and prices[i] < prices[i+1]:
            price_lows.append((i, prices[i]))
            rsi_lows.append((i, rsis[i]))
        
        # Maxima locaux
        if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
            price_highs.append((i, prices[i]))
            rsi_highs.append((i, rsis[i]))
    
    # Vérifier divergence haussière (2 derniers minima)
    if len(price_lows) >= 2 and len(rsi_lows) >= 2:
        last_price_low = price_lows[-1][1]
        prev_price_low = price_lows[-2][1]
        last_rsi_low = rsi_lows[-1][1]
        prev_rsi_low = rsi_lows[-2][1]
        
        # Prix fait des plus bas plus bas, RSI fait des plus bas plus hauts
        if last_price_low < prev_price_low and last_rsi_low > prev_rsi_low:
            return {
                'divergence_detected': True,
                'divergence_type': 'Bullish Divergence',
                'strength': 'Strong' if abs(last_rsi_low - prev_rsi_low) > 5 else 'Weak'
            }
    
    # Vérifier divergence baissière (2 derniers maxima)
    if len(price_highs) >= 2 and len(rsi_highs) >= 2:
        last_price_high = price_highs[-1][1]
        prev_price_high = price_highs[-2][1]
        last_rsi_high = rsi_highs[-1][1]
        prev_rsi_high = rsi_highs[-2][1]
        
        # Prix fait des plus hauts plus hauts, RSI fait des plus hauts plus bas
        if last_price_high > prev_price_high and last_rsi_high < prev_rsi_high:
            return {
                'divergence_detected': True,
                'divergence_type': 'Bearish Divergence',
                'strength': 'Strong' if abs(last_rsi_high - prev_rsi_high) > 5 else 'Weak'
            }
    
    return {'divergence_detected': False, 'divergence_type': None}


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
            'current_volume': None,
            'rsi_divergence': None
        }
    
    # Calculer les indicateurs
    df['sma20'] = calculate_sma(df['close'], 20)
    df['sma50'] = calculate_sma(df['close'], 50)
    df['rsi14'] = calculate_rsi(df['close'], 14)
    df['volume_ma20'] = calculate_volume_ma(df['volume'], 20)
    
    # Détecter divergence RSI
    rsi_divergence = detect_rsi_divergence(df, period=14, lookback=20)
    
    # Récupérer les dernières valeurs
    last = df.iloc[-1]
    
    return {
        'sma20': float(last['sma20']) if pd.notna(last['sma20']) else None,
        'sma50': float(last['sma50']) if pd.notna(last['sma50']) else None,
        'rsi14': float(last['rsi14']) if pd.notna(last['rsi14']) else None,
        'volume_ma20': float(last['volume_ma20']) if pd.notna(last['volume_ma20']) else None,
        'current_price': float(last['close']),
        'current_volume': float(last['volume']),
        'rsi_divergence': rsi_divergence
    }

