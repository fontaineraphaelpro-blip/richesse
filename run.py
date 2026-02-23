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

    # Lancer le bot de trading (SHORT) en arrière-plan
    scanner_thread = threading.Thread(target=run_loop, daemon=True)
    scanner_thread.start()

    # Lancer le bot d'arbitrage (APIs publiques, paper trading) en arrière-plan
    arbitrage_thread = threading.Thread(
        target=run_arbitrage_autonomous,
        kwargs={
            'logs_list': shared_data['arbitrage_logs'],
            'symbol': 'BTC/USDT',
            'threshold_pct': 0.3,
            'poll_interval_sec': 45,
            'paper_trading': True,
        },
        daemon=True,
    )
    arbitrage_thread.start()

    port = int(os.environ.get('PORT', 8080))
    print("\n" + "="*60)
    print("  2 BOTS AUTONOMES — PAPER TRADING")
    print("="*60)
    print("  Bot 1: SHORT grandes baisses (Binance 15m)")
    print("  Bot 2: Arbitrage CEX (Binance / KuCoin / Bybit — APIs publiques)")
    print("  Dashboard: http://localhost:{}".format(port))
    print("="*60 + "\n")

    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
