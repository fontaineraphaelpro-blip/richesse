"""
Module pour récupérer les données OHLCV depuis Binance.
Utilise l'API publique REST (pas besoin de clé API).
"""

import pandas as pd
import time
from binance_api import get_klines
from typing import Optional


def fetch_klines(symbol: str, interval: str = '1h', limit: int = 200) -> Optional[pd.DataFrame]:
    """
    Récupère les données OHLCV (bougies) pour une paire donnée (API publique, pas besoin de clé).
    
    Args:
        symbol: Symbole de la paire (ex: 'BTCUSDT')
        interval: Intervalle de temps ('1h', '4h', '1d', etc.)
        limit: Nombre de bougies à récupérer (max 1000)
    
    Returns:
        DataFrame avec colonnes: timestamp, open, high, low, close, volume
        Retourne None en cas d'erreur
    """
    try:
        # Récupérer les klines via API publique (retry géré dans binance_api)
        klines = get_klines(symbol=symbol, interval=interval, limit=limit)
        
        if klines is None or len(klines) == 0:
            return None
        
        # Convertir en DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # Convertir les types numériques
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convertir le timestamp en datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Garder seulement les colonnes nécessaires
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        # Vérifier qu'on a des données valides
        if df.empty or df.isna().any().any():
            print(f"⚠️ Données incomplètes pour {symbol}")
            return None
        
        return df
    
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des données pour {symbol}: {e}")
        return None


def fetch_multiple_pairs(symbols: list, interval: str = '1h', limit: int = 200) -> dict:
    """
    Récupère les données OHLCV pour plusieurs paires (API publique, pas besoin de clé).
    
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
        # Délai entre chaque paire pour éviter le rate limiting
        if i < total:
            time.sleep(0.2)
    
    print(f"\n✅ {len(data)}/{total} paires récupérées avec succès")
    return data

