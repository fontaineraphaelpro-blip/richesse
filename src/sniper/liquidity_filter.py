"""
Liquidity filter: keep only Binance USDT pairs with 24h volume > threshold (default 20M USD).
"""

from typing import List
import sys
import os

_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src not in sys.path:
    sys.path.insert(0, _src)

from data_fetcher import fetch_usdt_pairs_from_binance
from . import config as cfg


def get_tradable_symbols(
    min_volume_usdt: float = None,
    limit: int = 500,
) -> List[str]:
    """
    Fetch Binance USDT pairs and filter by 24h quote volume.
    Returns list of symbols sorted by volume (highest first).

    Args:
        min_volume_usdt: Minimum 24h volume in USD (default from config: 20M).
        limit: Max number of pairs to return.

    Returns:
        List of symbol strings (e.g. ['BTCUSDT', 'ETHUSDT', ...]).
    """
    if min_volume_usdt is None:
        min_volume_usdt = cfg.MIN_QUOTE_VOLUME_24H_USDT
    return fetch_usdt_pairs_from_binance(
        limit=limit,
        min_quote_volume_usdt=min_volume_usdt,
    )
