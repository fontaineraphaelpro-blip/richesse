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

print(f"📂 Répertoire de travail: {os.getcwd()}")
print(f"📂 Chemin src: {src_dir}")
print(f"📂 Fichier web_app.py existe: {os.path.exists(os.path.join(src_dir, 'web_app.py'))}")

try:
    # Importer l'application Flask
    from web_app import app
    print("✅ Import de web_app réussi")
    
    # Exporter pour Gunicorn
    application = app
    print("✅ Application exportée pour Gunicorn")
except Exception as e:
    print(f"❌ Erreur lors de l'import: {e}")
    import traceback
    traceback.print_exc()
    # Créer une application minimale pour éviter le crash
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def error():
        return f"❌ Erreur: Impossible de charger l'application. {str(e)}", 500
    
    @application.route('/health')
    def health():
        return {"status": "error", "error": str(e)}, 500

