"""
Module pour détecter les niveaux de support.
"""

import pandas as pd
import numpy as np
from typing import Optional


def find_swing_low(df: pd.DataFrame, lookback: int = 30) -> Optional[float]:
    """
    Détecte le dernier swing low (support) sur les N dernières bougies.
    
    Un swing low est un point où le prix est plus bas que les points adjacents.
    
    Args:
        df: DataFrame avec colonnes high, low, close
        lookback: Nombre de bougies à analyser (défaut: 30)
    
    Returns:
        Prix du swing low (support) ou None si non trouvé
    """
    if df.empty or len(df) < 3:
        return None
    
    # Prendre les N dernières bougies
    recent_df = df.tail(lookback).copy()
    
    if len(recent_df) < 3:
        return None
    
    # Trouver les minima locaux
    # Un swing low est un point où low[i] < low[i-1] et low[i] < low[i+1]
    lows = recent_df['low'].values
    swing_lows = []
    
    for i in range(1, len(lows) - 1):
        # Vérifier si c'est un minimum local
        if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
            swing_lows.append(lows[i])
    
    # Si aucun swing low trouvé, prendre le minimum simple
    if not swing_lows:
        return float(recent_df['low'].min())
    
    # Retourner le dernier swing low (le plus récent)
    return float(max(swing_lows))  # Le plus haut des swing lows récents = support plus fort


def calculate_distance_to_support(current_price: float, support: Optional[float]) -> Optional[float]:
    """
    Calcule la distance en pourcentage entre le prix actuel et le support.
    
    Args:
        current_price: Prix actuel
        support: Niveau de support
    
    Returns:
        Distance en pourcentage (positif si prix > support, négatif sinon)
        None si support non disponible
    """
    if support is None or support <= 0:
        return None
    
    if current_price <= 0:
        return None
    
    # Distance en pourcentage
    distance = ((current_price - support) / support) * 100
    return distance

