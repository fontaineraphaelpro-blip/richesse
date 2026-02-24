# -*- coding: utf-8 -*-
"""
Bot d'arbitrage CEX/CEX — autonome, connecté aux APIs publiques.

Compare les prix d'un actif (ex. BTC/USDT) sur plusieurs exchanges via CCXT
(APIs publiques, pas de clé nécessaire pour lire les prix). Quand le spread
dépasse le seuil, signale une opportunité et en paper trading simule l'arbitrage
avec un capital paper dédié (ex. 100 €).
"""

import time
import os
import json
from datetime import datetime

# Logs vers le dashboard (liste partagée avec main)
_arbitrage_logs_ref = None
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER_ARBITRAGE_FILE = os.path.join(_PROJECT_ROOT, 'paper_arbitrage_wallet.json')
PAPER_ARBITRAGE_INITIAL = 100.0   # 100 € de paper trading pour ce bot
PAPER_TRADE_SIZE_USDT = 10.0     # Montant simulé par opération d'arbitrage

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
        if len(_arbitrage_logs_ref) > 200:
            _arbitrage_logs_ref[:] = _arbitrage_logs_ref[-150:]


def _load_paper_wallet():
    """Charge le portefeuille paper arbitrage (100 € au premier run)."""
    if os.path.exists(PAPER_ARBITRAGE_FILE):
        try:
            with open(PAPER_ARBITRAGE_FILE, 'r') as f:
                data = json.load(f)
            return float(data.get('USDT', PAPER_ARBITRAGE_INITIAL)), data.get('trades', [])
        except Exception:
            pass
    return PAPER_ARBITRAGE_INITIAL, []


def _save_paper_wallet(balance_usdt, trades_list):
    """Sauvegarde le portefeuille paper arbitrage."""
    data = {
        'USDT': round(balance_usdt, 2),
        'initial': PAPER_ARBITRAGE_INITIAL,
        'trades': trades_list[-100:],
    }
    with open(PAPER_ARBITRAGE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def run_arbitrage_autonomous(
    logs_list,
    symbol='BTC/USDT',
    threshold_pct=0.3,
    poll_interval_sec=45,
    paper_trading=True,
    shared_data=None,
):
    """
    Boucle autonome du bot d'arbitrage. Capital paper dédié 100 € (fichier paper_arbitrage_wallet.json).
    shared_data: si fourni, met à jour shared_data['arbitrage_paper_balance'] et ['arbitrage_paper_trades'].
    """
    set_arbitrage_logs(logs_list)
    try:
        import ccxt
    except ImportError:
        _log('ERROR', 'ccxt non installé. Installez: pip install ccxt')
        _log('INFO', 'Bot arbitrage actif mais en attente (installez ccxt puis redémarrez).')
        while True:
            time.sleep(60)
            _log('WARN', 'Toujours sans ccxt — pip install ccxt puis redémarrer run.py')

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
        _log('ERROR', 'Au moins 2 exchanges requis. Bot arbitrage actif, réessaie au prochain cycle.')
        while True:
            time.sleep(poll_interval_sec)
            _log('INFO', 'En attente de 2+ exchanges (redémarrez après avoir installé ccxt / corrigé les APIs)...')

    paper_balance, paper_trades = _load_paper_wallet()
    if shared_data is not None:
        shared_data['arbitrage_paper_balance'] = paper_balance
        shared_data['arbitrage_paper_trades'] = paper_trades

    _log('INFO', f'Bot arbitrage démarré — {symbol} — seuil {threshold_pct}% — PAPER 100 €')
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
                    # Simuler gain: taille fixe * spread %
                    profit = PAPER_TRADE_SIZE_USDT * (spread_pct / 100.0)
                    profit = round(profit, 2)
                    paper_balance += profit
                    trade_record = {
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'buy_ex': buy_ex,
                        'sell_ex': sell_ex,
                        'spread_pct': round(spread_pct, 2),
                        'profit_usdt': profit,
                        'balance_after': round(paper_balance, 2),
                    }
                    paper_trades.append(trade_record)
                    _save_paper_wallet(paper_balance, paper_trades)
                    if shared_data is not None:
                        shared_data['arbitrage_paper_balance'] = paper_balance
                        shared_data['arbitrage_paper_trades'] = paper_trades
                    _log('INFO', f'[PAPER] +{profit} € — Solde: {paper_balance:.2f} €')
            else:
                _log('INFO', f'Scan — Spread max {spread_pct:.2f}% (seuil {threshold_pct}%) — pas d\'opportunité')
            if shared_data is not None:
                shared_data['arbitrage_paper_balance'] = paper_balance
        except Exception as e:
            _log('ERROR', str(e)[:100])

        time.sleep(poll_interval_sec)
