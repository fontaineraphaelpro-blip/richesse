"""
Point d'entrée WSGI pour Gunicorn.
Simple et direct.
"""

import sys
import os

# Ajouter src au path Python
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Importer l'application Flask
from web_app import app

# Exporter pour Gunicorn
application = app

