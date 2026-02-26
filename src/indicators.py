"""
Module complet de calcul d'indicateurs techniques.
Optimisé pour le SWING TRADING et le DAY TRADING.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

# Import optionnel des patterns si le fichier existe
try:
    from pattern_detection import (
        detect_candlestick_patterns,
        detect_chart_patterns,
        find_liquidity_zones,
        calculate_fibonacci_levels
    )
    HAS_PATTERNS = True
except ImportError:
    HAS_PATTERNS = False


def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """Calcule la Moyenne Mobile Simple (SMA)."""
    return data.rolling(window=period).mean()


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """Calcule la Moyenne Mobile Exponentielle (EMA)."""
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calcule le RSI (Relative Strength Index).
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
    """
    Calcule le MACD (Trend & Momentum).
    """
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict:
    """
    Calcule les Bandes de Bollinger (Volatilité).
    """
    sma = calculate_sma(data, period)
    std = data.rolling(window=period).std()
    
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    return {
        'upper': upper,
        'middle': sma,
        'lower': lower,
        'width': (upper - lower) / sma  # Écartement des bandes (Bandwidth)
    }


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calcule l'ATR (Average True Range) pour les Stop Loss.
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


def calculate_adx(df: pd.DataFrame, period: int = 14) -> Dict:
    """
    Calcule l'ADX (Force de la tendance) + DI+ et DI-.
    ADX > 25 = Tendance forte.
    Returns: {'adx': Series, 'plus_di': Series, 'minus_di': Series}
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    dx_denominator = plus_di + minus_di
    dx = 100 * abs(plus_di - minus_di) / dx_denominator.replace(0, np.nan)
    adx = dx.rolling(window=period).mean()
    
    return {'adx': adx, 'plus_di': plus_di, 'minus_di': minus_di}


def calculate_stochastic(df: pd.DataFrame, period: int = 14, k_period: int = 3, d_period: int = 3) -> Dict:
    """
    Calcule l'Oscillateur Stochastique.
    """
    low_min = df['low'].rolling(window=period).min()
    high_max = df['high'].rolling(window=period).max()
    
    k = 100 * ((df['close'] - low_min) / (high_max - low_min))
    d = k.rolling(window=d_period).mean()  # Signal line
    
    return {'k': k, 'd': d}


def calculate_ichimoku(df: pd.DataFrame) -> Dict:
    """
    Calcule les bases d'Ichimoku (Tenkan & Kijun) pour confirmation supplémentaire.
    """
    # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2))
    period9_high = df['high'].rolling(window=9).max()
    period9_low = df['low'].rolling(window=9).min()
    tenkan_sen = (period9_high + period9_low) / 2

    # Kijun-sen (Base Line): (26-period high + 26-period low)/2))
    period26_high = df['high'].rolling(window=26).max()
    period26_low = df['low'].rolling(window=26).min()
    kijun_sen = (period26_high + period26_low) / 2
    
    return {'tenkan': tenkan_sen, 'kijun': kijun_sen}


def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """
    On-Balance Volume: cumul du volume selon la direction du prix.
    Confirme la force d'un mouvement (volume suit le prix).
    """
    if df is None or len(df) < 2:
        return pd.Series(dtype=float)
    close = df['close']
    volume = df['volume']
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv


def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Money Flow Index: RSI pondere par le volume.
    Combine prix et volume pour detecter surchauffe/oversold.
    """
    if df is None or len(df) < period + 2:
        return pd.Series(dtype=float)
    high = df['high']
    low = df['low']
    close = df['close']
    volume = df['volume']
    typical_price = (high + low + close) / 3
    raw_money_flow = typical_price * volume
    delta = typical_price.diff()
    positive_flow = raw_money_flow.where(delta > 0, 0).rolling(period).sum()
    negative_flow = raw_money_flow.where(delta < 0, 0).rolling(period).sum()
    mfi_ratio = positive_flow / negative_flow.replace(0, np.nan)
    mfi = 100 - (100 / (1 + mfi_ratio))
    return mfi


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Calcule le VWAP (Volume Weighted Average Price).
    Reference institutionnelle pour les entrees optimales.
    """
    if df is None or len(df) < 2:
        return pd.Series(dtype=float)
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    cumulative_tp_vol = (typical_price * df['volume']).cumsum()
    cumulative_vol = df['volume'].cumsum()
    vwap = cumulative_tp_vol / cumulative_vol.replace(0, np.nan)
    return vwap


