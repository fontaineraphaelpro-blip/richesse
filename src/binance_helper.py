"""
Helper pour initialiser le client Binance avec meilleure gestion d'erreur.
"""

import os
from binance.client import Client
from binance.exceptions import BinanceAPIException


def create_binance_client():
    """
    Crée un client Binance avec gestion d'erreur améliorée.
    
    Returns:
        Client Binance ou None si échec
    """
    try:
        api_key = os.environ.get('BINANCE_API_KEY')
        api_secret = os.environ.get('BINANCE_API_SECRET')
        
        # Configuration avec timeout
        config = {
            'requests_params': {
                'timeout': 10
            }
        }
        
        if api_key and api_secret:
            client = Client(api_key=api_key, api_secret=api_secret, **config)
            print("✅ Client Binance initialisé avec clés API")
        else:
            client = Client(**config)
            print("✅ Client Binance initialisé (mode public)")
        
        # Tester la connexion (mais ne pas bloquer si échoue)
        try:
            # Utiliser get_server_time au lieu de ping (plus fiable)
            server_time = client.get_server_time()
            print(f"✅ Connexion Binance OK (server time: {server_time})")
        except Exception as test_error:
            print(f"⚠️ Test connexion Binance échoué: {str(test_error)[:150]}")
            print("⚠️ Continuons quand même, certaines API peuvent fonctionner...")
        
        return client
    
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation du client Binance: {str(e)[:200]}")
        print("❌ Détails:", type(e).__name__)
        return None

