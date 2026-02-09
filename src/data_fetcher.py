"""
Module pour récupérer les prix réels et générer des données OHLCV réalistes.
"""

import pandas as pd
import numpy as np
import requests
import time
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


def generate_ohlc_data(symbol: str, base_price: float, limit: int = 200, interval_minutes: int = 15) -> pd.DataFrame:
    """
    Génère des données OHLC réalistes basées sur un prix de référence.
    Optimisé pour le scalping (timeframe 15min).
    
    Args:
        symbol: Symbole de la paire
        base_price: Prix de référence
        limit: Nombre de bougies
        interval_minutes: Intervalle en minutes (défaut: 15 pour scalping)
    
    Returns:
        DataFrame OHLCV avec colonnes: timestamp, open, high, low, close, volume
    """
    # Générer timestamps (15 minutes par bougie pour scalping)
    timestamps = [datetime.now() - timedelta(minutes=interval_minutes*i) for i in range(limit-1, -1, -1)]
    
    # Générer prix avec tendance réaliste et volatilité
    # Utiliser un seed basé sur le symbole pour avoir des prix cohérents
    np.random.seed(hash(symbol) % (2**32))
    
    prices = []
    price = base_price
    
    # Ajouter une tendance légère (bullish ou bearish) mais cohérente
    trend = np.random.uniform(-0.0003, 0.0003)
    
    # Volatilité variable selon le type de crypto (plus élevée pour scalping)
    volatility = 0.006 if base_price > 100 else 0.010  # Volatilité adaptée au timeframe 15min
    
    for i in range(limit):
        # Variation aléatoire mais réaliste avec marche aléatoire
        change = np.random.normal(0, volatility)  # Distribution normale
        price = price * (1 + change + trend)
        
        # Garder dans une plage raisonnable (±20% du prix de base pour plus de cohérence)
        price = max(base_price * 0.85, min(base_price * 1.15, price))
        prices.append(price)
    
    # FORCER le dernier prix à être EXACTEMENT le prix réel récupéré
    # C'est le prix actuel du marché, il ne doit pas être modifié
    prices[-1] = base_price
    
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


def get_real_price(symbol: str) -> Optional[float]:
    """
    Récupère le prix réel actuel d'une crypto depuis CoinGecko (API publique gratuite).
    
    Args:
        symbol: Symbole de la paire (ex: 'BTCUSDT')
    
    Returns:
        Prix réel en USD ou None
    """
    try:
        # Convertir le symbole Binance en ID CoinGecko
        symbol_map = {
            'BTCUSDT': 'bitcoin', 'ETHUSDT': 'ethereum', 'BNBUSDT': 'binancecoin',
            'SOLUSDT': 'solana', 'XRPUSDT': 'ripple', 'ADAUSDT': 'cardano',
            'DOGEUSDT': 'dogecoin', 'DOTUSDT': 'polkadot', 'MATICUSDT': 'matic-network',
            'AVAXUSDT': 'avalanche-2', 'LINKUSDT': 'chainlink', 'UNIUSDT': 'uniswap',
            'LTCUSDT': 'litecoin', 'ATOMUSDT': 'cosmos', 'ETCUSDT': 'ethereum-classic',
            'XLMUSDT': 'stellar', 'ALGOUSDT': 'algorand', 'VETUSDT': 'vechain',
            'ICPUSDT': 'internet-computer', 'FILUSDT': 'filecoin', 'TRXUSDT': 'tron',
            'EOSUSDT': 'eos', 'AAVEUSDT': 'aave', 'THETAUSDT': 'theta-token',
            'SANDUSDT': 'the-sandbox', 'MANAUSDT': 'decentraland', 'AXSUSDT': 'axie-infinity',
            'NEARUSDT': 'near', 'FTMUSDT': 'fantom', 'GRTUSDT': 'the-graph',
            'HBARUSDT': 'hedera-hashgraph', 'EGLDUSDT': 'elrond-erd-2', 'ZECUSDT': 'zcash',
            'CHZUSDT': 'chiliz', 'ENJUSDT': 'enjincoin', 'BATUSDT': 'basic-attention-token',
            'ZILUSDT': 'zilliqa', 'IOTAUSDT': 'iota', 'ONTUSDT': 'ontology',
            'QTUMUSDT': 'qtum', 'WAVESUSDT': 'waves', 'OMGUSDT': 'omisego',
            'SNXUSDT': 'synthetix-network-token', 'MKRUSDT': 'maker', 'COMPUSDT': 'compound-governance-token',
            'YFIUSDT': 'yearn-finance', 'SUSHIUSDT': 'sushi', 'CRVUSDT': 'curve-dao-token',
            '1INCHUSDT': '1inch', 'RENUSDT': 'republic-protocol', 'APTUSDT': 'aptos',
            'ARBUSDT': 'arbitrum'
        }
        
        coin_id = symbol_map.get(symbol)
        if not coin_id:
            return None
        
        # API CoinGecko simple price (gratuite, pas de clé API nécessaire)
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': 'usd'
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if coin_id in data and 'usd' in data[coin_id]:
                price = float(data[coin_id]['usd'])
                return price
        
        return None
        
    except Exception as e:
        return None


