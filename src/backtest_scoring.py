# -*- coding: utf-8 -*-
"""
Backtest scoring et seuils sur données historiques.
Simule des trades bar-by-bar pour optimiser: score min, R:R, volume, spread.
Usage: python -m src.backtest_scoring
       BACKTEST_SYMBOLS=20 BACKTEST_BARS=1000 python -m src.backtest_scoring
"""
import os
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

if __name__ == '__main__':
    _src = os.path.dirname(os.path.abspath(__file__))
    if _src not in sys.path:
        sys.path.insert(0, _src)

from data_fetcher import get_binance_klines, get_top_pairs
from indicators import calculate_indicators
from short_crash_strategy import compute_sl_tp_from_chart
from adaptive_scorer import score_adaptive


@dataclass
class TradeResult:
    symbol: str
    direction: str
    entry_bar: int
    exit_bar: int
    entry_price: float
    exit_price: float
    pnl_pct: float
    hit_tp: bool
    score: float
    rr: float


def simulate_trade(
    df,
    entry_bar: int,
    entry_price: float,
    sl: float,
    tp: float,
    direction: str,
) -> Optional[Tuple[int, float, bool]]:
    """
    Simule le trade: parcourt les barres suivantes jusqu'à SL ou TP.
    Returns: (exit_bar, exit_price, hit_tp) ou None si jamais atteint.
    """
    for i in range(entry_bar + 1, len(df)):
        row = df.iloc[i]
        high, low = float(row['high']), float(row['low'])
        close = float(row['close'])
        if direction == 'LONG':
            if low <= sl:
                return (i, sl, False)
            if high >= tp:
                return (i, tp, True)
        else:  # SHORT
            if high >= sl:
                return (i, sl, False)
            if low <= tp:
                return (i, tp, True)
    return None  # Position encore ouverte à la fin des données


def run_backtest(
    symbols: List[str],
    limit: int = 500,
    min_score: int = 65,
    min_rr: float = 1.5,
    min_volume_ratio: float = 1.2,
    max_spread_pct: float = 0.10,
    max_trades_per_symbol: int = 5,
) -> Dict:
    """Exécute le backtest et retourne les statistiques."""
    all_trades: List[TradeResult] = []
    start_bar = 100  # Besoin d'assez de bougies pour les indicateurs

    for symbol in symbols:
        df = get_binance_klines(symbol, '15m', limit)
        if df is None or len(df) < start_bar + 50:
            continue

        trades_this_symbol = 0
        for i in range(start_bar, len(df) - 5):
            if trades_this_symbol >= max_trades_per_symbol:
                break
            df_slice = df.iloc[: i + 1].copy()
            try:
                ind = calculate_indicators(df_slice)
            except Exception:
                continue
            if not ind:
                continue

            vol_r = ind.get('volume_ratio')
            if vol_r is None or vol_r < min_volume_ratio:
                continue

            close = float(df_slice['close'].iloc[-1])
            spread_pct = (float(df_slice['high'].iloc[-1]) - float(df_slice['low'].iloc[-1])) / close * 100
            if spread_pct > max_spread_pct:
                continue

            atr_pct = ind.get('atr_percent') or 2.0
            momentum_15m = ind.get('price_momentum') or 'NEUTRAL'
            momentum_1h = momentum_15m  # Simplification: même que 15m en backtest 15m seul

            score_long, score_short, regime = score_adaptive(
                ind, momentum_15m, momentum_1h, None, spread_pct, atr_pct
            )

            for direction, score in [('LONG', score_long), ('SHORT', score_short)]:
                if score < min_score:
                    continue
                sl, tp, sl_pct = compute_sl_tp_from_chart(close, ind, direction)
                if sl is None:
                    continue
                if direction == 'LONG':
                    rr = (tp - close) / (close - sl) if sl < close else 0
                else:
                    rr = (close - tp) / (sl - close) if sl > close else 0
                if rr < min_rr:
                    continue

                result = simulate_trade(df, i, close, sl, tp, direction)
                if result is None:
                    continue
                exit_bar, exit_price, hit_tp = result
                if direction == 'LONG':
                    pnl_pct = (exit_price - close) / close * 100
                else:
                    pnl_pct = (close - exit_price) / close * 100

                all_trades.append(TradeResult(
                    symbol=symbol,
                    direction=direction,
                    entry_bar=i,
                    exit_bar=exit_bar,
                    entry_price=close,
                    exit_price=exit_price,
                    pnl_pct=pnl_pct,
                    hit_tp=hit_tp,
                    score=score,
                    rr=rr,
                ))
                trades_this_symbol += 1
                break  # Un seul trade par bar

    # Statistiques
    if not all_trades:
        return {
            'total_trades': 0,
            'win_rate': 0,
            'avg_pnl_pct': 0,
            'total_pnl_pct': 0,
            'params': {'min_score': min_score, 'min_rr': min_rr, 'min_volume_ratio': min_volume_ratio, 'max_spread_pct': max_spread_pct},
        }

    wins = sum(1 for t in all_trades if t.pnl_pct > 0)
    total_pnl = sum(t.pnl_pct for t in all_trades)
    avg_pnl = total_pnl / len(all_trades)

    return {
        'total_trades': len(all_trades),
        'win_rate': wins / len(all_trades) * 100,
        'avg_pnl_pct': avg_pnl,
        'total_pnl_pct': total_pnl,
        'avg_win_pct': sum(t.pnl_pct for t in all_trades if t.pnl_pct > 0) / wins if wins else 0,
        'avg_loss_pct': sum(t.pnl_pct for t in all_trades if t.pnl_pct < 0) / (len(all_trades) - wins) if (len(all_trades) - wins) > 0 else 0,
        'params': {'min_score': min_score, 'min_rr': min_rr, 'min_volume_ratio': min_volume_ratio, 'max_spread_pct': max_spread_pct},
        'trades': all_trades,
    }


