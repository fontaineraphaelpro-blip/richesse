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

VOLUME_RATIO_MIN = 1.2       # Volume >= 120% de la moyenne
STOP_LOSS_PCT = 1.5
TAKE_PROFIT_PCT = 1.5         # TP = SL (R:R 1:1 pour 60% WR)
LONG_STOP_LOSS_PCT = 1.5
LONG_TAKE_PROFIT_PCT = 1.5
MIN_SCORE_TO_OPEN = 70        # Score strict (backtest single-TF = moins strict que live)
MIN_ADX = 22                  # ADX 22+ = tendance confirmee
INITIAL_CAPITAL = 100.0
POSITION_PCT = 25
SLIPPAGE_PCT = 0.05
SAMPLE_EVERY = 4
LOOKBACK = 250
REQUIRE_TRENDING = False      # Pas de filtre regime strict en backtest (le live a multi-TF)
LEVERAGE = 10                 # Levier 10x LONG et SHORT


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

            # Breakeven a +0.5% (SL -> entry + 0.25% = vrai profit)
            # Trailing a +0.8%
            if direction == 'LONG':
                gain_pct = ((c - entry) / entry) * 100
                highest = max(open_position.get('highest', entry), h)
                open_position['highest'] = highest
                be_sl = entry * (1 + 0.25 / 100)
                if gain_pct >= 0.5 and sl < be_sl:
                    sl = be_sl
                    open_position['sl'] = sl
                if gain_pct >= 0.8:
                    trail_sl = highest * (1 - 0.35 / 100)
                    if trail_sl > sl:
                        sl = trail_sl
                        open_position['sl'] = sl
            else:
                gain_pct = ((entry - c) / entry) * 100
                lowest = min(open_position.get('lowest', entry), l)
                open_position['lowest'] = lowest
                be_sl = entry * (1 - 0.25 / 100)
                if gain_pct >= 0.5 and sl > be_sl:
                    sl = be_sl
                    open_position['sl'] = sl
                if gain_pct >= 0.8:
                    trail_sl = lowest * (1 + 0.35 / 100)
                    if trail_sl < sl:
                        sl = trail_sl
                        open_position['sl'] = sl

            exit_price = None
            exit_reason = None

            if direction == 'LONG':
                if l <= sl:
                    exit_price = sl
                    exit_reason = 'stop_loss' if sl < entry else 'breakeven'
                elif h >= tp:
                    exit_price = tp
                    exit_reason = 'take_profit'
            else:
                if h >= sl:
                    exit_price = sl
                    exit_reason = 'stop_loss' if sl > entry else 'breakeven'
                elif l <= tp:
                    exit_price = tp
                    exit_reason = 'take_profit'

            # Time-based exit: fermer apres 48 bars (48h en 1h)
            bars_held = i - open_position.get('entry_bar', i)
            if exit_price is None and bars_held >= 48:
                exit_price = c
                exit_reason = 'time_exit'

            if exit_price is not None:
                if direction == 'LONG':
                    exit_price *= (1 - slippage_pct / 100)
                    pnl = amount_usdt * LEVERAGE * (exit_price - entry) / entry
                else:
                    exit_price *= (1 + slippage_pct / 100)
                    pnl = amount_usdt * LEVERAGE * (entry - exit_price) / entry

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

        if REQUIRE_TRENDING and regime != 'TRENDING':
            continue
        elif not REQUIRE_TRENDING and regime == 'VOLATILE':
            continue
        adx = indicators.get('adx')
        if adx is not None and adx < MIN_ADX:
            continue

        # MACD + Bollinger + EMA proximity filters
        macd_hist = indicators.get('macd_hist')
        bb_pct = indicators.get('bb_percent')
        current_price = indicators.get('current_price')
        ema21 = indicators.get('ema21')
        if current_price and ema21 and ema21 > 0:
            ema_dist = abs(current_price - ema21) / ema21 * 100
            if ema_dist > 2.5:
                continue  # trop loin de l'EMA

        # SHORT
        if macd_hist is not None and macd_hist < 0 and signal_short_big_drop(df_slice, indicators, VOLUME_RATIO_MIN):
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
                    'entry_time': ts, 'entry_bar': i,
                    'sl': sl, 'tp': tp,
                    'amount_usdt': amount_usdt,
                }
                continue

        # LONG (MACD histogram > 0 = momentum haussier)
        if macd_hist is not None and macd_hist > 0 and signal_long_buy_dip(df_slice, indicators, VOLUME_RATIO_MIN):
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
                    'entry_time': ts, 'entry_bar': i,
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
    pairs = TOP_USDT_PAIRS[:10]
    months = 2
    interval = '1h'
    print("=" * 60)
    print("BACKTEST SNIPER MODE -- {} $ | {} mois | {} paires | {}".format(
        INITIAL_CAPITAL, months, len(pairs), interval))
    print("Score min: {} | ADX min: {} | Volume min: {}x | R:R {:.1f}:1".format(
        MIN_SCORE_TO_OPEN, MIN_ADX, VOLUME_RATIO_MIN, TAKE_PROFIT_PCT / STOP_LOSS_PCT))
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
    print("RESULTATS SNIPER MODE")
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
        profit_factor = abs(sum(t['pnl'] for t in wins)) / abs(sum(t['pnl'] for t in losses)) if losses and sum(t['pnl'] for t in losses) != 0 else 999
        print("  PnL moyen:  {:.4f} $".format(avg_pnl))
        print("  Gain moyen: +{:.4f} $ | Perte moy: {:.4f} $".format(avg_win, avg_loss))
        print("  Profit Factor: {:.2f}".format(profit_factor))
        longs = [t for t in result['trades'] if t['direction'] == 'LONG']
        shorts = [t for t in result['trades'] if t['direction'] == 'SHORT']
        print("  LONG: {} trades | SHORT: {} trades".format(len(longs), len(shorts)))
        be_trades = [t for t in result['trades'] if t.get('exit_reason') == 'breakeven']
        tp_trades = [t for t in result['trades'] if t.get('exit_reason') == 'take_profit']
        sl_trades = [t for t in result['trades'] if t.get('exit_reason') == 'stop_loss']
        print("  Sorties: {} TP | {} SL | {} Breakeven".format(len(tp_trades), len(sl_trades), len(be_trades)))
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
