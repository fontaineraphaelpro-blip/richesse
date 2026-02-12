"""
Module de Paper Trading (Simulation de Portefeuille).
Gère :
- Le solde USDT.
- Les positions ouvertes (Entry, Quantity, SL, TP).
- L'historique des trades (Journal).
- La fermeture automatique des positions (Stop Loss / Take Profit).
"""

import json
import os
from datetime import datetime

class PaperTrader:
    def __init__(self, initial_balance=1000):
        # Fichiers de stockage (base de données locale)
        self.balance_file = 'paper_wallet.json'
        self.trades_file = 'paper_trades.json'
        
        # Initialisation ou Chargement du portefeuille
        if os.path.exists(self.balance_file):
            try:
                with open(self.balance_file, 'r') as f:
                    self.wallet = json.load(f)
            except json.JSONDecodeError:
                # Si fichier corrompu, on reset
                self.wallet = {'USDT': initial_balance, 'positions': {}}
        else:
            self.wallet = {'USDT': initial_balance, 'positions': {}}
            self.save_wallet()

    def save_wallet(self):
        """Sauvegarde l'état actuel du portefeuille dans le JSON."""
        with open(self.balance_file, 'w') as f:
            json.dump(self.wallet, f, indent=4)

    def log_trade(self, trade_data):
        """Enregistre une transaction dans l'historique."""
        history = []
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, 'r') as f:
                    history = json.load(f)
            except: pass
        
        # Ajout du nouveau trade au début de la liste
        history.insert(0, trade_data)
        
        with open(self.trades_file, 'w') as f:
            json.dump(history, f, indent=4)

    def get_usdt_balance(self):
        """Retourne le solde disponible pour trader."""
        return self.wallet.get('USDT', 0)

    def get_open_positions(self):
        """Retourne le dictionnaire des positions ouvertes."""
        return self.wallet.get('positions', {})
        
    def get_trades_history(self):
        """Retourne tout l'historique des transactions."""
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, 'r') as f:
                    return json.load(f)
            except: return []
        return []

    def place_buy_order(self, symbol, amount_usdt, current_price, stop_loss_price, take_profit_price):
        """
        Exécute un ordre d'ACHAT (Simulation).
        """
        # 1. Vérification du solde
        if self.wallet['USDT'] < amount_usdt:
            print(f"❌ Fonds insuffisants pour {symbol} (Requis: {amount_usdt}, Dispo: {self.wallet['USDT']})")
            return False

        # 2. Calcul de la quantité (Ex: 100 USDT de BTC à 50000$ = 0.002 BTC)
        # Levier 10x appliqué
        quantity = (amount_usdt / current_price) * 10
        
        # 3. Mise à jour du portefeuille
        self.wallet['USDT'] -= amount_usdt
        self.wallet['positions'][symbol] = {
            'amount_usdt': amount_usdt,      # Montant investi
            'quantity': quantity,            # Quantité de tokens
            'entry_price': current_price,
            'entry_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price
        }
        self.save_wallet()
        
        # 4. Log
        self.log_trade({
            'type': 'ACHAT',
            'symbol': symbol,
            'price': current_price,
            'amount': amount_usdt,
            'quantity': quantity,
            'time': datetime.now().strftime('%d/%m %H:%M'),
            'pnl': 0,
            'pnl_percent': 0
        })
        print(f"🛒 ACHAT CONFIRMÉ : {symbol} | Prix: ${current_price} | Investi: ${amount_usdt}")
        return True

    def close_position(self, symbol, current_price, reason="MANUAL"):
        """
        Exécute un ordre de VENTE (Clôture de position).
        Calcule le PnL (Profit and Loss).
        """
        if symbol not in self.wallet['positions']:
            return False

        # Récupération des données de la position
        pos = self.wallet['positions'][symbol]
        quantity = pos['quantity']
        entry_amount = pos['amount_usdt']
        
        # 1. Calcul de la valeur de sortie
        exit_value = quantity * current_price
        
        # 2. Calcul du PnL
        pnl_value = exit_value - entry_amount
        pnl_percent = ((exit_value - entry_amount) / entry_amount) * 100
        
        # 3. Mise à jour du portefeuille (Récupération du cash)
        self.wallet['USDT'] += exit_value
        del self.wallet['positions'][symbol] # Suppression de la position
        self.save_wallet()
        
        # 4. Log
        log_entry = {
            'type': f'VENTE ({reason})',
            'symbol': symbol,
            'price': current_price,
            'amount': round(exit_value, 2),
            'quantity': quantity,
            'time': datetime.now().strftime('%d/%m %H:%M'),
            'pnl': round(pnl_value, 2),
            'pnl_percent': round(pnl_percent, 2)
        }
        self.log_trade(log_entry)
        
        # Affichage Terminal avec couleurs simulées
        status = "✅ GAIN" if pnl_value > 0 else "❌ PERTE"
        print(f"💰 VENTE {symbol} ({reason}) | {status}: ${pnl_value:.2f} ({pnl_percent:.2f}%)")
        return True

    def check_positions(self, real_prices: dict):
        """
        Vérifie toutes les positions ouvertes par rapport aux prix actuels.
        Déclenche la vente si SL ou TP touché.
        
        Args:
            real_prices: Dictionnaire { 'BTCUSDT': 65000.50, ... }
        """
        # On stocke les positions à fermer pour ne pas modifier le dictionnaire pendant qu'on boucle dessus
        positions_to_close = []
        
        for symbol, pos in self.wallet['positions'].items():
            current_price = real_prices.get(symbol)
            
            # Si on n'a pas le prix actuel (ex: erreur API), on passe
            if not current_price:
                continue
            
            stop_loss = pos['stop_loss']
            take_profit = pos['take_profit']
            
            # --- Règle 1 : Stop Loss touché ? ---
            # Pour un LONG : Si prix <= SL, on vend
            if current_price <= stop_loss:
                positions_to_close.append((symbol, current_price, "STOP LOSS 🛑"))
            
            # --- Règle 2 : Take Profit touché ? ---
            # Pour un LONG : Si prix >= TP, on vend
            elif current_price >= take_profit:
                positions_to_close.append((symbol, current_price, "TAKE PROFIT 🎯"))

        # Exécution des fermetures
        for symbol, price, reason in positions_to_close:
            self.close_position(symbol, price, reason)