def run_optimization(
    symbols_count: int = 8,
    limit: int = 300,
) -> None:
    """Teste plusieurs combinaisons de paramètres et affiche les meilleures."""
    symbols = list(get_top_pairs(limit=30))[:symbols_count]  # Liste statique = pas d'appel API
    print("Backtest optimisation scoring/seuils sur {} paires, {} bougies".format(len(symbols), limit))
    print("(BACKTEST_SYMBOLS=8 BACKTEST_BARS=300 par defaut, peut prendre 2-5 min)")
    print("=" * 70)

    param_grid = [
        {'min_score': 60, 'min_rr': 1.3, 'min_volume_ratio': 1.0, 'max_spread_pct': 0.12},
        {'min_score': 65, 'min_rr': 1.5, 'min_volume_ratio': 1.2, 'max_spread_pct': 0.10},
        {'min_score': 68, 'min_rr': 1.5, 'min_volume_ratio': 1.2, 'max_spread_pct': 0.10},
        {'min_score': 70, 'min_rr': 1.6, 'min_volume_ratio': 1.3, 'max_spread_pct': 0.09},
        {'min_score': 65, 'min_rr': 1.8, 'min_volume_ratio': 1.2, 'max_spread_pct': 0.10},
    ]

    results = []
    for params in param_grid:
        r = run_backtest(symbols, limit=limit, **params)
        if r['total_trades'] >= 1:
            score_metric = r['win_rate'] * 0.4 + r['avg_pnl_pct'] * 10 + r['total_trades'] * 0.1
            results.append((score_metric, r, params))

    results.sort(key=lambda x: x[0], reverse=True)

    if not results:
        print("\nAucun trade généré. Essayer plus de paires (BACKTEST_SYMBOLS=20) ou plus de bougies (BACKTEST_BARS=500).")
        return results

    print("\nTop 5 combinaisons (score = WR*0.4 + avg_pnl*10 + nb_trades*0.1):")
    print("-" * 70)
    for i, (_, r, params) in enumerate(results[:5], 1):
        print("{}. Score min={} R:R={} vol>={} spread<={}%".format(
            i, params['min_score'], params['min_rr'], params['min_volume_ratio'], params['max_spread_pct']))
        print("   Trades: {} | WR: {:.1f}% | Avg PnL: {:.2f}% | Total: {:.2f}%".format(
            r['total_trades'], r['win_rate'], r['avg_pnl_pct'], r['total_pnl_pct']))
        if r['total_trades'] > 0:
            print("   Avg win: {:.2f}% | Avg loss: {:.2f}%".format(r.get('avg_win_pct', 0), r.get('avg_loss_pct', 0)))
        print()
    return results


if __name__ == '__main__':
    n_symbols = int(os.environ.get('BACKTEST_SYMBOLS', '15'))
    n_bars = int(os.environ.get('BACKTEST_BARS', '500'))
    run_optimization(symbols_count=n_symbols, limit=n_bars)
