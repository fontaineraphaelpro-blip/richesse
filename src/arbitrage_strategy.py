# -*- coding: utf-8 -*-
"""
Bot d'arbitrage CEX/CEX — autonome, connecté aux APIs publiques.

Compare les prix d'un actif (ex. BTC/USDT) sur plusieurs exchanges via CCXT
(APIs publiques, pas de clé nécessaire pour lire les prix). Quand le spread
dépasse le seuil, signale une opportunité et en paper trading simule l'arbitrage.

Exchanges utilisés par défaut: Binance, KuCoin, Bybit (ticker public).
"""

import time
import logging
from datetime import datetime

# Logs vers le dashboard (liste partagée avec main)
_arbitrage_logs_ref = None

def set_arbitrage_logs(logs_list):
    """À appeler au démarrage pour envoyer les logs vers l'interface."""
    global _arbitrage_logs_ref
    _arbitrage_logs_ref = logs_list

def _log(level, msg):
    if _arbitrage_logs_ref is not None:
        _arbitrage_logs_ref.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'level': level,
            'msg': msg
        })
        # Garder une taille max
        if len(_arbitrage_logs_ref) > 200:
            _arbitrage_logs_ref[:] = _arbitrage_logs_ref[-150:]


def run_arbitrage_autonomous(
    logs_list,
    symbol='BTC/USDT',
    threshold_pct=0.3,
    poll_interval_sec=45,
    paper_trading=True,
):
    """
    Boucle autonome du bot d'arbitrage. Utilise les APIs publiques (CCXT)
    pour récupérer les prix sur plusieurs CEX. Aucune clé API requise.

    Args:
        logs_list: liste partagée pour les logs (ex. shared_data['arbitrage_logs'])
        symbol: paire à surveiller (ex. BTC/USDT, ETH/USDT)
        threshold_pct: seuil de spread en % (ex. 0.3 = 0.3%)
        poll_interval_sec: secondes entre chaque scan
        paper_trading: True = simuler, pas d'ordres réels
    """
    set_arbitrage_logs(logs_list)
    try:
        import ccxt
    except ImportError:
        _log('ERROR', 'ccxt non installé: pip install ccxt')
        return

    # Exchanges en lecture seule (APIs publiques)
    exchange_ids = ['binance', 'kucoin', 'bybit']
    exchanges = []
    for ex_id in exchange_ids:
        try:
            klass = getattr(ccxt, ex_id)
            ex = klass({'enableRateLimit': True})
            exchanges.append(ex)
        except Exception as e:
            _log('WARN', f'Exchange {ex_id} non chargé: {e}')

    if len(exchanges) < 2:
        _log('ERROR', 'Au moins 2 exchanges requis pour l\'arbitrage.')
        return

    _log('INFO', f'Bot arbitrage démarré — {symbol} — seuil {threshold_pct}% — PAPER' if paper_trading else 'LIVE')
    threshold = threshold_pct / 100.0

    while True:
        try:
            prices = {}
            for ex in exchanges:
                try:
                    ticker = ex.fetch_ticker(symbol)
                    last = ticker.get('last')
                    if last is not None and last > 0:
                        prices[ex.id] = last
                except Exception as e:
                    _log('DEBUG', f'{ex.id}: {str(e)[:50]}')

            if len(prices) < 2:
                _log('WARN', 'Pas assez de prix (APIs indisponibles?)')
                time.sleep(poll_interval_sec)
                continue

            best_buy = min(prices.values())
            best_sell = max(prices.values())
            spread = (best_sell - best_buy) / best_buy if best_buy else 0
            spread_pct = spread * 100

            if spread >= threshold:
                buy_ex = next(k for k, v in prices.items() if v == best_buy)
                sell_ex = next(k for k, v in prices.items() if v == best_sell)
                _log('INFO', f'Arbitrage détecté! Spread {spread_pct:.2f}% — Acheter {buy_ex} @ {best_buy:.2f}, Vendre {sell_ex} @ {best_sell:.2f}')
                if paper_trading:
                    _log('INFO', f'[PAPER] Simuler achat sur {buy_ex}, vente sur {sell_ex}')
            else:
                _log('DEBUG', f'Scan — Spread max {spread_pct:.2f}% (seuil {threshold_pct}%)')

        except Exception as e:
            _log('ERROR', str(e)[:100])

        time.sleep(poll_interval_sec)
