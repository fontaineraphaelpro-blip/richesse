"""
Script pour lancer à la fois le scanner et le serveur web.
Utile pour le développement local.
"""

import threading
import time
import os
from web_app import app
from main import main as scanner_main


def run_scanner():
    """Lance le scanner en arrière-plan."""
    scanner_main()


def run_web():
    """Lance le serveur web Flask."""
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Serveur web démarré sur http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    print("🚀 Démarrage du Crypto Signal Scanner avec interface web")
    print("="*60)
    
    # Lancer le scanner dans un thread séparé
    scanner_thread = threading.Thread(target=run_scanner, daemon=True)
    scanner_thread.start()
    
    # Lancer le serveur web (bloquant)
    run_web()

