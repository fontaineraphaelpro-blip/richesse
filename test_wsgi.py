"""
Script de test pour vérifier que wsgi.py fonctionne.
"""

import sys
import os

# Ajouter src au path
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

print("Test d'import...")
try:
    from web_app import app
    print("✅ Import réussi")
    print(f"✅ App type: {type(app)}")
    print(f"✅ App name: {app.name}")
    
    # Tester une route
    with app.test_client() as client:
        response = client.get('/health')
        print(f"✅ Route /health: {response.status_code}")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

