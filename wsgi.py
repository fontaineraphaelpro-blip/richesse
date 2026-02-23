"""
Point d'entrée WSGI pour Gunicorn (production).
Délègue à l'application principale (Scanner Ultime / Micro Scalp Bot) dans src/main.py.
"""

import sys
import os
import threading

base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import de l'app et du scanner depuis le module principal
from main import app, run_loop

# Démarrer le scanner en arrière-plan (comme run.py)
scanner_thread = threading.Thread(target=run_loop, daemon=True)
scanner_thread.start()

# Exporter pour Gunicorn
application = app
