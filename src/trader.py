"""
Module de Paper Trading (Simulation) - Version Indépendante & Robuste
Gère Entrées (Achat) ET Sorties (SL/TP) avec gestion d'erreurs et persistance.
"""
import json
import os
from datetime import datetime

class PaperTrader:
    def __init__(self, initial_balance=None):
        # Utilisation d'un dossier 'data' pour la propreté (utile pour les Volumes Railway)
        self.data_dir = 'data'
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        self.balance_file = os.path.join(self.data_dir, 'paper_wallet.json')
        self.trades_file = os.path.join(self.data_dir, 'paper_trades.json')
        
        # Récupère le solde initial depuis l'environnement ou utilise 1000$ par défaut
        if initial_balance is None:
            initial_balance = float(os.environ.get('INITIAL_BALANCE', 1000))
        
        self.wallet = self._load_wallet(initial_balance)

    def _load_wallet(self, initial_balance):
        """Charge le portefeuille de manière sécurisée."""
        if os.path.exists(self.balance_file):
            try:
                with open(self.balance_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print("⚠️ Erreur lecture wallet, création d'un nouveau.")
        
        # Création d'un nouveau wallet si fichier absent ou corrompu
        new_wallet = {'USDT': initial_balance, 'positions': {}}
        self.save_wallet(new_wallet)
        return new_wallet

    def save_wallet(self, wallet_to_save=None):
        if wallet_to_save:
            self.wallet = wallet_to_save
        try:
            with open(self.balance_file, 'w') as f:
                json.dump(self.wallet, f, indent=4)
        except Exception as e:
            print(f"❌ Erreur sauvegarde wallet: {e}")

    def log_trade(self, trade_data):
        history = []
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        history.insert(0, trade_data)
        
        # OPTIMISATION : On ne garde que les 100 derniers trades pour économiser l'espace
        history = history[:100]
        
        try:
            with open(self.trades_file, 'w') as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            print(f"❌ Erreur sauvegarde trade: {e}")

    def get_usdt_balance(self):
        return self.wallet.get('USDT', 0)

    def get_open_positions(self):
        return self.wallet.get('positions', {})
        
    def get_trades_history(self):
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def check_positions(self, current_prices):
        """
        Vérifie si les positions ouvertes doivent être fermées (TP ou SL).
        """
        positions = self.wallet.get('positions', {})
        positions_to_close = []
        wallet_modified = False
        
        for symbol, pos in positions.items():
            current_price = current_prices.get(symbol)
            
            # Si pas de prix actuel, on ignore
            if not current_price: continue
            
            sl = pos.get('stop_loss')
            tp = pos.get('take_profit')
            quantity = pos.get('quantity')
            entry_cost = pos.get('entry_cost')
            
            exit_type = None
            exit_reason = ""
            
            # Vérifications
            if sl and current_price <= sl:
                exit_type = 'VENTE (SL)'
                exit_reason = f"🛑 Stop Loss touché à ${current_price}"
            elif tp and current_price >= tp:
                exit_type = 'VENTE (TP)'
                exit_reason = f"✅ Take Profit touché à ${current_price}"
            
            if exit_type:
                amount_recovered = quantity * current_price
                pnl = amount_recovered - entry_cost
                
                print(f"{exit_reason} sur {symbol} | PnL: {pnl:.2f} USDT")
                
                # Mise à jour en mémoire
                self.wallet['USDT'] += amount_recovered
                wallet_modified = True
                
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
        
        # Nettoyage
        for symbol in positions_to_close:
            del self.wallet['positions'][symbol]
            
        if wallet_modified:
            self.save_wallet()

    def place_buy_order(self, symbol, amount_usdt, current_price, stop_loss_price, take_profit_price):
        """Simule un ordre d'achat."""
        if self.wallet['USDT'] < amount_usdt:
            print(f"⚠️ Fonds insuffisants pour {symbol}")
            return False

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
