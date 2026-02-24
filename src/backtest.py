# -*- coding: utf-8 -*-
"""
Backtest V4 du day trader sur donnees historiques Binance.
Optimise: indicateurs pre-calcules, echantillonnage intelligent.
"""

import time
import sys
from typing import Optional, List, Dict, Any

import pandas as pd

from data_fetcher import get_binance_klines_range, TOP_USDT_PAIRS
from indicators import calculate_indicators
from short_crash_strategy import (
    signal_long_buy_dip,
    signal_short_big_drop,
    score_long_opportunity,
    score_short_opportunity,
    compute_sl_tp_from_chart,
)

VOLUME_RATIO_MIN = 0.35
STOP_LOSS_PCT = 1.0
TAKE_PROFIT_PCT = 2.0
LONG_STOP_LOSS_PCT = 1.0
LONG_TAKE_PROFIT_PCT = 2.0
MIN_SCORE_TO_OPEN = 60
INITIAL_CAPITAL = 100.0
POSITION_PCT = 30
SLIPPAGE_PCT = 0.05
SAMPLE_EVERY = 4
LOOKBACK = 250


def _run_backtest_one_symbol(
    symbol: str,
    df: pd.DataFrame,
    initial_capital: float,
    position_pct: float,
    slippage_pct: float,
) -> tuple:
    equity = initial_capital
    open_position = None
    trades = []
    n = len(df)

    for i in range(LOOKBACK, n):
        row = df.iloc[i]
        ts = row['timestamp']
        h, l, c = row['high'], row['low'], row['close']

        if open_position is not None:
            direction = open_position['direction']
            sl = open_position['sl']
            tp = open_position['tp']
            amount_usdt = open_position['amount_usdt']
            entry = open_position['entry_price']

            exit_price = None
            exit_reason = None

            if direction == 'LONG':
                if l <= sl:
                    exit_price = sl
                    exit_reason = 'stop_loss' if sl < entry else 'trailing_stop'
                elif h >= tp:
                    exit_price = tp
                    exit_reason = 'take_profit'
            else:
                if h >= sl:
                    exit_price = sl
                    exit_reason = 'stop_loss' if sl > entry else 'trailing_stop'
                elif l <= tp:
                    exit_price = tp
                    exit_reason = 'take_profit'

            if exit_price is not None:
                if direction == 'LONG':
                    exit_price *= (1 - slippage_pct / 100)
                    pnl = amount_usdt * (exit_price - entry) / entry
                else:
                    exit_price *= (1 + slippage_pct / 100)
                    pnl = amount_usdt * (entry - exit_price) / entry

                equity += pnl
                trades.append({
                    'symbol': symbol,
                    'direction': direction,
                    'entry_time': open_position['entry_time'],
                    'exit_time': ts,
                    'entry_price': entry,
                    'exit_price': exit_price,
                    'amount_usdt': amount_usdt,
                    'pnl': round(pnl, 4),
                    'exit_reason': exit_reason,
                })
                open_position = None
                continue

        # Only check for new entries every SAMPLE_EVERY bars
        if i % SAMPLE_EVERY != 0:
            continue

        # Use a fixed-size window instead of growing slice
        start_idx = max(0, i - LOOKBACK)
        df_slice = df.iloc[start_idx:i + 1]

        indicators = calculate_indicators(df_slice)
        if not indicators or indicators.get('volume_ratio') is None:
            continue

        spread_pct = (h - l) / c * 100
        atr_pct = indicators.get('atr_percent') or 0
        momentum_15m = indicators.get('price_momentum') or 'NEUTRAL'
        regime = indicators.get('market_regime', 'UNKNOWN')

        # Skip volatile/unknown regimes
        if regime == 'VOLATILE':
            continue

        # SHORT
        if signal_short_big_drop(df_slice, indicators, VOLUME_RATIO_MIN):
            details = score_short_opportunity(
                indicators, spread_pct, atr_pct,
                momentum_15m=momentum_15m, momentum_1h=momentum_15m,
                stop_loss_pct=STOP_LOSS_PCT, take_profit_pct=TAKE_PROFIT_PCT,
            )
            if details['score'] >= MIN_SCORE_TO_OPEN:
                entry_price = c * (1 - slippage_pct / 100)
                sl_c, tp_c, _ = compute_sl_tp_from_chart(entry_price, indicators, 'SHORT')
                sl = sl_c if sl_c else entry_price * (1 + STOP_LOSS_PCT / 100)
                tp = tp_c if tp_c else entry_price * (1 - TAKE_PROFIT_PCT / 100)
                amount_usdt = equity * position_pct / 100
                open_position = {
                    'direction': 'SHORT',
                    'entry_price': entry_price,
                    'entry_time': ts,
                    'sl': sl, 'tp': tp,
                    'amount_usdt': amount_usdt,
                }
                continue

        # LONG
        if signal_long_buy_dip(df_slice, indicators, VOLUME_RATIO_MIN):
            details = score_long_opportunity(
                indicators, spread_pct, atr_pct,
                momentum_15m=momentum_15m, momentum_1h=momentum_15m,
                stop_loss_pct=LONG_STOP_LOSS_PCT, take_profit_pct=LONG_TAKE_PROFIT_PCT,
            )
            if details['score'] >= MIN_SCORE_TO_OPEN:
                entry_price = c * (1 + slippage_pct / 100)
                sl_c, tp_c, _ = compute_sl_tp_from_chart(entry_price, indicators, 'LONG')
                sl = sl_c if sl_c else entry_price * (1 - LONG_STOP_LOSS_PCT / 100)
                tp = tp_c if tp_c else entry_price * (1 + LONG_TAKE_PROFIT_PCT / 100)
                amount_usdt = equity * position_pct / 100
                open_position = {
                    'direction': 'LONG',
                    'entry_price': entry_price,
                    'entry_time': ts,
                    'sl': sl, 'tp': tp,
                    'amount_usdt': amount_usdt,
                }

    return trades, equity


