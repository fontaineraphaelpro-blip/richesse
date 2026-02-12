"""
Module de Paper Trading (Simulation de Portefeuille) — VERSION ULTIME v2.0
Gère :
- Positions LONG et SHORT
- Solde USDT
- SL/TP automatiques
- Journal détaillé des trades
- Statistiques de performance
"""

import json
import os
from datetime import datetime


class PaperTrader:
    def __init__(self, initial_balance=1000):
        self.balance_file  = 'paper_wallet.json'
        self.trades_file   = 'paper_trades.json'

        # Chargement ou création du portefeuille
        if os.path.exists(self.balance_file):
            try:
                with open(self.balance_file, 'r') as f:
                    self.wallet = json.load(f)
                # Migration: s'assurer que les nouveaux champs existent
                if 'positions' not in self.wallet:
                    self.wallet['positions'] = {}
            except (json.JSONDecodeError, Exception):
                self.wallet = {'USDT': initial_balance, 'positions': {}}
        else:
            self.wallet = {'USDT': initial_balance, 'positions': {}}
            self.save_wallet()

    # ─────────────────────────────────────────────────────────
    # PERSISTANCE
    # ─────────────────────────────────────────────────────────

    def save_wallet(self):
        """Sauvegarde l'état du portefeuille."""
        with open(self.balance_file, 'w') as f:
            json.dump(self.wallet, f, indent=4)

    def log_trade(self, trade_data: dict):
        """Enregistre une transaction dans l'historique."""
        history = []
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, 'r') as f:
                    history = json.load(f)
            except Exception:
                history = []

        history.insert(0, trade_data)
        # Conserver max 500 trades
        history = history[:500]

        with open(self.trades_file, 'w') as f:
            json.dump(history, f, indent=4)

    # ─────────────────────────────────────────────────────────
    # LECTURE
    # ─────────────────────────────────────────────────────────

    def get_usdt_balance(self) -> float:
        return float(self.wallet.get('USDT', 0))

    def get_open_positions(self) -> dict:
        return self.wallet.get('positions', {})

    def get_trades_history(self) -> list:
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def get_stats(self) -> dict:
        """Calcule les stats de performance depuis l'historique."""
        history = self.get_trades_history()
        sales   = [t for t in history if 'VENTE' in t.get('type', '')]

        total    = len(sales)
        winners  = sum(1 for t in sales if t.get('pnl', 0) > 0)
        total_pnl = sum(t.get('pnl', 0) for t in sales)
        avg_pnl  = total_pnl / total if total > 0 else 0
        win_rate = (winners / total * 100) if total > 0 else 0

        return {
            'total_trades':   total,
            'winning_trades': winners,
            'losing_trades':  total - winners,
            'total_pnl':      round(total_pnl, 2),
            'avg_pnl':        round(avg_pnl, 2),
            'win_rate':       round(win_rate, 1),
        }

    # ─────────────────────────────────────────────────────────
    # ORDRES
    # ─────────────────────────────────────────────────────────

    def place_buy_order(
        self,
        symbol: str,
        amount_usdt: float,
        current_price: float,
        stop_loss_price: float,
        take_profit_price: float,
    ) -> bool:
        """Exécute un ordre d'ACHAT (position LONG)."""
        if self.wallet['USDT'] < amount_usdt:
            print(f"❌ Fonds insuffisants pour {symbol} "
                  f"(Requis: {amount_usdt:.2f}, Dispo: {self.wallet['USDT']:.2f})")
            return False

        if symbol in self.wallet['positions']:
            print(f"⚠️ Position déjà ouverte sur {symbol}")
            return False

        quantity = amount_usdt / current_price

        self.wallet['USDT'] -= amount_usdt
        self.wallet['positions'][symbol] = {
            'direction':   'LONG',
            'amount_usdt': amount_usdt,
            'quantity':    quantity,
            'entry_price': current_price,
            'entry_time':  datetime.now().strftime('%Y-%m-%d %H:%M'),
            'stop_loss':   stop_loss_price,
            'take_profit': take_profit_price,
        }
        self.save_wallet()

        self.log_trade({
            'type':        'ACHAT',
            'symbol':      symbol,
            'direction':   'LONG',
            'price':       current_price,
            'amount':      amount_usdt,
            'quantity':    quantity,
            'stop_loss':   stop_loss_price,
            'take_profit': take_profit_price,
            'time':        datetime.now().strftime('%d/%m %H:%M'),
            'pnl':         0,
            'pnl_percent': 0,
        })

        sl_dist_pct = abs((current_price - stop_loss_price) / current_price * 100)
        tp_dist_pct = abs((take_profit_price - current_price) / current_price * 100)
        print(f"🛒 ACHAT  {symbol:<12} | ${current_price:.6f} | "
              f"SL:-{sl_dist_pct:.2f}% | TP:+{tp_dist_pct:.2f}% | Investi:${amount_usdt:.2f}")
        return True

    def place_short_order(
        self,
        symbol: str,
        amount_usdt: float,
        current_price: float,
        stop_loss_price: float,
        take_profit_price: float,
    ) -> bool:
        """Exécute un ordre de VENTE À DÉCOUVERT (position SHORT)."""
        if self.wallet['USDT'] < amount_usdt:
            print(f"❌ Fonds insuffisants pour short {symbol}")
            return False

        if symbol in self.wallet['positions']:
            print(f"⚠️ Position déjà ouverte sur {symbol}")
            return False

        quantity = (amount_usdt / current_price) * 15  # Levier 15x appliqué
        self.wallet['USDT'] -= amount_usdt
        self.wallet['positions'][symbol] = {
            'direction':   'SHORT',
            'amount_usdt': amount_usdt,
            'quantity':    quantity,
            'entry_price': current_price,
            'entry_time':  datetime.now().strftime('%Y-%m-%d %H:%M'),
            'stop_loss':   stop_loss_price,
            'take_profit': take_profit_price,
        }
        self.save_wallet()

        self.log_trade({
            'type':        'SHORT',
            'symbol':      symbol,
            'direction':   'SHORT',
            'price':       current_price,
            'amount':      amount_usdt,
            'quantity':    quantity,
            'stop_loss':   stop_loss_price,
            'take_profit': take_profit_price,
            'time':        datetime.now().strftime('%d/%m %H:%M'),
            'pnl':         0,
            'pnl_percent': 0,
        })

        print(f"📉 SHORT  {symbol:<12} | ${current_price:.6f} | "
              f"SL:${stop_loss_price:.6f} | TP:${take_profit_price:.6f} | Marge:${amount_usdt:.2f}")
        return True

    def close_position(self, symbol: str, current_price: float, reason: str = "MANUEL") -> bool:
        """Ferme une position (LONG ou SHORT) et calcule le PnL."""
        if symbol not in self.wallet['positions']:
            return False

        pos          = self.wallet['positions'][symbol]
        direction    = pos.get('direction', 'LONG')
        quantity     = pos['quantity']
        entry_amount = pos['amount_usdt']
        entry_price  = pos['entry_price']

        # Calcul PnL selon direction
        if direction == 'LONG':
            exit_value  = quantity * current_price
            pnl_value   = exit_value - entry_amount
            pnl_percent = ((current_price - entry_price) / entry_price) * 100
            returned    = exit_value
        else:  # SHORT
            # PnL short = (entry - exit) * qty (on gagne si le prix baisse)
            pnl_value   = (entry_price - current_price) * quantity
            pnl_percent = ((entry_price - current_price) / entry_price) * 100
            returned    = entry_amount + pnl_value  # marge + gain/perte

        # Mise à jour du solde (jamais négatif)
        self.wallet['USDT'] += max(returned, 0)
        del self.wallet['positions'][symbol]
        self.save_wallet()

        status = "✅ GAIN" if pnl_value > 0 else "❌ PERTE"
        print(f"💰 VENTE {symbol:<12} ({reason}) | {status}: "
              f"${pnl_value:+.2f} ({pnl_percent:+.2f}%)")

        self.log_trade({
            'type':        f'VENTE ({reason})',
            'symbol':      symbol,
            'direction':   direction,
            'price':       current_price,
            'amount':      round(abs(returned), 2),
            'quantity':    quantity,
            'entry_price': entry_price,
            'time':        datetime.now().strftime('%d/%m %H:%M'),
            'pnl':         round(pnl_value, 2),
            'pnl_percent': round(pnl_percent, 2),
            'reason':      reason,
        })
        return True

    # ─────────────────────────────────────────────────────────
    # SURVEILLANCE AUTOMATIQUE
    # ─────────────────────────────────────────────────────────

    def check_positions(self, real_prices: dict):
        """
        Vérifie toutes les positions ouvertes.
        Déclenche SL ou TP si le prix les atteint.
        """
        positions_to_close = []

        for symbol, pos in self.wallet['positions'].items():
            current_price = real_prices.get(symbol)
            if not current_price:
                continue

            direction  = pos.get('direction', 'LONG')
            stop_loss  = pos['stop_loss']
            take_profit = pos['take_profit']

            if direction == 'LONG':
                if current_price <= stop_loss:
                    positions_to_close.append((symbol, current_price, "STOP LOSS 🛑"))
                elif current_price >= take_profit:
                    positions_to_close.append((symbol, current_price, "TAKE PROFIT 🎯"))
            else:  # SHORT
                # Pour un short : SL est au-dessus, TP est en dessous
                if current_price >= stop_loss:
                    positions_to_close.append((symbol, current_price, "STOP LOSS 🛑"))
                elif current_price <= take_profit:
                    positions_to_close.append((symbol, current_price, "TAKE PROFIT 🎯"))

        for symbol, price, reason in positions_to_close:
            self.close_position(symbol, price, reason)

    def reset_wallet(self, initial_balance: float = 1000.0):
        """Remet le portefeuille à zéro (utile pour les tests)."""
        self.wallet = {'USDT': initial_balance, 'positions': {}}
        self.save_wallet()
        print(f"🔄 Portefeuille réinitialisé à ${initial_balance:.2f}")
