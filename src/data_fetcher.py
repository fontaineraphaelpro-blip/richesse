"""
Module pour récupérer les données OHLCV depuis plusieurs sources.
Utilise CryptoCompare, CoinCap et génération de données en fallback.
"""

import pandas as pd
import time
from crypto_api import get_klines_unified
from typing import Optional


def fetch_klines(symbol: str, interval: str = '1h', limit: int = 200) -> Optional[pd.DataFrame]:
    """
    Récupère les données OHLCV (bougies) pour une paire donnée.
    Utilise plusieurs sources avec fallback automatique.
    
    Args:
        symbol: Symbole de la paire (ex: 'BTCUSDT')
        interval: Intervalle de temps ('1h', '4h', '1d', etc.)
        limit: Nombre de bougies à récupérer (max 1000)
    
    Returns:
        DataFrame avec colonnes: timestamp, open, high, low, close, volume
        Retourne None en cas d'erreur
    """
    try:
        # Utiliser l'API unifiée (CryptoCompare -> CoinCap -> génération)
        df = get_klines_unified(symbol=symbol, interval=interval, limit=limit)
        
        if df is not None and len(df) > 0:
            return df
        
        return None
    
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des données pour {symbol}: {e}")
        return None


def fetch_multiple_pairs(symbols: list, interval: str = '1h', limit: int = 200) -> dict:
    """
    Récupère les données OHLCV pour plusieurs paires via CoinGecko.
    
    Args:
        symbols: Liste des symboles de paires
        interval: Intervalle de temps
        limit: Nombre de bougies par paire
    
    Returns:
        Dictionnaire {symbol: DataFrame}
    """
    data = {}
    total = len(symbols)
    
    for i, symbol in enumerate(symbols, 1):
        print(f"📊 Récupération {symbol} ({i}/{total})...", end='\r')
        df = fetch_klines(symbol, interval, limit)
        if df is not None:
            data[symbol] = df
        # Délai entre chaque paire pour éviter le rate limiting CoinGecko
        # CoinGecko free tier limite à ~10-30 req/min, donc on attend 4 secondes
        if i < total:
            time.sleep(4.0)  # 4 secondes = max 15 req/min (sous la limite)
    
    print(f"\n✅ {len(data)}/{total} paires récupérées avec succès")
    return data

