"""
Module de Paper Trading (Simulation).
Simule un portefeuille et des ordres sans connexion à Binance.
"""
import json
import os
import time
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
        """Sauvegarde l'état du portefeuille."""
        with open(self.balance_file, 'w') as f:
            json.dump(self.wallet, f, indent=4)

    def log_trade(self, trade_data):
        """Enregistre l'historique des trades."""
        history = []
        if os.path.exists(self.trades_file):
            with open(self.trades_file, 'r') as f:
                try:
                    history = json.load(f)
                except: pass
        
        # On insère au début pour avoir les plus récents en premier
        history.insert(0, trade_data)
        
        with open(self.trades_file, 'w') as f:
            json.dump(history, f, indent=4)

    def get_usdt_balance(self):
        """Retourne le solde USDT fictif."""
        return self.wallet['USDT']

    def get_open_positions(self):
        """Retourne la liste des paires qu'on possède déjà."""
        return list(self.wallet['positions'].keys())
        
    def get_trades_history(self):
        """Récupère tout l'historique des trades pour le site web."""
        if os.path.exists(self.trades_file):
            with open(self.trades_file, 'r') as f:
                try:
                    return json.load(f)
                except: return []
        return []

    def place_buy_order(self, symbol, amount_usdt, stop_loss_price, take_profit_price):
        """Simule un ordre d'achat."""
        if self.wallet['USDT'] < amount_usdt:
            print(f"❌ Fonds insuffisants pour simuler l'achat de {symbol}")
            return False

        print(f"🛒 SIMULATION ACHAT: {amount_usdt} USDT de {symbol}")
        
        # Mise à jour du portefeuille fictif
        self.wallet['USDT'] -= amount_usdt
        
        # On enregistre la position
        self.wallet['positions'][symbol] = {
            'entry_amount_usdt': amount_usdt,
            'entry_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price
        }
        
        self.save_wallet()
        
        # Log du trade
        trade_record = {
            'type': 'ACHAT',
            'symbol': symbol,
            'amount_usdt': amount_usdt,
            'time': datetime.now().strftime('%d/%m %H:%M'),
            'sl': stop_loss_price,
            'tp': take_profit_price
        }
        self.log_trade(trade_record)
        
        return True