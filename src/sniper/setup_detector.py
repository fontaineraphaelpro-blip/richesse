"""
Setup detector: evaluates trend, pullback, volatility contraction, momentum breakout,
volume/accumulation, relative strength vs BTC, and anti-fake breakout.
Returns a structured setup dict for scoring.
"""

from typing import Dict, Optional, Any
import sys
import os

_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src not in sys.path:
    sys.path.insert(0, _src)

from . import config as cfg
from .indicator_engine import compute_sniper_indicators


def _check_trend(ind: Dict) -> tuple:
    """EMA50 > EMA200, Price > EMA50, ADX(14) > 20."""
    ema50 = ind.get("ema50")
    ema200 = ind.get("ema200")
    close = ind.get("close")
    adx = ind.get("adx14")
    if None in (ema50, ema200, close, adx):
        return False, "Missing trend data"
    ok = (ema50 > ema200) and (close > ema50) and (adx > cfg.TREND_ADX_MIN)
    return ok, "Trend OK" if ok else "Trend fail (EMA50>EMA200, price>EMA50, ADX>20)"


def _check_pullback(ind: Dict) -> tuple:
    """Candle low touches EMA20, close > EMA50, distance from EMA50 < 3%."""
    if not ind.get("low_touches_ema20"):
        return False, "Low does not touch EMA20"
    if not ind.get("close", 0) > ind.get("ema50", 0):
        return False, "Close not above EMA50"
    dist = ind.get("dist_ema50_pct")
    if dist is None:
        return False, "Missing dist to EMA50"
    if abs(dist) > cfg.PULLBACK_DIST_EMA50_MAX_PCT:
        return False, "Too extended from EMA50 ({:.2f}% > {}%)".format(abs(dist), cfg.PULLBACK_DIST_EMA50_MAX_PCT)
    return True, "Pullback OK"


def _check_volatility_contraction(ind: Dict) -> tuple:
    """ATR(5) < ATR(20)."""
    ok = ind.get("atr_contraction", False)
    return ok, "Vol contraction OK" if ok else "ATR5 >= ATR20"


def _check_momentum_breakout(ind: Dict) -> tuple:
    """RSI(14) > 55, close > open, close > prev high, volume > VolumeMA(20)."""
    rsi = ind.get("rsi14")
    if rsi is None or rsi <= cfg.RSI_MIN:
        return False, "RSI <= {}".format(cfg.RSI_MIN)
    if not ind.get("is_bullish_candle", False):
        return False, "Candle not bullish (close <= open)"
    if not ind.get("close_above_prev_high", False):
        return False, "Close not above previous high"
    if not ind.get("volume_above_ma20", False):
        return False, "Volume not above VolumeMA20"
    return True, "Momentum breakout OK"


def _check_volume_accumulation(ind: Dict) -> tuple:
    """Volume spike: Volume > 1.5 * VolumeMA20; or progressive increase / range compression."""
    if ind.get("volume_spike", False):
        return True, "Volume spike OK"
    # Alternative: ATR decreasing (range compression)
    if ind.get("atr_contraction", False):
        return True, "Range compression (ATR contraction)"
    return False, "No volume spike or range compression"


def _check_anti_fake(ind: Dict) -> tuple:
    """Breakout candle body > 60% of range; close above highest high of last 5-20."""
    body_pct = ind.get("body_pct_of_range") or 0
    if body_pct < cfg.BREAKOUT_BODY_PCT_MIN:
        return False, "Body {:.0%} < {:.0%} of range".format(body_pct, cfg.BREAKOUT_BODY_PCT_MIN)
    hh = ind.get("highest_high_5_20")
    close = ind.get("close")
    if hh is not None and close is not None and close <= hh:
        return False, "Close not above highest high (5-20)"
    if not ind.get("volume_spike", False):
        return False, "No volume spike on breakout"
    return True, "Anti-fake OK"


def compute_relative_strength(
    alt_price_now: float,
    alt_price_50_ago: float,
    btc_price_now: float,
    btc_price_50_ago: float,
) -> Optional[float]:
    """
    relative_strength = (alt_now/alt_50) - (btc_now/btc_50).
    > 0 means alt outperforming BTC.
    """
    if None in (alt_price_now, alt_price_50_ago, btc_price_now, btc_price_50_ago):
        return None
    if alt_price_now <= 0 or alt_price_50_ago <= 0 or btc_price_now <= 0 or btc_price_50_ago <= 0:
        return None
    ret_alt = (alt_price_now / alt_price_50_ago) - 1.0
    ret_btc = (btc_price_now / btc_price_50_ago) - 1.0
    return ret_alt - ret_btc


def detect_setup(
    df_primary,
    df_higher=None,
    btc_regime: Dict = None,
    btc_price_now: float = None,
    btc_price_50_ago: float = None,
) -> Optional[Dict[str, Any]]:
    """
    Run full setup detection on primary TF data.
    Optionally use higher TF for extra filter; BTC for regime and relative strength.

    Returns:
        Setup dict with:
        - trend_ok, pullback_ok, volatility_ok, momentum_ok, volume_ok, anti_fake_ok, relative_strength_ok
        - btc_bullish
        - relative_strength (float)
        - indicator snapshot (for logging)
        - reasons (str per check)
    """
    if df_primary is None or len(df_primary) < 200:
        return None

    ind = compute_sniper_indicators(df_primary)
    if ind is None:
        return None

    trend_ok, trend_reason = _check_trend(ind)
    pullback_ok, pullback_reason = _check_pullback(ind)
    vol_ok, vol_reason = _check_volatility_contraction(ind)
    momentum_ok, momentum_reason = _check_momentum_breakout(ind)
    volume_ok, volume_reason = _check_volume_accumulation(ind)
    anti_fake_ok, anti_fake_reason = _check_anti_fake(ind)

    btc_bullish = btc_regime.get("is_bullish", False) if btc_regime else False

    alt_price_now = ind.get("close")
    alt_price_50_ago = ind.get("price_50_ago")
    if btc_regime:
        btc_price_now = btc_price_now or btc_regime.get("close")
        btc_price_50_ago = btc_price_50_ago or btc_regime.get("close_50_ago")
    rel_strength = compute_relative_strength(
        alt_price_now or 0, alt_price_50_ago or 0,
        btc_price_now or 0, btc_price_50_ago or 0,
    )
    relative_strength_ok = rel_strength is not None and rel_strength > 0

    return {
        "trend_ok": trend_ok,
        "pullback_ok": pullback_ok,
        "volatility_ok": vol_ok,
        "momentum_ok": momentum_ok,
        "volume_ok": volume_ok,
        "anti_fake_ok": anti_fake_ok,
        "btc_bullish": btc_bullish,
        "relative_strength_ok": relative_strength_ok,
        "relative_strength": rel_strength,
        "reasons": {
            "trend": trend_reason,
            "pullback": pullback_reason,
            "volatility": vol_reason,
            "momentum": momentum_reason,
            "volume": volume_reason,
            "anti_fake": anti_fake_reason,
        },
        "indicators": ind,
    }
