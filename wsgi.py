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
try:
    from web_app import app
    application = app
except ImportError as e:
    # Si l'import échoue, essayer avec le chemin complet
    import importlib.util
    web_app_path = os.path.join(src_dir, 'web_app.py')
    if os.path.exists(web_app_path):
        spec = importlib.util.spec_from_file_location("web_app", web_app_path)
        web_app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web_app_module)
        application = web_app_module.app
    else:
        # Créer une application minimale en dernier recours
        from flask import Flask
        application = Flask(__name__)
        
        @application.route('/')
        def error():
            return f"❌ Erreur: Impossible de charger web_app.py. {str(e)}", 500
        
        @application.route('/health')
        def health():
            return {"status": "error", "error": str(e)}, 500
except Exception as e:
    # Créer une application minimale pour éviter le crash
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def error():
        return f"❌ Erreur: {str(e)}", 500
    
    @application.route('/health')
    def health():
        return {"status": "error", "error": str(e)}, 500

