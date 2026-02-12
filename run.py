#!/usr/bin/env python3
"""
Point d'entrée simple pour lancer le bot de paper trading.
Utilise src/main.py
"""

import sys
import os

# Ajouter src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Lancer le bot principal
if __name__ == '__main__':
    from main import app, run_loop
    import threading
    
    print("\n" + "="*70)
    print("🦁 SWING BOT PAPER TRADING - DÉMARRAGE")
    print("="*70)
    print("✅ Scanner thread en arrière-plan")
    print("✅ Dashboard Web sur http://localhost:8080")
    print("✅ API temps réel sur http://localhost:8080/api/data")
    print("="*70 + "\n")
    
    # Lancer le scanner en arrière-plan
    scanner_thread = threading.Thread(target=run_loop, daemon=True)
    scanner_thread.start()
    
    # Lancer le serveur Flask
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
