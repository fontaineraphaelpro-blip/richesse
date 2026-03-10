"""
Point d'entrée WSGI pour Gunicorn (production).
Lance le Setup Sniper uniquement.
"""

import sys
import os
import threading

base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from main import app, run_loop

scanner_thread = threading.Thread(target=run_loop, daemon=True)
scanner_thread.start()

application = app
