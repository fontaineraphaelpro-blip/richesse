"""
Module pour détecter les niveaux de support.
"""

import pandas as pd
from typing import Optional


def find_swing_low(df: pd.DataFrame, lookback: int = 30) -> Optional[float]:
    """
    Trouve le dernier swing low (support) sur les N dernières bougies.
    
    Args:
        df: DataFrame avec colonnes: open, high, low, close
        lookback: Nombre de bougies à analyser (défaut: 30)
    
    Returns:
        Prix du swing low (support) ou None
    """
    if df is None or len(df) < lookback:
        return None
    
    # Prendre les N dernières bougies
    recent_data = df.tail(lookback)
    
    # Trouver le minimum (swing low)
    swing_low = recent_data['low'].min()
    
    return float(swing_low)


def calculate_distance_to_support(current_price: float, support: float) -> Optional[float]:
    """
    Calcule la distance en pourcentage entre le prix actuel et le support.
    
    Args:
        current_price: Prix actuel
        support: Prix du support
    
    Returns:
        Distance en pourcentage (positif si prix > support, négatif sinon)
    """
    if current_price is None or support is None or support == 0:
        return None
    
    distance = ((current_price - support) / support) * 100
    return float(distance)
