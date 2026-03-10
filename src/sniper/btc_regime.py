"""
Global market regime (BTC): must be bullish for altcoin longs.
BTC close > BTC EMA200 and BTC RSI(14) > 50.
"""

from typing import Dict, Optional
import sys
import os

_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src not in sys.path:
    sys.path.insert(0, _src)

from data_fetcher import get_binance_klines
from indicators import calculate_ema, calculate_rsi
from . import config as cfg


def get_btc_regime(limit: int = 250) -> Dict:
    """
    Fetch BTC OHLCV, compute EMA200 and RSI(14).
    Bullish = close > EMA200 and RSI(14) > 50.

    Returns:
        {
            'is_bullish': bool,
            'close': float,
            'ema200': float,
            'rsi14': float,
            'reason': str,
        }
    """
    df = get_binance_klines(
        cfg.BTC_SYMBOL,
        interval=cfg.TIMEFRAME_PRIMARY,
        limit=limit,
    )
    if df is None or len(df) < cfg.BTC_EMA200_PERIOD + 5:
        return {
            "is_bullish": False,
            "close": None,
            "close_50_ago": None,
            "ema200": None,
            "rsi14": None,
            "reason": "Insufficient BTC data",
        }

    close = df["close"]
    ema200 = calculate_ema(close, cfg.BTC_EMA200_PERIOD)
    rsi14 = calculate_rsi(close, cfg.BTC_RSI_PERIOD)

    c = close.iloc[-1]
    e = ema200.iloc[-1]
    r = rsi14.iloc[-1]
    close_50_ago = close.iloc[-cfg.RELATIVE_STRENGTH_LOOKBACK - 1] if len(close) > cfg.RELATIVE_STRENGTH_LOOKBACK else None

    import pandas as pd
    above_ema = c > e if (c and e) else False
    rsi_ok = r > cfg.BTC_BULLISH_RSI_MIN if (r is not None and not pd.isna(r)) else False
    is_bullish = above_ema and rsi_ok

    reason = "Bullish" if is_bullish else "Bearish or weak (close>EMA200={}, RSI>50={})".format(
        above_ema, rsi_ok
    )

    return {
        "is_bullish": is_bullish,
        "close": float(c),
        "close_50_ago": float(close_50_ago) if close_50_ago is not None else None,
        "ema200": float(e),
        "rsi14": float(r) if r is not None else None,
        "reason": reason,
    }
