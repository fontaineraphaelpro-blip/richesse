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
        self.cooldown_minutes = 10  # Aligner sur la config globale (10 min)
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
                print(f"🔒 BREAK-EVEN {symbol}: SL déplacé à ${entry_price:.4f} (gain: +{gain_pct:.1f}%)")
        
        if modified_count > 0:
            self.save_wallet()
        
        return modified_count

    def check_and_apply_trailing_stop(self, real_prices: dict):
        """
        Applique le Trailing Stop Loss sur toutes les positions.
        
        Le trailing stop suit le prix:
        - S'active quand gain >= trailing_stop_activation_pct
        - Maintient le SL à trailing_stop_distance_pct sous le plus haut atteint
        - Ne descend JAMAIS (pour LONG) / ne monte JAMAIS (pour SHORT)
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
            
            # Récupérer ou initialiser le plus haut/bas atteint
            if direction == 'LONG':
                highest_price = pos.get('highest_price', entry_price)
                # Mettre à jour le plus haut si le prix actuel est plus élevé
                if current_price > highest_price:
                    highest_price = current_price
                    self.wallet['positions'][symbol]['highest_price'] = highest_price
                
                # Calculer le gain depuis l'entrée
                gain_pct = ((current_price - entry_price) / entry_price) * 100
                
                # Activer le trailing si gain >= seuil d'activation
                if gain_pct >= self.trailing_stop_activation_pct:
                    # Calculer le nouveau SL trailing (distance % sous le plus haut)
                    new_trailing_sl = highest_price * (1 - self.trailing_stop_distance_pct / 100)
                    
                    # Le SL ne doit JAMAIS descendre (pour LONG)
                    if new_trailing_sl > current_sl:
                        old_sl = current_sl
                        self.wallet['positions'][symbol]['stop_loss'] = new_trailing_sl
                        self.wallet['positions'][symbol]['trailing_active'] = True
                        modified_count += 1
                        print(f"📈 TRAILING SL {symbol}: ${old_sl:.4f} → ${new_trailing_sl:.4f} "
                              f"(plus haut: ${highest_price:.4f}, gain: +{gain_pct:.1f}%)")
            
            else:  # SHORT
                lowest_price = pos.get('lowest_price', entry_price)
                # Mettre à jour le plus bas si le prix actuel est plus bas
                if current_price < lowest_price:
                    lowest_price = current_price
                    self.wallet['positions'][symbol]['lowest_price'] = lowest_price
                
                # Calculer le gain depuis l'entrée (pour short, gain = prix baisse)
                gain_pct = ((entry_price - current_price) / entry_price) * 100
                
                # Activer le trailing si gain >= seuil d'activation
                if gain_pct >= self.trailing_stop_activation_pct:
                    # Calculer le nouveau SL trailing (distance % au-dessus du plus bas)
                    new_trailing_sl = lowest_price * (1 + self.trailing_stop_distance_pct / 100)
                    
                    # Le SL ne doit JAMAIS monter (pour SHORT)
                    if new_trailing_sl < current_sl:
                        old_sl = current_sl
                        self.wallet['positions'][symbol]['stop_loss'] = new_trailing_sl
                        self.wallet['positions'][symbol]['trailing_active'] = True
                        modified_count += 1
                        print(f"📉 TRAILING SL {symbol}: ${old_sl:.4f} → ${new_trailing_sl:.4f} "
                              f"(plus bas: ${lowest_price:.4f}, gain: +{gain_pct:.1f}%)")
        
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
                self.close_position(symbol, current_price, f"🚨 {reason}")
                print(f"🚨 FERMETURE URGENTE {symbol} - {reason}")
        
        return len(positions_to_close)

    # ─────────────────────────────────────────────────────────
    # TAKE PROFIT PARTIEL (SCALING OUT)
    # ─────────────────────────────────────────────────────────

    def check_and_apply_partial_tp(self, real_prices: dict):
        """
        Vérifie si des positions ont atteint TP1 et prend des profits partiels.
        Prend partial_tp_ratio (50%) à TP1, laisse le reste courir vers TP2.
        """
        if not self.partial_tp_enabled:
            return 0
        
        partial_count = 0
        
        for symbol, pos in list(self.wallet['positions'].items()):
            current_price = real_prices.get(symbol)
            if not current_price:
                continue
            
            # Vérifier si déjà partiellement fermé
            if pos.get('partial_tp_taken', False):
                continue
            
            direction = pos.get('direction', 'LONG')
            take_profit = pos.get('take_profit', 0)
            take_profit_2 = pos.get('take_profit_2')  # TP2 optionnel
            
            # Vérifier si TP1 est atteint
            tp1_reached = False
            if direction == 'LONG':
                tp1_reached = current_price >= take_profit
            else:  # SHORT
                tp1_reached = current_price <= take_profit
            
            if tp1_reached:
                # Prendre 50% des profits
                quantity = pos['quantity']
                partial_qty = quantity * self.partial_tp_ratio
                remaining_qty = quantity - partial_qty
                
                entry_price = pos['entry_price']
                
                # Calculer PnL partiel
                if direction == 'LONG':
                    partial_pnl = (current_price - entry_price) * partial_qty
                else:
                    partial_pnl = (entry_price - current_price) * partial_qty
                
                partial_value = pos['amount_usdt'] * self.partial_tp_ratio + partial_pnl
                
                # Mettre à jour le portefeuille
                self.wallet['USDT'] += partial_value
                self.wallet['positions'][symbol]['quantity'] = remaining_qty
                self.wallet['positions'][symbol]['amount_usdt'] = pos['amount_usdt'] * (1 - self.partial_tp_ratio)
                self.wallet['positions'][symbol]['partial_tp_taken'] = True
                
                # Si TP2 existe, l'utiliser comme nouveau TP
                if take_profit_2:
                    self.wallet['positions'][symbol]['take_profit'] = take_profit_2
                
                # Déplacer SL au break-even après TP partiel
                self.wallet['positions'][symbol]['stop_loss'] = entry_price
                
                partial_count += 1
                print(f"💰 TP PARTIEL {symbol}: {self.partial_tp_ratio*100:.0f}% vendu à ${current_price:.4f} "
                      f"| PnL: ${partial_pnl:.2f} | Reste: {remaining_qty:.6f}")
                
                self.log_trade({
                    'type':        'TP PARTIEL',
                    'symbol':      symbol,
                    'direction':   direction,
                    'price':       current_price,
                    'quantity':    partial_qty,
                    'pnl':         round(partial_pnl, 2),
                    'time':        datetime.now().strftime('%d/%m %H:%M'),
                })
        
        if partial_count > 0:
            self.save_wallet()
        
        return partial_count

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
        # Levier désactivé : quantité inchangée

        self.wallet['USDT'] -= amount_usdt
        self.wallet['positions'][symbol] = {
            'direction':   'LONG',
            'amount_usdt': amount_usdt,
            'quantity':    quantity,
            'entry_price': current_price,
            'entry_time':  datetime.now().strftime('%Y-%m-%d %H:%M'),
            'stop_loss':   stop_loss_price,
            'take_profit': take_profit_price,
            'take_profit_2': take_profit_2,  # TP2 pour scaling out
            'entry_trend': entry_trend,  # NOUVEAU: Mémoriser la tendance
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
        position_size = amount_usdt  # Levier désactivé
        print(f"🛒 ACHAT  {symbol:<12} | ${current_price:.6f} | "
              f"SL:-{sl_dist_pct:.2f}% | TP:+{tp_dist_pct:.2f}% | Taille position:${position_size:.2f} (levier désactivé, marge ${amount_usdt:.2f})")
        return True

    def place_short_order(
        self,
        symbol: str,
        amount_usdt: float,
        current_price: float,
        stop_loss_price: float,
        take_profit_price: float,
        entry_trend: str = 'UNKNOWN',  # Tendance à l'ouverture
    ) -> bool:
        """Exécute un ordre de VENTE À DÉCOUVERT (position SHORT)."""
        if self.wallet['USDT'] < amount_usdt:
            print(f"❌ Fonds insuffisants pour short {symbol}")
            return False

        if symbol in self.wallet['positions']:
            print(f"⚠️ Position déjà ouverte sur {symbol}")
            return False

        # Marge = amount_usdt, notional = marge × levier, quantité = notional / prix
        lev = self.short_leverage
        quantity = (amount_usdt * lev) / current_price
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
            'entry_price': current_price,
            'entry_time':  datetime.now().strftime('%Y-%m-%d %H:%M'),
            'stop_loss':   stop_loss_price,
            'take_profit': take_profit_price,
            'entry_trend': entry_trend,
            'leverage':    lev,
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

        notional = amount_usdt * self.short_leverage
        print(f"📉 SHORT  {symbol:<12} | ${current_price:.6f} | "
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

        # Calcul PnL selon direction
        if direction == 'LONG':
            exit_value  = quantity * current_price
            pnl_value   = exit_value - entry_amount
            pnl_percent = ((current_price - entry_price) / entry_price) * 100
            returned    = exit_value
        else:  # SHORT
            pnl_value   = (entry_price - current_price) * quantity
            pnl_percent = ((entry_price - current_price) / entry_price) * 100
            exit_notional = quantity * current_price
            fee_close = exit_notional * self.fee_pct
            self.wallet['total_fees_usdt'] = self.wallet.get('total_fees_usdt', 0) + fee_close
            returned = entry_amount + pnl_value - fee_close

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
            print(f"⛔ CIRCUIT BREAKER ACTIF - Trading suspendu ({cb_remaining}s)")
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
                    positions_to_close.append((symbol, current_price, f"STOP LOSS 🛑 {protect_reason}"))
                    self.protector.record_sl_close(symbol)

            # Vérifier TP (toujours valide)
            is_at_tp = False
            if direction == 'LONG':
                is_at_tp = current_price >= take_profit
            else:  # SHORT
                is_at_tp = current_price <= take_profit

            if is_at_tp:
                positions_to_close.append((symbol, current_price, "TAKE PROFIT 🎯"))

        # Fermer les positions à fermer
        for symbol, price, reason in positions_to_close:
            self.close_position(symbol, price, reason)
        # Logger les positions protégées
        for symbol, reason in protected_positions:
            print(f"🛡️  {symbol} PROTÉGÉ: {reason}")

    def reset_wallet(self, initial_balance: float = 100):
        """Remet le portefeuille à zéro (utile pour les tests)."""
        self.wallet = {'USDT': 100, 'positions': {}, 'initial_capital': 100}
        self.save_wallet()
        print(f"🔄 Portefeuille réinitialisé à $100.00")

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
            print(f"⚠️ Pas de position existante sur {symbol} à inverser")
            return False
        
        current_pos = self.wallet['positions'][symbol]
        current_direction = current_pos.get('direction', 'LONG')
        
        # Vérifier qu'on inverse vraiment (pas la même direction)
        if current_direction == new_direction:
            print(f"⚠️ {symbol} déjà en {new_direction}, pas d'inversion nécessaire")
            return False
        
        # Fermer la position actuelle
        self.close_position(symbol, current_price, f"INVERSION → {new_direction} 🔄")
        
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
            print(f"🔄 INVERSION {symbol}: {current_direction} → {new_direction} @ ${current_price:.6f}")
        
        return success

    def get_position_direction(self, symbol: str) -> str:
        """Retourne la direction d'une position ('LONG', 'SHORT', ou None si pas de position)"""
        if symbol in self.wallet['positions']:
            return self.wallet['positions'][symbol].get('direction', 'LONG')
        return None
