
"""
arbitrage_strategy.py

Bot d'arbitrage CEX/CEX ou CEX/DEX: acheter sur l'exchange le moins cher,
vendre sur le plus cher quand le spread dépasse un seuil.

Rentabilité: le threshold (ex: 0.5% ou 1%) doit être supérieur aux frais
des deux côtés (maker/taker) pour dégager un gain net.
Fonctionne actuellement entre plusieurs CEX; les prix DEX sont à brancher (get_dex_prices).
Ce module est indépendant du bot Micro Scalp (main.py).
"""


import time
import logging
import ccxt
from web3 import Web3
from datetime import datetime

# Pour journaliser dans l'interface web (dashboard principal)
try:
    from main import shared_data
    arbitrage_logs = shared_data.get('arbitrage_logs', [])
except ImportError:
    arbitrage_logs = None
    try:
        from wsgi import arbitrage_logs
    except ImportError:
        pass

class MultiExchangeArbitrageBot:
    def __init__(self, cex_configs, dex_configs, symbol, threshold=0.002, trade_amount=0.1, paper_trading=True):
        """
        cex_configs: liste de dicts { 'id': 'binance', 'apiKey': '...', 'secret': '...' }
        dex_configs: liste de dicts { 'name': 'uniswap', 'rpc_url': '...', ... }
        symbol: le symbole à trader (ex: 'ETH/USDT')
        threshold: écart minimum (en %) pour déclencher l'arbitrage
        trade_amount: montant à trader
        """
        self.cex_configs = cex_configs
        self.dex_configs = dex_configs
        self.symbol = symbol
        self.threshold = threshold
        self.trade_amount = trade_amount
        self.running = False
        self.logger = logging.getLogger('MultiExchangeArbitrageBot')
        self.paper_trading = paper_trading
        self.cex_exchanges = self._init_cex_exchanges()
        self.dex_exchanges = self._init_dex_exchanges()

    def _init_cex_exchanges(self):
        exchanges = []
        for conf in self.cex_configs:
            ex = getattr(ccxt, conf['id'])({
                'apiKey': conf.get('apiKey'),
                'secret': conf.get('secret'),
                'enableRateLimit': True
            })
            exchanges.append(ex)
        return exchanges

    def _init_dex_exchanges(self):
        # Pour Uniswap v2/v3, PancakeSwap, etc. (exemple de base)
        dexes = []
        for conf in self.dex_configs:
            w3 = Web3(Web3.HTTPProvider(conf['rpc_url']))
            dexes.append({'name': conf['name'], 'web3': w3, 'router_address': conf.get('router_address')})
        return dexes

    def get_cex_prices(self):
        prices = {}
        for ex in self.cex_exchanges:
            try:
                ticker = ex.fetch_ticker(self.symbol)
                prices[ex.id] = ticker['last']
            except Exception as e:
                self.logger.warning(f"Erreur prix {ex.id}: {e}")
        return prices

    def get_dex_prices(self):
        """Prix DEX (Uniswap, etc.). À implémenter selon le router du DEX."""
        prices = {}
        for dex in self.dex_exchanges:
            # TODO: appeler le smart contract (router) pour obtenir le prix spot
            prices[dex['name']] = None
        return prices

    def scan_all(self):
        cex_prices = self.get_cex_prices()
        dex_prices = self.get_dex_prices()
        all_prices = {**cex_prices, **dex_prices}
        return all_prices

    def find_arbitrage(self, all_prices):
        """Trouve une opportunité: acheter au moins cher, vendre au plus cher si spread >= threshold."""
        valid_prices = {k: v for k, v in all_prices.items() if v is not None and v > 0}
        if len(valid_prices) < 2:
            return None, None, 0.0
        best_buy = min(valid_prices.values())
        best_sell = max(valid_prices.values())
        spread = (best_sell - best_buy) / best_buy if best_buy else 0
        if spread >= self.threshold:
            buy_ex = next(k for k, v in valid_prices.items() if v == best_buy)
            sell_ex = next(k for k, v in valid_prices.items() if v == best_sell)
            if buy_ex != sell_ex:
                return buy_ex, sell_ex, spread
        return None, None, spread

    def log_web(self, level, msg):
        if arbitrage_logs is not None:
            arbitrage_logs.append({
                'time': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'level': level,
                'msg': msg
            })

    def execute_arbitrage(self, buy_ex, sell_ex):
        log_msg = f"Arbitrage: Acheter sur {buy_ex}, vendre sur {sell_ex} (montant: {self.trade_amount} {self.symbol})"
        self.logger.info(log_msg)
        self.log_web('INFO', log_msg)
        if self.paper_trading:
            sim_msg = f"[PAPER] Simuler achat sur {buy_ex}, vente sur {sell_ex}"
            self.logger.info(sim_msg)
            self.log_web('INFO', sim_msg)
        else:
            # À compléter: placer les ordres réels sur les exchanges concernés
            pass

    def start(self, poll_interval=5):
        self.running = True
        self.logger.info("Multi-exchange arbitrage bot started.")
        self.log_web('INFO', "Multi-exchange arbitrage bot started.")
        while self.running:
            try:
                all_prices = self.scan_all()
                buy_ex, sell_ex, spread = self.find_arbitrage(all_prices)
                if buy_ex and sell_ex:
                    msg = f"Arbitrage détecté! Spread: {spread*100:.2f}% entre {buy_ex} et {sell_ex}"
                    self.logger.info(msg)
                    self.log_web('INFO', msg)
                    self.execute_arbitrage(buy_ex, sell_ex)
                else:
                    debug_msg = f"Aucune opportunité. Spread max: {spread*100:.2f}%"
                    self.logger.debug(debug_msg)
                    self.log_web('DEBUG', debug_msg)
                time.sleep(poll_interval)
            except Exception as e:
                err_msg = f"Erreur: {e}"
                self.logger.error(err_msg)
                self.log_web('ERROR', err_msg)
                time.sleep(5)

    def stop(self):
        self.running = False
        self.logger.info("Arbitrage bot stopped.")

# Exemple de configuration (threshold > frais pour être rentable, ex: 0.5% à 1%)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cex_configs = [
        {'id': 'binance', 'apiKey': 'VOTRE_API_KEY', 'secret': 'VOTRE_SECRET'},
        {'id': 'kucoin', 'apiKey': 'VOTRE_API_KEY', 'secret': 'VOTRE_SECRET'},
    ]
    dex_configs = [
        {'name': 'uniswap', 'rpc_url': 'https://mainnet.infura.io/v3/VOTRE_INFURA_KEY', 'router_address': '0x...'},
    ]
    # threshold=0.005 = 0.5% (rentable si frais totaux < 0.5%)
    bot = MultiExchangeArbitrageBot(
        cex_configs, dex_configs, 'ETH/USDT', threshold=0.005, trade_amount=0.05, paper_trading=True
    )
    try:
        bot.start(poll_interval=10)
    except KeyboardInterrupt:
        bot.stop()
