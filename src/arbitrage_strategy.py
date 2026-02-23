
"""
arbitrage_strategy.py

Bot d'arbitrage simple pour détecter et exploiter les écarts de prix entre deux exchanges.
Ce module fonctionne indépendamment du bot de trading principal.
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
        # À compléter selon le DEX (Uniswap, PancakeSwap, etc.)
        prices = {}
        for dex in self.dex_exchanges:
            # Ici, il faudrait appeler le smart contract du DEX pour obtenir le prix
            # Placeholder: prix fictif
            prices[dex['name']] = None
        return prices

    def scan_all(self):
        cex_prices = self.get_cex_prices()
        dex_prices = self.get_dex_prices()
        all_prices = {**cex_prices, **dex_prices}
        return all_prices

    def find_arbitrage(self, all_prices):
        best_buy = min((v for v in all_prices.values() if v), default=None)
        best_sell = max((v for v in all_prices.values() if v), default=None)
        if best_buy is None or best_sell is None:
            return None, None, 0
        spread = (best_sell - best_buy) / best_buy
        if spread >= self.threshold:
            buy_ex = [k for k, v in all_prices.items() if v == best_buy][0]
            sell_ex = [k for k, v in all_prices.items() if v == best_sell][0]
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

# Exemple de configuration (à remplacer par vos vraies clés et RPC)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cex_configs = [
        {'id': 'binance', 'apiKey': 'VOTRE_API_KEY', 'secret': 'VOTRE_SECRET'},
        {'id': 'kucoin', 'apiKey': 'VOTRE_API_KEY', 'secret': 'VOTRE_SECRET'},
        # Ajoutez d'autres exchanges ici
    ]
    dex_configs = [
        {'name': 'uniswap', 'rpc_url': 'https://mainnet.infura.io/v3/VOTRE_INFURA_KEY', 'router_address': '0x...'},
        # Ajoutez d'autres DEX ici
    ]
    bot = MultiExchangeArbitrageBot(
        cex_configs, dex_configs, 'ETH/USDT', threshold=0.01, trade_amount=0.05, paper_trading=True
    )
    try:
        bot.start(poll_interval=10)
    except KeyboardInterrupt:
        bot.stop()
