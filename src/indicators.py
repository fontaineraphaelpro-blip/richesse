"""
Module pour calculer les indicateurs techniques adaptés au scalping.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """Calcule la moyenne mobile simple (SMA)."""
    return data.rolling(window=period).mean()


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """
    Calcule la moyenne mobile exponentielle (EMA).
    Plus réactive que SMA pour le scalping.
    """
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calcule l'indicateur RSI (Relative Strength Index)."""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
    """
    Calcule le MACD (Moving Average Convergence Divergence).
    
    Returns:
        Dictionnaire avec macd_line, signal_line, histogram
    """
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict:
    """
    Calcule les Bandes de Bollinger.
    
    Returns:
        Dictionnaire avec upper, middle, lower
    """
    sma = calculate_sma(data, period)
    std = data.rolling(window=period).std()
    
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    return {
        'upper': upper,
        'middle': sma,
        'lower': lower
    }


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calcule l'ATR (Average True Range) pour mesurer la volatilité.
    Important pour le scalping (stop-loss dynamique).
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_momentum(data: pd.Series, period: int = 10) -> pd.Series:
    """Calcule le momentum (taux de changement)."""
    return data.diff(period)


def calculate_stochastic(df: pd.DataFrame, period: int = 14) -> Dict:
    """
    Calcule le Stochastic Oscillator (%K et %D).
    Utile pour détecter les zones de surachat/survente.
    
    Returns:
        Dictionnaire avec k (stoch_k) et d (stoch_d)
    """
    low_min = df['low'].rolling(window=period).min()
    high_max = df['high'].rolling(window=period).max()
    
    stoch_k = 100 * ((df['close'] - low_min) / (high_max - low_min))
    stoch_d = stoch_k.rolling(window=3).mean()
    
    return {
        'k': stoch_k,
        'd': stoch_d
    }


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calcule l'ADX (Average Directional Index) pour mesurer la force de la tendance.
    ADX > 25 = tendance forte, ADX < 20 = tendance faible.
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Directional Movement
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    # Smoothing
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    # ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return adx


def detect_rsi_divergence(df: pd.DataFrame, rsi: pd.Series, lookback: int = 20) -> Dict:
    """
    Détecte les divergences RSI (bearish divergence = signal SHORT fort).
    
    Returns:
        Dictionnaire avec 'has_divergence' (bool) et 'type' ('bearish' ou None)
    """
    if len(df) < lookback or len(rsi) < lookback:
        return {'has_divergence': False, 'type': None}
    
    try:
        recent_prices = df['close'].tail(lookback)
        recent_rsi = rsi.tail(lookback)
        
        # Chercher un pic de prix suivi d'un pic RSI plus bas (divergence bearish)
        price_peaks = []
        rsi_peaks = []
        
        for i in range(2, len(recent_prices) - 2):
            if recent_prices.iloc[i] > recent_prices.iloc[i-1] and recent_prices.iloc[i] > recent_prices.iloc[i+1]:
                price_peaks.append((i, recent_prices.iloc[i]))
            if recent_rsi.iloc[i] > recent_rsi.iloc[i-1] and recent_rsi.iloc[i] > recent_rsi.iloc[i+1]:
                rsi_peaks.append((i, recent_rsi.iloc[i]))
        
        # Vérifier divergence bearish (prix monte mais RSI baisse)
        if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
            last_price_peak = price_peaks[-1][1]
            prev_price_peak = price_peaks[-2][1]
            last_rsi_peak = rsi_peaks[-1][1]
            prev_rsi_peak = rsi_peaks[-2][1]
            
            if last_price_peak > prev_price_peak and last_rsi_peak < prev_rsi_peak:
                return {'has_divergence': True, 'type': 'bearish'}
    except Exception:
        pass
    
    return {'has_divergence': False, 'type': None}


