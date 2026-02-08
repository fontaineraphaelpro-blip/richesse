"""
Module pour accéder à l'API CoinGecko (alternative à Binance).
API gratuite, pas besoin de clé, moins de restrictions géographiques.
"""

import requests
import time
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime, timedelta

# URL de base de l'API CoinGecko
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

# Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}

# Mapping des symboles Binance vers CoinGecko IDs
SYMBOL_TO_ID = {
    'BTCUSDT': 'bitcoin',
    'ETHUSDT': 'ethereum',
    'BNBUSDT': 'binancecoin',
    'SOLUSDT': 'solana',
    'XRPUSDT': 'ripple',
    'ADAUSDT': 'cardano',
    'DOGEUSDT': 'dogecoin',
    'DOTUSDT': 'polkadot',
    'MATICUSDT': 'matic-network',
    'AVAXUSDT': 'avalanche-2',
    'LINKUSDT': 'chainlink',
    'UNIUSDT': 'uniswap',
    'LTCUSDT': 'litecoin',
    'ATOMUSDT': 'cosmos',
    'ETCUSDT': 'ethereum-classic',
    'XLMUSDT': 'stellar',
    'ALGOUSDT': 'algorand',
    'VETUSDT': 'vechain',
    'ICPUSDT': 'internet-computer',
    'FILUSDT': 'filecoin',
    'TRXUSDT': 'tron',
    'EOSUSDT': 'eos',
    'AAVEUSDT': 'aave',
    'THETAUSDT': 'theta-token',
    'SANDUSDT': 'the-sandbox',
    'MANAUSDT': 'decentraland',
    'AXSUSDT': 'axie-infinity',
    'NEARUSDT': 'near',
    'FTMUSDT': 'fantom',
    'GRTUSDT': 'the-graph',
    'HBARUSDT': 'hedera-hashgraph',
    'EGLDUSDT': 'elrond-erd-2',
    'ZECUSDT': 'zcash',
    'CHZUSDT': 'chiliz',
    'ENJUSDT': 'enjincoin',
    'BATUSDT': 'basic-attention-token',
    'ZILUSDT': 'zilliqa',
    'IOTAUSDT': 'iota',
    'ONTUSDT': 'ontology',
    'QTUMUSDT': 'qtum',
    'WAVESUSDT': 'waves',
    'OMGUSDT': 'omisego',
    'SNXUSDT': 'havven',
    'MKRUSDT': 'maker',
    'COMPUSDT': 'compound-governance-token',
    'YFIUSDT': 'yearn-finance',
    'SUSHIUSDT': 'sushi',
    'CRVUSDT': 'curve-dao-token',
    '1INCHUSDT': '1inch',
    'RENUSDT': 'republic-protocol'
}


def get_coingecko_id(symbol: str) -> Optional[str]:
    """Convertit un symbole Binance en ID CoinGecko."""
    return SYMBOL_TO_ID.get(symbol)


def get_klines_coingecko(symbol: str, interval: str = '1h', limit: int = 200) -> Optional[pd.DataFrame]:
    """
    Récupère les données OHLCV depuis CoinGecko.
    
    Args:
        symbol: Symbole de la paire (ex: 'BTCUSDT')
        interval: Intervalle (CoinGecko supporte: 1m, 5m, 15m, 30m, 1h, 4h, 12h, 1d)
        limit: Nombre de bougies
    
    Returns:
        DataFrame avec colonnes: timestamp, open, high, low, close, volume
    """
    try:
        coin_id = get_coingecko_id(symbol)
        if not coin_id:
            return None
        
        # Convertir interval Binance vers CoinGecko
        interval_map = {
            '1h': 'hourly',
            '4h': '4hourly',
            '1d': 'daily'
        }
        vs_currency = 'usd'
        days = max(1, limit // 24) if interval == '1h' else max(1, limit)
        
        url = f"{COINGECKO_API_BASE}/coins/{coin_id}/ohlc"
        params = {
            'vs_currency': vs_currency,
            'days': min(days, 365)  # Max 365 jours
        }
        
        time.sleep(0.5)  # Rate limiting CoinGecko
        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            return None
        
        # Convertir en DataFrame
        # Format CoinGecko: [timestamp, open, high, low, close]
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        
        # Ajouter volume (0 car CoinGecko ne fournit pas de volume dans OHLC)
        df['volume'] = 0
        
        # Convertir timestamp (millisecondes)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Filtrer pour avoir le bon nombre de bougies
        if len(df) > limit:
            df = df.tail(limit)
        
        # Trier par timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    except Exception as e:
        print(f"⚠️ Erreur CoinGecko pour {symbol}: {e}")
        return None


def test_coingecko_connection() -> bool:
    """Teste la connexion à CoinGecko."""
    try:
        url = f"{COINGECKO_API_BASE}/ping"
        response = requests.get(url, headers=HEADERS, timeout=10)
        return response.status_code == 200
    except:
        return False