def detect_volatility_cluster(df: pd.DataFrame, atr: pd.Series, lookback: int = 20) -> Dict:
    """
    Detecte les clusters de volatilite (haute vol suit haute vol).
    Retourne si on est dans un cluster et le ratio vs moyenne.
    """
    if atr is None or len(atr) < lookback + 5:
        return {'in_cluster': False, 'vol_ratio': 1.0}
    
    avg_atr = atr.iloc[-lookback:].mean()
    recent_atr = atr.iloc[-3:].mean()
    
    if pd.isna(avg_atr) or avg_atr == 0:
        return {'in_cluster': False, 'vol_ratio': 1.0}
    
    vol_ratio = recent_atr / avg_atr
    in_cluster = vol_ratio > 1.5
    
    return {
        'in_cluster': bool(in_cluster),
        'vol_ratio': float(vol_ratio),
    }


def detect_intraday_pattern(df: pd.DataFrame, lookback_days: int = 14) -> Dict:
    """
    Detecte les patterns intraday recurrents (heures favorables).
    Analyse les mouvements de prix par heure UTC sur les N derniers jours.
    """
    if df is None or len(df) < 50:
        return {'bullish_hours': [], 'bearish_hours': [], 'current_hour_bias': 'NEUTRAL'}
    
    try:
        df_copy = df.copy()
        if 'timestamp' in df_copy.columns:
            df_copy['hour'] = pd.to_datetime(df_copy['timestamp'], unit='ms').dt.hour
        else:
            df_copy['hour'] = list(range(len(df_copy)))
            return {'bullish_hours': [], 'bearish_hours': [], 'current_hour_bias': 'NEUTRAL'}
        
        df_copy['return_pct'] = df_copy['close'].pct_change() * 100
        
        hourly_stats = df_copy.groupby('hour')['return_pct'].agg(['mean', 'count'])
        hourly_stats = hourly_stats[hourly_stats['count'] >= 3]
        
        bullish_hours = hourly_stats[hourly_stats['mean'] > 0.05].index.tolist()
        bearish_hours = hourly_stats[hourly_stats['mean'] < -0.05].index.tolist()
        
        from datetime import datetime
        current_hour = datetime.utcnow().hour
        bias = 'NEUTRAL'
        if current_hour in bullish_hours:
            bias = 'BULLISH'
        elif current_hour in bearish_hours:
            bias = 'BEARISH'
        
        return {
            'bullish_hours': bullish_hours[:5],
            'bearish_hours': bearish_hours[:5],
            'current_hour_bias': bias,
        }
    except Exception:
        return {'bullish_hours': [], 'bearish_hours': [], 'current_hour_bias': 'NEUTRAL'}


def detect_rsi_divergence(df: pd.DataFrame, rsi: pd.Series, lookback: int = 14) -> Dict:
    """
    Detecte les divergences RSI (prix vs RSI).
    Bullish: prix fait un nouveau bas mais RSI non (signal de retournement haussier).
    Bearish: prix fait un nouveau haut mais RSI non (signal de retournement baissier).
    """
    if df is None or len(df) < lookback + 5 or len(rsi) < lookback + 5:
        return {'bullish_divergence': False, 'bearish_divergence': False}
    
    close = df['close']
    # Comparer les 2 derniers creux/sommets sur lookback bougies
    recent_low = close.iloc[-lookback:].min()
    prev_low = close.iloc[-2*lookback:-lookback].min()
    recent_high = close.iloc[-lookback:].max()
    prev_high = close.iloc[-2*lookback:-lookback].max()
    
    recent_rsi_at_low = rsi.iloc[-lookback:].min()
    prev_rsi_at_low = rsi.iloc[-2*lookback:-lookback].min()
    recent_rsi_at_high = rsi.iloc[-lookback:].max()
    prev_rsi_at_high = rsi.iloc[-2*lookback:-lookback].max()
    
    # Bullish: prix lower low, RSI higher low
    bullish_div = (recent_low < prev_low) and (recent_rsi_at_low > prev_rsi_at_low + 2)
    # Bearish: prix higher high, RSI lower high
    bearish_div = (recent_high > prev_high) and (recent_rsi_at_high < prev_rsi_at_high - 2)
    
    return {
        'bullish_divergence': bool(bullish_div),
        'bearish_divergence': bool(bearish_div),
    }


