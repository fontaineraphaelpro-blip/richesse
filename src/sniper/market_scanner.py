"""
Market scanner: fetch tradable symbols (via liquidity filter), then OHLCV for primary and higher TF.
Uses async/parallel fetch for efficiency.
"""

from typing import List, Dict, Tuple, Optional
import sys
import os

_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src not in sys.path:
    sys.path.insert(0, _src)

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from data_fetcher import get_binance_klines
from .liquidity_filter import get_tradable_symbols
from . import config as cfg


def _fetch_klines(args: Tuple[str, str, int]) -> Tuple[str, str, Optional[pd.DataFrame]]:
    symbol, interval, limit = args
    df = get_binance_klines(symbol, interval=interval, limit=limit)
    return symbol, interval, df


def scan_markets(
    symbols: List[str] = None,
    primary_tf: str = None,
    higher_tf: str = None,
    limit_primary: int = None,
    limit_higher: int = None,
    max_workers: int = None,
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame], Dict[str, float]]:
    """
    Fetch OHLCV for all symbols on primary (15m) and higher (1h) timeframes in parallel.

    Args:
        symbols: List of symbols. If None, uses get_tradable_symbols().
        primary_tf: e.g. '15m'
        higher_tf: e.g. '1h'
        limit_primary: candles to fetch for primary
        limit_higher: candles to fetch for higher
        max_workers: parallel workers

    Returns:
        (data_primary, data_higher, last_prices)
        - data_primary[symbol] = DataFrame 15m
        - data_higher[symbol] = DataFrame 1h
        - last_prices[symbol] = last close on primary
    """
    if symbols is None:
        symbols = get_tradable_symbols(limit=500)
    if primary_tf is None:
        primary_tf = cfg.TIMEFRAME_PRIMARY
    if higher_tf is None:
        higher_tf = cfg.TIMEFRAME_HIGHER
    if limit_primary is None:
        limit_primary = cfg.CANDLE_LIMIT_PRIMARY
    if limit_higher is None:
        limit_higher = cfg.CANDLE_LIMIT_HIGHER
    if max_workers is None:
        max_workers = cfg.ASYNC_WORKERS

    args_list = []
    for s in symbols:
        args_list.append((s, primary_tf, limit_primary))
        args_list.append((s, higher_tf, limit_higher))

    data_primary = {}
    data_higher = {}
    last_prices = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch_klines, a): a for a in args_list}
        for future in as_completed(futures):
            try:
                symbol, interval, df = future.result()
                if df is None or df.empty:
                    continue
                if interval == primary_tf:
                    data_primary[symbol] = df
                    last_prices[symbol] = float(df["close"].iloc[-1])
                else:
                    data_higher[symbol] = df
            except Exception:
                pass

    # Only keep symbols that have both TFs
    common = set(data_primary.keys()) & set(data_higher.keys())
    data_primary = {s: data_primary[s] for s in common}
    data_higher = {s: data_higher[s] for s in common}
    last_prices = {s: last_prices[s] for s in common}

    scan_info = {
        "symbols_requested": len(symbols),
        "symbols_with_data": len(common),
    }
    return data_primary, data_higher, last_prices, scan_info
