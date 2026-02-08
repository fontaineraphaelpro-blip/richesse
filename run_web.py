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
    # Exporter l'app pour Gunicorn (toujours disponible au niveau module)
    application = app
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print(f"📂 sys.path: {sys.path}")
    import traceback
    traceback.print_exc()
    # Créer une application vide pour éviter l'erreur Gunicorn
    from flask import Flask
    application = Flask(__name__)
    @application.route('/')
    def error():
        return "❌ Erreur: Impossible de charger l'application", 500

if __name__ == '__main__':
    # Détecter si on est en production (Railway, Heroku, etc.)
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('DYNO') or os.environ.get('PORT')
    
    if is_production:
        # En production, lancer Gunicorn automatiquement
        print("🚀 Mode PRODUCTION détecté - Lancement de Gunicorn")
        port = int(os.environ.get('PORT', 8080))
        
        try:
            import gunicorn.app.wsgiapp as wsgi
            
            # Configuration Gunicorn
            sys.argv = [
                'gunicorn',
                '--bind', f'0.0.0.0:{port}',
                '--workers', '2',
                '--threads', '2',
                '--timeout', '120',
                '--access-logfile', '-',
                '--error-logfile', '-',
                '--log-level', 'info',
                '--worker-class', 'gthread',
                'run_web:application'
            ]
            
            wsgi.run()
        except ImportError:
            print("❌ Gunicorn non installé, utilisation du serveur Flask (non recommandé en production)")
            app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        except Exception as e:
            print(f"❌ Erreur au démarrage Gunicorn: {e}")
            import traceback
            traceback.print_exc()
            # Fallback sur Flask si Gunicorn échoue
            print("⚠️ Fallback sur serveur Flask...")
            app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    else:
        # Mode développement local
        port = int(os.environ.get('PORT', 5000))
        print(f"🌐 Démarrage du serveur web Flask (mode développement)")
        print(f"📱 Port: {port}")
        
        try:
            app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        except Exception as e:
            print(f"❌ Erreur au démarrage: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

