"""
Crypto Setup Sniper — high-probability multi-filter strategy on Binance.
"""

from .config import (
    MIN_SETUP_SCORE,
    TOP_N_SETUPS,
    TIMEFRAME_PRIMARY,
    TIMEFRAME_HIGHER,
    RISK_PCT_PER_TRADE,
    MAX_SIMULTANEOUS_TRADES,
)

__all__ = [
    "MIN_SETUP_SCORE",
    "TOP_N_SETUPS",
    "TIMEFRAME_PRIMARY",
    "TIMEFRAME_HIGHER",
    "RISK_PCT_PER_TRADE",
    "MAX_SIMULTANEOUS_TRADES",
]
