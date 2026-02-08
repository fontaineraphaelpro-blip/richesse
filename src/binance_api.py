"""
Module pour accéder à l'API publique Binance sans clé API.
Utilise directement les endpoints REST publics.
"""

import requests
import time
from typing import List, Dict, Optional
import pandas as pd


# URL de base de l'API publique Binance
BINANCE_API_BASE = "https://api.binance.com/api/v3"

# Headers pour éviter les blocages
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache'
}


def get_ticker_24h() -> List[Dict]:
    """
    Récupère les tickers 24h de toutes les paires (API publique, pas besoin de clé).
    
    Returns:
        Liste de dictionnaires avec les données des tickers
    """
    try:
        url = f"{BINANCE_API_BASE}/ticker/24hr"
        # Ajouter un délai pour éviter le rate limiting
        time.sleep(0.5)
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 451:
            print(f"⚠️ Erreur 451: Binance bloque les requêtes depuis cette IP/région")
            print(f"💡 Solution: Utilisation de la liste de fallback")
        else:
            print(f"❌ Erreur HTTP {e.response.status_code}: {e}")
        return []
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des tickers: {e}")
        return []


def get_klines(symbol: str, interval: str = '1h', limit: int = 200) -> Optional[List]:
    """
    Récupère les klines (bougies) pour une paire (API publique, pas besoin de clé).
    
    Args:
        symbol: Symbole de la paire (ex: 'BTCUSDT')
        interval: Intervalle de temps ('1m', '5m', '15m', '1h', '4h', '1d', etc.)
        limit: Nombre de bougies à récupérer (max 1000)
    
    Returns:
        Liste de klines ou None en cas d'erreur
    """
    try:
        url = f"{BINANCE_API_BASE}/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': min(limit, 1000)  # Limite max de l'API
        }
        
        max_retries = 2  # Réduire les tentatives
        for attempt in range(max_retries):
            try:
                # Délai entre les requêtes pour éviter le rate limiting
                if attempt > 0:
                    time.sleep(2)
                else:
                    time.sleep(0.3)  # Petit délai même pour la première tentative
                
                response = requests.get(url, params=params, headers=HEADERS, timeout=15)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as http_error:
                if http_error.response.status_code == 451:
                    # Erreur 451 = bloqué, pas la peine de retry
                    print(f"⚠️ {symbol}: Bloqué par Binance (451)")
                    return None
                elif attempt == max_retries - 1:
                    raise http_error
                print(f"⚠️ Tentative {attempt + 1}/{max_retries} échouée pour {symbol} (HTTP {http_error.response.status_code}), retry...")
            except Exception as api_error:
                if attempt == max_retries - 1:
                    raise api_error
                print(f"⚠️ Tentative {attempt + 1}/{max_retries} échouée pour {symbol}, retry...")
                time.sleep(1)
        
        return None
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des klines pour {symbol}: {e}")
        return None


def test_connection() -> bool:
    """
    Teste la connexion à l'API Binance (ping).
    
    Returns:
        True si la connexion fonctionne, False sinon
    """
    try:
        url = f"{BINANCE_API_BASE}/ping"
        response = requests.get(url, headers=HEADERS, timeout=10)
        return response.status_code == 200
    except:
        return False

