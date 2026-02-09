"""
Module pour générer des données OHLCV réalistes (sans API).
Utilise des données de démonstration basées sur des prix de référence.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
from datetime import datetime, timedelta


# Prix de référence réalistes par crypto (basés sur données historiques)
REFERENCE_PRICES = {
    'BTCUSDT': 50000.0,
    'ETHUSDT': 3000.0,
    'BNBUSDT': 400.0,
    'SOLUSDT': 120.0,
    'XRPUSDT': 0.6,
    'ADAUSDT': 0.5,
    'DOGEUSDT': 0.08,
    'DOTUSDT': 7.0,
    'MATICUSDT': 0.8,
    'AVAXUSDT': 35.0,
    'LINKUSDT': 15.0,
    'UNIUSDT': 6.0,
    'LTCUSDT': 70.0,
    'ATOMUSDT': 10.0,
    'ETCUSDT': 20.0,
    'XLMUSDT': 0.12,
    'ALGOUSDT': 0.15,
    'VETUSDT': 0.03,
    'ICPUSDT': 12.0,
    'FILUSDT': 5.0,
    'TRXUSDT': 0.10,
    'EOSUSDT': 0.8,
    'AAVEUSDT': 80.0,
    'THETAUSDT': 1.0,
    'SANDUSDT': 0.5,
    'MANAUSDT': 0.4,
    'AXSUSDT': 6.0,
    'NEARUSDT': 3.0,
    'FTMUSDT': 0.3,
    'GRTUSDT': 0.15,
    'HBARUSDT': 0.08,
    'EGLDUSDT': 40.0,
    'ZECUSDT': 25.0,
    'CHZUSDT': 0.10,
    'ENJUSDT': 0.3,
    'BATUSDT': 0.25,
    'ZILUSDT': 0.02,
    'IOTAUSDT': 0.2,
    'ONTUSDT': 0.3,
    'QTUMUSDT': 3.0,
    'WAVESUSDT': 2.0,
    'OMGUSDT': 0.8,
    'SNXUSDT': 3.0,
    'MKRUSDT': 2000.0,
    'COMPUSDT': 50.0,
    'YFIUSDT': 5000.0,
    'SUSHIUSDT': 1.0,
    'CRVUSDT': 0.5,
    '1INCHUSDT': 0.4,
    'RENUSDT': 0.1,
    'LUNAUSDT': 0.5,
    'USTCUSDT': 0.01,
    'LUNCUSDT': 0.0001,
    'APTUSDT': 8.0,
    'ARBUSDT': 1.0
}


def generate_ohlc_data(symbol: str, base_price: float, limit: int = 200) -> pd.DataFrame:
    """
    Génère des données OHLC réalistes basées sur un prix de référence.
    
    Args:
        symbol: Symbole de la paire
        base_price: Prix de référence
        limit: Nombre de bougies
    
    Returns:
        DataFrame OHLCV avec colonnes: timestamp, open, high, low, close, volume
    """
    # Générer timestamps (1 heure par bougie, en ordre chronologique)
    timestamps = [datetime.now() - timedelta(hours=i) for i in range(limit-1, -1, -1)]
    
    # Générer prix avec tendance réaliste et volatilité
    prices = []
    price = base_price
    
    # Ajouter une tendance légère (bullish ou bearish)
    trend = np.random.uniform(-0.0005, 0.0005)
    
    # Volatilité variable selon le type de crypto
    volatility = 0.015 if base_price > 100 else 0.02  # Plus volatil pour petites cryptos
    
    for i in range(limit):
        # Variation aléatoire mais réaliste
        change = np.random.normal(0, volatility)  # Distribution normale
        price = price * (1 + change + trend)
        
        # Garder dans une plage raisonnable (±30% du prix de base)
        price = max(base_price * 0.7, min(base_price * 1.3, price))
        prices.append(price)
    
    # Créer DataFrame OHLC
    df_data = []
    for i, (ts, close_price) in enumerate(zip(timestamps, prices)):
        # Générer open (proche du close précédent ou du close actuel)
        if i == 0:
            open_price = close_price * np.random.uniform(0.995, 1.005)
        else:
            open_price = prices[i-1] * np.random.uniform(0.998, 1.002)
        
        # Générer high et low (variation de 0.5% à 2%)
        price_range = close_price * np.random.uniform(0.005, 0.02)
        high_price = max(open_price, close_price) + price_range * np.random.uniform(0.3, 0.7)
        low_price = min(open_price, close_price) - price_range * np.random.uniform(0.3, 0.7)
        
        # Volume (plus élevé pour les grandes cryptos)
        base_volume = 10000000 if base_price > 100 else 1000000
        volume = base_volume * np.random.uniform(0.5, 2.0)
        
        df_data.append({
            'timestamp': ts,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(df_data)
    
    # S'assurer que high >= max(open, close) et low <= min(open, close)
    df['high'] = df[['open', 'close', 'high']].max(axis=1)
    df['low'] = df[['open', 'close', 'low']].min(axis=1)
    
    return df


def fetch_klines(symbol: str, interval: str = '1h', limit: int = 200) -> Optional[pd.DataFrame]:
    """
    Génère des données OHLCV (bougies) pour une paire donnée.
    
    Args:
        symbol: Symbole de la paire (ex: 'BTCUSDT')
        interval: Intervalle de temps ('1h')
        limit: Nombre de bougies à générer
    
    Returns:
        DataFrame avec colonnes: timestamp, open, high, low, close, volume
    """
    try:
        # Récupérer le prix de référence
        base_price = REFERENCE_PRICES.get(symbol, 100.0)
        
        # Générer des données OHLC basées sur le prix de référence
        return generate_ohlc_data(symbol, base_price, limit)
    
    except Exception as e:
        print(f"❌ Erreur lors de la génération des données pour {symbol}: {e}")
        return None


def fetch_multiple_pairs(symbols: list, interval: str = '1h', limit: int = 200) -> dict:
    """
    Génère les données OHLCV pour plusieurs paires.
    
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
        print(f"📊 Génération {symbol} ({i}/{total})...", end='\r')
        df = fetch_klines(symbol, interval, limit)
        if df is not None:
            data[symbol] = df
    
    print(f"\n✅ {len(data)}/{total} paires générées avec succès")
    return data
