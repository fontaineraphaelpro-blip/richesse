"""
Fonctions utilitaires pour filtrer les paires avant d'exécuter le scanner.
Inclut : spread check, liquidité (volume), et fenêtre d'activité (basée sur volume/ADX).
"""
from typing import Optional
import pandas as pd


def is_liquid(df: pd.DataFrame, min_avg_volume: float = 1000.0, window: int = 20) -> bool:
    """
    Vérifie si la paire a un volume moyen suffisant sur la fenêtre donnée.
    Retourne True si liquide.
    """
    if df is None or len(df) < window:
        return False
    avg_vol = df['volume'].tail(window).mean()
    return avg_vol >= min_avg_volume


def is_spread_ok(bid: Optional[float], ask: Optional[float], last_candle: Optional[dict] = None, max_spread_pct: float = 0.2) -> bool:
    """
    Vérifie que le spread est raisonnable.

    - Si `bid` et `ask` fournis, utilise (ask - bid)/ask * 100
    - Sinon, approxime le spread avec (high-low)/close de la dernière bougie

    max_spread_pct: pourcentage maximal du spread en pourcent (ex: 0.2 = 0.2%)
    """
    try:
        if bid and ask and ask > 0:
            spread_pct = (ask - bid) / ask * 100
            return spread_pct <= max_spread_pct

        if last_candle is not None:
            high = last_candle.get('high')
            low = last_candle.get('low')
            close = last_candle.get('close')
            if high and low and close and close > 0:
                spread_pct = (high - low) / close * 100
                return spread_pct <= max_spread_pct
    except Exception:
        return False

    # Sans données, on ne trade pas
    return False


def is_tradeable_time(df: pd.DataFrame, min_volume_ratio: float = 0.6, lookback: int = 20) -> bool:
    """
    Pour le crypto, le marché est 24/7. On filtre plutôt selon l'activité récente :
    - Si le volume récent est faible par rapport à sa moyenne, on retourne False.

    min_volume_ratio: fraction minimale du ratio volume/ma (ex: 0.6 signifie 60% de la MA)
    """
    if df is None or len(df) < lookback:
        return False
    recent_vol = df['volume'].tail(lookback).mean()
    overall_vol = df['volume'].rolling(window=lookback).mean().mean()
    if overall_vol == 0 or pd.isna(overall_vol):
        return False
    return (recent_vol / overall_vol) >= min_volume_ratio
