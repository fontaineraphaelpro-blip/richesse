"""
Module pour récupérer les VRAIES données de marché (OHLCV) depuis Binance.
Inclut la liste des 50 principales paires pour le scalping.
Gère le basculement automatique vers Binance US en cas de blocage (Erreur 451).
"""

import pandas as pd
import requests
import time
from typing import Optional, Dict, Tuple, List

# --- LISTE DES 50 PRINCIPALES PAIRES USDT (Liquidité élevée pour scalping) ---
TOP_USDT_PAIRS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
    'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'MATICUSDT',
    'LINKUSDT', 'SHIBUSDT', 'LTCUSDT', 'BCHUSDT',
    'ATOMUSDT', 'UNIUSDT', 'XLMUSDT', 'ETCUSDT', 'FILUSDT',
    'ICPUSDT', 'HBARUSDT', 'APTUSDT', 'VETUSDT', 'NEARUSDT',
    'QNTUSDT', 'MKRUSDT', 'GRTUSDT', 'AAVEUSDT', 'ALGOUSDT',
    'AXSUSDT', 'SANDUSDT', 'EGLDUSDT', 'EOSUSDT', 'THETAUSDT',
    'FTMUSDT', 'SNXUSDT', 'NEOUSDT', 'FLOWUSDT', 'KAVAUSDT',
    'XTZUSDT', 'GALAUSDT', 'CHZUSDT', 'MINAUSDT', 'ARBUSDT',
    'OPUSDT', 'INJUSDT', 'RNDRUSDT', 'SUIUSDT', 'SEIUSDT'
]

def get_binance_klines(symbol: str, interval: str = '15m', limit: int = 200) -> Optional[pd.DataFrame]:
    """
    Récupère les bougies (Klines) historiques depuis l'API Binance (Publique).
    Tente Binance Global puis Binance US si bloqué (Erreur 451).
    """
    # URLs possibles (Global et US)
    base_urls = [
        "https://api.binance.com/api/v3/klines", # Global
        "https://api.binance.us/api/v3/klines"   # US (Fallback)
    ]
    
    # Validation de l'intervalle
    valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d']
    if interval not in valid_intervals:
        interval = '15m'

    params = {
        'symbol': symbol.upper(),
        'interval': interval,
        'limit': limit
    }
    
    for base_url in base_urls:
        try:
            response = requests.get(base_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if not data:
                    return None
                    
                # Colonnes API Binance
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'trades', 
                    'taker_buy_base', 'taker_buy_quote', 'ignore'
                ])
                
                # Nettoyage
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                
                # Conversion types (float)
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                
                # Conversion timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                return df
                
            elif response.status_code == 451:
                # Géoblocage détecté, on tente l'URL suivante (US)
                continue
                
            elif response.status_code == 429:
                print(f"⚠️ Rate Limit Binance atteint. Pause de 2s...")
                time.sleep(2)
                return None
            
            elif response.status_code == 400:
                # Symbole peut-être inexistant sur cette version de l'échange
                # (Certaines paires existent sur .com mais pas sur .us)
                return None
                
            else:
                print(f"⚠️ Erreur API Binance {symbol}: {response.status_code}")
                return None
                
        except Exception as e:
            # En cas d'erreur réseau, on essaie l'URL suivante si possible
            continue

    # Si on arrive ici, toutes les URLs ont échoué
    print(f"❌ Échec récupération {symbol} (Toutes API inaccessibles)")
    return None


def fetch_klines(symbol: str, interval: str = '15m', limit: int = 200) -> Tuple[Optional[pd.DataFrame], Optional[float]]:
    """
    Récupère les données et le prix actuel pour une paire.
    """
    df = get_binance_klines(symbol, interval, limit)
    
    real_price = None
    if df is not None and not df.empty:
        real_price = df.iloc[-1]['close']
    
    return df, real_price


def fetch_multiple_pairs(symbols: List[str] = None, interval: str = '15m', limit: int = 200) -> Tuple[Dict[str, pd.DataFrame], Dict[str, float]]:
    """
    Récupère les données pour une liste de paires.
    Utilise la liste TOP_USDT_PAIRS par défaut si 'symbols' est None.
    """
    # Si aucune liste n'est fournie, on utilise la liste interne
    if symbols is None or len(symbols) == 0:
        symbols = TOP_USDT_PAIRS
        
    data = {}
    real_prices = {}
    total = len(symbols)
    success_count = 0
    
    print(f"📊 Récupération des données réelles (Binance) pour {total} paires...")
    
    for i, symbol in enumerate(symbols, 1):
        print(f"⏳ ({i}/{total}) Fetching {symbol}...", end='\r')
        
        df, real_price = fetch_klines(symbol, interval, limit)
        
        if df is not None and real_price is not None:
            data[symbol] = df
            real_prices[symbol] = real_price
            success_count += 1
        
        # Petit délai pour éviter le ban IP (Rate Limit Binance)
        time.sleep(0.15)
    
    print(f"\n✅ {success_count}/{total} paires récupérées avec succès.")
    
    return data, real_prices

def get_top_pairs() -> List[str]:
    """Retourne simplement la liste des paires configurées."""
    return TOP_USDT_PAIRS