# -*- coding: utf-8 -*-
"""
Backtest du day trader sur données historiques Binance.
Utilise la même logique que le scanner (indicateurs, signaux LONG/SHORT, SL/TP).
Affiche: win rate, rendement total %, drawdown max %, nombre de trades.
"""

import time
from datetime import datetime
from typing import Optional, List, Dict, Any

import pandas as pd

from data_fetcher import get_binance_klines_range, TOP_USDT_PAIRS
from indicators import calculate_indicators
from short_crash_strategy import (
    signal_long_buy_dip,
    signal_short_big_drop,
    score_long_opportunity,
    score_short_opportunity,
)

# Paramètres alignés sur main.py (paper trading)
VOLUME_RATIO_MIN = 1.0
STOP_LOSS_PCT = 1.0
TAKE_PROFIT_PCT = 2.0
LONG_STOP_LOSS_PCT = 1.0
LONG_TAKE_PROFIT_PCT = 2.0
MIN_SCORE_TO_OPEN = 68
INITIAL_CAPITAL = 10_000.0
POSITION_PCT = 0.30
SLIPPAGE_PCT = 0.05


def _run_backtest_one_symbol(
    symbol: str,
    df: pd.DataFrame,
    initial_capital: float,
    position_pct: float,
    slippage_pct: float,
) -> tuple:
    """
    Simule les trades sur une paire. Une seule position à la fois.
    Retourne (liste des trades fermés, capital final).
    """
    equity = initial_capital
    open_position = None  # { 'direction', 'entry_price', 'entry_idx', 'sl', 'tp', 'amount_usdt' }
    trades = []
    n = len(df)

    for i in range(200, n):
        row = df.iloc[i]
        ts = row['timestamp']
        o, h, l, c = row['open'], row['high'], row['low'], row['close']

        # —— Gestion sortie position (même bar) ——
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
                    exit_reason = 'stop_loss'
                elif h >= tp:
                    exit_price = tp
                    exit_reason = 'take_profit'
            else:  # SHORT
                if h >= sl:
                    exit_price = sl
                    exit_reason = 'stop_loss'
                elif l <= tp:
                    exit_price = tp
                    exit_reason = 'take_profit'

            if exit_price is not None:
                # Slippage sortie
                if direction == 'LONG':
                    exit_price = exit_price * (1 - slippage_pct / 100)
                else:
                    exit_price = exit_price * (1 + slippage_pct / 100)

                if direction == 'LONG':
                    pnl = amount_usdt * (exit_price - entry) / entry
                else:
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
                    'pnl': round(pnl, 2),
                    'exit_reason': exit_reason,
                })
                open_position = None
                continue

        # —— Recherche nouvelle entrée (une seule par bar si signal) ——
        df_slice = df.iloc[: i + 1]
        indicators = calculate_indicators(df_slice)
        if not indicators or indicators.get('volume_ratio') is None:
            continue

        spread_pct = (df_slice['high'].iloc[-1] - df_slice['low'].iloc[-1]) / df_slice['close'].iloc[-1] * 100
        atr_pct = indicators.get('atr_percent') or 0
        momentum_15m = indicators.get('price_momentum') or 'NEUTRAL'

        # SHORT
        if indicators.get('price_momentum') == 'BEARISH' and signal_short_big_drop(df_slice, indicators, VOLUME_RATIO_MIN):
            details = score_short_opportunity(
                indicators, spread_pct, atr_pct,
                momentum_15m=momentum_15m, momentum_1h=momentum_15m,
                stop_loss_pct=STOP_LOSS_PCT, take_profit_pct=TAKE_PROFIT_PCT,
            )
            if details['score'] >= MIN_SCORE_TO_OPEN:
                entry_price = c * (1 - slippage_pct / 100)
                sl = entry_price * (1 + STOP_LOSS_PCT / 100)
                tp = entry_price * (1 - TAKE_PROFIT_PCT / 100)
                amount_usdt = equity * position_pct / 100
                open_position = {
                    'direction': 'SHORT',
                    'entry_price': entry_price,
                    'entry_time': ts,
                    'sl': sl,
                    'tp': tp,
                    'amount_usdt': amount_usdt,
                }
                continue

        # LONG
        if indicators.get('price_momentum') == 'BULLISH' and signal_long_buy_dip(df_slice, indicators, VOLUME_RATIO_MIN):
            details = score_long_opportunity(
                indicators, spread_pct, atr_pct,
                momentum_15m=momentum_15m, momentum_1h=momentum_15m,
                stop_loss_pct=LONG_STOP_LOSS_PCT, take_profit_pct=LONG_TAKE_PROFIT_PCT,
            )
            if details['score'] >= MIN_SCORE_TO_OPEN:
                entry_price = c * (1 + slippage_pct / 100)
                sl = entry_price * (1 - LONG_STOP_LOSS_PCT / 100)
                tp = entry_price * (1 + LONG_TAKE_PROFIT_PCT / 100)
                amount_usdt = equity * position_pct / 100
                open_position = {
                    'direction': 'LONG',
                    'entry_price': entry_price,
                    'entry_time': ts,
                    'sl': sl,
                    'tp': tp,
                    'amount_usdt': amount_usdt,
                }

    return trades, equity


