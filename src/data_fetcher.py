"""
Module pour récupérer les VRAIES données de marché (OHLCV) depuis Binance.
Inclut la liste des 200 principales paires pour le trading.
Gère le basculement automatique vers Binance US en cas de blocage (Erreur 451).
"""

import pandas as pd
import requests
import time
from typing import Optional, Dict, Tuple, List

BASE_URL = "https://api.binance.com"

# --- LISTE DES 200 PRINCIPALES PAIRES USDT (Maximum Coverage) ---
TOP_USDT_PAIRS = [
    # Top 20 - Ultra Liquid (>$1B daily volume)
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
    'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'TONUSDT',
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
                print(f"[WARN] Rate Limit Binance atteint. Pause de 2s...")
                time.sleep(2)
                return None
            
            elif response.status_code == 400:
                # Symbole peut-être inexistant sur cette version de l'échange
                # (Certaines paires existent sur .com mais pas sur .us)
                return None
                
            else:
                print(f"[WARN] Erreur API Binance {symbol}: {response.status_code}")
                return None
                
        except Exception as e:
            # En cas d'erreur réseau, on essaie l'URL suivante si possible
            continue

    # Si on arrive ici, toutes les URLs ont échoué
    print("[X] Echec recuperation {} (Toutes API inaccessibles)".format(symbol))
    return None


def get_binance_klines_range(symbol: str, interval: str = '15m', start_time_ms: Optional[int] = None,
                             end_time_ms: Optional[int] = None, max_bars: Optional[int] = None) -> Optional[pd.DataFrame]:
    """
    Récupère les bougies sur une plage de temps (pour backtest).
    Boucle par chunks de 1000 (limite API Binance) jusqu'à end_time ou max_bars.
    
    Args:
        symbol: Paire (ex: BTCUSDT)
        interval: 15m, 1h, 4h, etc.
        start_time_ms: Début en millisecondes (epoch). Si None = il y a 6 mois.
        end_time_ms: Fin en millisecondes. Si None = maintenant.
        max_bars: Nombre max de bougies à récupérer (ex: 10000).
    
    Returns:
        DataFrame OHLCV trié par timestamp croissant, ou None.
    """
    import time as _time
    base_urls = [
        "https://api.binance.com/api/v3/klines",
        "https://api.binance.us/api/v3/klines"
    ]
    valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d']
    if interval not in valid_intervals:
        interval = '15m'

    now_ms = int(_time.time() * 1000)
    if end_time_ms is None:
        end_time_ms = now_ms
    if start_time_ms is None:
        # ~6 mois en 15m ≈ 17 500 bougies
        start_time_ms = end_time_ms - (180 * 24 * 60 * 60 * 1000)

    all_rows = []
    current_start = start_time_ms
    chunk_size = 1000

    while current_start < end_time_ms:
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'startTime': current_start,
            'endTime': end_time_ms,
            'limit': chunk_size
        }
        for base_url in base_urls:
            try:
                response = requests.get(base_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if not data:
                        current_start = end_time_ms
                        break
                    all_rows.extend(data)
                    if len(data) < chunk_size:
                        current_start = end_time_ms
                        break
                    current_start = data[-1][0] + 1
                    if max_bars and len(all_rows) >= max_bars:
                        all_rows = all_rows[:max_bars]
                        current_start = end_time_ms
                    _time.sleep(0.12)
                    break
                elif response.status_code == 451:
                    continue
                elif response.status_code == 429:
                    _time.sleep(2)
                    continue
                else:
                    continue
            except Exception:
                continue
        else:
            break

    if not all_rows:
        return None

    df = pd.DataFrame(all_rows, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
    return df


def fetch_klines(symbol: str, interval: str = '15m', limit: int = 200) -> Tuple[Optional[pd.DataFrame], Optional[float]]:
    """
    Récupère les données et le prix actuel pour une paire.
    """
    df = get_binance_klines(symbol, interval, limit)
    
    real_price = None
    if df is not None and not df.empty:
        real_price = df.iloc[-1]['close']
    
    return df, real_price


def _fetch_one(args):
    """Helper pour le fetch parallele."""
    symbol, interval, limit = args
    df, real_price = fetch_klines(symbol, interval, limit)
    return symbol, df, real_price

def fetch_multiple_pairs(symbols: List[str] = None, interval: str = '15m', limit: int = 200) -> Tuple[Dict[str, pd.DataFrame], Dict[str, float]]:
    """
    Recupere les donnees pour une liste de paires en PARALLELE (5x plus rapide).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if symbols is None or len(symbols) == 0:
        symbols = TOP_USDT_PAIRS

    data = {}
    real_prices = {}
    total = len(symbols)
    success_count = 0

    print("Fetch parallele {} paires...".format(total))

    args_list = [(s, interval, limit) for s in symbols]
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_fetch_one, args): args[0] for args in args_list}
        for future in as_completed(futures):
            try:
                symbol, df, real_price = future.result()
                if df is not None and real_price is not None:
                    data[symbol] = df
                    real_prices[symbol] = real_price
                    success_count += 1
            except Exception:
                pass

    print("{}/{} paires OK.".format(success_count, total))
    return data, real_prices

def get_top_pairs() -> List[str]:
    """Retourne simplement la liste des paires configurées."""
    return TOP_USDT_PAIRS


def fetch_current_prices(symbols: List[str]) -> Dict[str, float]:
    """
    Récupère le prix actuel pour une liste de paires (API ticker Binance, léger).
    Utile pour le dashboard quand des positions ne sont pas dans last_prices.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    prices = {}
    if not symbols:
        return prices
    urls = [
        "https://api.binance.com/api/v3/ticker/price",
        "https://api.binance.us/api/v3/ticker/price",
    ]
    def _get_one(sym):
        for base in urls:
            try:
                r = requests.get(base, params={"symbol": sym.upper()}, timeout=3)
                if r.status_code == 200:
                    d = r.json()
                    return sym, float(d.get("price", 0))
            except Exception:
                continue
        return sym, None
    with ThreadPoolExecutor(max_workers=min(5, len(symbols))) as ex:
        futs = {ex.submit(_get_one, s): s for s in symbols}
        for fut in as_completed(futs):
            try:
                sym, price = fut.result()
                if price is not None:
                    prices[sym] = price
            except Exception:
                pass
    return prices


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
        recommendation = "[OK] FORT: Toutes les timeframes sont haussières"
    elif bearish_count == total:
        consensus = 'Bearish'
        alignment_score = 100
        recommendation = "[OK] FORT: Toutes les timeframes sont baissières"
    elif bullish_count > bearish_count:
        consensus = 'Bullish'
        alignment_score = int((bullish_count / total) * 100)
        recommendation = f"[WARN] MODÉRÉ: {bullish_count}/{total} timeframes haussières"
    elif bearish_count > bullish_count:
        consensus = 'Bearish'
        alignment_score = int((bearish_count / total) * 100)
        recommendation = f"[WARN] MODÉRÉ: {bearish_count}/{total} timeframes baissières"
    else:
        consensus = 'Mixed'
        alignment_score = 0
        recommendation = "[X] CONFLICTUEL: Timeframes en désaccord, attendre"
    
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
        reason = f"[X] Signal {signal} rejeté: Timeframes en conflit"
    elif mtf['consensus'] != expected_consensus:
        reason = f"[X] Signal {signal} rejeté: Tendance globale {mtf['consensus']}"
    elif mtf['alignment_score'] < 66:
        reason = f"[WARN] Signal {signal} faible: Alignement {mtf['alignment_score']}%"
    else:
        reason = f"[OK] Signal {signal} confirmé: {mtf['recommendation']}"
    
    return {
        'is_valid': is_valid,
        'alignment_score': mtf['alignment_score'],
        'reason': reason,
        'details': mtf
    }


def fetch_order_flow(symbol: str, limit: int = 500) -> Dict:
    """
    Analyse l'order flow: ratio buy/sell des trades recents.
    Utilise l'API Binance aggTrades.
    """
    try:
        url = f"{BASE_URL}/api/v3/trades"
        params = {'symbol': symbol, 'limit': limit}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            return {'buy_ratio': 0.5, 'imbalance': 0.0, 'pressure': 'NEUTRAL'}
        
        trades = resp.json()
        buy_volume = 0.0
        sell_volume = 0.0
        
        for t in trades:
            qty = float(t.get('qty', 0)) * float(t.get('price', 0))
            if t.get('isBuyerMaker', False):
                sell_volume += qty
            else:
                buy_volume += qty
        
        total = buy_volume + sell_volume
        if total == 0:
            return {'buy_ratio': 0.5, 'imbalance': 0.0, 'pressure': 'NEUTRAL'}
        
        buy_ratio = buy_volume / total
        imbalance = (buy_volume - sell_volume) / total
        
        if imbalance > 0.15:
            pressure = 'BUY'
        elif imbalance < -0.15:
            pressure = 'SELL'
        else:
            pressure = 'NEUTRAL'
        
        return {
            'buy_ratio': round(buy_ratio, 3),
            'imbalance': round(imbalance, 3),
            'pressure': pressure,
        }
    except Exception:
        return {'buy_ratio': 0.5, 'imbalance': 0.0, 'pressure': 'NEUTRAL'}


def fetch_orderbook_depth(symbol: str, levels: int = 20) -> Dict:
    """
    Analyse la profondeur du carnet d'ordres sur plusieurs niveaux.
    Detecte les desequilibres bid/ask et les murs d'ordres.
    """
    try:
        url = f"{BASE_URL}/api/v3/depth"
        params = {'symbol': symbol, 'limit': levels}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            return {'bid_depth': 0, 'ask_depth': 0, 'depth_imbalance': 0, 'wall_detected': None}
        
        data = resp.json()
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        bid_depth = sum(float(b[0]) * float(b[1]) for b in bids)
        ask_depth = sum(float(a[0]) * float(a[1]) for a in asks)
        
        total_depth = bid_depth + ask_depth
        if total_depth == 0:
            return {'bid_depth': 0, 'ask_depth': 0, 'depth_imbalance': 0, 'wall_detected': None}
        
        depth_imbalance = (bid_depth - ask_depth) / total_depth
        
        wall_detected = None
        if bids:
            avg_bid_size = bid_depth / len(bids)
            for b in bids:
                size = float(b[0]) * float(b[1])
                if size > avg_bid_size * 5:
                    wall_detected = 'BID_WALL'
                    break
        if asks and wall_detected is None:
            avg_ask_size = ask_depth / len(asks)
            for a in asks:
                size = float(a[0]) * float(a[1])
                if size > avg_ask_size * 5:
                    wall_detected = 'ASK_WALL'
                    break
        
        return {
            'bid_depth': round(bid_depth, 2),
            'ask_depth': round(ask_depth, 2),
            'depth_imbalance': round(depth_imbalance, 3),
            'wall_detected': wall_detected,
        }
    except Exception:
        return {'bid_depth': 0, 'ask_depth': 0, 'depth_imbalance': 0, 'wall_detected': None}