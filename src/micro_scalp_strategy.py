"""
Stratégie MICRO SCALP 1€ BOT
Conditions d'entrée, calcul de taille de position, et gestion du trade.
"""

import pandas as pd
import numpy as np

def micro_scalp_entry_long(df, indicators, volume_ratio_min=1.1):
    """
    Détecte un signal d'entrée LONG micro scalp selon la stratégie.
    """
    # RSI 1m < 30
    if indicators.get('rsi14', 50) >= 30:
        return False
    # Prix touche bande basse de Bollinger
    if not (indicators.get('bb_percent', 0) <= 0.05):
        return False
    # Volume légèrement au-dessus de la moyenne
    if indicators.get('volume_ratio', 1) < volume_ratio_min:
        return False
    # Pas de forte tendance baissière sur 15m (à vérifier dans le main)
    return True

def micro_scalp_entry_short(df, indicators, volume_ratio_min=1.1):
    """
    Détecte un signal d'entrée SHORT micro scalp selon la stratégie.
    """
    # RSI 1m > 70
    if indicators.get('rsi14', 50) <= 70:
        return False
    # Prix touche bande haute de Bollinger
    if not (indicators.get('bb_percent', 0) >= 0.95):
        return False
    # Volume légèrement au-dessus de la moyenne
    if indicators.get('volume_ratio', 1) < volume_ratio_min:
        return False
    # Pas de forte tendance haussière sur 15m (à vérifier dans le main)
    return True

def calculate_position_size(profit_target, target_pct):
    """
    Calcule la taille de position pour viser un profit fixe.
    """
    if target_pct <= 0:
        return 0
    return profit_target / (target_pct / 100)
