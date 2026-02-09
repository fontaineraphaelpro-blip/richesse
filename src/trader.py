"""
Module de Paper Trading (Simulation) - COMPLET
Gère Entrées (Achat) ET Sorties (SL/TP).
"""
import json
import os
from datetime import datetime

class PaperTrader:
    def __init__(self, initial_balance=1000):
        self.balance_file = 'paper_wallet.json'
        self.trades_file = 'paper_trades.json'
        
        # Charger ou créer le portefeuille
        if os.path.exists(self.balance_file):
            with open(self.balance_file, 'r') as f:
                self.wallet = json.load(f)
        else:
            self.wallet = {'USDT': initial_balance, 'positions': {}}
            self.save_wallet()

    def save_wallet(self):
        with open(self.balance_file, 'w') as f:
            json.dump(self.wallet, f, indent=4)

    def log_trade(self, trade_data):
        history = []
        if os.path.exists(self.trades_file):
            with open(self.trades_file, 'r') as f:
                try: history = json.load(f)
                except: pass
        history.insert(0, trade_data)
        with open(self.trades_file, 'w') as f:
            json.dump(history, f, indent=4)

    def get_usdt_balance(self):
        return self.wallet['USDT']

    def get_open_positions(self):
        return list(self.wallet['positions'].keys())
        
    def get_trades_history(self):
        if os.path.exists(self.trades_file):
            with open(self.trades_file, 'r') as f:
                try: return json.load(f)
                except: return []
        return []

    # --- NOUVELLE FONCTION : GESTION DES SORTIES ---
    def check_positions(self, current_prices):
        """
        Vérifie si les positions ouvertes doivent être fermées (TP ou SL).
        current_prices: Dictionnaire {symbol: prix_actuel}
        """
        positions_to_close = []
        
        for symbol, pos in self.wallet['positions'].items():
            current_price = current_prices.get(symbol)
            
            # Si on n'a pas le prix actuel, on passe
            if not current_price: continue
            
            sl = pos['stop_loss']
            tp = pos['take_profit']
            quantity = pos['quantity']
            
            exit_type = None
            exit_reason = ""
            
            # Vérification STOP LOSS (Le prix passe sous le SL)
            if current_price <= sl:
                exit_type = 'VENTE (SL)'
                exit_reason = f"🛑 Stop Loss touché à ${current_price}"
                
            # Vérification TAKE PROFIT (Le prix dépasse le TP)
            elif current_price >= tp:
                exit_type = 'VENTE (TP)'
                exit_reason = f"✅ Take Profit touché à ${current_price}"
            
            # Si une condition de sortie est remplie, on vend
            if exit_type:
                # Calcul du montant récupéré
                amount_recovered = quantity * current_price
                pnl = amount_recovered - pos['entry_cost']
                
                print(f"{exit_reason} sur {symbol} | PnL: {pnl:.2f} USDT")
                
                # Mise à jour Wallet
                self.wallet['USDT'] += amount_recovered
                
                # Log
                self.log_trade({
                    'type': exit_type,
                    'symbol': symbol,
                    'amount_usdt': amount_recovered,
                    'pnl': round(pnl, 2),
                    'time': datetime.now().strftime('%d/%m %H:%M'),
                    'sl': '-', 'tp': '-'
                })
                
                positions_to_close.append(symbol)
        
        # Supprimer les positions fermées du portefeuille
        for symbol in positions_to_close:
            del self.wallet['positions'][symbol]
            
        if positions_to_close:
            self.save_wallet()

    def place_buy_order(self, symbol, amount_usdt, current_price, stop_loss_price, take_profit_price):
        """Simule un ordre d'achat avec calcul de quantité."""
        if self.wallet['USDT'] < amount_usdt:
            return False

        # Calcul de la quantité de tokens achetée
        quantity = amount_usdt / current_price
        
        print(f"🛒 ACHAT {symbol}: {amount_usdt}$ ({quantity:.4f} tokens) à ${current_price}")
        
        self.wallet['USDT'] -= amount_usdt
        self.wallet['positions'][symbol] = {
            'entry_cost': amount_usdt,
            'quantity': quantity,
            'entry_price': current_price,
            'entry_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price
        }
        
        self.save_wallet()
        
        self.log_trade({
            'type': 'ACHAT',
            'symbol': symbol,
            'amount_usdt': amount_usdt,
            'pnl': 0,
            'time': datetime.now().strftime('%d/%m %H:%M'),
            'sl': stop_loss_price,
            'tp': take_profit_price
        })
        return True