"""
Scoring engine: points per filter, total score. Trade only if score >= MIN_SETUP_SCORE.
"""

from typing import Dict, Any
from . import config as cfg


def score_setup(setup: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply points system:
    - Trend alignment = +2
    - BTC market confirmation = +1
    - Pullback quality = +1
    - Volatility contraction = +1
    - Momentum breakout = +2
    - Volume / accumulation = +1
    - Anti fake breakout passed = +1
    - Relative strength > 0 = +1

    Returns:
        setup dict with added keys: score, score_breakdown, passed (bool).
    """
    if not setup:
        return {"score": 0, "score_breakdown": {}, "passed": False}

    points = 0
    breakdown = {}

    if setup.get("trend_ok"):
        points += cfg.SCORE_TREND_ALIGNMENT
        breakdown["trend"] = cfg.SCORE_TREND_ALIGNMENT
    else:
        breakdown["trend"] = 0

    if setup.get("btc_bullish"):
        points += cfg.SCORE_BTC_CONFIRMATION
        breakdown["btc"] = cfg.SCORE_BTC_CONFIRMATION
    else:
        breakdown["btc"] = 0

    if setup.get("pullback_ok"):
        points += cfg.SCORE_PULLBACK_QUALITY
        breakdown["pullback"] = cfg.SCORE_PULLBACK_QUALITY
    else:
        breakdown["pullback"] = 0

    if setup.get("volatility_ok"):
        points += cfg.SCORE_VOLATILITY_CONTRACTION
        breakdown["volatility"] = cfg.SCORE_VOLATILITY_CONTRACTION
    else:
        breakdown["volatility"] = 0

    if setup.get("momentum_ok"):
        points += cfg.SCORE_MOMENTUM_BREAKOUT
        breakdown["momentum"] = cfg.SCORE_MOMENTUM_BREAKOUT
    else:
        breakdown["momentum"] = 0

    if setup.get("volume_ok"):
        points += cfg.SCORE_VOLUME_ACCUMULATION
        breakdown["volume"] = cfg.SCORE_VOLUME_ACCUMULATION
    else:
        breakdown["volume"] = 0

    if setup.get("anti_fake_ok"):
        points += cfg.SCORE_ANTI_FAKE_PASSED
        breakdown["anti_fake"] = cfg.SCORE_ANTI_FAKE_PASSED
    else:
        breakdown["anti_fake"] = 0

    if setup.get("relative_strength_ok"):
        points += cfg.SCORE_RELATIVE_STRENGTH
        breakdown["relative_strength"] = cfg.SCORE_RELATIVE_STRENGTH
    else:
        breakdown["relative_strength"] = 0

    setup["score"] = points
    setup["score_breakdown"] = breakdown
    setup["passed"] = points >= cfg.MIN_SETUP_SCORE
    return setup
