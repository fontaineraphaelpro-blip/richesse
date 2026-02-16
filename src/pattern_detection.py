"""
Module pour détecter les patterns de chandeliers et chartistes.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


def detect_candlestick_patterns(df: pd.DataFrame) -> Dict:
    """
    Détecte les patterns de chandeliers japonais.
    
    Returns:
        Dictionnaire avec les patterns détectés
    """
    if df is None or len(df) < 3:
        return {'patterns': [], 'bearish_signals': 0}
    
    patterns = []
    bearish_signals = 0
    
    # Prendre les 3 dernières bougies
    recent = df.tail(3)
    
    if len(recent) < 3:
        return {'patterns': [], 'bearish_signals': 0}
    
    # Bougie actuelle
    current = recent.iloc[-1]
    prev = recent.iloc[-2]
    prev2 = recent.iloc[-3] if len(recent) >= 3 else None
    
    open_price = current['open']
    close_price = current['close']
    high_price = current['high']
    low_price = current['low']
    
    prev_open = prev['open']
    prev_close = prev['close']
    prev_high = prev['high']
    prev_low = prev['low']
    
    body = abs(close_price - open_price)
    upper_shadow = high_price - max(open_price, close_price)
    lower_shadow = min(open_price, close_price) - low_price
    total_range = high_price - low_price
    
    # Pré-calcul des ratios pour éviter les erreurs "UnboundLocalError"
    # et gérer le cas où total_range est 0
    upper_shadow_ratio = 0.0
    lower_shadow_ratio = 0.0
    body_ratio = 0.0
    
    if total_range > 0:
        upper_shadow_ratio = upper_shadow / total_range
        lower_shadow_ratio = lower_shadow / total_range
        body_ratio = body / total_range
    
    # 1. Bearish Engulfing (très bearish)
    if prev_close > prev_open and close_price < open_price:
        if open_price > prev_close and close_price < prev_open:
            patterns.append('Bearish Engulfing')
            bearish_signals += 3
    
    # 2. Dark Cloud Cover (bearish)
    if prev_close > prev_open and close_price < open_price:
        if open_price > prev_high and close_price < (prev_open + prev_close) / 2:
            patterns.append('Dark Cloud Cover')
            bearish_signals += 2
    
    # 3. Shooting Star (bearish reversal) - Longue mèche haute
    if total_range > 0:
        if upper_shadow_ratio > 0.6 and body_ratio < 0.3 and close_price < open_price:
            patterns.append('Shooting Star')
            bearish_signals += 2
    
    # 4. Hanging Man (bearish si après hausse) - Longue mèche basse
    # Le Hanging Man ressemble à un marteau (Hammer) mais en haut de tendance
    if prev_close > prev_open:
        # On utilise lower_shadow_ratio ici (correction du bug)
        if lower_shadow_ratio > 0.6 and body_ratio < 0.3:
             # Confirmation supplémentaire: petite mèche haute
             if upper_shadow_ratio < 0.1:
                patterns.append('Hanging Man')
                bearish_signals += 1
    
    # 5. Three Black Crows (très bearish)
    if prev2 is not None and len(recent) >= 3:
        if (prev2['close'] < prev2['open'] and 
            prev_close < prev_open and 
            close_price < open_price):
            if (prev2['close'] > prev_close and prev_close > close_price):
                patterns.append('Three Black Crows')
                bearish_signals += 4
    
    # 6. Bearish Harami
    if prev_close > prev_open and close_price < open_price:
        if (open_price > prev_low and close_price > prev_low and
            open_price < prev_high and close_price < prev_high):
            patterns.append('Bearish Harami')
            bearish_signals += 1
    
    return {
        'patterns': patterns,
        'bearish_signals': bearish_signals,
        'has_bearish_pattern': bearish_signals > 0
    }


def detect_chart_patterns(df: pd.DataFrame, lookback: int = 50) -> Dict:
    """
    Détecte les patterns chartistes (double top, head and shoulders, etc.).
    
    Returns:
        Dictionnaire avec les patterns détectés
    """
    if df is None or len(df) < lookback:
        return {'patterns': [], 'bearish_signals': 0}
    
    patterns = []
    bearish_signals = 0
    
    recent = df.tail(lookback)
    highs = recent['high'].values
    lows = recent['low'].values
    closes = recent['close'].values
    
    # 1. Double Top (bearish)
    if len(highs) >= 20:
        # Trouver les deux pics
        peaks = []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                peaks.append((i, highs[i]))
        
        if len(peaks) >= 2:
            # Vérifier si les deux pics sont similaires (écart < 2%)
            last_peak = peaks[-1]
            prev_peak = peaks[-2]
            
            if abs(last_peak[1] - prev_peak[1]) / prev_peak[1] < 0.02:
                # Vérifier si le prix actuel est en dessous du creux entre les pics
                if last_peak[0] > prev_peak[0]:
                    valley = lows[prev_peak[0]:last_peak[0]].min()
                    if closes[-1] < valley:
                        patterns.append('Double Top')
                        bearish_signals += 3
    
    # 2. Head and Shoulders (bearish)
    if len(highs) >= 30:
        # Chercher 3 pics avec le milieu plus haut
        peaks = []
        for i in range(3, len(highs) - 3):
            if (highs[i] > highs[i-1] and highs[i] > highs[i+1] and
                highs[i] > highs[i-2] and highs[i] > highs[i+2]):
                peaks.append((i, highs[i]))
        
        if len(peaks) >= 3:
            # Vérifier pattern H&S
            left_shoulder = peaks[-3]
            head = peaks[-2]
            right_shoulder = peaks[-1]
            
            if (head[1] > left_shoulder[1] and head[1] > right_shoulder[1] and
                abs(left_shoulder[1] - right_shoulder[1]) / left_shoulder[1] < 0.03):
                patterns.append('Head and Shoulders')
                bearish_signals += 4
    
    # 3. Descending Triangle (bearish)
    if len(highs) >= 20:
        # Vérifier si les hauts descendent et les bas sont stables
        recent_highs = highs[-20:]
        recent_lows = lows[-20:]
        
        high_trend = np.polyfit(range(len(recent_highs)), recent_highs, 1)[0]
        low_trend = np.polyfit(range(len(recent_lows)), recent_lows, 1)[0]
        
        if high_trend < -0.001 and abs(low_trend) < 0.001:
            patterns.append('Descending Triangle')
            bearish_signals += 2
    
    return {
        'patterns': patterns,
        'bearish_signals': bearish_signals,
        'has_bearish_pattern': bearish_signals > 0
    }


def find_liquidity_zones(df: pd.DataFrame, lookback: int = 100) -> Dict:
    """
    Trouve les zones de liquidité (support/résistance forts).
    
    Utilise:
    - Clusters de volume (zones où beaucoup de volume a été échangé)
    - Niveaux psychologiques (round numbers)
    - Pics et creux répétés
    
    Returns:
        Dictionnaire avec les zones de liquidité
    """
    if df is None or len(df) < lookback:
        return {
            'support_zones': [],
            'resistance_zones': [],
            'liquidity_clusters': []
        }
    
    recent = df.tail(lookback)
    current_price = recent['close'].iloc[-1]
    
    # 1. Zones de volume (clusters)
    volume_clusters = []
    price_bins = np.linspace(recent['low'].min(), recent['high'].max(), 20)
    
    for i in range(len(price_bins) - 1):
        bin_low = price_bins[i]
        bin_high = price_bins[i + 1]
        
        # Volume dans cette zone de prix
        mask = (recent['low'] <= bin_high) & (recent['high'] >= bin_low)
        volume_in_zone = recent[mask]['volume'].sum()
        
        if volume_in_zone > recent['volume'].mean() * 1.5:
            volume_clusters.append({
                'price': (bin_low + bin_high) / 2,
                'volume': volume_in_zone,
                'strength': min(volume_in_zone / recent['volume'].mean(), 3.0)
            })
    
    # 2. Niveaux psychologiques (round numbers)
    psychological_levels = []
    price_range = recent['high'].max() - recent['low'].min()
    
    if current_price > 100:
        # Niveaux à 100, 500, 1000, etc.
        base = 10 ** (len(str(int(current_price))) - 1)
        for multiplier in [1, 2, 5, 10, 20, 50, 100]:
            level = base * multiplier
            if recent['low'].min() <= level <= recent['high'].max():
                psychological_levels.append(level)
    elif current_price > 1:
        # Niveaux à 1, 2, 5, 10, etc.
        for level in [1, 2, 5, 10, 20, 50]:
            if recent['low'].min() <= level <= recent['high'].max():
                psychological_levels.append(level)
    else:
        # Niveaux à 0.1, 0.2, 0.5, etc.
        for level in [0.1, 0.2, 0.5, 1.0, 2.0, 5.0]:
            if recent['low'].min() <= level <= recent['high'].max():
                psychological_levels.append(level)
    
    # 3. Support et résistance (pics et creux répétés)
    support_zones = []
    resistance_zones = []
    
    # Trouver les creux (support potentiel)
    for i in range(5, len(recent) - 5):
        if recent['low'].iloc[i] == recent['low'].iloc[i-5:i+5].min():
            support_level = recent['low'].iloc[i]
            # Vérifier si ce niveau a été touché plusieurs fois
            touches = ((recent['low'] <= support_level * 1.01) & 
                      (recent['low'] >= support_level * 0.99)).sum()
            if touches >= 2:
                support_zones.append({
                    'price': support_level,
                    'strength': touches,
                    'distance': ((current_price - support_level) / current_price) * 100
                })
    
    # Trouver les pics (résistance potentielle)
    for i in range(5, len(recent) - 5):
        if recent['high'].iloc[i] == recent['high'].iloc[i-5:i+5].max():
            resistance_level = recent['high'].iloc[i]
            # Vérifier si ce niveau a été touché plusieurs fois
            touches = ((recent['high'] <= resistance_level * 1.01) & 
                      (recent['high'] >= resistance_level * 0.99)).sum()
            if touches >= 2:
                resistance_zones.append({
                    'price': resistance_level,
                    'strength': touches,
                    'distance': ((resistance_level - current_price) / current_price) * 100
                })
    
    # Trier par force
    support_zones.sort(key=lambda x: x['strength'], reverse=True)
    resistance_zones.sort(key=lambda x: x['strength'], reverse=True)
    volume_clusters.sort(key=lambda x: x['strength'], reverse=True)
    
    return {
        'support_zones': support_zones[:5],  # Top 5
        'resistance_zones': resistance_zones[:5],  # Top 5
        'liquidity_clusters': volume_clusters[:5],  # Top 5
        'psychological_levels': psychological_levels,
        'nearest_support': support_zones[0]['price'] if support_zones else None,
        'nearest_resistance': resistance_zones[0]['price'] if resistance_zones else None
    }


def calculate_fibonacci_levels(df: pd.DataFrame, lookback: int = 50) -> Dict:
    """
    Calcule les niveaux de Fibonacci retracement.
    
    Returns:
        Dictionnaire avec les niveaux Fibonacci
    """
    if df is None or len(df) < lookback:
        return {'levels': [], 'nearest_level': None}
    
    recent = df.tail(lookback)
    high = recent['high'].max()
    low = recent['low'].min()
    current_price = recent['close'].iloc[-1]
    
    diff = high - low
    if diff == 0:
        return {'levels': [], 'nearest_level': None}
    
    # Niveaux Fibonacci classiques
    fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
    
    levels = []
    for fib in fib_levels:
        level = high - (diff * fib)
        distance = ((current_price - level) / current_price) * 100
        levels.append({
            'price': level,
            'fibonacci': fib,
            'distance': distance
        })
    
    # Trouver le niveau le plus proche
    nearest = min(levels, key=lambda x: abs(x['distance'])) if levels else None
    
    return {
        'levels': levels,
        'nearest_level': nearest['price'] if nearest else None,
        'nearest_fib': nearest['fibonacci'] if nearest else None
    }