def calculate_indicators(df: pd.DataFrame) -> Dict:
    """
    Calcule tous les indicateurs techniques pour le scalping.
    
    Args:
        df: DataFrame avec colonnes: timestamp, open, high, low, close, volume
    
    Returns:
        Dictionnaire avec tous les indicateurs calculés
    """
    if df is None or len(df) == 0:
        return {}
    
    close = df['close']
    volume = df['volume']
    
    # Indicateurs de base
    sma20 = calculate_sma(close, 20)
    sma50 = calculate_sma(close, 50)
    
    # EMA rapides pour scalping (9, 21)
    ema9 = calculate_ema(close, 9)
    ema21 = calculate_ema(close, 21)
    
    # RSI
    rsi14 = calculate_rsi(close, 14)
    
    # MACD
    macd_data = calculate_macd(close, fast=12, slow=26, signal=9)
    
    # Bollinger Bands
    bb = calculate_bollinger_bands(close, period=20, std_dev=2.0)
    
    # ATR (volatilité)
    atr = calculate_atr(df, period=14)
    
    # Momentum
    momentum = calculate_momentum(close, period=10)
    
    # Stochastic
    stoch = calculate_stochastic(df, period=14)
    
    # ADX (force de la tendance)
    adx = calculate_adx(df, period=14)
    
    # Divergence RSI
    rsi_divergence = detect_rsi_divergence(df, rsi14, lookback=20)
    
    # Volume
    volume_ma20 = calculate_sma(volume, 20)
    
    # Récupérer les dernières valeurs
    indicators = {
        # Moyennes mobiles
        'sma20': sma20.iloc[-1] if len(sma20) > 0 and not pd.isna(sma20.iloc[-1]) else None,
        'sma50': sma50.iloc[-1] if len(sma50) > 0 and not pd.isna(sma50.iloc[-1]) else None,
        'ema9': ema9.iloc[-1] if len(ema9) > 0 and not pd.isna(ema9.iloc[-1]) else None,
        'ema21': ema21.iloc[-1] if len(ema21) > 0 and not pd.isna(ema21.iloc[-1]) else None,
        
        # RSI
        'rsi14': rsi14.iloc[-1] if len(rsi14) > 0 and not pd.isna(rsi14.iloc[-1]) else None,
        
        # MACD
        'macd': macd_data['macd'].iloc[-1] if len(macd_data['macd']) > 0 and not pd.isna(macd_data['macd'].iloc[-1]) else None,
        'macd_signal': macd_data['signal'].iloc[-1] if len(macd_data['signal']) > 0 and not pd.isna(macd_data['signal'].iloc[-1]) else None,
        'macd_histogram': macd_data['histogram'].iloc[-1] if len(macd_data['histogram']) > 0 and not pd.isna(macd_data['histogram'].iloc[-1]) else None,
        
        # Bollinger Bands
        'bb_upper': bb['upper'].iloc[-1] if len(bb['upper']) > 0 and not pd.isna(bb['upper'].iloc[-1]) else None,
        'bb_middle': bb['middle'].iloc[-1] if len(bb['middle']) > 0 and not pd.isna(bb['middle'].iloc[-1]) else None,
        'bb_lower': bb['lower'].iloc[-1] if len(bb['lower']) > 0 and not pd.isna(bb['lower'].iloc[-1]) else None,
        
        # ATR (volatilité)
        'atr': atr.iloc[-1] if len(atr) > 0 and not pd.isna(atr.iloc[-1]) else None,
        'atr_percent': (atr.iloc[-1] / close.iloc[-1] * 100) if len(atr) > 0 and len(close) > 0 and not pd.isna(atr.iloc[-1]) and close.iloc[-1] > 0 else None,
        
        # Momentum
        'momentum': momentum.iloc[-1] if len(momentum) > 0 and not pd.isna(momentum.iloc[-1]) else None,
        'momentum_percent': (momentum.iloc[-1] / close.iloc[-10] * 100) if len(momentum) > 0 and len(close) > 10 and not pd.isna(momentum.iloc[-1]) and close.iloc[-10] > 0 else None,
        
        # Stochastic
        'stoch_k': stoch['k'].iloc[-1] if len(stoch['k']) > 0 and not pd.isna(stoch['k'].iloc[-1]) else None,
        'stoch_d': stoch['d'].iloc[-1] if len(stoch['d']) > 0 and not pd.isna(stoch['d'].iloc[-1]) else None,
        
        # ADX
        'adx': adx.iloc[-1] if len(adx) > 0 and not pd.isna(adx.iloc[-1]) else None,
        
        # Divergence RSI
        'rsi_divergence': rsi_divergence.get('has_divergence', False),
        'rsi_divergence_type': rsi_divergence.get('type'),
        
        # Volume
        'volume_ma20': volume_ma20.iloc[-1] if len(volume_ma20) > 0 and not pd.isna(volume_ma20.iloc[-1]) else None,
        'current_volume': volume.iloc[-1] if len(volume) > 0 else None,
        
        # Prix actuel
        'current_price': close.iloc[-1] if len(close) > 0 else None,
        'high_24h': df['high'].tail(96).max() if len(df) >= 96 else df['high'].max(),  # 24h en 15min = 96 bougies
        'low_24h': df['low'].tail(96).min() if len(df) >= 96 else df['low'].min(),
    }
    
    return indicators
