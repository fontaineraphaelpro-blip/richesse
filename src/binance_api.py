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


def get_ticker_24h() -> List[Dict]:
    """
    Récupère les tickers 24h de toutes les paires (API publique, pas besoin de clé).
    
    Returns:
        Liste de dictionnaires avec les données des tickers
    """
    try:
        url = f"{BINANCE_API_BASE}/ticker/24hr"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
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
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
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
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False

