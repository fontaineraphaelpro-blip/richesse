"""
Point d'entrée WSGI pour Gunicorn.
Version simplifiée pour garantir le démarrage.
"""

import sys
import os

# Ajouter src au path Python
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Importer l'application Flask
try:
    from web_app import app
    application = app
except Exception as e:
    # En cas d'erreur, créer une application minimale qui fonctionne
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def home():
        return """
        <h1>🚀 Crypto Signal Scanner</h1>
        <p>Le serveur web fonctionne !</p>
        <p>Si vous voyez ce message, l'application principale n'a pas pu être chargée.</p>
        <p>Erreur: {}</p>
        <p><a href="/health">Health Check</a></p>
        """.format(str(e))
    
    @application.route('/health')
    def health():
        return {"status": "partial", "error": str(e)}, 200
