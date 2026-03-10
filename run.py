#!/usr/bin/env python3
"""
Point d'entrée — lance les 2 bots en paper trading de façon autonome:
  • Bot de trading (SHORT grandes baisses) — scan Binance, ouvre des shorts en paper
  • Bot d'arbitrage — compare les prix sur Binance, KuCoin, Bybit via APIs publiques
"""

import sys
import os
import threading

# Ajouter src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == '__main__':
    from main import app, run_loop, shared_data
    from arbitrage_strategy import run_arbitrage_autonomous

    env = os.environ.get('ENV', 'development').lower()
    paper = os.environ.get('PAPER_TRADING', 'true').lower() in ('1', 'true', 'yes')
    port = int(os.environ.get('PORT', 8080))
    scan_interval = int(os.environ.get('SCAN_INTERVAL', '900'))
    arb_symbol = os.environ.get('ARBITRAGE_SYMBOL', 'BTC/USDT')
    arb_threshold = os.environ.get('ARBITRAGE_THRESHOLD_PCT', '0.3')
    arb_poll = os.environ.get('ARBITRAGE_POLL_SEC', '45')

    # Lancer le bot de trading (SHORT) en arrière-plan
    scanner_thread = threading.Thread(target=run_loop, daemon=True)
    scanner_thread.start()

    # Lancer le bot d'arbitrage (APIs publiques)
    arbitrage_thread = threading.Thread(
        target=run_arbitrage_autonomous,
        kwargs={
            'logs_list': shared_data['arbitrage_logs'],
            'symbol': arb_symbol,
            'threshold_pct': float(arb_threshold),
            'poll_interval_sec': int(arb_poll),
            'paper_trading': paper,
            'shared_data': shared_data,
        },
        daemon=True,
    )
    arbitrage_thread.start()

    # Affichage terminal
    mode = 'PRODUCTION' if env == 'production' else 'PAPER TRADING'
    scan_min = scan_interval // 60
    print()
    print("  " + "=" * 56)
    print("  RICHESSE CRYPTO — 2 BOTS AUTONOMES")
    print("  " + "=" * 56)
    print("  Mode          " + mode)
    print("  Dashboard     http://localhost:{}  (Ctrl+C pour arreter)".format(port))
    print()
    print("  Bot 1 — Setup Sniper (multi-filtre, score>=7, top 3)")
    print("    Timeframe 15m | Scan toutes les {} s | Risk 1% | SL ATR | TP 2:1".format(scan_interval))
    print("    Binance USDT | Vol 24h>20M | Max 5 positions")
    print()
    print("  Bot 2 — Arbitrage CEX")
    print("    {} | Seuil {}% | Poll {} s | Paper {}".format(arb_symbol, arb_threshold, arb_poll, "OUI" if paper else "NON"))
    print("    Exchanges: Binance, KuCoin, Bybit")
    print()
    print("  Logs: [INFO] [TRADE] [WARN] ci-dessous.")
    print("  " + "=" * 56)
    print()

    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
