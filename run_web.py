"""
Script à la racine pour lancer le serveur web Flask sur Railway.
"""

import os
import sys

# S'assurer qu'on est dans le bon répertoire
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Ajouter src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from web_app import app

if __name__ == '__main__':
    # Pour Railway, utiliser le PORT de l'environnement
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Démarrage du serveur web Flask")
    print(f"📱 Port: {port}")
    print(f"📂 Répertoire: {os.getcwd()}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"❌ Erreur au démarrage: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