def fetch_klines(symbol: str, interval: str = '15m', limit: int = 200) -> Optional[pd.DataFrame]:
    """
    Récupère le prix réel et génère des données OHLCV réalistes.
    
    Args:
        symbol: Symbole de la paire (ex: 'BTCUSDT')
        interval: Intervalle de temps ('15m')
        limit: Nombre de bougies à générer
    
    Returns:
        DataFrame avec colonnes: timestamp, open, high, low, close, volume
        Le dernier prix (close) sera EXACTEMENT le prix réel récupéré
    """
    try:
        # 1. Récupérer le prix réel actuel
        real_price = get_real_price(symbol)
        
        if real_price and real_price > 0:
            base_price = real_price
            print(f"✓ {symbol}: ${real_price:,.4f} (prix réel)")
        else:
            # Fallback: utiliser le prix de référence
            base_price = REFERENCE_PRICES.get(symbol, 100.0)
            print(f"⚠ {symbol}: ${base_price:,.4f} (prix de référence - API indisponible)")
        
        # Déterminer l'intervalle en minutes
        interval_map = {'15m': 15, '1h': 60, '5m': 5, '1m': 1}
        interval_minutes = interval_map.get(interval, 15)
        
        # Générer des données OHLC basées sur le prix réel
        # Le dernier prix sera FORCÉ à être exactement le prix réel
        df = generate_ohlc_data(symbol, base_price, limit, interval_minutes)
        
        # S'assurer que le dernier prix est EXACTEMENT le prix réel
        if df is not None and len(df) > 0 and real_price and real_price > 0:
            df.iloc[-1, df.columns.get_loc('close')] = real_price
            # Ajuster aussi high et low pour être cohérents
            last_high = df.iloc[-1]['high']
            last_low = df.iloc[-1]['low']
            if real_price > last_high:
                df.iloc[-1, df.columns.get_loc('high')] = real_price * 1.001
            if real_price < last_low:
                df.iloc[-1, df.columns.get_loc('low')] = real_price * 0.999
        
        return df
    
    except Exception as e:
        print(f"❌ Erreur lors de la génération des données pour {symbol}: {e}")
        return None


def fetch_multiple_pairs(symbols: list, interval: str = '15m', limit: int = 200) -> dict:
    """
    Récupère les prix réels et génère les données OHLCV pour plusieurs paires.
    
    Args:
        symbols: Liste des symboles de paires
        interval: Intervalle de temps
        limit: Nombre de bougies par paire
    
    Returns:
        Dictionnaire {symbol: DataFrame}
    """
    data = {}
    total = len(symbols)
    
    print(f"📊 Récupération des prix réels pour {total} paires...")
    
    for i, symbol in enumerate(symbols, 1):
        print(f"📊 {symbol} ({i}/{total})...", end='\r')
        df = fetch_klines(symbol, interval, limit)
        if df is not None:
            data[symbol] = df
        # Délai pour éviter rate limiting (CoinGecko: 10-50 req/min)
        # Réduire le délai pour accélérer le scan initial
        if i < total:
            time.sleep(0.8)  # ~75 requêtes par minute (limite: 50/min mais on prend une marge)
    
    print(f"\n✅ {len(data)}/{total} paires récupérées avec succès")
    return data
