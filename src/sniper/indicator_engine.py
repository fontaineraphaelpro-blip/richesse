"""
Indicator engine for the setup sniper.
Computes EMAs (20, 50, 200), ATR(5), ATR(20), ATR(14), RSI(14), ADX(14), volume, VolumeMA(20).
All values are taken at candle close (last completed bar when evaluating).
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Any

# Use project root for imports when run as package
import sys
import os
_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src not in sys.path:
    sys.path.insert(0, _src)

from indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_atr,
    calculate_adx,
)

from . import config as cfg


def _ema(series: pd.Series, period: int) -> pd.Series:
    return calculate_ema(series, period)


def compute_sniper_indicators(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Compute all indicators required for the setup sniper strategy.
    Uses the LAST COMPLETED candle (iloc[-1]) for signal evaluation at candle close.

    Args:
        df: OHLCV DataFrame with columns timestamp, open, high, low, close, volume

    Returns:
        Dict with scalar values and series for the current bar, or None if insufficient data.
    """
    if df is None or len(df) < max(cfg.TREND_EMA_SLOW, cfg.RELATIVE_STRENGTH_LOOKBACK) + 5:
        return None

    close = df["close"]
    high = df["high"]
    low = df["low"]
    open_ = df["open"]
    volume = df["volume"]

    # EMAs
    ema20 = _ema(close, cfg.PULLBACK_EMA)
    ema50 = _ema(close, cfg.TREND_EMA_FAST)
    ema200 = _ema(close, cfg.TREND_EMA_SLOW)

    # ATR
    atr5 = calculate_atr(df, cfg.ATR_SHORT)
    atr20 = calculate_atr(df, cfg.ATR_LONG)
    atr14 = calculate_atr(df, cfg.SL_ATR_PERIOD)

    # RSI
    rsi14 = calculate_rsi(close, cfg.RSI_PERIOD)

    # ADX
    adx_data = calculate_adx(df, cfg.TREND_ADX_PERIOD)
    adx = adx_data["adx"]

    # Volume
    volume_ma20 = volume.rolling(window=cfg.VOLUME_MA_PERIOD).mean()

    # Index of "current" bar (last closed candle)
    i = -1

    # Previous candle for breakout check
    prev_high = high.iloc[-2] if len(high) >= 2 else None
    prev_low = low.iloc[-2] if len(low) >= 2 else None
    prev_close = close.iloc[-2] if len(close) >= 2 else None

    # Highest high / lowest low over lookback 5-20
    lookback = cfg.BREAKOUT_LOOKBACK_HIGH
    if len(high) >= lookback + 1:
        highest_high_5_20 = high.iloc[-lookback - 1 : -1].max()
        lowest_low_5_20 = low.iloc[-lookback - 1 : -1].min()
    else:
        highest_high_5_20 = None
        lowest_low_5_20 = None

    # Price 50 candles ago (relative strength)
    if len(close) >= cfg.RELATIVE_STRENGTH_LOOKBACK + 1:
        price_50_ago = close.iloc[-cfg.RELATIVE_STRENGTH_LOOKBACK - 1]
    else:
        price_50_ago = None

    current_price = close.iloc[i]
    current_low = low.iloc[i]
    current_open = open_.iloc[i]
    current_high = high.iloc[i]
    current_volume = volume.iloc[i]

    ema20_val = ema20.iloc[i]
    ema50_val = ema50.iloc[i]
    ema200_val = ema200.iloc[i]

    atr5_val = atr5.iloc[i]
    atr20_val = atr20.iloc[i]
    atr14_val = atr14.iloc[i]

    rsi_val = rsi14.iloc[i]
    adx_val = adx.iloc[i]
    vol_ma20_val = volume_ma20.iloc[i] if not pd.isna(volume_ma20.iloc[i]) else 0

    # Candle body and range (for anti-fake)
    body = abs(current_price - current_open)
    candle_range = current_high - current_low
    body_pct_of_range = (body / candle_range) if candle_range > 0 else 0

    # Distance from EMA50 (%)
    dist_ema50_pct = ((current_price - ema50_val) / ema50_val) * 100 if ema50_val and ema50_val > 0 else None

    # Low touches or crosses EMA20 (within some tolerance) — LONG pullback
    tol_ema20 = ema20_val * 0.002 if ema20_val else 0
    low_touches_ema20 = current_low <= (ema20_val + tol_ema20) and current_high >= (ema20_val - tol_ema20)
    # High touches or crosses EMA20 — SHORT pullback
    high_touches_ema20 = current_high >= (ema20_val - tol_ema20) and current_low <= (ema20_val + tol_ema20)

    return {
        "close": current_price,
        "open": current_open,
        "high": current_high,
        "low": current_low,
        "volume": current_volume,
        "ema20": ema20_val,
        "ema50": ema50_val,
        "ema200": ema200_val,
        "atr5": atr5_val,
        "atr20": atr20_val,
        "atr14": atr14_val,
        "rsi14": rsi_val,
        "adx14": adx_val,
        "volume_ma20": vol_ma20_val,
        "prev_high": prev_high,
        "prev_low": prev_low,
        "prev_close": prev_close,
        "highest_high_5_20": highest_high_5_20,
        "lowest_low_5_20": lowest_low_5_20,
        "price_50_ago": price_50_ago,
        "body_pct_of_range": body_pct_of_range,
        "dist_ema50_pct": dist_ema50_pct,
        "low_touches_ema20": low_touches_ema20,
        "high_touches_ema20": high_touches_ema20,
        "is_bullish_candle": current_price > current_open,
        "is_bearish_candle": current_price < current_open,
        "close_above_prev_high": prev_high is not None and current_price > prev_high,
        "close_below_prev_low": prev_low is not None and current_price < prev_low,
        "volume_above_ma20": vol_ma20_val > 0 and current_volume > vol_ma20_val,
        "volume_spike": vol_ma20_val > 0 and current_volume >= (vol_ma20_val * cfg.VOLUME_SPIKE_MULT),
        "atr_contraction": atr5_val < atr20_val if (atr5_val and atr20_val) else False,
    }
