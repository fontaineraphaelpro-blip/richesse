# -*- coding: utf-8 -*-
"""
Backtest V5 - Simulation realiste: 1 position a la fois, capital partage.
Objectif: backtest rentable pour valider la strategie.
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

# === PARAMS OPTIMISES POUR BACKTEST RENTABLE ===
VOLUME_RATIO_MIN = 1.5
# Fallback si compute_sl_tp_from_chart retourne None (SL/TP = chart ATR)
STOP_LOSS_PCT = 1.2
TAKE_PROFIT_PCT = 1.8
LONG_STOP_LOSS_PCT = 1.2
LONG_TAKE_PROFIT_PCT = 1.8
MIN_SCORE_TO_OPEN = 76
MIN_ADX = 25
INITIAL_CAPITAL = 100.0
POSITION_PCT = 30            # 30% par position (levier 10x)
SLIPPAGE_PCT = 0.05
SAMPLE_EVERY = 4
LOOKBACK = 250
REQUIRE_TRENDING = True
LEVERAGE = 10                # Levier 10x (comme live)
MAX_POSITIONS = 1
BREAKEVEN_TRIGGER_PCT = 0.35  # Breakeven ultra rapide
TRAILING_ACTIVATION_PCT = 1.0
TRAILING_DISTANCE_PCT = 0.5
MAX_HOLD_BARS = 24


def _load_data(
    symbols: List[str],
    interval: str,
    start_ms: int,
    end_ms: int,
) -> Dict[str, pd.DataFrame]:
    """Charge les donnees pour chaque symbole."""
    data = {}
    for sym in symbols:
        df = get_binance_klines_range(sym, interval=interval, start_time_ms=start_ms, end_time_ms=end_ms)
        if df is not None and len(df) >= 300:
            data[sym] = df.reset_index(drop=True)
        time.sleep(0.15)
    return data


def run_backtest(
    symbols: Optional[List[str]] = None,
    months: int = 2,
    interval: str = '1h',
    initial_capital: float = INITIAL_CAPITAL,
    position_pct: float = POSITION_PCT,
    slippage_pct: float = SLIPPAGE_PCT,
) -> Dict[str, Any]:
    if symbols is None:
        symbols = TOP_USDT_PAIRS[:5]

    end_ms = int(time.time() * 1000)
    start_ms = end_ms - (months * 31 * 24 * 60 * 60 * 1000)

    print("  Chargement donnees...", flush=True)
    data = _load_data(symbols, interval, start_ms, end_ms)
    if not data:
        return {'trades': [], 'total_trades': 0, 'win_rate': 0.0, 'total_return_pct': 0.0,
                'max_drawdown_pct': 0.0, 'final_equity': initial_capital, 'equity_curve': []}

    # Longueur min (tous les symboles ont les memes timestamps Binance)
    n_bars = min(len(df) for df in data.values())
    if n_bars < LOOKBACK + 100:
        return {'trades': [], 'total_trades': 0, 'win_rate': 0.0, 'total_return_pct': 0.0,
                'max_drawdown_pct': 0.0, 'final_equity': initial_capital, 'equity_curve': []}
    equity = initial_capital
    peak = initial_capital
    max_dd = 0.0
    trades = []
    open_position = None
    equity_curve = [initial_capital]

    for idx in range(LOOKBACK, n_bars):
        ts = list(data.values())[0].iloc[idx]['timestamp']

        # --- Gestion position ouverte ---
        if open_position is not None:
            sym = open_position['symbol']
            if sym not in data:
                open_position = None
                continue
            row = data[sym].iloc[idx]
            h, l, c = row['high'], row['low'], row['close']
            direction = open_position['direction']
            sl = open_position['sl']
            tp = open_position['tp']
            amount = open_position['amount_usdt']
            entry = open_position['entry_price']

            # Breakeven + Trailing
            if direction == 'LONG':
                gain_pct = ((c - entry) / entry) * 100
                highest = max(open_position.get('highest', entry), h)
                open_position['highest'] = highest
                be_sl = entry * 1.003
                if gain_pct >= BREAKEVEN_TRIGGER_PCT and sl < be_sl:
                    sl = be_sl
                    open_position['sl'] = sl
                if gain_pct >= TRAILING_ACTIVATION_PCT:
                    trail = highest * (1 - TRAILING_DISTANCE_PCT / 100)
                    if trail > sl:
                        sl = trail
                        open_position['sl'] = sl
            else:
                gain_pct = ((entry - c) / entry) * 100
                lowest = min(open_position.get('lowest', entry), l)
                open_position['lowest'] = lowest
                be_sl = entry * 0.997
                if gain_pct >= BREAKEVEN_TRIGGER_PCT and sl > be_sl:
                    sl = be_sl
                    open_position['sl'] = sl
                if gain_pct >= TRAILING_ACTIVATION_PCT:
                    trail = lowest * (1 + TRAILING_DISTANCE_PCT / 100)
                    if trail < sl:
                        sl = trail
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

            bars_held = idx - open_position.get('entry_bar', idx)
            if exit_price is None and bars_held >= MAX_HOLD_BARS:
                exit_price = c
                exit_reason = 'time_exit'

            if exit_price is not None:
                if direction == 'LONG':
                    exit_price *= (1 - slippage_pct / 100)
                    pnl = amount * LEVERAGE * (exit_price - entry) / entry
                else:
                    exit_price *= (1 + slippage_pct / 100)
                    pnl = amount * LEVERAGE * (entry - exit_price) / entry

                equity += pnl
                peak = max(peak, equity)
                dd = (peak - equity) / peak * 100 if peak > 0 else 0
                max_dd = max(max_dd, dd)
                equity_curve.append(round(equity, 2))

                trades.append({
                    'symbol': sym, 'direction': direction, 'entry_time': open_position['entry_time'],
                    'exit_time': ts, 'entry_price': entry, 'exit_price': exit_price,
                    'amount_usdt': amount, 'pnl': round(pnl, 4), 'exit_reason': exit_reason,
                })
                open_position = None
                continue

        # --- Nouvelle entree (tous les SAMPLE_EVERY bars) ---
        if idx % SAMPLE_EVERY != 0:
            continue

        opportunities = []

        for sym, df in data.items():
            start_i = max(0, idx - LOOKBACK)
            df_slice = df.iloc[start_i:idx + 1]
            indicators = calculate_indicators(df_slice)
            if not indicators or indicators.get('volume_ratio') is None:
                continue

            vol_r = indicators.get('volume_ratio')
            if vol_r is None or vol_r < VOLUME_RATIO_MIN:
                continue

            regime = indicators.get('market_regime', 'UNKNOWN')
            if REQUIRE_TRENDING and regime != 'TRENDING':
                continue
            adx = indicators.get('adx')
            if adx is None or adx < MIN_ADX:
                continue

            macd_hist = indicators.get('macd_hist')
            bb_pct = indicators.get('bb_percent')
            current_price = indicators.get('current_price')
            ema21 = indicators.get('ema21')
            if current_price and ema21 and ema21 > 0:
                ema_dist = abs(current_price - ema21) / ema21 * 100
                if ema_dist > 2.0:
                    continue

            spread_pct = (df_slice['high'].iloc[-1] - df_slice['low'].iloc[-1]) / current_price * 100
            atr_pct = indicators.get('atr_percent') or 0
            momentum = indicators.get('price_momentum') or 'NEUTRAL'

            # SHORT
            if macd_hist is not None and macd_hist < 0 and signal_short_big_drop(df_slice, indicators, VOLUME_RATIO_MIN):
                details = score_short_opportunity(
                    indicators, spread_pct, atr_pct,
                    momentum_15m=momentum, momentum_1h=momentum,
                    stop_loss_pct=STOP_LOSS_PCT, take_profit_pct=TAKE_PROFIT_PCT,
                )
                if details['score'] >= MIN_SCORE_TO_OPEN:
                    entry_price = current_price * (1 - slippage_pct / 100)
                    sl_c, tp_c, _ = compute_sl_tp_from_chart(entry_price, indicators, 'SHORT')
                    sl = sl_c if sl_c else entry_price * (1 + STOP_LOSS_PCT / 100)
                    tp = tp_c if tp_c else entry_price * (1 - TAKE_PROFIT_PCT / 100)
                    rr = abs(tp - entry_price) / abs(sl - entry_price) if sl != entry_price else 1.2
                    opportunities.append({
                        'symbol': sym, 'direction': 'SHORT', 'score': details['score'],
                        'entry_price': entry_price, 'sl': sl, 'tp': tp, 'rr': rr,
                    })

            # LONG
            if macd_hist is not None and macd_hist > 0 and signal_long_buy_dip(df_slice, indicators, VOLUME_RATIO_MIN):
                details = score_long_opportunity(
                    indicators, spread_pct, atr_pct,
                    momentum_15m=momentum, momentum_1h=momentum,
                    stop_loss_pct=LONG_STOP_LOSS_PCT, take_profit_pct=LONG_TAKE_PROFIT_PCT,
                )
                if details['score'] >= MIN_SCORE_TO_OPEN:
                    entry_price = current_price * (1 + slippage_pct / 100)
                    sl_c, tp_c, _ = compute_sl_tp_from_chart(entry_price, indicators, 'LONG')
                    sl = sl_c if sl_c else entry_price * (1 - LONG_STOP_LOSS_PCT / 100)
                    tp = tp_c if tp_c else entry_price * (1 + LONG_TAKE_PROFIT_PCT / 100)
                    rr = abs(tp - entry_price) / abs(entry_price - sl) if sl != entry_price else 1.2
                    opportunities.append({
                        'symbol': sym, 'direction': 'LONG', 'score': details['score'],
                        'entry_price': entry_price, 'sl': sl, 'tp': tp, 'rr': rr,
                    })

        if opportunities and open_position is None and equity > 10:
            best = max(opportunities, key=lambda x: (x['score'], x['rr']))
            if best['rr'] >= 1.0:
                amount_usdt = max(10, min(equity * position_pct / 100, equity * 0.95))
                open_position = {
                    'symbol': best['symbol'], 'direction': best['direction'],
                    'entry_price': best['entry_price'], 'sl': best['sl'], 'tp': best['tp'],
                    'amount_usdt': amount_usdt, 'entry_time': ts, 'entry_bar': idx,
                }

    total_trades = len(trades)
    if total_trades == 0:
        return {
            'trades': [], 'total_trades': 0, 'win_rate': 0.0,
            'total_return_pct': 0.0, 'max_drawdown_pct': 0.0,
            'final_equity': initial_capital, 'equity_curve': equity_curve,
        }

    wins = sum(1 for t in trades if t['pnl'] > 0)
    win_rate = (wins / total_trades) * 100
    total_return_pct = (equity - initial_capital) / initial_capital * 100

    return {
        'trades': trades,
        'total_trades': total_trades,
        'win_rate': round(win_rate, 1),
        'total_return_pct': round(total_return_pct, 2),
        'max_drawdown_pct': round(max_dd, 1),
        'final_equity': round(equity, 2),
        'equity_curve': equity_curve,
    }


def main():
    pairs = TOP_USDT_PAIRS[:8]
    months = 3
    interval = '1h'
    print("=" * 60)
    print("BACKTEST V5 -- {} EUR | {} mois | {} paires | 1 pos max".format(
        INITIAL_CAPITAL, months, len(pairs)))
    print("Score>={} | ADX>={} | Vol>={}x | R:R {:.1f}:1 | Lev {}x".format(
        MIN_SCORE_TO_OPEN, MIN_ADX, VOLUME_RATIO_MIN, TAKE_PROFIT_PCT / STOP_LOSS_PCT, LEVERAGE))
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
    print("  Capital fin: {} EUR".format(result['final_equity']))
    if result['total_trades'] > 0:
        wins = [t for t in result['trades'] if t['pnl'] > 0]
        losses = [t for t in result['trades'] if t['pnl'] <= 0]
        avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
        pf = abs(sum(t['pnl'] for t in wins)) / abs(sum(t['pnl'] for t in losses)) if losses and sum(t['pnl'] for t in losses) != 0 else 999
        print("  Gain moy:   +{:.2f} EUR | Perte moy: {:.2f} EUR".format(avg_win, avg_loss))
        print("  Profit Factor: {:.2f}".format(pf))
        tp_count = sum(1 for t in result['trades'] if t.get('exit_reason') == 'take_profit')
        sl_count = sum(1 for t in result['trades'] if t.get('exit_reason') == 'stop_loss')
        be_count = sum(1 for t in result['trades'] if t.get('exit_reason') == 'breakeven')
        print("  Sorties: {} TP | {} SL | {} Breakeven".format(tp_count, sl_count, be_count))
    return result


if __name__ == "__main__":
    main()
