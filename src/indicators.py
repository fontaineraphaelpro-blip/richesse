"""
Module complet de calcul d'indicateurs techniques.
Optimisé pour le SWING TRADING et le DAY TRADING.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

# Import optionnel des patterns si le fichier existe
try:
    from pattern_detection import (
        detect_candlestick_patterns,
        detect_chart_patterns,
        find_liquidity_zones,
        calculate_fibonacci_levels
    )
    HAS_PATTERNS = True
except ImportError:
    HAS_PATTERNS = False


def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """Calcule la Moyenne Mobile Simple (SMA)."""
    return data.rolling(window=period).mean()


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """Calcule la Moyenne Mobile Exponentielle (EMA)."""
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calcule le RSI (Relative Strength Index).
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
    """
    Calcule le MACD (Trend & Momentum).
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
    Calcule les Bandes de Bollinger (Volatilité).
    """
    sma = calculate_sma(data, period)
    std = data.rolling(window=period).std()
    
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    return {
        'upper': upper,
        'middle': sma,
        'lower': lower,
        'width': (upper - lower) / sma  # Écartement des bandes (Bandwidth)
    }


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calcule l'ATR (Average True Range) pour les Stop Loss.
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


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calcule l'ADX (Force de la tendance).
    ADX > 25 = Tendance forte.
    ADX < 20 = Range (Pas de trade en swing).
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    dx_denominator = plus_di + minus_di
    dx = 100 * abs(plus_di - minus_di) / dx_denominator.replace(0, np.nan)
    adx = dx.rolling(window=period).mean()
    
    return adx


def calculate_stochastic(df: pd.DataFrame, period: int = 14, k_period: int = 3, d_period: int = 3) -> Dict:
    """
    Calcule l'Oscillateur Stochastique.
    """
    low_min = df['low'].rolling(window=period).min()
    high_max = df['high'].rolling(window=period).max()
    
    k = 100 * ((df['close'] - low_min) / (high_max - low_min))
    d = k.rolling(window=d_period).mean()  # Signal line
    
    return {'k': k, 'd': d}


def calculate_ichimoku(df: pd.DataFrame) -> Dict:
    """
    Calcule les bases d'Ichimoku (Tenkan & Kijun) pour confirmation supplémentaire.
    """
    # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2))
    period9_high = df['high'].rolling(window=9).max()
    period9_low = df['low'].rolling(window=9).min()
    tenkan_sen = (period9_high + period9_low) / 2

    # Kijun-sen (Base Line): (26-period high + 26-period low)/2))
    period26_high = df['high'].rolling(window=26).max()
    period26_low = df['low'].rolling(window=26).min()
    kijun_sen = (period26_high + period26_low) / 2
    
    return {'tenkan': tenkan_sen, 'kijun': kijun_sen}


def calculate_indicators(df: pd.DataFrame) -> Dict:
    """
    Fonction MAÎTRESSE : Calcule TOUS les indicateurs et retourne un dictionnaire complet.
    
    Args:
        df: DataFrame avec colonnes: timestamp, open, high, low, close, volume
    
    Returns:
        Dictionnaire riche avec valeurs actuelles et état du marché.
    """
    if df is None or len(df) < 200:
        return {}
    
    close = df['close']
    volume = df['volume']
    
    # 1. MOYENNES MOBILES (Tendance)
    # ----------------------------------------
    sma50 = calculate_sma(close, 50)
    sma200 = calculate_sma(close, 200)
    ema9 = calculate_ema(close, 9)   # Pour entrées rapides
    ema21 = calculate_ema(close, 21) # Pour entrées rapides
    
    # 2. MOMENTUM & OSCILLATEURS
    # ----------------------------------------
    rsi14 = calculate_rsi(close, 14)
    macd_data = calculate_macd(close)
    stoch_data = calculate_stochastic(df)
    
    # 3. VOLATILITÉ & FORCE
    # ----------------------------------------
    atr = calculate_atr(df, 14)
    adx = calculate_adx(df, 14)
    bb = calculate_bollinger_bands(close, 20, 2.0)
    
    # 4. VOLUME
    # ----------------------------------------
    volume_ma20 = calculate_sma(volume, 20)
    
    # 5. PATTERNS & SUPPORTS (Si disponibles)
    # ----------------------------------------
    patterns = {}
    support_zones = []
    if HAS_PATTERNS:
        try:
            patterns = detect_candlestick_patterns(df)
            liquidity = find_liquidity_zones(df, lookback=100)
            support_zones = liquidity.get('support_zones', [])
        except Exception:
            pass

    # 6. MOMENTUM CONFIRMATION (Direction récente du prix)
    # ----------------------------------------
    # Vérifier si le prix MONTE ou DESCEND actuellement (dernières 3 bougies)
    price_momentum = 'NEUTRAL'
    momentum_strength = 0
    
    if len(close) >= 4:
        # Calculer le changement de prix sur les 3 dernières bougies
        price_3_candles_ago = close.iloc[-4]
        price_2_candles_ago = close.iloc[-3]
        price_1_candle_ago = close.iloc[-2]
        current = close.iloc[-1]
        
        # Changement en %
        change_3 = ((current - price_3_candles_ago) / price_3_candles_ago) * 100
        change_2 = ((current - price_2_candles_ago) / price_2_candles_ago) * 100
        
        # Vérifier si les bougies font des hauts plus hauts (bullish) ou bas plus bas (bearish)
        higher_highs = df['high'].iloc[-1] > df['high'].iloc[-2] and df['high'].iloc[-2] > df['high'].iloc[-3]
        lower_lows = df['low'].iloc[-1] < df['low'].iloc[-2] and df['low'].iloc[-2] < df['low'].iloc[-3]
        
        # Bougies vertes vs rouges (close > open = vert)
        green_candles = sum([
            1 if df['close'].iloc[-i] > df['open'].iloc[-i] else 0 
            for i in range(1, 4)
        ])
        red_candles = 3 - green_candles
        
        # Déterminer le momentum
        if change_3 > 0.5 and green_candles >= 2:
            price_momentum = 'BULLISH'
            momentum_strength = min(change_3 * 10, 100)  # Force du momentum
        elif change_3 < -0.5 and red_candles >= 2:
            price_momentum = 'BEARISH'
            momentum_strength = min(abs(change_3) * 10, 100)
        elif higher_highs:
            price_momentum = 'BULLISH'
            momentum_strength = 50
        elif lower_lows:
            price_momentum = 'BEARISH'
            momentum_strength = 50
    
    # 7. CONSTRUCTION DU DICTIONNAIRE FINAL
    # ----------------------------------------
    # On prend la dernière valeur (.iloc[-1]) pour le temps réel
    # On prend parfois l'avant-dernière (.iloc[-2]) pour confirmer une clôture
    
    current_price = close.iloc[-1]
    
    indicators = {
        # --- PRIX ---
        'current_price': current_price,
        'open_price': df['open'].iloc[-1],
        'high_price': df['high'].iloc[-1],
        'low_price': df['low'].iloc[-1],
        
        # --- MOYENNES MOBILES (Fondamental pour Swing) ---
        'sma50': sma50.iloc[-1],
        'sma200': sma200.iloc[-1],
        'ema9': ema9.iloc[-1],
        'ema21': ema21.iloc[-1],
        
        # Écarts (%) par rapport aux moyennes (utile pour détecter les extensions)
        'dist_sma50_percent': ((current_price - sma50.iloc[-1]) / sma50.iloc[-1]) * 100,
        'dist_sma200_percent': ((current_price - sma200.iloc[-1]) / sma200.iloc[-1]) * 100,
        
        # --- MOMENTUM ---
        'rsi14': rsi14.iloc[-1],
        'rsi14_prev': rsi14.iloc[-2], # Pour voir la pente du RSI
        
        'macd': macd_data['macd'].iloc[-1],
        'macd_signal': macd_data['signal'].iloc[-1],
        'macd_hist': macd_data['histogram'].iloc[-1],
        'macd_hist_prev': macd_data['histogram'].iloc[-2], # Pour détecter retournement MACD
        
        'stoch_k': stoch_data['k'].iloc[-1],
        'stoch_d': stoch_data['d'].iloc[-1],
        
        # --- VOLATILITÉ & TENDANCE ---
        'atr': atr.iloc[-1],
        'atr_percent': (atr.iloc[-1] / current_price) * 100,
        'adx': adx.iloc[-1],
        
        # --- BANDES DE BOLLINGER ---
        'bb_upper': bb['upper'].iloc[-1],
        'bb_lower': bb['lower'].iloc[-1],
        'bb_width': bb['width'].iloc[-1],
        'bb_percent': (current_price - bb['lower'].iloc[-1]) / (bb['upper'].iloc[-1] - bb['lower'].iloc[-1]) if (bb['upper'].iloc[-1] - bb['lower'].iloc[-1]) != 0 else 0.5,
        
        # --- VOLUME ---
        'current_volume': volume.iloc[-1],
        'volume_ma20': volume_ma20.iloc[-1],
        'volume_ratio': volume.iloc[-1] / volume_ma20.iloc[-1] if volume_ma20.iloc[-1] > 0 else 0,
        
        # --- PATTERNS & EXTRA ---
        'candlestick_patterns': patterns.get('patterns', []),
        'is_bearish_candle': patterns.get('has_bearish_pattern', False),
        'support_zones': support_zones,
        
        # --- MOMENTUM CONFIRMATION (TREND FOLLOWING) ---
        'price_momentum': price_momentum,        # 'BULLISH', 'BEARISH', 'NEUTRAL'
        'momentum_strength': momentum_strength,  # 0-100
    }
    
    # Nettoyage des valeurs NaN (au cas où)
    for k, v in indicators.items():
        if isinstance(v, (float, np.float64, np.float32)) and np.isnan(v):
            indicators[k] = None
            
    return indicators
