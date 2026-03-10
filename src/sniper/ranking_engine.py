"""
Ranking engine: rank setups by score, trend strength, relative strength, volume expansion, volatility expansion.
Return top N for execution.
"""

from typing import List, Dict, Any
from . import config as cfg


def rank_setups(
    setups: List[Dict[str, Any]],
    top_n: int = None,
) -> List[Dict[str, Any]]:
    """
    Rank by:
    1. Score (desc)
    2. Trend strength (e.g. ADX; desc)
    3. Relative strength vs BTC (desc)
    4. Volume expansion (volume ratio; desc)
    5. Volatility expansion (ATR; secondary)

    Returns top_n setups (default from config).
    """
    if top_n is None:
        top_n = cfg.TOP_N_SETUPS
    if not setups:
        return []

    # Only passed setups
    passed = [s for s in setups if s.get("passed", False)]
    if not passed:
        return []

    def sort_key(s):
        ind = s.get("indicators") or {}
        score = s.get("score", 0)
        adx = ind.get("adx14") or 0
        rel = s.get("relative_strength") or 0
        vol_ratio = (ind.get("volume", 0) / ind.get("volume_ma20", 1)) if ind.get("volume_ma20") else 0
        atr = ind.get("atr14") or 0
        return (score, adx, rel, vol_ratio, atr)

    passed.sort(key=sort_key, reverse=True)
    return passed[:top_n]
