"""
Point d'entrée WSGI pour Gunicorn (production).
Lance les 2 bots autonomes: trading (SHORT) + arbitrage (APIs publiques).
"""

import sys
import os
import threading

base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from main import app, run_loop, shared_data
from arbitrage_strategy import run_arbitrage_autonomous

# Bot 1: scanner SHORT grandes baisses
scanner_thread = threading.Thread(target=run_loop, daemon=True)
scanner_thread.start()

# Bot 2: arbitrage CEX (APIs publiques, paper)
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

application = app
