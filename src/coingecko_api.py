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
    Utilise l'endpoint market_chart qui est plus fiable.
    
    Args:
        symbol: Symbole de la paire (ex: 'BTCUSDT')
        interval: Intervalle (1h = hourly data)
        limit: Nombre de bougies
    
    Returns:
        DataFrame avec colonnes: timestamp, open, high, low, close, volume
    """
    try:
        coin_id = get_coingecko_id(symbol)
        if not coin_id:
            return None
        
        # Calculer le nombre de jours nécessaire
        # Pour 200 bougies 1h = ~8 jours
        days = max(1, (limit * 1) // 24 + 1)  # +1 pour marge
        days = min(days, 365)  # Max 365 jours (limite CoinGecko)
        
        url = f"{COINGECKO_API_BASE}/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'hourly' if interval == '1h' else 'daily'
        }
        
        # Délai important pour éviter rate limiting (CoinGecko limite à 10-50 req/min)
        time.sleep(1.5)
        
        response = requests.get(url, params=params, headers=HEADERS, timeout=20)
        
        # Gérer rate limiting
        if response.status_code == 429:
            print(f"  ⏳ Rate limit CoinGecko, attente...", end='\r')
            time.sleep(5)
            response = requests.get(url, params=params, headers=HEADERS, timeout=20)
        
        response.raise_for_status()
        data = response.json()
        
        if not data or 'prices' not in data:
            return None
        
        # Extraire les prix (format: [[timestamp_ms, price], ...])
        prices = data.get('prices', [])
        market_caps = data.get('market_caps', [])
        total_volumes = data.get('total_volumes', [])
        
        if not prices or len(prices) < 2:
            return None
        
        # Créer DataFrame avec les prix
        df_prices = pd.DataFrame(prices, columns=['timestamp', 'close'])
        df_prices['timestamp'] = pd.to_datetime(df_prices['timestamp'], unit='ms')
        
        # Calculer open, high, low à partir des prix
        # Pour simplifier, on utilise le prix comme open/high/low/close
        # (CoinGecko market_chart ne donne que le prix de clôture)
        df_prices['open'] = df_prices['close'].shift(1).fillna(df_prices['close'])
        df_prices['high'] = df_prices[['open', 'close']].max(axis=1)
        df_prices['low'] = df_prices[['open', 'close']].min(axis=1)
        
        # Ajouter volume si disponible
        if total_volumes and len(total_volumes) == len(prices):
            df_volumes = pd.DataFrame(total_volumes, columns=['timestamp', 'volume'])
            df_prices['volume'] = df_volumes['volume'].values
        else:
            df_prices['volume'] = 0
        
        # Filtrer pour avoir le bon nombre de bougies
        if len(df_prices) > limit:
            df_prices = df_prices.tail(limit)
        
        # Trier par timestamp
        df_prices = df_prices.sort_values('timestamp').reset_index(drop=True)
        
        return df_prices[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print(f"  ⚠️ Rate limit CoinGecko atteint pour {symbol}")
        else:
            print(f"  ⚠️ Erreur HTTP CoinGecko pour {symbol}: {e.response.status_code}")
        return None
    except Exception as e:
        print(f"  ⚠️ Erreur CoinGecko pour {symbol}: {str(e)[:100]}")
        return None


def test_coingecko_connection() -> bool:
    """Teste la connexion à CoinGecko."""
    try:
        url = f"{COINGECKO_API_BASE}/ping"
        response = requests.get(url, headers=HEADERS, timeout=10)
        return response.status_code == 200
    except:
        return False

