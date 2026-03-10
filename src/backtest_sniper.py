# -*- coding: utf-8 -*-
"""
Backtest for the Setup Sniper strategy.
Uses the same signal generation (setup_detector, scoring_engine) without live execution.
Evaluates at candle close on 15m; optional 1h filter.
Usage: python -m src.backtest_sniper [--symbols 20] [--limit 500]
"""

import os
import sys
import argparse

_src = os.path.dirname(os.path.abspath(__file__))
if _src not in sys.path:
    sys.path.insert(0, _src)

from data_fetcher import get_binance_klines, fetch_usdt_pairs_from_binance
from sniper.btc_regime import get_btc_regime
from sniper.setup_detector import detect_setup
from sniper.scoring_engine import score_setup
from sniper.ranking_engine import rank_setups
from sniper import config as cfg

# Default: small set for quick backtest
DEFAULT_SYMBOLS = 30
DEFAULT_LIMIT = 500


def run_backtest(symbols_limit: int = DEFAULT_SYMBOLS, candle_limit: int = DEFAULT_LIMIT):
    symbols = fetch_usdt_pairs_from_binance(
        limit=symbols_limit,
        min_quote_volume_usdt=cfg.MIN_QUOTE_VOLUME_24H_USDT,
    )
    btc_regime = get_btc_regime(limit=candle_limit)
    print("BTC regime:", btc_regime.get("reason", "?"))
    print("Scanning {} symbols, {} candles each...".format(len(symbols), candle_limit))

    all_setups = []
    for symbol in symbols:
        df = get_binance_klines(symbol, cfg.TIMEFRAME_PRIMARY, candle_limit)
        if df is None or len(df) < 220:
            continue
        try:
            setup = detect_setup(
                df_primary=df,
                btc_regime=btc_regime,
                btc_price_now=btc_regime.get("close"),
                btc_price_50_ago=btc_regime.get("close_50_ago"),
            )
            if setup is None:
                continue
            setup = score_setup(setup)
            setup["_symbol"] = symbol
            all_setups.append(setup)
        except Exception as e:
            print("  {} error: {}".format(symbol, e))

    passed = [s for s in all_setups if s.get("passed")]
    ranked = rank_setups(passed, top_n=cfg.TOP_N_SETUPS)

    print("\n--- Results ---")
    print("Candidates:", len(all_setups))
    print("Passed (score>={}):".format(cfg.MIN_SETUP_SCORE), len(passed))
    print("Top {} setups:".format(len(ranked)))
    for s in ranked:
        sym = s.get("_symbol", "?")
        score = s.get("score", 0)
        ind = s.get("indicators") or {}
        entry = ind.get("close")
        print("  {} score={} entry={} RSI={} ADX={}".format(
            sym, score, entry, ind.get("rsi14"), ind.get("adx14")))

    return ranked


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backtest Setup Sniper signals")
    parser.add_argument("--symbols", type=int, default=DEFAULT_SYMBOLS, help="Max symbols to scan")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Candles per symbol")
    args = parser.parse_args()
    run_backtest(symbols_limit=args.symbols, candle_limit=args.limit)