def run_backtest(
    symbols: Optional[List[str]] = None,
    months: int = 6,
    interval: str = '15m',
    initial_capital: float = INITIAL_CAPITAL,
    position_pct: float = POSITION_PCT,
    slippage_pct: float = SLIPPAGE_PCT,
) -> Dict[str, Any]:
    """
    Lance le backtest sur les symboles donnés (ou top 5 par défaut).

    Returns:
        dict avec trades, total_trades, win_rate, total_return_pct, max_drawdown_pct, final_equity
    """
    if symbols is None:
        symbols = TOP_USDT_PAIRS[:5]

    end_ms = int(time.time() * 1000)
    start_ms = end_ms - (months * 31 * 24 * 60 * 60 * 1000)

    all_trades = []

    for sym in symbols:
        print(f"  Fetching {sym}...", end=" ", flush=True)
        df = get_binance_klines_range(sym, interval=interval, start_time_ms=start_ms, end_time_ms=end_ms)
        if df is None or len(df) < 250:
            print("skip (no data)")
            continue
        print(f"{len(df)} bars", flush=True)
        trades, _ = _run_backtest_one_symbol(sym, df, initial_capital, position_pct, slippage_pct)
        all_trades.extend(trades)
        time.sleep(0.2)

    # Trier par date de sortie pour une courbe d'équité cohérente
    all_trades.sort(key=lambda t: t['exit_time'])

    # Recalculer équité finale et drawdown sur la séquence globale
    capital = initial_capital
    peak = initial_capital
    max_dd = 0
    for t in all_trades:
        capital += t['pnl']
        peak = max(peak, capital)
        dd = (peak - capital) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)

    total_trades = len(all_trades)
    if total_trades == 0:
        return {
            'trades': [],
            'total_trades': 0,
            'win_rate': 0.0,
            'total_return_pct': 0.0,
            'max_drawdown_pct': 0.0,
            'final_equity': initial_capital,
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
    }


def main():
    print("Backtest Day Trader — données Binance 15m")
    print("Symboles: top 5 | Période: 6 mois | Capital initial: 10 000 $")
    print("-" * 50)
    result = run_backtest(months=6, position_pct=30, slippage_pct=0.05)
    print(f"  Trades:     {result['total_trades']}")
    print(f"  Win rate:   {result['win_rate']}%")
    print(f"  Rendement:  {result['total_return_pct']}%")
    print(f"  Drawdown:   {result['max_drawdown_pct']}%")
    print(f"  Équité fin: {result['final_equity']} $")
    return result


if __name__ == "__main__":
    main()
