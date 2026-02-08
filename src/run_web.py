"""
Script pour lancer le serveur web Flask.
À utiliser pour afficher le dashboard dans un navigateur.
"""

from web_app import app
import os

if __name__ == '__main__':
    # Pour Railway, utiliser le PORT de l'environnement
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Démarrage du serveur web sur le port {port}")
    print(f"📱 Accédez au dashboard: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)

