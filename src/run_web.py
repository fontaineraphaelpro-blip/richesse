"""
Script pour lancer le serveur web Flask.
À utiliser pour afficher le dashboard dans un navigateur.
"""

import os
import sys

# Ajouter le répertoire courant au path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Importer l'app
try:
    from web_app import app
except ImportError:
    # Essayer avec src.web_app
    try:
        from src.web_app import app
    except ImportError:
        # Dernier essai avec import direct
        import importlib.util
        spec = importlib.util.spec_from_file_location("web_app", os.path.join(current_dir, "web_app.py"))
        web_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web_app)
        app = web_app.app

if __name__ == '__main__':
    # Pour Railway, utiliser le PORT de l'environnement
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Démarrage du serveur web sur le port {port}")
    print(f"📱 Dashboard accessible sur http://0.0.0.0:{port}")
    print(f"📂 Répertoire de travail: {os.getcwd()}")
    print(f"📂 Fichier web_app.py existe: {os.path.exists(os.path.join(current_dir, 'web_app.py'))}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"❌ Erreur au démarrage du serveur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