def run_backtest(
    symbols: Optional[List[str]] = None,
    months: int = 3,
    interval: str = '15m',
    initial_capital: float = INITIAL_CAPITAL,
    position_pct: float = POSITION_PCT,
    slippage_pct: float = SLIPPAGE_PCT,
) -> Dict[str, Any]:
    if symbols is None:
        symbols = TOP_USDT_PAIRS[:5]

    end_ms = int(time.time() * 1000)
    start_ms = end_ms - (months * 31 * 24 * 60 * 60 * 1000)

    all_trades = []

    for idx, sym in enumerate(symbols):
        sys.stdout.write("  [{}/{}] {}... ".format(idx + 1, len(symbols), sym))
        sys.stdout.flush()
        df = get_binance_klines_range(sym, interval=interval, start_time_ms=start_ms, end_time_ms=end_ms)
        if df is None or len(df) < 300:
            print("skip")
            continue
        print("{} bars".format(len(df)), end=" ", flush=True)
        trades, _ = _run_backtest_one_symbol(sym, df, initial_capital, position_pct, slippage_pct)
        all_trades.extend(trades)
        print("-> {} trades".format(len(trades)))
        time.sleep(0.2)

    all_trades.sort(key=lambda t: t['exit_time'])

    capital = initial_capital
    peak = initial_capital
    max_dd = 0
    equity_curve = []
    for t in all_trades:
        capital += t['pnl']
        peak = max(peak, capital)
        dd = (peak - capital) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)
        equity_curve.append(round(capital, 2))

    total_trades = len(all_trades)
    if total_trades == 0:
        return {
            'trades': [], 'total_trades': 0, 'win_rate': 0.0,
            'total_return_pct': 0.0, 'max_drawdown_pct': 0.0,
            'final_equity': initial_capital, 'equity_curve': [],
        }

    wins = sum(1 for t in all_trades if t['pnl'] > 0)
    win_rate = (wins / total_trades) * 100
    total_return_pct = (capital - initial_capital) / initial_capital * 100

    return {
        'trades': all_trades,
        'total_trades': total_trades,
        'win_rate': round(win_rate, 1),
        'total_return_pct': round(total_return_pct, 2),
        'max_drawdown_pct': round(max_dd, 1),
        'final_equity': round(capital, 2),
        'equity_curve': equity_curve,
    }


def main():
    pairs = TOP_USDT_PAIRS[:5]
    months = 1
    interval = '1h'
    print("=" * 60)
    print("BACKTEST V4 -- Capital {} $ | {} mois | {} paires | {}".format(
        INITIAL_CAPITAL, months, len(pairs), interval))
    print("=" * 60)
    result = run_backtest(
        symbols=pairs,
        months=months,
        interval=interval,
        position_pct=POSITION_PCT,
        slippage_pct=SLIPPAGE_PCT,
        initial_capital=INITIAL_CAPITAL,
    )
    print("\n" + "=" * 60)
    print("RESULTATS")
    print("=" * 60)
    print("  Trades:     {}".format(result['total_trades']))
    print("  Win rate:   {}%".format(result['win_rate']))
    print("  Rendement:  {}%".format(result['total_return_pct']))
    print("  Drawdown:   {}%".format(result['max_drawdown_pct']))
    print("  Capital fin: {} $".format(result['final_equity']))
    if result['total_trades'] > 0:
        avg_pnl = sum(t['pnl'] for t in result['trades']) / result['total_trades']
        wins = [t for t in result['trades'] if t['pnl'] > 0]
        losses = [t for t in result['trades'] if t['pnl'] <= 0]
        avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
        print("  PnL moyen:  {:.4f} $".format(avg_pnl))
        print("  Gain moyen: +{:.4f} $ | Perte moy: {:.4f} $".format(avg_win, avg_loss))
        longs = [t for t in result['trades'] if t['direction'] == 'LONG']
        shorts = [t for t in result['trades'] if t['direction'] == 'SHORT']
        print("  LONG: {} trades | SHORT: {} trades".format(len(longs), len(shorts)))
        by_sym = {}
        for t in result['trades']:
            s = t['symbol']
            by_sym.setdefault(s, []).append(t)
        print("\n  Par paire:")
        for s, tlist in sorted(by_sym.items()):
            w = sum(1 for t in tlist if t['pnl'] > 0)
            total_pnl = sum(t['pnl'] for t in tlist)
            print("    {} : {} trades, WR {:.0f}%, PnL {:.4f} $".format(
                s, len(tlist), w / len(tlist) * 100, total_pnl))
    return result


if __name__ == "__main__":
    main()
