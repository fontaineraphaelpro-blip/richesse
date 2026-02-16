"""
Module pour récupérer les VRAIES données de marché (OHLCV) depuis Binance.
Inclut la liste des 50 principales paires pour le scalping.
Gère le basculement automatique vers Binance US en cas de blocage (Erreur 451).
"""

import pandas as pd
import requests
import time
from typing import Optional, Dict, Tuple, List

# --- LISTE DES 200 PRINCIPALES PAIRES USDT (Maximum Coverage) ---
TOP_USDT_PAIRS = [
    # Top 20 - Ultra Liquid (>$1B daily volume)
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
    'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'TRXUSDT',
    'MATICUSDT', 'LINKUSDT', 'SHIBUSDT', 'LTCUSDT', 'BCHUSDT',
    'ATOMUSDT', 'UNIUSDT', 'XLMUSDT', 'ETCUSDT', 'FILUSDT',
    
    # 21-40 - High Liquid
    'ICPUSDT', 'HBARUSDT', 'APTUSDT', 'VETUSDT', 'NEARUSDT',
    'QNTUSDT', 'MKRUSDT', 'GRTUSDT', 'AAVEUSDT', 'ALGOUSDT',
    'AXSUSDT', 'SANDUSDT', 'EGLDUSDT', 'EOSUSDT', 'THETAUSDT',
    'FTMUSDT', 'SNXUSDT', 'NEOUSDT', 'FLOWUSDT', 'KAVAUSDT',
    
    # 41-60 - Medium-High Liquid
    'XTZUSDT', 'GALAUSDT', 'CHZUSDT', 'MINAUSDT', 'ARBUSDT',
    'OPUSDT', 'INJUSDT', 'RNDRUSDT', 'SUIUSDT', 'SEIUSDT',
    'PEPEUSDT', 'WLDUSDT', 'FETUSDT', 'AGIXUSDT', 'OCEANUSDT',
    'TIAUSDT', 'IMXUSDT', 'LDOUSDT', 'STXUSDT', 'RUNEUSDT',
    
    # 61-80 - Solid Volume
    'ENAUSDT', 'ZROUSDT', 'JUPUSDT', 'PENDLEUSDT', 'ONDOUSDT',
    'WIFUSDT', 'BONKUSDT', 'FLOKIUSDT', 'ORDIUSDT', 'SATSUSDT',
    'CFXUSDT', 'KASUSDT', 'BEAMUSDT', 'DYDXUSDT', 'GMXUSDT',
    'BLURUSDT', 'COMPUSDT', 'CRVUSDT', '1INCHUSDT', 'LRCUSDT',
    
    # 81-100 - Active Trading
    'ENSUSDT', 'APEUSDT', 'CAKEUSDT', 'DASHUSDT', 'WAVESUSDT',
    'ZECUSDT', 'XMRUSDT', 'IOTAUSDT', 'ZILUSDT', 'BATUSDT',
    'SKLUSDT', 'IOTXUSDT', 'CELRUSDT', 'ANKRUSDT', 'ONEUSDT',
    'RVNUSDT', 'STMXUSDT', 'CKBUSDT', 'CELOUSDT', 'HOTUSDT',
    
    # 101-120 - DeFi & Gaming
    'SUSHIUSDT', 'YFIUSDT', 'BALUSDT', 'RENUSDT', 'KNCUSDT',
    'BANDUSDT', 'STORJUSDT', 'OMGUSDT', 'ZRXUSDT', 'ENJUSDT',
    'MANAUSDT', 'AUDIOUSDT', 'MASKUSDT', 'LPTUSDT', 'RSRUSDT',
    'NMRUSDT', 'ANTUSDT', 'CTSIUSDT', 'RLCUSDT', 'REQUSDT',
    
    # 121-140 - Layer 1 & Layer 2
    'KSMUSDT', 'MOVRUSDT', 'ARUSDT', 'ROSEUUSDT', 'CELOUSUSDT',
    'HARMONYUSDT', 'SYSCOINUSDT', 'IOTXUSDT', 'ONTUSDT', 'QTUMUSDT',
    'ICXUSDT', 'LSKUSDT', 'ARDRUSDT', 'STRATUSDT', 'RVNUSDT',
    'DGBUSDT', 'SCUSDT', 'ZENUSDT', 'BTGUSDT', 'BTSUSDT',
    
    # 141-160 - Memecoins & New Trends
    'WOOUSDT', 'TUSDT', 'HIGHUSDT', 'HOOKUSDT', 'MAGICUSDT',
    'IDUSDT', 'RDNTUSDT', 'AMBUSDT', 'PHBUSDT', 'LEVERUSDT',
    'MDTUSDT', 'XVSUSDT', 'ALPACAUSDT', 'TRUUSDT', 'CVXUSDT',
    'FXSUSDT', 'QUICKUSDT', 'RADUSDT', 'RAREUSDT', 'SUPERUSDT',
    
    # 161-180 - Infrastructure & Oracle
    'APIUSDT', 'ACHUSDT', 'SSVUSDT', 'PROMUSDT', 'QIUSDT',
    'PERPUSDT', 'COMBOUSDT', 'MAVUSDT', 'XVSUSDT', 'POLYXUSDT',
    'ARKMUSDT', 'NTROUSDT', 'MBLUSDT', 'OAXUSDT', 'KEYUSDT',
    'WANUSDT', 'DOCKUSDT', 'VITEUSDT', 'FUNUSDT', 'OGNUSDT',
    
    # 181-200 - Emerging & New Listings
    'ASTUSDT', 'ATAUSDT', 'BAKEUSDT', 'BETAUSDT', 'BUSDUSDT',
    'COCOSUSDT', 'CTKUSDT', 'DATAUSDT', 'DENTUSDT', 'DEXEUSDT',
    'DFUSDT', 'DUSKUSDT', 'ELFUSDT', 'FIROUSDT', 'FORUSDT',
    'FORTHUSDT', 'GHSTUSDT', 'GLMRUSDT', 'GTCUSDT', 'HARDUSDT'
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


# ─────────────────────────────────────────────────────────────
# MULTI-TIMEFRAME ANALYSIS
# ─────────────────────────────────────────────────────────────

def fetch_multi_timeframe(symbol: str, timeframes: List[str] = None, limit: int = 200) -> Dict[str, pd.DataFrame]:
    """
    Récupère les données pour plusieurs timeframes d'une même paire.
    
    Args:
        symbol: La paire (ex: 'BTCUSDT')
        timeframes: Liste des timeframes (ex: ['15m', '1h', '4h'])
        limit: Nombre de bougies par timeframe
    
    Returns:
        Dict avec les DataFrames par timeframe: {'15m': df, '1h': df, '4h': df}
    """
    if timeframes is None:
        timeframes = ['15m', '1h', '4h']
    
    data = {}
    
    for tf in timeframes:
        df = get_binance_klines(symbol, interval=tf, limit=limit)
        if df is not None and not df.empty:
            data[tf] = df
        time.sleep(0.1)  # Éviter rate limit
    
    return data


def analyze_multi_timeframe_trend(symbol: str, timeframes: List[str] = None) -> Dict:
    """
    Analyse la tendance sur plusieurs timeframes.
    Retourne un consensus de tendance.
    
    Args:
        symbol: La paire à analyser
        timeframes: Liste des timeframes (défaut: ['15m', '1h', '4h'])
    
    Returns:
        {
            'symbol': str,
            'trends': {tf: 'Bullish'|'Bearish'|'Neutral'},
            'consensus': 'Bullish'|'Bearish'|'Neutral'|'Mixed',
            'alignment_score': 0-100,
            'recommendation': str
        }
    """
    if timeframes is None:
        timeframes = ['15m', '1h', '4h']
    
    data = fetch_multi_timeframe(symbol, timeframes)
    
    if not data:
        return {
            'symbol': symbol,
            'trends': {},
            'consensus': 'UNKNOWN',
            'alignment_score': 0,
            'recommendation': 'Pas de données'
        }
    
    trends = {}
    bullish_count = 0
    bearish_count = 0
    
    for tf, df in data.items():
        trend = _detect_trend_from_df(df)
        trends[tf] = trend
        
        if trend == 'Bullish':
            bullish_count += 1
        elif trend == 'Bearish':
            bearish_count += 1
    
    total = len(data)
    
    # Consensus
    if bullish_count == total:
        consensus = 'Bullish'
        alignment_score = 100
        recommendation = "✅ FORT: Toutes les timeframes sont haussières"
    elif bearish_count == total:
        consensus = 'Bearish'
        alignment_score = 100
        recommendation = "✅ FORT: Toutes les timeframes sont baissières"
    elif bullish_count > bearish_count:
        consensus = 'Bullish'
        alignment_score = int((bullish_count / total) * 100)
        recommendation = f"⚠️ MODÉRÉ: {bullish_count}/{total} timeframes haussières"
    elif bearish_count > bullish_count:
        consensus = 'Bearish'
        alignment_score = int((bearish_count / total) * 100)
        recommendation = f"⚠️ MODÉRÉ: {bearish_count}/{total} timeframes baissières"
    else:
        consensus = 'Mixed'
        alignment_score = 0
        recommendation = "❌ CONFLICTUEL: Timeframes en désaccord, attendre"
    
    return {
        'symbol': symbol,
        'trends': trends,
        'consensus': consensus,
        'alignment_score': alignment_score,
        'recommendation': recommendation
    }


def _detect_trend_from_df(df: pd.DataFrame) -> str:
    """
    Détecte la tendance depuis un DataFrame OHLCV.
    Utilise EMA9/EMA21 cross et position du prix.
    """
    if df is None or len(df) < 21:
        return 'Neutral'
    
    close = df['close']
    
    # Calcul EMA9 et EMA21
    ema9 = close.ewm(span=9, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    
    current_price = close.iloc[-1]
    current_ema9 = ema9.iloc[-1]
    current_ema21 = ema21.iloc[-1]
    
    # Tendance basée sur EMA cross et position du prix
    bullish_signals = 0
    bearish_signals = 0
    
    # EMA9 > EMA21 = Bullish
    if current_ema9 > current_ema21:
        bullish_signals += 1
    elif current_ema9 < current_ema21:
        bearish_signals += 1
    
    # Prix au-dessus des EMAs = Bullish
    if current_price > current_ema9 and current_price > current_ema21:
        bullish_signals += 1
    elif current_price < current_ema9 and current_price < current_ema21:
        bearish_signals += 1
    
    # Pente de l'EMA21 (tendance de fond)
    if len(ema21) >= 5:
        ema21_slope = ema21.iloc[-1] - ema21.iloc[-5]
        if ema21_slope > 0:
            bullish_signals += 1
        elif ema21_slope < 0:
            bearish_signals += 1
    
    if bullish_signals > bearish_signals:
        return 'Bullish'
    elif bearish_signals > bullish_signals:
        return 'Bearish'
    else:
        return 'Neutral'


def validate_signal_multi_timeframe(symbol: str, signal: str, timeframes: List[str] = None) -> Dict:
    """
    Valide un signal de trading avec l'analyse multi-timeframe.
    
    Args:
        symbol: La paire
        signal: 'LONG' ou 'SHORT'
        timeframes: Timeframes à analyser
    
    Returns:
        {
            'is_valid': bool,
            'alignment_score': int,
            'reason': str,
            'details': dict
        }
    """
    mtf = analyze_multi_timeframe_trend(symbol, timeframes)
    
    expected_consensus = 'Bullish' if signal == 'LONG' else 'Bearish'
    
    is_valid = mtf['consensus'] == expected_consensus and mtf['alignment_score'] >= 66
    
    if mtf['consensus'] == 'Mixed':
        reason = f"❌ Signal {signal} rejeté: Timeframes en conflit"
    elif mtf['consensus'] != expected_consensus:
        reason = f"❌ Signal {signal} rejeté: Tendance globale {mtf['consensus']}"
    elif mtf['alignment_score'] < 66:
        reason = f"⚠️ Signal {signal} faible: Alignement {mtf['alignment_score']}%"
    else:
        reason = f"✅ Signal {signal} confirmé: {mtf['recommendation']}"
    
    return {
        'is_valid': is_valid,
        'alignment_score': mtf['alignment_score'],
        'reason': reason,
        'details': mtf
    }