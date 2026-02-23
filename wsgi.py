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

# Config depuis variables d'environnement (production)
def _env_bool(key, default='true'):
    return os.environ.get(key, default).lower() in ('1', 'true', 'yes')

paper_trading = _env_bool('PAPER_TRADING', 'true')
arbitrage_symbol = os.environ.get('ARBITRAGE_SYMBOL', 'BTC/USDT')
arbitrage_threshold = float(os.environ.get('ARBITRAGE_THRESHOLD_PCT', '0.3'))
arbitrage_poll = int(os.environ.get('ARBITRAGE_POLL_SEC', '45'))

# Bot 1: scanner SHORT grandes baisses
scanner_thread = threading.Thread(target=run_loop, daemon=True)
scanner_thread.start()

# Bot 2: arbitrage CEX
arbitrage_thread = threading.Thread(
    target=run_arbitrage_autonomous,
    kwargs={
        'logs_list': shared_data['arbitrage_logs'],
        'symbol': arbitrage_symbol,
        'threshold_pct': arbitrage_threshold,
        'poll_interval_sec': arbitrage_poll,
        'paper_trading': paper_trading,
        'shared_data': shared_data,
    },
    daemon=True,
)
arbitrage_thread.start()

application = app