def calculate_volume_profile(df: pd.DataFrame, bins: int = 20, lookback: int = 100) -> Dict:
    """
    Calcule le Volume Profile: identifie les zones de prix avec le plus de volume (support/resistance).
    POC = Point of Control (prix avec le plus de volume = support/resistance majeur).
    """
    if df is None or len(df) < lookback:
        return {'poc': None, 'value_area_high': None, 'value_area_low': None}
    
    data = df.iloc[-lookback:]
    price_min = data['low'].min()
    price_max = data['high'].max()
    
    if price_max <= price_min:
        return {'poc': None, 'value_area_high': None, 'value_area_low': None}
    
    bin_edges = np.linspace(price_min, price_max, bins + 1)
    volume_at_price = np.zeros(bins)
    
    for _, row in data.iterrows():
        for j in range(bins):
            if row['low'] <= bin_edges[j+1] and row['high'] >= bin_edges[j]:
                volume_at_price[j] += row['volume'] / max(1, int((row['high'] - row['low']) / ((price_max - price_min) / bins)))
    
    poc_idx = np.argmax(volume_at_price)
    poc_price = (bin_edges[poc_idx] + bin_edges[poc_idx + 1]) / 2
    
    # Value Area (70% du volume)
    total_vol = volume_at_price.sum()
    if total_vol == 0:
        return {'poc': poc_price, 'value_area_high': price_max, 'value_area_low': price_min}
    
    sorted_indices = np.argsort(volume_at_price)[::-1]
    cumulative = 0
    va_indices = []
    for idx in sorted_indices:
        cumulative += volume_at_price[idx]
        va_indices.append(idx)
        if cumulative >= total_vol * 0.7:
            break
    
    va_low = bin_edges[min(va_indices)]
    va_high = bin_edges[max(va_indices) + 1]
    
    return {
        'poc': poc_price,
        'value_area_high': va_high,
        'value_area_low': va_low,
    }


def detect_market_regime(df: pd.DataFrame, adx: pd.Series, bb_width: pd.Series) -> str:
    """
    Detecte le regime de marche: TRENDING, RANGING, ou VOLATILE.
    - TRENDING: ADX > 25 (tendance forte)
    - RANGING: ADX < 20 et BB width faible (marche compresse)
    - VOLATILE: BB width eleve (forte volatilite sans direction)
    """
    if df is None or adx is None or bb_width is None:
        return 'UNKNOWN'
    if len(adx) < 5 or len(bb_width) < 5:
        return 'UNKNOWN'
    
    current_adx = adx.iloc[-1]
    avg_bb_width = bb_width.iloc[-10:].mean() if len(bb_width) >= 10 else bb_width.iloc[-1]
    
    if pd.isna(current_adx) or pd.isna(avg_bb_width):
        return 'UNKNOWN'
    
    if current_adx >= 25:
        return 'TRENDING'
    elif current_adx < 20 and avg_bb_width < 0.03:
        return 'RANGING'
    elif avg_bb_width > 0.06:
        return 'VOLATILE'
    elif current_adx >= 20:
        return 'TRENDING'
    else:
        return 'RANGING'


