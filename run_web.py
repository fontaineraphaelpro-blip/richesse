"""
Script à la racine pour lancer le serveur web Flask sur Railway.
"""

import os
import sys

# S'assurer qu'on est dans le bon répertoire
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Ajouter src au path
src_path = os.path.join(script_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print(f"📂 Répertoire de travail: {os.getcwd()}")
print(f"📂 Chemin src: {src_path}")
print(f"📂 Fichier web_app.py existe: {os.path.exists(os.path.join(src_path, 'web_app.py'))}")

try:
    from web_app import app
    print("✅ Import de web_app réussi")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print(f"📂 sys.path: {sys.path}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == '__main__':
    # En production, utiliser Gunicorn (défini dans Procfile)
    # Ce code ne sera utilisé qu'en développement local
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Démarrage du serveur web Flask (mode développement)")
    print(f"📱 Port: {port}")
    print(f"⚠️ Pour la production, utilisez Gunicorn via le Procfile")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        print(f"❌ Erreur au démarrage: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

