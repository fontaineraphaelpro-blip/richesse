# -*- coding: utf-8 -*-
"""
Day Trader Pro Adaptive - Detection dynamique des opportunites.
Pas de strategie fixe: combine une multitude d'indicateurs pour scorer
chaque paire en LONG et SHORT. S'adapte au regime de marche.
H24: detecte quand et ou rentrer via confluence maximale.
"""

from typing import Dict, Any, Optional, Tuple


def score_adaptive(
    indicators: Dict[str, Any],
    momentum_15m: str,
    momentum_1h: str,
    momentum_4h: Optional[str],
    spread_pct: float,
    atr_pct: float,
    momentum_5m: Optional[str] = None,
    order_flow: Optional[Dict] = None,
    depth_imbalance: Optional[float] = None,
    fear_greed: Optional[int] = None,
) -> Tuple[float, float, str]:
    """
    Score composite LONG et SHORT (0-100).
    Base explicite: RSI, MACD, Bollinger Bands, VWAP, ATR (core).
    Puis regime, confluence, autres indicateurs.
    Returns: (score_long, score_short, regime)
    """
    regime = indicators.get('market_regime', 'UNKNOWN')
    rsi = indicators.get('rsi14')
    macd_hist = indicators.get('macd_hist')
    adx = indicators.get('adx')
    bb_pct = indicators.get('bb_percent')
    ema21 = indicators.get('ema21')
    vol_ratio = indicators.get('volume_ratio')
    stoch_k = indicators.get('stoch_k')
    stoch_d = indicators.get('stoch_d')
    tenkan = indicators.get('tenkan')
    kijun = indicators.get('kijun')
    price = indicators.get('current_price')
    vwap_dist = indicators.get('vwap_distance_pct')
    rsi_bull_div = indicators.get('rsi_bullish_divergence')
    rsi_bear_div = indicators.get('rsi_bearish_divergence')
    obv_slope = indicators.get('obv_slope')
    mfi = indicators.get('mfi14')
    volume_poc = indicators.get('volume_poc')
    di_plus = indicators.get('di_plus')
    di_minus = indicators.get('di_minus')
    momentum_strength = indicators.get('momentum_strength') or 0
    value_area_high = indicators.get('value_area_high')
    value_area_low = indicators.get('value_area_low')
    open_price = indicators.get('open_price')
    in_vol_cluster = indicators.get('in_vol_cluster', False)
    vol_cluster_ratio = indicators.get('vol_cluster_ratio') or 1.0

    score_long = 50.0
    score_short = 50.0

    # --- VOLUME (obligatoire) ---
    if vol_ratio is None or vol_ratio < 1.0:
        return 0, 0, regime
    score_long += min(10, (vol_ratio - 1) * 5)
    score_short += min(10, (vol_ratio - 1) * 5)

    # --- SPREAD (penalite si trop large) ---
    if spread_pct > 0.15:
        score_long -= 15
        score_short -= 15
    elif spread_pct > 0.10:
        score_long -= 5
        score_short -= 5

    # ═══ CORE: RSI, MACD, Bollinger Bands, VWAP, ATR (base de la décision) ═══
    # 1) RSI (Relative Strength Index)
    if rsi is not None:
        if rsi < 30:
            score_long += 12
            score_short -= 8
        elif rsi < 40:
            score_long += 6
            score_short -= 3
        elif 45 <= rsi <= 58:
            score_long += 4
        elif 42 <= rsi <= 55:
            score_short += 4
        elif rsi > 70:
            score_short += 12
            score_long -= 8
        elif rsi > 60:
            score_short += 6
            score_long -= 3
    # 2) MACD (Moving Average Convergence Divergence) — histogramme
    if macd_hist is not None:
        if macd_hist > 0:
            score_long += 10
            score_short -= 6
        else:
            score_short += 10
            score_long -= 6
    # 3) Bollinger Bands (position du prix dans les bandes)
    if bb_pct is not None:
        if bb_pct < 0.2:
            score_long += 10
            score_short -= 6
        elif bb_pct < 0.4:
            score_long += 4
        elif bb_pct > 0.8:
            score_short += 10
            score_long -= 6
        elif bb_pct > 0.6:
            score_short += 4
    # 4) VWAP (Volume Weighted Average Price) — prix au-dessus / en-dessous
    if vwap_dist is not None:
        if vwap_dist > 0.5:
            score_long += 8
            score_short -= 5
        elif vwap_dist > 0.15:
            score_long += 3
        elif vwap_dist < -0.5:
            score_short += 8
            score_long -= 5
        elif vwap_dist < -0.15:
            score_short += 3
    # 5) ATR (Average True Range) — volatilité: zone raisonnable = confiance
    if atr_pct is not None and atr_pct > 0:
        if 0.8 <= atr_pct <= 4.0:
            score_long += 4
            score_short += 4
        elif atr_pct > 6:
            score_long -= 6
            score_short -= 6
        elif atr_pct > 4:
            score_long -= 2
            score_short -= 2

    # --- REGIME ADAPTATIF ---
    if regime == 'TRENDING':
        # Trend-following: MACD + momentum + ADX
        if macd_hist is not None:
            if macd_hist > 0:
                score_long += 12
                score_short -= 8
            else:
                score_short += 12
                score_long -= 8
        if adx is not None:
            if adx >= 25:
                score_long += 5
                score_short += 5
            elif adx >= 20:
                score_long += 2
                score_short += 2
        # Multi-TF momentum
        if momentum_15m == 'BULLISH':
            score_long += 6
            score_short -= 4
        elif momentum_15m == 'BEARISH':
            score_short += 6
            score_long -= 4
        if momentum_1h == 'BULLISH':
            score_long += 6
            score_short -= 4
        elif momentum_1h == 'BEARISH':
            score_short += 6
            score_long -= 4
        if momentum_4h == 'BULLISH':
            score_long += 4
            score_short -= 2
        elif momentum_4h == 'BEARISH':
            score_short += 4
            score_long -= 2

    elif regime == 'RANGING':
        # Mean reversion: RSI extremes + Bollinger
        if rsi is not None:
            if rsi < 35:
                score_long += 15
                score_short -= 10
            elif rsi < 45:
                score_long += 5
            elif rsi > 65:
                score_short += 15
                score_long -= 10
            elif rsi > 55:
                score_short += 5
        if bb_pct is not None:
            if bb_pct < 0.25:
                score_long += 8
            elif bb_pct > 0.75:
                score_short += 8
        # MACD crossover (reversal)
        if macd_hist is not None:
            if macd_hist > 0:
                score_long += 5
            else:
                score_short += 5

    else:  # VOLATILE ou UNKNOWN
        # Strict: besoin de forte confluence
        if macd_hist is not None and adx is not None and adx >= 25:
            if macd_hist > 0:
                score_long += 8
            else:
                score_short += 8
        if rsi is not None:
            if 40 < rsi < 60:
                score_long -= 5
                score_short -= 5  # zone neutre = moins d'edge

    # --- RSI (complément zones continuation, déjà traité en CORE) ---
    if rsi is not None:
        if 48 <= rsi <= 58:
            score_long += 2
        if 42 <= rsi <= 52:
            score_short += 2

    # --- PRICE MOMENTUM (15m) + force du momentum ---
    price_mom = indicators.get('price_momentum')
    if price_mom == 'BULLISH':
        score_long += 4
        score_short -= 3
        if momentum_strength >= 50:
            score_long += 3
            score_short -= 2
        elif momentum_strength >= 30:
            score_long += 1
    elif price_mom == 'BEARISH':
        score_short += 4
        score_long -= 3
        if momentum_strength >= 50:
            score_short += 3
            score_long -= 2
        elif momentum_strength >= 30:
            score_short += 1

    # --- INTRADAY BIAS ---
    intraday = indicators.get('intraday_bias')
    if intraday == 'BULLISH':
        score_long += 2
    elif intraday == 'BEARISH':
        score_short += 2

    # --- BOLLINGER (milieu de bande = neutre, déjà traité en CORE) ---
    if bb_pct is not None and 0.35 <= bb_pct <= 0.65:
        score_long += 1
        score_short += 1

    # --- ICHIMOKU ---
    if tenkan is not None and kijun is not None and price:
        if tenkan > kijun:
            score_long += 4
            score_short -= 2
        else:
            score_short += 4
            score_long -= 2

    # --- STOCHASTIC ---
    if stoch_k is not None and stoch_d is not None:
        if stoch_k > stoch_d and stoch_k < 80:
            score_long += 3
        elif stoch_k < stoch_d and stoch_k > 20:
            score_short += 3

    # --- EMA21 PROXIMITE ---
    if ema21 and price and ema21 > 0:
        dist_pct = abs(price - ema21) / ema21 * 100
        if dist_pct < 1.5:
            score_long += 3
            score_short += 3
        elif dist_pct > 3:
            score_long -= 5
            score_short -= 5

    # --- VWAP (proximité neutre uniquement, direction déjà en CORE) ---
    if vwap_dist is not None and -0.4 < vwap_dist < 0.4:
        score_long += 2
        score_short += 2

    # --- DIVERGENCES ---
    if rsi_bull_div:
        score_long += 8
    if rsi_bear_div:
        score_short += 8

    # --- OBV (On-Balance Volume) ---
    if obv_slope is not None:
        if obv_slope > 0:
            score_long += 6
            score_short -= 4
        else:
            score_short += 6
            score_long -= 4

    # --- MFI (Money Flow Index) ---
    if mfi is not None:
        if mfi < 25:
            score_long += 8
            score_short -= 5
        elif mfi < 40:
            score_long += 3
        elif mfi > 75:
            score_short += 8
            score_long -= 5
        elif mfi > 60:
            score_short += 3

    # --- DI+ / DI- (direction) ---
    if di_plus is not None and di_minus is not None:
        if di_plus > di_minus + 5:
            score_long += 4
            score_short -= 2
        elif di_minus > di_plus + 5:
            score_short += 4
            score_long -= 2

    # --- VOLUME POC + VALUE AREA (zones de valeur) ---
    if volume_poc and price and volume_poc > 0:
        dist_poc = abs(price - volume_poc) / volume_poc * 100
        if dist_poc < 0.5:
            score_long += 3
            score_short += 3
    if value_area_low and value_area_high and price and value_area_high > value_area_low:
        pct_in_range = (price - value_area_low) / (value_area_high - value_area_low)
        if pct_in_range < 0.2:
            score_long += 5
            score_short -= 2
        elif pct_in_range > 0.8:
            score_short += 5
            score_long -= 2

    # --- MOMENTUM 5m (scalping rapide) ---
    if momentum_5m == 'BULLISH':
        score_long += 4
        score_short -= 3
    elif momentum_5m == 'BEARISH':
        score_short += 4
        score_long -= 3

    # --- ORDER FLOW (confluence) ---
    if order_flow:
        pressure = order_flow.get('pressure', 'NEUTRAL')
        if pressure == 'BUY':
            score_long += 6
            score_short -= 4
        elif pressure == 'SELL':
            score_short += 6
            score_long -= 4

    # --- DEPTH IMBALANCE (order book) ---
    if depth_imbalance is not None:
        if depth_imbalance > 0.15:
            score_long += 4
            score_short -= 3
        elif depth_imbalance < -0.15:
            score_short += 4
            score_long -= 3

    # --- FEAR & GREED (sentiment) ---
    if fear_greed is not None:
        if fear_greed < 30:
            score_long += 4
            score_short -= 2
        elif fear_greed > 70:
            score_short += 4
            score_long -= 2

    # --- Dernière bougie (confirmations) ---
    if open_price and price and open_price > 0:
        if price > open_price:
            score_long += 2
            score_short -= 1
        elif price < open_price:
            score_short += 2
            score_long -= 1

    # --- Confluence bonus: plusieurs signaux alignés ---
    bull_signals = sum([
        1 if (price_mom == 'BULLISH' and momentum_strength >= 30) else 0,
        1 if (obv_slope is not None and obv_slope > 0) else 0,
        1 if (mfi is not None and mfi < 50) else 0,
        1 if (di_plus is not None and di_minus is not None and di_plus > di_minus) else 0,
        1 if (vwap_dist is not None and vwap_dist > 0) else 0,
    ])
    bear_signals = sum([
        1 if (price_mom == 'BEARISH' and momentum_strength >= 30) else 0,
        1 if (obv_slope is not None and obv_slope <= 0) else 0,
        1 if (mfi is not None and mfi > 50) else 0,
        1 if (di_plus is not None and di_minus is not None and di_minus > di_plus) else 0,
        1 if (vwap_dist is not None and vwap_dist < 0) else 0,
    ])
    if bull_signals >= 3:
        score_long += 5
        score_short -= 3
    if bear_signals >= 3:
        score_short += 5
        score_long -= 3

    # --- Vol cluster (éviter surpondérer en forte incertitude) ---
    if in_vol_cluster and vol_cluster_ratio > 1.5:
        score_long -= 2
        score_short -= 2

    # --- ATR (seuil extrême uniquement, reste déjà en CORE) ---
    if atr_pct is not None and atr_pct > 7:
        score_long -= 4
        score_short -= 4

    score_long = max(0, min(100, score_long))
    score_short = max(0, min(100, score_short))
    return round(score_long, 1), round(score_short, 1), regime


def get_best_direction(score_long: float, score_short: float, min_edge: float = 5) -> Optional[str]:
    """Retourne LONG, SHORT ou None si pas d'edge suffisant."""
    if score_long - score_short >= min_edge and score_long >= 55:
        return 'LONG'
    if score_short - score_long >= min_edge and score_short >= 55:
        return 'SHORT'
    return None
