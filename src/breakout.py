"""
Module pour détecter les breakouts et pullbacks.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple


def find_resistance(df: pd.DataFrame, lookback: int = 30) -> Optional[float]:
    """
    Détecte le dernier swing high (résistance) sur les N dernières bougies.
    
    Un swing high est un point où le prix est plus haut que les points adjacents.
    
    Args:
        df: DataFrame avec colonnes high, low, close
        lookback: Nombre de bougies à analyser (défaut: 30)
    
    Returns:
        Prix du swing high (résistance) ou None si non trouvé
    """
    if df.empty or len(df) < 3:
        return None
    
    # Prendre les N dernières bougies
    recent_df = df.tail(lookback).copy()
    
    if len(recent_df) < 3:
        return None
    
    # Trouver les maxima locaux
    highs = recent_df['high'].values
    swing_highs = []
    
    for i in range(1, len(highs) - 1):
        # Vérifier si c'est un maximum local
        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
            swing_highs.append(highs[i])
    
    # Si aucun swing high trouvé, prendre le maximum simple
    if not swing_highs:
        return float(recent_df['high'].max())
    
    # Retourner le dernier swing high (le plus récent)
    return float(min(swing_highs))  # Le plus bas des swing highs récents = résistance plus faible


def detect_breakout(df: pd.DataFrame, indicators: Dict, volume_ratio: float) -> Dict:
    """
    Détecte si le prix a cassé une résistance récente avec volume élevé.
    
    Un breakout est détecté si:
    - Le prix actuel > résistance récente
    - Le volume actuel > 1.5× volume moyen
    
    Args:
        df: DataFrame OHLCV
        indicators: Dictionnaire avec les indicateurs (current_price, current_volume, volume_ma20)
        volume_ratio: Ratio volume actuel / volume moyen
    
    Returns:
        Dictionnaire avec les informations du breakout
    """
    current_price = indicators.get('current_price')
    if current_price is None:
        return {'breakout_detected': False, 'breakout_type': None}
    
    # Trouver la résistance récente
    resistance = find_resistance(df, lookback=30)
    
    if resistance is None:
        return {'breakout_detected': False, 'breakout_type': None}
    
    # Vérifier si le prix a cassé la résistance
    price_above_resistance = current_price > resistance
    
    # Vérifier le volume (doit être > 1.5× volume moyen)
    volume_confirmed = volume_ratio > 1.5
    
    if price_above_resistance and volume_confirmed:
        # Calculer la distance au-dessus de la résistance
        distance = ((current_price - resistance) / resistance) * 100
        
        return {
            'breakout_detected': True,
            'breakout_type': 'Resistance Breakout',
            'resistance_level': resistance,
            'distance_above': distance,
            'volume_ratio': volume_ratio
        }
    
    return {'breakout_detected': False, 'breakout_type': None}


def detect_pullback(df: pd.DataFrame, indicators: Dict, support: Optional[float], 
                   support_distance: Optional[float]) -> Dict:
    """
    Détecte si le prix revient sur un support ou SMA20 dans une tendance bullish.
    
    Un pullback est détecté si:
    - Trend bullish (SMA20 > SMA50)
    - Prix proche du support (< 3%) OU proche de SMA20 (< 2%)
    
    Args:
        df: DataFrame OHLCV
        indicators: Dictionnaire avec les indicateurs
        support: Niveau de support
        support_distance: Distance au support en pourcentage
    
    Returns:
        Dictionnaire avec les informations du pullback
    """
    sma20 = indicators.get('sma20')
    sma50 = indicators.get('sma50')
    current_price = indicators.get('current_price')
    
    if current_price is None or sma20 is None or sma50 is None:
        return {'pullback_detected': False, 'pullback_type': None}
    
    # Vérifier que la tendance est bullish
    is_bullish = sma20 > sma50
    
    if not is_bullish:
        return {'pullback_detected': False, 'pullback_type': None}
    
    # Vérifier distance à SMA20
    distance_to_sma20 = abs((current_price - sma20) / sma20) * 100 if sma20 > 0 else None
    
    # Vérifier distance au support
    near_support = False
    if support_distance is not None and 0 <= support_distance < 3:
        near_support = True
    
    # Vérifier si proche de SMA20
    near_sma20 = False
    if distance_to_sma20 is not None and distance_to_sma20 < 2:
        near_sma20 = True
    
    if near_support or near_sma20:
        pullback_type = []
        if near_support:
            pullback_type.append('Support')
        if near_sma20:
            pullback_type.append('SMA20')
        
        return {
            'pullback_detected': True,
            'pullback_type': ' + '.join(pullback_type),
            'distance_to_sma20': distance_to_sma20,
            'support_distance': support_distance
        }
    
    return {'pullback_detected': False, 'pullback_type': None}


def get_breakout_signals(df: pd.DataFrame, indicators: Dict, support: Optional[float],
                         support_distance: Optional[float], volume_ratio: float) -> Dict:
    """
    Fonction principale pour obtenir tous les signaux de breakout et pullback.
    
    Args:
        df: DataFrame OHLCV
        indicators: Dictionnaire avec les indicateurs
        support: Niveau de support
        support_distance: Distance au support
        volume_ratio: Ratio volume actuel / volume moyen
    
    Returns:
        Dictionnaire avec tous les signaux détectés
    """
    breakout = detect_breakout(df, indicators, volume_ratio)
    pullback = detect_pullback(df, indicators, support, support_distance)
    
    return {
        'breakout': breakout,
        'pullback': pullback
    }

