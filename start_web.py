"""
Script de démarrage alternatif pour le serveur web.
À utiliser si wsgi.py ne fonctionne pas.
"""

import os
import sys

# Ajouter src au path
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Importer et lancer l'app
from web_app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Démarrage du serveur web sur le port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

