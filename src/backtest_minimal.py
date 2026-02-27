# -*- coding: utf-8 -*-
"""
Backtest minimal: valide la stratégie (SL/TP, score min, R:R) sur données 15m.
Usage: BACKTEST_MIN_SCORE=58 BACKTEST_MIN_RR=1.5 python -m src.backtest_minimal
"""
import os
import sys

if __name__ == '__main__':
    _src = os.path.dirname(os.path.abspath(__file__))
    if _src not in sys.path:
        sys.path.insert(0, _src)

from datetime import datetime, timedelta
from data_fetcher import get_binance_klines, get_top_pairs
from indicators import calculate_indicators
from short_crash_strategy import compute_sl_tp_from_chart

MIN_SCORE = int(os.environ.get('BACKTEST_MIN_SCORE', '58'))
MIN_RR = float(os.environ.get('BACKTEST_MIN_RR', '1.5'))
SYMBOLS = list(get_top_pairs())[:10]
LIMIT = 500


def run():
    print("Backtest minimal (score>={}, R:R>={}) sur {} paires, {} bougies".format(MIN_SCORE, MIN_RR, len(SYMBOLS), LIMIT))
    results = []
    for symbol in SYMBOLS:
        df = get_binance_klines(symbol, '15m', LIMIT)
        if df is None or len(df) < 100:
            continue
        ind = calculate_indicators(df)
        if not ind:
            continue
        price = float(df['close'].iloc[-1])
        for direction in ('LONG', 'SHORT'):
            sl, tp, sl_pct = compute_sl_tp_from_chart(price, ind, direction)
            if sl is None:
                continue
            if direction == 'LONG':
                rr = (tp - price) / (price - sl) if sl < price else 0
            else:
                rr = (price - tp) / (sl - price) if sl > price else 0
            if rr >= MIN_RR:
                results.append({'symbol': symbol, 'direction': direction, 'price': price, 'sl': sl, 'tp': tp, 'rr': rr, 'sl_pct': sl_pct})
    print("Signaux R:R>={}: {}".format(MIN_RR, len(results)))
    for r in results[:15]:
        print("  {} {} @ {:.4f} SL {:.4f} TP {:.4f} R:R {:.2f}".format(r['symbol'], r['direction'], r['price'], r['sl'], r['tp'], r['rr']))
    return results


if __name__ == '__main__':
    run()