def calculate_indicators(df: pd.DataFrame) -> Dict:
    """
    Fonction MAÎTRESSE : Calcule TOUS les indicateurs et retourne un dictionnaire complet.
    
    Args:
        df: DataFrame avec colonnes: timestamp, open, high, low, close, volume
    
    Returns:
        Dictionnaire riche avec valeurs actuelles et état du marché.
    """
    if df is None or len(df) < 200:
        return {}
    
    close = df['close']
    volume = df['volume']
    
    # 1. MOYENNES MOBILES (Tendance)
    # ----------------------------------------
    sma50 = calculate_sma(close, 50)
    sma200 = calculate_sma(close, 200)
    ema9 = calculate_ema(close, 9)   # Pour entrées rapides
    ema21 = calculate_ema(close, 21) # Pour entrées rapides
    
    # 2. MOMENTUM & OSCILLATEURS
    # ----------------------------------------
    rsi14 = calculate_rsi(close, 14)
    macd_data = calculate_macd(close)
    stoch_data = calculate_stochastic(df)
    
    # 3. VOLATILITÉ & FORCE
    # ----------------------------------------
    atr = calculate_atr(df, 14)
    adx_data = calculate_adx(df, 14)
    adx = adx_data['adx'] if isinstance(adx_data, dict) else adx_data
    bb = calculate_bollinger_bands(close, 20, 2.0)
    
    # 3b. ICHIMOKU (Tenkan/Kijun pour confluence)
    # ----------------------------------------
    ichimoku = calculate_ichimoku(df)

    # 3c. VWAP
    vwap = calculate_vwap(df)

    # 4. VOLUME
    # ----------------------------------------
    volume_ma20 = calculate_sma(volume, 20)
    obv = calculate_obv(df)
    mfi14 = calculate_mfi(df, 14)
    
    # 5. PATTERNS & SUPPORTS (Si disponibles)
    # ----------------------------------------
    patterns = {}
    support_zones = []
    if HAS_PATTERNS:
        try:
            patterns = detect_candlestick_patterns(df)
            liquidity = find_liquidity_zones(df, lookback=100)
            support_zones = liquidity.get('support_zones', [])
        except Exception:
            pass

    # 6. MOMENTUM CONFIRMATION (Direction récente du prix)
    # ----------------------------------------
    # Vérifier si le prix MONTE ou DESCEND actuellement (dernières 3 bougies)
    price_momentum = 'NEUTRAL'
    momentum_strength = 0
    
    if len(close) >= 4:
        # Calculer le changement de prix sur les 3 dernières bougies
        price_3_candles_ago = close.iloc[-4]
        price_2_candles_ago = close.iloc[-3]
        price_1_candle_ago = close.iloc[-2]
        current = close.iloc[-1]
        
        # Changement en %
        change_3 = ((current - price_3_candles_ago) / price_3_candles_ago) * 100
        change_2 = ((current - price_2_candles_ago) / price_2_candles_ago) * 100
        
        # Vérifier si les bougies font des hauts plus hauts (bullish) ou bas plus bas (bearish)
        higher_highs = df['high'].iloc[-1] > df['high'].iloc[-2] and df['high'].iloc[-2] > df['high'].iloc[-3]
        lower_lows = df['low'].iloc[-1] < df['low'].iloc[-2] and df['low'].iloc[-2] < df['low'].iloc[-3]
        
        # Bougies vertes vs rouges (close > open = vert)
        green_candles = sum([
            1 if df['close'].iloc[-i] > df['open'].iloc[-i] else 0 
            for i in range(1, 4)
        ])
        red_candles = 3 - green_candles
        
        # Déterminer le momentum
        if change_3 > 0.5 and green_candles >= 2:
            price_momentum = 'BULLISH'
            momentum_strength = min(change_3 * 10, 100)  # Force du momentum
        elif change_3 < -0.5 and red_candles >= 2:
            price_momentum = 'BEARISH'
            momentum_strength = min(abs(change_3) * 10, 100)
        elif higher_highs:
            price_momentum = 'BULLISH'
            momentum_strength = 50
        elif lower_lows:
            price_momentum = 'BEARISH'
            momentum_strength = 50
    
    # 7. CONSTRUCTION DU DICTIONNAIRE FINAL
    # ----------------------------------------
    # On prend la dernière valeur (.iloc[-1]) pour le temps réel
    # On prend parfois l'avant-dernière (.iloc[-2]) pour confirmer une clôture
    
    current_price = close.iloc[-1]
    
    indicators = {
        # --- PRIX ---
        'current_price': current_price,
        'open_price': df['open'].iloc[-1],
        'high_price': df['high'].iloc[-1],
        'low_price': df['low'].iloc[-1],
        
        # --- MOYENNES MOBILES (Fondamental pour Swing) ---
        'sma50': sma50.iloc[-1],
        'sma200': sma200.iloc[-1],
        'ema9': ema9.iloc[-1],
        'ema21': ema21.iloc[-1],
        
        # Écarts (%) par rapport aux moyennes (utile pour détecter les extensions)
        'dist_sma50_percent': ((current_price - sma50.iloc[-1]) / sma50.iloc[-1]) * 100,
        'dist_sma200_percent': ((current_price - sma200.iloc[-1]) / sma200.iloc[-1]) * 100,
        
        # --- MOMENTUM ---
        'rsi14': rsi14.iloc[-1],
        'rsi14_prev': rsi14.iloc[-2], # Pour voir la pente du RSI
        
        'macd': macd_data['macd'].iloc[-1],
        'macd_signal': macd_data['signal'].iloc[-1],
        'macd_hist': macd_data['histogram'].iloc[-1],
        'macd_hist_prev': macd_data['histogram'].iloc[-2], # Pour détecter retournement MACD
        
        'stoch_k': stoch_data['k'].iloc[-1],
        'stoch_d': stoch_data['d'].iloc[-1],
        'stoch_k_prev': stoch_data['k'].iloc[-2] if len(stoch_data['k']) >= 2 else None,
        'stoch_d_prev': stoch_data['d'].iloc[-2] if len(stoch_data['d']) >= 2 else None,
        
        # --- VOLATILITÉ & TENDANCE ---
        'atr': atr.iloc[-1],
        'atr_percent': (atr.iloc[-1] / current_price) * 100,
        'adx': adx.iloc[-1],
        'di_plus': adx_data['plus_di'].iloc[-1] if isinstance(adx_data, dict) else None,
        'di_minus': adx_data['minus_di'].iloc[-1] if isinstance(adx_data, dict) else None,
        
        # --- BANDES DE BOLLINGER ---
        'bb_upper': bb['upper'].iloc[-1],
        'bb_lower': bb['lower'].iloc[-1],
        'bb_width': bb['width'].iloc[-1],
        'bb_percent': (current_price - bb['lower'].iloc[-1]) / (bb['upper'].iloc[-1] - bb['lower'].iloc[-1]) if (bb['upper'].iloc[-1] - bb['lower'].iloc[-1]) != 0 else 0.5,
        
        # --- VOLUME ---
        'current_volume': volume.iloc[-1],
        'volume_ma20': volume_ma20.iloc[-1] if not pd.isna(volume_ma20.iloc[-1]) else 0,
        'volume_ratio': volume.iloc[-1] / volume_ma20.iloc[-1] if (not pd.isna(volume_ma20.iloc[-1]) and volume_ma20.iloc[-1] > 0) else None,
        'obv': obv.iloc[-1] if len(obv) > 0 and not pd.isna(obv.iloc[-1]) else None,
        'obv_slope': (obv.iloc[-1] - obv.iloc[-5]) if len(obv) >= 5 else None,
        'mfi14': mfi14.iloc[-1] if len(mfi14) > 0 and not pd.isna(mfi14.iloc[-1]) else None,
        
        # --- PATTERNS & EXTRA ---
        'candlestick_patterns': patterns.get('patterns', []),
        'is_bearish_candle': patterns.get('has_bearish_pattern', False),
        'support_zones': support_zones,
        
        # --- ICHIMOKU ---
        'tenkan': ichimoku['tenkan'].iloc[-1] if not pd.isna(ichimoku['tenkan'].iloc[-1]) else None,
        'kijun': ichimoku['kijun'].iloc[-1] if not pd.isna(ichimoku['kijun'].iloc[-1]) else None,

        # --- MOMENTUM CONFIRMATION (TREND FOLLOWING) ---
        'price_momentum': price_momentum,        # 'BULLISH', 'BEARISH', 'NEUTRAL'
        'momentum_strength': momentum_strength,  # 0-100

        # --- RSI DIVERGENCE ---
        'rsi_bullish_divergence': False,
        'rsi_bearish_divergence': False,
        
        # --- VOLUME PROFILE ---
        'volume_poc': None,
        'value_area_high': None,
        'value_area_low': None,
        
        # --- MARKET REGIME ---
        'market_regime': 'UNKNOWN',

        # --- VWAP ---
        'vwap': vwap.iloc[-1] if len(vwap) > 0 and not pd.isna(vwap.iloc[-1]) else None,
        'vwap_distance_pct': ((close.iloc[-1] - vwap.iloc[-1]) / vwap.iloc[-1] * 100) if (len(vwap) > 0 and not pd.isna(vwap.iloc[-1]) and vwap.iloc[-1] > 0) else None,
        
        # --- VOLATILITY CLUSTER ---
        'in_vol_cluster': False,
        'vol_cluster_ratio': 1.0,
        
        # --- INTRADAY PATTERN ---
        'intraday_bias': 'NEUTRAL',
    }
    
    # Calcul des nouvelles métriques
    try:
        rsi_div = detect_rsi_divergence(df, rsi14)
        indicators['rsi_bullish_divergence'] = rsi_div['bullish_divergence']
        indicators['rsi_bearish_divergence'] = rsi_div['bearish_divergence']
    except Exception:
        pass
    
    try:
        vp = calculate_volume_profile(df)
        indicators['volume_poc'] = vp['poc']
        indicators['value_area_high'] = vp['value_area_high']
        indicators['value_area_low'] = vp['value_area_low']
    except Exception:
        pass
    
    try:
        indicators['market_regime'] = detect_market_regime(df, adx, bb['width'])
    except Exception:
        pass

    try:
        vol_cluster = detect_volatility_cluster(df, atr)
        indicators['in_vol_cluster'] = vol_cluster['in_cluster']
        indicators['vol_cluster_ratio'] = vol_cluster['vol_ratio']
    except Exception:
        pass
    
    try:
        intraday = detect_intraday_pattern(df)
        indicators['intraday_bias'] = intraday['current_hour_bias']
    except Exception:
        pass

    # Nettoyage des valeurs NaN (au cas où)
    for k, v in indicators.items():
        if isinstance(v, (float, np.float64, np.float32)) and np.isnan(v):
            indicators[k] = None
            
    return indicators
