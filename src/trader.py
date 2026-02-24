"""
Module de Paper Trading (Simulation de Portefeuille) — VERSION ULTIME v2.0
Gère :
- Positions LONG et SHORT
- Solde USDT
- SL/TP automatiques
- Journal détaillé des trades
- Statistiques de performance
+ Protection contre les reversals soudains
"""

import json
import os
from datetime import datetime
from reversal_protection import ReversalProtector

# Racine du projet (pour chemins absolus en production)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class PaperTrader:
    def __init__(self, initial_balance=100):
        self.protector = ReversalProtector()  # Protection contre reversals
        self.short_leverage = 10.0  # Levier 10x sur les positions SHORT
        self.long_leverage = 1.0   # Levier désactivé (positions long)
        # Frais simulés 0.05% par côté (open/close)
        self.fee_pct = 0.0005
        # Slippage simulé en paper (0.05% par défaut, ex: SLIPPAGE_PCT=0.1 pour 0.1%)
        _slippage = os.environ.get('SLIPPAGE_PCT', '0.05').strip()
        try:
            self.slippage_pct = float(_slippage) / 100.0
        except ValueError:
            self.slippage_pct = 0.0005
        
        # Configuration Break-Even & Drawdown
        self.breakeven_trigger_pct = 1.0   # Activer break-even à +1% de gain
        self.max_drawdown_pct = 10.0       # Arrêter trading si perte > 10%
        self.initial_capital = initial_balance  # Capital de référence
        
        # Configuration Trailing Stop Loss
        self.trailing_stop_enabled = True
        self.trailing_stop_activation_pct = 1.5  # Activer trailing à +1.5% de gain
        self.trailing_stop_distance_pct = 1.0     # Distance du trailing (1% sous le plus haut)
        
        # Configuration Take Profit Partiel
        self.partial_tp_enabled = True
        self.partial_tp_ratio = 0.5  # Prendre 50% à TP1
        
        # Cooldown après trade
        self.cooldown_enabled = True
        self.cooldown_minutes = 5
        self.recent_trades = {}  # {symbol: last_trade_timestamp}

        # Fichiers dans la racine du projet (production: cwd peut être ailleurs)
        self.balance_file = os.path.join(_PROJECT_ROOT, 'paper_wallet.json')
        self.trades_file = os.path.join(_PROJECT_ROOT, 'paper_trades.json')

        # Chargement ou création du portefeuille
        if os.path.exists(self.balance_file):
            try:
                with open(self.balance_file, 'r') as f:
                    self.wallet = json.load(f)
                if 'positions' not in self.wallet:
                    self.wallet['positions'] = {}
                if 'initial_capital' not in self.wallet:
                    self.wallet['initial_capital'] = 100
                if 'total_fees_usdt' not in self.wallet:
                    self.wallet['total_fees_usdt'] = 0.0
                if 'daily_start_balance' not in self.wallet:
                    self.wallet['daily_start_balance'] = float(self.wallet.get('USDT', 100))
                if 'daily_start_date' not in self.wallet:
                    self.wallet['daily_start_date'] = datetime.now().strftime('%Y-%m-%d')
            except (json.JSONDecodeError, Exception):
                self.wallet = {'USDT': 100, 'positions': {}, 'initial_capital': 100, 'total_fees_usdt': 0.0,
                               'daily_start_balance': 100, 'daily_start_date': datetime.now().strftime('%Y-%m-%d')}
        else:
            self.wallet = {'USDT': 100, 'positions': {}, 'initial_capital': 100, 'total_fees_usdt': 0.0,
                           'daily_start_balance': 100, 'daily_start_date': datetime.now().strftime('%Y-%m-%d')}
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

    def get_total_fees_usdt(self) -> float:
        return float(self.wallet.get('total_fees_usdt', 0))

    def update_daily_start_if_new_day(self, total_capital: float):
        """Réinitialise le solde de référence du jour si on change de jour."""
        today = datetime.now().strftime('%Y-%m-%d')
        if self.wallet.get('daily_start_date') != today:
            self.wallet['daily_start_date'] = today
            self.wallet['daily_start_balance'] = total_capital
            self.save_wallet()

    def get_daily_drawdown_pct(self, total_capital: float) -> float:
        """Drawdown du jour en % (positif = perte)."""
        start = float(self.wallet.get('daily_start_balance', total_capital))
        if start <= 0:
            return 0.0
        return ((start - total_capital) / start) * 100

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
    # BREAK-EVEN & DRAWDOWN
    # ─────────────────────────────────────────────────────────

    def check_and_apply_breakeven(self, real_prices: dict):
        """
        Vérifie toutes les positions et applique le break-even automatique.
        Si une position a un gain >= breakeven_trigger_pct, on déplace le SL au prix d'entrée.
        """
        modified_count = 0
        
        for symbol, pos in self.wallet['positions'].items():
            current_price = real_prices.get(symbol)
            if not current_price:
                continue
            
            entry_price = pos['entry_price']
            direction = pos.get('direction', 'LONG')
            current_sl = pos['stop_loss']
            
            # Calculer le gain actuel en %
            if direction == 'LONG':
                gain_pct = ((current_price - entry_price) / entry_price) * 100
                # Break-even: SL doit être en dessous de entry pour LONG
                sl_is_below_entry = current_sl < entry_price
            else:  # SHORT
                gain_pct = ((entry_price - current_price) / entry_price) * 100
                # Break-even: SL doit être au-dessus de entry pour SHORT
                sl_is_below_entry = current_sl > entry_price
            
            # Si gain >= trigger ET SL n'est pas encore à break-even
            if gain_pct >= self.breakeven_trigger_pct and sl_is_below_entry:
                # Déplacer SL au prix d'entrée (break-even)
                self.wallet['positions'][symbol]['stop_loss'] = entry_price
                self.wallet['positions'][symbol]['breakeven_active'] = True
                modified_count += 1
                print(f"[LOCK] BREAK-EVEN {symbol}: SL déplacé à ${entry_price:.4f} (gain: +{gain_pct:.1f}%)")
        
        if modified_count > 0:
            self.save_wallet()
        
        return modified_count

    def check_and_apply_trailing_stop(self, real_prices: dict):
        """
        Trailing Stop a 2 paliers:
        - Palier 1: gain >= act_pct -> trailing large (distance = dist_pct)
        - Palier 2: gain >= 2 * act_pct -> trailing serre (distance = dist_pct * 0.5)
        """
        if not self.trailing_stop_enabled:
            return 0

        modified_count = 0

        for symbol, pos in self.wallet['positions'].items():
            current_price = real_prices.get(symbol)
            if not current_price:
                continue

            entry_price = pos['entry_price']
            direction = pos.get('direction', 'LONG')
            current_sl = pos['stop_loss']
            atr_pct = pos.get('atr_pct')
            act_pct = max(1.0, min(3.0, atr_pct * 0.6)) if atr_pct else self.trailing_stop_activation_pct
            dist_pct = max(0.5, min(2.0, atr_pct * 0.5)) if atr_pct else self.trailing_stop_distance_pct

            if direction == 'LONG':
                highest_price = pos.get('highest_price', entry_price)
                if current_price > highest_price:
                    highest_price = current_price
                    self.wallet['positions'][symbol]['highest_price'] = highest_price
                gain_pct = ((current_price - entry_price) / entry_price) * 100

                # Palier 2: gain >= 2x activation -> trailing serre
                if gain_pct >= act_pct * 2:
                    effective_dist = dist_pct * 0.5
                    trail_level = 2
                elif gain_pct >= act_pct:
                    effective_dist = dist_pct
                    trail_level = 1
                else:
                    continue

                new_trailing_sl = highest_price * (1 - effective_dist / 100)
                if new_trailing_sl > current_sl:
                    self.wallet['positions'][symbol]['stop_loss'] = new_trailing_sl
                    self.wallet['positions'][symbol]['trailing_active'] = True
                    self.wallet['positions'][symbol]['trailing_level'] = trail_level
                    modified_count += 1
                    print("TRAILING L{} {} SL -> {:.4f} (high: {:.4f}, +{:.1f}%)".format(
                        trail_level, symbol, new_trailing_sl, highest_price, gain_pct))
            else:
                lowest_price = pos.get('lowest_price', entry_price)
                if current_price < lowest_price:
                    lowest_price = current_price
                    self.wallet['positions'][symbol]['lowest_price'] = lowest_price
                gain_pct = ((entry_price - current_price) / entry_price) * 100

                if gain_pct >= act_pct * 2:
                    effective_dist = dist_pct * 0.5
                    trail_level = 2
                elif gain_pct >= act_pct:
                    effective_dist = dist_pct
                    trail_level = 1
                else:
                    continue

                new_trailing_sl = lowest_price * (1 + effective_dist / 100)
                if new_trailing_sl < current_sl:
                    self.wallet['positions'][symbol]['stop_loss'] = new_trailing_sl
                    self.wallet['positions'][symbol]['trailing_active'] = True
                    self.wallet['positions'][symbol]['trailing_level'] = trail_level
                    modified_count += 1
                    print("TRAILING L{} {} SL -> {:.4f} (low: {:.4f}, +{:.1f}%)".format(
                        trail_level, symbol, new_trailing_sl, lowest_price, gain_pct))

        if modified_count > 0:
            self.save_wallet()
        return modified_count

    def get_total_capital(self, real_prices: dict) -> float:
        """Calcule le capital total = solde USDT + valeur des positions ouvertes."""
        balance = self.get_usdt_balance()
        positions_value = 0
        
        for symbol, pos in self.wallet['positions'].items():
            current_price = real_prices.get(symbol, pos['entry_price'])
            direction = pos.get('direction', 'LONG')
            entry_price = pos['entry_price']
            quantity = pos['quantity']
            
            if direction == 'LONG':
                positions_value += quantity * current_price
            else:  # SHORT
                pnl = (entry_price - current_price) * quantity
                positions_value += pos['amount_usdt'] + pnl
        
        return balance + positions_value

    def check_drawdown(self, real_prices: dict) -> tuple:
        """
        Vérifie si le drawdown maximum est atteint.
        
        Returns:
            (is_exceeded, current_drawdown_pct, total_capital)
        """
        total_capital = self.get_total_capital(real_prices)
        
        # Récupérer le capital initial depuis le wallet (ou utiliser la valeur par défaut)
        initial = self.wallet.get('initial_capital', self.initial_capital)
        
        # Calculer le drawdown
        if initial > 0:
            drawdown_pct = ((initial - total_capital) / initial) * 100
        else:
            drawdown_pct = 0
        
        is_exceeded = drawdown_pct >= self.max_drawdown_pct
        
        return is_exceeded, drawdown_pct, total_capital

    def emergency_close_all(self, real_prices: dict, reason: str = "DRAWDOWN MAX", close_direction: str = "ALL"):
        """
        Ferme les positions ouvertes en urgence.
        
        Args:
            real_prices: Prix actuels
            reason: Raison de la fermeture
            close_direction: "ALL" = tout, "LONG" = seulement LONG, "SHORT" = seulement SHORT
        """
        positions_to_close = []
        
        for symbol, pos in self.wallet['positions'].items():
            direction = pos.get('direction', 'LONG')
            
            if close_direction == "ALL":
                positions_to_close.append(symbol)
            elif close_direction == direction:
                positions_to_close.append(symbol)
            # Si CRASH (close_direction != "ALL"), garder les positions opposées
        
        for symbol in positions_to_close:
            current_price = real_prices.get(symbol)
            if current_price:
                self.close_position(symbol, current_price, f"[ALERT] {reason}")
                print(f"[ALERT] FERMETURE URGENTE {symbol} - {reason}")
        
        return len(positions_to_close)

    # ─────────────────────────────────────────────────────────
    # TAKE PROFIT PARTIEL (SCALING OUT)
    # ─────────────────────────────────────────────────────────

    def check_and_apply_partial_tp(self, real_prices: dict):
        """
        TP a 3 niveaux: 25% a TP1, 50% a TP2, 25% runners (trailing serre).
        """
        if not self.partial_tp_enabled:
            return 0

        partial_count = 0

        for symbol, pos in list(self.wallet['positions'].items()):
            current_price = real_prices.get(symbol)
            if not current_price:
                continue

            direction = pos.get('direction', 'LONG')
            take_profit = pos.get('take_profit', 0)
            take_profit_2 = pos.get('take_profit_2')
            entry_price = pos['entry_price']
            tp_level = pos.get('tp_level', 0)

            tp1_reached = False
            tp2_reached = False
            if direction == 'LONG':
                tp1_reached = current_price >= take_profit
                tp2_reached = take_profit_2 is not None and current_price >= take_profit_2
            else:
                tp1_reached = current_price <= take_profit
                tp2_reached = take_profit_2 is not None and current_price <= take_profit_2

            if tp2_reached and tp_level < 2:
                # TP2: prendre 50% supplementaire (total 75% sorti)
                quantity = pos['quantity']
                sell_pct = 0.50 / (1.0 - 0.25 * min(tp_level, 1)) if tp_level >= 1 else 0.75
                sell_pct = min(sell_pct, 0.90)
                partial_qty = quantity * sell_pct
                remaining_qty = quantity - partial_qty

                if direction == 'LONG':
                    partial_pnl = (current_price - entry_price) * partial_qty
                else:
                    partial_pnl = (entry_price - current_price) * partial_qty

                partial_value = pos['amount_usdt'] * (partial_qty / quantity) + partial_pnl
                self.wallet['USDT'] += partial_value
                self.wallet['positions'][symbol]['quantity'] = remaining_qty
                self.wallet['positions'][symbol]['amount_usdt'] = pos['amount_usdt'] * (remaining_qty / quantity)
                self.wallet['positions'][symbol]['tp_level'] = 2
                self.wallet['positions'][symbol]['stop_loss'] = entry_price + (take_profit - entry_price) * 0.5 if direction == 'LONG' else entry_price - (entry_price - take_profit) * 0.5
                partial_count += 1
                print("TP2 {} {:.0f}% vendu @ {:.4f} (+{:.2f}$), 25% runners".format(
                    symbol, sell_pct * 100, current_price, partial_pnl))

            elif tp1_reached and tp_level < 1:
                # TP1: prendre 25%
                quantity = pos['quantity']
                partial_qty = quantity * 0.25
                remaining_qty = quantity - partial_qty

                if direction == 'LONG':
                    partial_pnl = (current_price - entry_price) * partial_qty
                else:
                    partial_pnl = (entry_price - current_price) * partial_qty

                partial_value = pos['amount_usdt'] * 0.25 + partial_pnl
                self.wallet['USDT'] += partial_value
                self.wallet['positions'][symbol]['quantity'] = remaining_qty
                self.wallet['positions'][symbol]['amount_usdt'] = pos['amount_usdt'] * 0.75
                self.wallet['positions'][symbol]['tp_level'] = 1
                self.wallet['positions'][symbol]['stop_loss'] = entry_price
                if take_profit_2:
                    self.wallet['positions'][symbol]['take_profit'] = take_profit_2
                partial_count += 1
                print("TP1 {} 25% vendu @ {:.4f} (+{:.2f}$), SL -> breakeven".format(
                    symbol, current_price, partial_pnl))

        if partial_count > 0:
            self.save_wallet()
        return partial_count

    def check_time_based_exits(self, real_prices: dict, max_hold_hours: float = 48):
        """
        Ferme les positions qui stagnent trop longtemps sans atteindre le TP.
        Si une position est ouverte depuis > max_hold_hours et le PnL est < +0.5%, on ferme.
        """
        from datetime import datetime, timedelta
        closed_count = 0

        for symbol, pos in list(self.wallet['positions'].items()):
            current_price = real_prices.get(symbol)
            if not current_price:
                continue

            open_time_str = pos.get('open_time')
            if not open_time_str:
                continue

            try:
                open_time = datetime.strptime(open_time_str, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                continue

            hours_open = (datetime.now() - open_time).total_seconds() / 3600
            if hours_open < max_hold_hours:
                continue

            entry_price = pos['entry_price']
            direction = pos.get('direction', 'LONG')
            if direction == 'LONG':
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = ((entry_price - current_price) / entry_price) * 100

            if pnl_pct < 0.5:
                self.close_position(symbol, current_price,
                    "TIME EXIT ({:.0f}h, PnL {:.2f}%)".format(hours_open, pnl_pct))
                closed_count += 1

        return closed_count

    def check_and_apply_dca(self, real_prices: dict, max_dca: int = 2, dca_threshold_pct: float = -1.5):
        """
        DCA automatique: renforce les positions perdantes si la tendance reste valide.
        - Si PnL < dca_threshold_pct et dca_count < max_dca: ajouter 50% de la position initiale
        - Recalculer le prix moyen d'entree
        """
        dca_count = 0
        
        for symbol, pos in list(self.wallet['positions'].items()):
            current_price = real_prices.get(symbol)
            if not current_price:
                continue
            
            entry_price = pos['entry_price']
            direction = pos.get('direction', 'LONG')
            current_dca = pos.get('dca_count', 0)
            
            if current_dca >= max_dca:
                continue
            
            if direction == 'LONG':
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = ((entry_price - current_price) / entry_price) * 100
            
            if pnl_pct > dca_threshold_pct:
                continue
            
            # DCA: ajouter 50% de la position initiale
            original_amount = pos['amount_usdt']
            dca_amount = original_amount * 0.5
            balance = self.get_usdt_balance()
            
            if dca_amount > balance * 0.3 or dca_amount < 5:
                continue
            
            # Recalculer le prix moyen
            old_qty = pos['quantity']
            new_qty = dca_amount / current_price
            total_qty = old_qty + new_qty
            avg_price = (entry_price * old_qty + current_price * new_qty) / total_qty
            
            self.wallet['USDT'] -= dca_amount
            self.wallet['positions'][symbol]['entry_price'] = avg_price
            self.wallet['positions'][symbol]['quantity'] = total_qty
            self.wallet['positions'][symbol]['amount_usdt'] = original_amount + dca_amount
            self.wallet['positions'][symbol]['dca_count'] = current_dca + 1
            
            atr_pct = pos.get('atr_pct') or 1.5
            if direction == 'LONG':
                self.wallet['positions'][symbol]['stop_loss'] = avg_price * (1 - atr_pct * 1.5 / 100)
            else:
                self.wallet['positions'][symbol]['stop_loss'] = avg_price * (1 + atr_pct * 1.5 / 100)
            
            dca_count += 1
            print("DCA #{} {} @ {:.4f} (+{:.2f}$), avg price {:.4f}".format(
                current_dca + 1, symbol, current_price, dca_amount, avg_price))
        
        if dca_count > 0:
            self.save_wallet()
        return dca_count

    def check_grid_opportunities(self, real_prices: dict, indicators_dict: dict):
        """
        Grid Trading: place des ordres dans un range detecte.
        Si le marche est en RANGING, achete en bas du range et vend en haut.
        """
        grid_trades = 0
        
        for symbol, ind in indicators_dict.items():
            if not ind:
                continue
            
            regime = ind.get('market_regime')
            if regime != 'RANGING':
                continue
            
            current_price = real_prices.get(symbol)
            if not current_price:
                continue
            
            # Deja en position sur ce symbole?
            if symbol in self.wallet.get('positions', {}):
                continue
            
            bb_lower = ind.get('bb_lower')
            bb_upper = ind.get('bb_upper')
            bb_percent = ind.get('bb_percent')
            
            if bb_lower is None or bb_upper is None or bb_percent is None:
                continue
            
            balance = self.get_usdt_balance()
            grid_size = min(balance * 0.15, 30)  # 15% du capital, max 30$
            
            if grid_size < 10:
                continue
            
            # Achat en bas du range (bb_percent < 0.2)
            if bb_percent < 0.2:
                sl = bb_lower * 0.99
                tp = bb_upper * 0.98
                if tp > current_price and sl < current_price:
                    if self.place_buy_order(symbol, grid_size, current_price, sl, tp, entry_trend='GRID_LONG'):
                        self.wallet['positions'][symbol]['grid_trade'] = True
                        grid_trades += 1
                        print("GRID LONG {} @ {:.4f} (range {:.4f}-{:.4f})".format(
                            symbol, current_price, bb_lower, bb_upper))
            
            # Vente en haut du range (bb_percent > 0.8) - uniquement si short possible
            elif bb_percent > 0.8:
                sl = bb_upper * 1.01
                tp = bb_lower * 1.02
                if tp < current_price and sl > current_price:
                    if self.place_short_order(symbol, grid_size, current_price, sl, tp, entry_trend='GRID_SHORT'):
                        self.wallet['positions'][symbol]['grid_trade'] = True
                        grid_trades += 1
                        print("GRID SHORT {} @ {:.4f} (range {:.4f}-{:.4f})".format(
                            symbol, current_price, bb_lower, bb_upper))
        
        return grid_trades

    # ─────────────────────────────────────────────────────────
    # COOLDOWN APRÈS TRADE
    # ─────────────────────────────────────────────────────────

    def record_trade_time(self, symbol: str):
        """Enregistre le timestamp du dernier trade sur une paire."""
        self.recent_trades[symbol] = datetime.now()

    def is_in_cooldown(self, symbol: str) -> tuple:
        """
        Vérifie si une paire est en période de cooldown.
        
        Returns:
            (is_in_cooldown, minutes_remaining)
        """
        if not self.cooldown_enabled:
            return False, 0
        
        if symbol not in self.recent_trades:
            return False, 0
        
        last_trade = self.recent_trades[symbol]
        elapsed = (datetime.now() - last_trade).total_seconds() / 60
        
        if elapsed < self.cooldown_minutes:
            remaining = self.cooldown_minutes - elapsed
            return True, remaining
        
        return False, 0

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
        entry_trend: str = 'UNKNOWN',  # Tendance à l'ouverture
        take_profit_2: float = None,   # TP2 pour scaling out
        atr_pct: float = None,         # ATR % pour trailing stop adaptatif
    ) -> bool:
        """Exécute un ordre d'ACHAT (position LONG)."""
        if self.wallet['USDT'] < amount_usdt:
            print(f"[X] Fonds insuffisants pour {symbol} "
                  f"(Requis: {amount_usdt:.2f}, Dispo: {self.wallet['USDT']:.2f})")
            return False

        if symbol in self.wallet['positions']:
            print(f"[WARN] Position déjà ouverte sur {symbol}")
            return False

        # Slippage simulé (entrée LONG = prix d'achat plus haut)
        entry_price = current_price * (1 + self.slippage_pct)
        quantity = amount_usdt / entry_price

        self.wallet['USDT'] -= amount_usdt
        self.wallet['positions'][symbol] = {
            'direction':   'LONG',
            'amount_usdt': amount_usdt,
            'quantity':    quantity,
            'entry_price': entry_price,
            'entry_time':  datetime.now().strftime('%Y-%m-%d %H:%M'),
            'stop_loss':   stop_loss_price,
            'take_profit': take_profit_price,
            'take_profit_2': take_profit_2,
            'entry_trend': entry_trend,
            'atr_pct': atr_pct,
        }
        self.save_wallet()

        self.log_trade({
            'type':        'ACHAT',
            'symbol':      symbol,
            'direction':   'LONG',
            'price':       entry_price,
            'amount':      amount_usdt,
            'quantity':    quantity,
            'stop_loss':   stop_loss_price,
            'take_profit': take_profit_price,
            'time':        datetime.now().strftime('%d/%m %H:%M'),
            'pnl':         0,
            'pnl_percent': 0,
        })

        sl_dist_pct = abs((entry_price - stop_loss_price) / entry_price * 100)
        tp_dist_pct = abs((take_profit_price - entry_price) / entry_price * 100)
        position_size = amount_usdt  # Levier désactivé
        print(f"[BUY] ACHAT  {symbol:<12} | ${entry_price:.6f} | "
              f"SL:-{sl_dist_pct:.2f}% | TP:+{tp_dist_pct:.2f}% | Taille position:${position_size:.2f} (levier désactivé, marge ${amount_usdt:.2f})")
        try:
            from notifier import on_trade_opened
            on_trade_opened('LONG', symbol, entry_price, amount_usdt, stop_loss_price, take_profit_price)
        except Exception:
            pass
        return True

    def place_short_order(
        self,
        symbol: str,
        amount_usdt: float,
        current_price: float,
        stop_loss_price: float,
        take_profit_price: float,
        entry_trend: str = 'UNKNOWN',
        take_profit_2: float = None,
        atr_pct: float = None,
    ) -> bool:
        """Exécute un ordre de VENTE À DÉCOUVERT (position SHORT)."""
        if self.wallet['USDT'] < amount_usdt:
            print(f"[X] Fonds insuffisants pour short {symbol}")
            return False

        if symbol in self.wallet['positions']:
            print(f"[WARN] Position déjà ouverte sur {symbol}")
            return False

        # Slippage simulé (entrée SHORT = prix de vente plus bas)
        entry_price = current_price * (1 - self.slippage_pct)
        lev = self.short_leverage
        quantity = (amount_usdt * lev) / entry_price
        notional = amount_usdt * lev
        fee_open = notional * self.fee_pct
        total_lock = amount_usdt + fee_open
        if self.wallet['USDT'] < total_lock:
            print(f"Fonds insuffisants (marge + frais): {total_lock:.2f} USDT")
            return False
        self.wallet['USDT'] -= total_lock
        self.wallet['total_fees_usdt'] = self.wallet.get('total_fees_usdt', 0) + fee_open
        self.wallet['positions'][symbol] = {
            'direction':   'SHORT',
            'amount_usdt': amount_usdt,
            'quantity':    quantity,
            'entry_price': entry_price,
            'entry_time':  datetime.now().strftime('%Y-%m-%d %H:%M'),
            'stop_loss':   stop_loss_price,
            'take_profit': take_profit_price,
            'take_profit_2': take_profit_2,
            'entry_trend': entry_trend,
            'leverage':    lev,
            'atr_pct': atr_pct,
        }
        self.save_wallet()

        self.log_trade({
            'type':        'SHORT',
            'symbol':      symbol,
            'direction':   'SHORT',
            'price':       entry_price,
            'amount':      amount_usdt,
            'quantity':    quantity,
            'stop_loss':   stop_loss_price,
            'take_profit': take_profit_price,
            'time':        datetime.now().strftime('%d/%m %H:%M'),
            'pnl':         0,
            'pnl_percent': 0,
        })
        try:
            from notifier import on_trade_opened
            on_trade_opened('SHORT', symbol, entry_price, amount_usdt, stop_loss_price, take_profit_price)
        except Exception:
            pass
        notional = amount_usdt * self.short_leverage
        print(f"[DOWN] SHORT  {symbol:<12} | ${entry_price:.6f} | "
              f"SL:${stop_loss_price:.6f} | TP:${take_profit_price:.6f} | "
              f"levier {int(self.short_leverage)}x | marge ${amount_usdt:.2f} | notional ${notional:.2f}")
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

        # Slippage simulé sur la sortie
        if direction == 'LONG':
            exit_price = current_price * (1 - self.slippage_pct)  # On vend plus bas
        else:
            exit_price = current_price * (1 + self.slippage_pct)  # On rachète plus haut (SHORT)

        # Calcul PnL selon direction
        if direction == 'LONG':
            exit_value  = quantity * exit_price
            pnl_value   = exit_value - entry_amount
            pnl_percent = ((exit_price - entry_price) / entry_price) * 100
            returned    = exit_value
        else:  # SHORT
            pnl_value   = (entry_price - exit_price) * quantity
            pnl_percent = ((entry_price - exit_price) / entry_price) * 100
            exit_notional = quantity * exit_price
            fee_close = exit_notional * self.fee_pct
            self.wallet['total_fees_usdt'] = self.wallet.get('total_fees_usdt', 0) + fee_close
            returned = entry_amount + pnl_value - fee_close

        # Mise à jour du solde (jamais négatif)
        self.wallet['USDT'] += max(returned, 0)
        del self.wallet['positions'][symbol]
        self.save_wallet()

        status = "[OK] GAIN" if pnl_value > 0 else "[X] PERTE"
        print(f"[MONEY] VENTE {symbol:<12} ({reason}) | {status}: "
              f"${pnl_value:+.2f} ({pnl_percent:+.2f}%)")

        trade_data = {
            'type':        f'VENTE ({reason})',
            'symbol':      symbol,
            'direction':   direction,
            'price':       exit_price,
            'amount':      round(abs(returned), 2),
            'quantity':    quantity,
            'entry_price': entry_price,
            'time':        datetime.now().strftime('%d/%m %H:%M'),
            'pnl':         round(pnl_value, 2),
            'pnl_percent': round(pnl_percent, 2),
            'reason':      reason,
        }
        self.log_trade(trade_data)
        try:
            from notifier import on_trade_closed
            on_trade_closed(trade_data)
        except Exception:
            pass
        # Mise à jour du position sizer (Kelly) pour adapter la taille des prochains trades
        try:
            from position_sizing import update_position_stats
            update_position_stats(is_win=(pnl_value > 0), pnl_pct=pnl_percent)
        except Exception:
            pass
        return True

    # ─────────────────────────────────────────────────────────
    # SURVEILLANCE AUTOMATIQUE
    # ─────────────────────────────────────────────────────────

    def check_positions(self, real_prices: dict):
        """
        Vérifie toutes les positions ouvertes.
        Déclenche SL ou TP si le prix les atteint.
        SIMPLE VERSION - sans protection reversal (appeler check_positions_with_protection_enabled pour protection).
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
                    positions_to_close.append((symbol, current_price, "STOP LOSS [STOP]"))
                elif current_price >= take_profit:
                    positions_to_close.append((symbol, current_price, "TAKE PROFIT [TARGET]"))
            else:  # SHORT
                # Pour un short : SL est au-dessus, TP est en dessous
                if current_price >= stop_loss:
                    positions_to_close.append((symbol, current_price, "STOP LOSS [STOP]"))
                elif current_price <= take_profit:
                    positions_to_close.append((symbol, current_price, "TAKE PROFIT [TARGET]"))

        for symbol, price, reason in positions_to_close:
            self.close_position(symbol, price, reason)

    def check_positions_with_protection(self, real_prices: dict, all_indicators: dict = None):
        """
        Vérifie toutes les positions avec PROTECTION contre reversals.
        Empêche les fermetures SL pendant les whipsaws.
        
        Args:
            real_prices: Dict de prix actuels
            all_indicators: Dict avec indicateurs par symbole {symbol: indicators_dict}
        """
        # Vérifier circuit breaker
        is_cb_active, cb_remaining = self.protector.is_circuit_breaker_active()
        if is_cb_active:
            print(f"[BLOCK] CIRCUIT BREAKER ACTIF - Trading suspendu ({cb_remaining}s)")
            return
        
        positions_to_close = []
        protected_positions = []

        for symbol, pos in list(self.wallet['positions'].items()):
            current_price = real_prices.get(symbol)
            if not current_price:
                continue

            direction = pos.get('direction', 'LONG')
            stop_loss = pos['stop_loss']
            take_profit = pos['take_profit']
            indicators = all_indicators.get(symbol, {}) if all_indicators else {}

            # --- NOUVEAU : FERMETURE IMMÉDIATE SUR REVERSAL ---
            action = self.protector.get_position_action(pos, indicators, current_price)
            if action['action'] in ['EMERGENCY_CLOSE', 'PARTIAL_CLOSE']:
                # Fermer immédiatement (ou partiellement si implémenté)
                self.close_position(symbol, current_price, f"REVERSAL TENDANCE: {action['reason']}")
                self.protector.record_sl_close(symbol)
                continue

            # Vérifier SL
            is_at_sl = False
            if direction == 'LONG':
                is_at_sl = current_price <= stop_loss
            else:  # SHORT
                is_at_sl = current_price >= stop_loss

            if is_at_sl:
                should_protect, protect_reason = self.protector.should_protect_position(
                    pos, indicators, current_price
                )
                if should_protect:
                    protected_positions.append((symbol, protect_reason))
                    continue
                else:
                    positions_to_close.append((symbol, current_price, f"STOP LOSS [STOP] {protect_reason}"))
                    self.protector.record_sl_close(symbol)

            # Vérifier TP (toujours valide)
            is_at_tp = False
            if direction == 'LONG':
                is_at_tp = current_price >= take_profit
            else:  # SHORT
                is_at_tp = current_price <= take_profit

            if is_at_tp:
                positions_to_close.append((symbol, current_price, "TAKE PROFIT [TARGET]"))

        # Fermer les positions à fermer
        for symbol, price, reason in positions_to_close:
            self.close_position(symbol, price, reason)
        # Logger les positions protégées
        for symbol, reason in protected_positions:
            print(f"[SHIELD]  {symbol} PROTÉGÉ: {reason}")

    def reset_wallet(self, initial_balance: float = 100):
        """Remet le portefeuille à zéro (utile pour les tests)."""
        self.wallet = {'USDT': 100, 'positions': {}, 'initial_capital': 100}
        self.save_wallet()
        print(f"[REFRESH] Portefeuille réinitialisé à $100.00")

    def reverse_position(
        self,
        symbol: str,
        current_price: float,
        new_direction: str,
        amount_usdt: float,
        stop_loss_price: float,
        take_profit_price: float,
        entry_trend: str = 'UNKNOWN',
        take_profit_2: float = None,
    ) -> bool:
        """
        Inverse une position existante: ferme la position actuelle et ouvre dans la direction opposée.
        
        Args:
            symbol: Symbole de la paire
            current_price: Prix actuel du marché
            new_direction: 'LONG' ou 'SHORT' - la nouvelle direction à prendre
            amount_usdt: Montant pour la nouvelle position
            stop_loss_price: Stop Loss de la nouvelle position
            take_profit_price: Take Profit de la nouvelle position
            entry_trend: Tendance d'entrée
            take_profit_2: TP2 optionnel
        
        Returns:
            True si l'inversion a réussi, False sinon
        """
        if symbol not in self.wallet['positions']:
            print(f"[WARN] Pas de position existante sur {symbol} à inverser")
            return False
        
        current_pos = self.wallet['positions'][symbol]
        current_direction = current_pos.get('direction', 'LONG')
        
        # Vérifier qu'on inverse vraiment (pas la même direction)
        if current_direction == new_direction:
            print(f"[WARN] {symbol} déjà en {new_direction}, pas d'inversion nécessaire")
            return False
        
        # Fermer la position actuelle
        self.close_position(symbol, current_price, f"INVERSION → {new_direction} [REFRESH]")
        
        # Ouvrir la nouvelle position dans la direction opposée
        if new_direction == 'LONG':
            success = self.place_buy_order(
                symbol=symbol,
                amount_usdt=amount_usdt,
                current_price=current_price,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                entry_trend=entry_trend,
                take_profit_2=take_profit_2
            )
        else:  # SHORT
            success = self.place_short_order(
                symbol=symbol,
                amount_usdt=amount_usdt,
                current_price=current_price,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                entry_trend=entry_trend
            )
        
        if success:
            print(f"[REFRESH] INVERSION {symbol}: {current_direction} → {new_direction} @ ${current_price:.6f}")
        
        return success

    def get_position_direction(self, symbol: str) -> str:
        """Retourne la direction d'une position ('LONG', 'SHORT', ou None si pas de position)"""
        if symbol in self.wallet['positions']:
            return self.wallet['positions'][symbol].get('direction', 'LONG')
        return None
