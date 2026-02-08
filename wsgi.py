"""
Fichier WSGI pour Gunicorn en production.
Point d'entrée simple et direct.
"""

import os
import sys

# Ajouter src au path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(script_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Importer l'application Flask
from web_app import app

# Exporter pour Gunicorn
application = app

if __name__ == '__main__':
    # Pour le développement local uniquement
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Mode développement - Serveur Flask")
    app.run(host='0.0.0.0', port=port, debug=True)

