"""
Backtester basique pour évaluer les signaux de `scalping_signals` sur des données historiques.

Fonctionnalités:
- Parcourt les bougies depuis l'indice minimum requis pour les indicateurs
- Génère signaux, applique filtres, ouvre positions simulées et détecte SL/TP
- Retourne un résumé simple: final balance, trades, winrate
"""
from typing import List, Dict, Optional
import pandas as pd
import math

from indicators import calculate_indicators
import scalping_signals
import signal_validation
import scanner_filters


class Backtester:
    def __init__(self, df: pd.DataFrame, initial_balance: float = 1000.0):
        self.df = df.copy()
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.trades: List[Dict] = []

    def simulate(self, risk_per_trade: float = 0.01, start_index: Optional[int] = None, max_steps: Optional[int] = None) -> Dict:
        """
        Simule en utilisant `scalping_signals.calculate_entry_exit_signals`.
        Commence à l'index `start_index` (par défaut 200 pour indicateurs complets).
        """
        if self.df is None or self.df.empty:
            return {'error': 'Empty dataframe'}

        n = len(self.df)
        start = start_index if start_index is not None else 200
        if start >= n:
            return {'error': 'Start index too large for dataframe'}

        end = n if max_steps is None else min(n, start + max_steps)

        open_position = None

        for i in range(start, end):
            window = self.df.iloc[:i+1]

            # 1) Vérifier filtres (liquidity / activity)
            if not scanner_filters.is_liquid(window, min_avg_volume=10):
                continue

            indicators = calculate_indicators(window)
            if not indicators:
                continue

            # calcul support/resistance simple
            support = scalping_signals.find_resistance(window, lookback=30)
            resistance = None

            sig = scalping_signals.calculate_entry_exit_signals(indicators, support, resistance)

            entry = sig.get('entry_signal')
            entry_price = sig.get('entry_price')
            stop_loss = sig.get('stop_loss')
            tp1 = sig.get('take_profit_1')

            # Validation de cohérence
            val = signal_validation.validate_signal_coherence(indicators, entry)
            if not val.get('is_valid'):
                continue

            # Si pas de position ouverte et signal valide -> ouvrir
            if open_position is None and entry in ['LONG', 'SHORT'] and entry_price and stop_loss and tp1:
                sizing = signal_validation.calculate_position_size(self.balance, entry_price, stop_loss, risk_per_trade)
                if sizing['position_usdt'] <= 0 or len(sizing['notes']) > 0 and 'too small' in ' '.join(sizing['notes']).lower():
                    continue

                # Simuler ouverture : on prendra la quantité basée sur sizing
                qty = sizing['quantity']
                open_position = {
                    'side': entry,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': tp1,
                    'quantity': qty,
                    'entry_index': i
                }

                # On réserve le montant investi
                self.balance -= sizing['position_usdt']

            # Si position ouverte, on vérifie si SL/TP touchés sur cette bougie
            if open_position is not None:
                row = self.df.iloc[i]
                high = row['high']
                low = row['low']
                exit_price = None
                reason = None

                if open_position['side'] == 'LONG':
                    # TP
                    if high >= open_position['take_profit']:
                        exit_price = open_position['take_profit']
                        reason = 'TP'
                    # SL
                    elif low <= open_position['stop_loss']:
                        exit_price = open_position['stop_loss']
                        reason = 'SL'
                else:  # SHORT
                    if low <= open_position['take_profit']:
                        exit_price = open_position['take_profit']
                        reason = 'TP'
                    elif high >= open_position['stop_loss']:
                        exit_price = open_position['stop_loss']
                        reason = 'SL'

                if exit_price is not None:
                    # Calcul du PnL
                    qty = open_position['quantity']
                    entry_px = open_position['entry_price']
                    if open_position['side'] == 'LONG':
                        exit_value = qty * exit_price
                        entry_value = qty * entry_px
                        pnl = exit_value - entry_value
                    else:
                        # short: gain si price baisse
                        entry_value = qty * entry_px
                        exit_value = qty * exit_price
                        pnl = entry_value - exit_value

                    # Remboursement du capital initial + gain
                    invested = qty * entry_px
                    self.balance += invested + pnl

                    self.trades.append({
                        'entry_index': open_position['entry_index'],
                        'exit_index': i,
                        'side': open_position['side'],
                        'entry': entry_px,
                        'exit': exit_price,
                        'pnl': round(pnl, 6)
                    })

                    open_position = None

        # Si position toujours ouverte à la fin, on clôture au dernier close
        if open_position is not None:
            last_close = self.df['close'].iloc[end-1]
            qty = open_position['quantity']
            entry_px = open_position['entry_price']
            if open_position['side'] == 'LONG':
                exit_value = qty * last_close
                entry_value = qty * entry_px
                pnl = exit_value - entry_value
            else:
                entry_value = qty * entry_px
                exit_value = qty * last_close
                pnl = entry_value - exit_value

            invested = qty * entry_px
            self.balance += invested + pnl
            self.trades.append({
                'entry_index': open_position['entry_index'],
                'exit_index': end-1,
                'side': open_position['side'],
                'entry': entry_px,
                'exit': last_close,
                'pnl': round(pnl, 6)
            })
            open_position = None

        # Résumé
        wins = len([t for t in self.trades if t['pnl'] > 0])
        losses = len([t for t in self.trades if t['pnl'] <= 0])
        total = len(self.trades)

        return {
            'initial_balance': self.initial_balance,
            'final_balance': round(self.balance, 6),
            'trades_count': total,
            'wins': wins,
            'losses': losses,
            'win_rate': round((wins / total * 100) if total > 0 else 0, 2),
            'trades': self.trades
        }


def quick_backtest_from_df(df: pd.DataFrame, initial_balance: float = 1000.0, risk_per_trade: float = 0.01) -> Dict:
    bt = Backtester(df, initial_balance)
    return bt.simulate(risk_per_trade=risk_per_trade)
