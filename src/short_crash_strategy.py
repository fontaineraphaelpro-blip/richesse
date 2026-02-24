# -*- coding: utf-8 -*-
"""
Stratégie DAY TRADING PRO — LONG et SHORT (SUIVI DE TENDANCE).

Le bot suit la tendance et n'entre pas sur les rebonds (pas d'achat oversold, pas de short oversold).
- LONG: continuation haussière (prix au-dessus de l'EMA, RSI dans la zone tendance).
- SHORT: continuation baissière (prix sous EMA, RSI pas en zone rebond).
"""


# Seuil ADX minimum (tendance claire, pas de range)
ADX_MIN_FOR_TREND = 18
# RSI: éviter les zones de rebond (oversold = bounce long, oversold short = bounce short)
RSI_LONG_MIN = 45   # Pas d'achat si RSI < 45 (rebond oversold)
RSI_SHORT_MIN = 30  # Pas de short si RSI < 30 (rebond après panique)
# Prix doit être clairement dans la tendance (pas "dip" à acheter)
LONG_PRICE_ABOVE_EMA_PCT = 0.1   # Prix >= EMA21 * (1 + 0.1%) = dans la tendance

# SL/TP dynamiques basés sur l'ATR (volatilité du graphique)
ATR_SL_MULTIPLIER = 1.5   # Distance SL = ATR * 1.5
ATR_TP_RR_RATIO = 2.0     # TP = SL_distance * 2 (R:R 2:1)
ATR_SL_MIN_PCT = 0.5      # SL min 0.5% si ATR très faible
ATR_SL_MAX_PCT = 5.0      # SL max 5% pour éviter des stops trop larges


def compute_sl_tp_from_chart(price, indicators, direction, sl_atr_mult=None, rr_ratio=None):
    """
    Calcule SL et TP à partir de la volatilité (ATR) du graphique.
    - SL = entry ± (ATR * sl_atr_mult)
    - TP = entry ± (ATR * sl_atr_mult * rr_ratio)
    direction: 'LONG' | 'SHORT'
    Returns: (stop_loss, take_profit, sl_pct_effective)
    """
    if price is None or price <= 0:
        return None, None, None
    sl_mult = sl_atr_mult if sl_atr_mult is not None else ATR_SL_MULTIPLIER
    rr = rr_ratio if rr_ratio is not None else ATR_TP_RR_RATIO
    atr = indicators.get('atr')
    atr_pct = indicators.get('atr_percent')
    if atr is None and atr_pct is not None and atr_pct > 0:
        atr = price * (atr_pct / 100.0)
    if atr is None or atr <= 0:
        atr = price * (ATR_SL_MIN_PCT / 100.0)
    sl_distance = atr * sl_mult
    sl_distance_pct = (sl_distance / price) * 100
    sl_distance_pct = max(ATR_SL_MIN_PCT, min(ATR_SL_MAX_PCT, sl_distance_pct))
    sl_distance = price * (sl_distance_pct / 100.0)
    tp_distance = sl_distance * rr
    if direction == 'LONG':
        stop_loss = price - sl_distance
        take_profit = price + tp_distance
    else:
        stop_loss = price + sl_distance
        take_profit = price - tp_distance
    sl_pct_effective = (sl_distance / price) * 100
    return stop_loss, take_profit, sl_pct_effective


# ─── LONG (continuation haussière, pas d'achat de rebond) ────────────────────

def signal_long_buy_dip(df, indicators, volume_ratio_min=1.0):
    """
    Détecte une opportunité LONG en SUIVI DE TENDANCE (continuation, pas de rebond oversold).

    Conditions (toutes requises):
      1. Tendance haussière: price_momentum == 'BULLISH'.
      2. Prix au-dessus de l'EMA21 (dans la tendance, pas en train de "dip").
      3. ADX >= 18 (tendance présente).
      4. RSI entre 45 et 70 (pas d'achat oversold = pas de trade rebond).
      5. Dernière bougie haussière (close > open).
      6. Volume >= volume_ratio_min × moyenne.
    """
    if indicators.get('price_momentum') != 'BULLISH':
        return False

    current = indicators.get('current_price')
    ema21 = indicators.get('ema21')
    if current is None or ema21 is None or current <= 0 or ema21 <= 0:
        return False
    # Prix clairement au-dessus de l'EMA = on suit la tendance, on n'achète pas un rebond
    if current < ema21 * (1 + LONG_PRICE_ABOVE_EMA_PCT / 100):
        return False

    adx = indicators.get('adx')
    if adx is not None and adx < ADX_MIN_FOR_TREND:
        return False

    rsi = indicators.get('rsi14')
    if rsi is None:
        return False
    if rsi >= 70:  # Surchauffé
        return False
    if rsi < RSI_LONG_MIN:  # Pas d'achat en zone oversold (rebond)
        return False

    is_bullish = indicators.get('open_price') is not None and current > indicators.get('open_price')
    if not is_bullish:
        return False

    vol_ratio = indicators.get('volume_ratio')
    if vol_ratio is None or vol_ratio < volume_ratio_min:
        return False

    return True


def score_long_opportunity(indicators, spread_pct, atr_pct, momentum_15m='BULLISH', momentum_1h='BULLISH',
                           momentum_4h=None, stop_loss_pct=1.0, take_profit_pct=2.0):
    """Score 0-100 pour une opportunité LONG (suivi tendance: zone 45-70). 4h alignée = bonus."""
    score = 0.0
    rsi = indicators.get('rsi14') or 50
    # RSI: zone 50-65 idéale pour continuation haussière (pas rebond)
    if 52 <= rsi < 62:
        score += 25
    elif 48 <= rsi < 52:
        score += 20
    elif 45 <= rsi < 48:
        score += 15
    elif 62 <= rsi < 70:
        score += 10

    vol_ratio = indicators.get('volume_ratio') or 0
    if vol_ratio >= 2.0:
        score += 20
    elif vol_ratio >= 1.5:
        score += 15
    elif vol_ratio >= 1.2:
        score += 10
    elif vol_ratio >= 1.0:
        score += 5

    if momentum_15m == 'BULLISH':
        score += 15
    elif momentum_15m == 'NEUTRAL':
        score += 7
    if momentum_1h == 'BULLISH':
        score += 15
    elif momentum_1h == 'NEUTRAL':
        score += 7
    if momentum_4h == 'BULLISH':
        score += 10
    elif momentum_4h == 'NEUTRAL':
        score += 5

    macd_hist = indicators.get('macd_hist')
    if macd_hist is not None and macd_hist > 0:
        score += 5

    adx = indicators.get('adx')
    if adx is not None:
        if adx >= 25:
            score += 5
        elif adx >= 20:
            score += 2

    bb_percent = indicators.get('bb_percent')
    if bb_percent is not None and 0.3 <= bb_percent <= 0.6:  # Ni oversold ni suracheté = tendance
        score += 3

    if spread_pct < 0.05:
        score += 10
    elif spread_pct < 0.10:
        score += 7
    elif spread_pct < 0.15:
        score += 4

    if atr_pct is None:
        atr_pct = 2.0
    if 1.0 <= atr_pct <= 3.0:
        score += 10
    elif atr_pct <= 4.0:
        score += 5

    current = indicators.get('current_price')
    ema21 = indicators.get('ema21')
    if current and ema21 and ema21 > 0 and current > ema21:
        dist_pct = ((current - ema21) / ema21) * 100
        if dist_pct > 0.5:
            score += 5

    score = min(100, round(score, 1))
    rr_ratio = take_profit_pct / stop_loss_pct if stop_loss_pct else 0
    return {
        'score': score,
        'rsi': round(rsi, 1),
        'volume_ratio': round(vol_ratio, 2),
        'momentum_15m': momentum_15m or '-',
        'momentum_1h': momentum_1h or '-',
        'momentum_4h': momentum_4h or '-',
        'spread_pct': round(spread_pct, 2),
        'atr_pct': round(atr_pct, 2),
        'rr_ratio': round(rr_ratio, 1),
        'adx': round(adx, 1) if adx is not None else None,
        'macd_bullish': macd_hist is not None and macd_hist > 0,
    }


def position_size_long_usdt(balance_usdt, risk_pct=0.01, sl_pct=1.0, max_pct_balance=0.25, min_usdt=10):
    """
    Taille de position LONG en USDT (pas de levier).
    Risque = risk_pct du capital. Perte si SL = position * (sl_pct/100).
    => position = (balance * risk_pct) / (sl_pct/100)
    """
    if balance_usdt <= 0:
        return 0.0
    risk_amount = balance_usdt * risk_pct
    position_by_risk = risk_amount * 100 / sl_pct
    position_by_cap = balance_usdt * max_pct_balance
    position = min(position_by_risk, position_by_cap)
    return max(min_usdt, min(position, balance_usdt * 0.98))


# ─── SHORT (continuation baissière, pas de short sur rebond) ───────────────────

def signal_short_big_drop(df, indicators, volume_ratio_min=1.0):
    """
    Détecte une opportunité SHORT en SUIVI DE TENDANCE (continuation, pas de short oversold).

    Conditions (toutes requises):
      1. Tendance baissière: price_momentum == 'BEARISH'.
      2. Prix sous EMA21 (confirmation tendance).
      3. ADX >= 18 (tendance présente).
      4. RSI >= 30 (pas de short en zone rebond oversold) et RSI < 55 (pas de force acheteuse).
      5. RSI pas en forte remontée (pas de rebond en cours): rsi <= rsi_prev + 5.
      6. Dernière bougie baissière (close < open).
      7. Volume >= volume_ratio_min × moyenne.

    Returns:
        True si signal SHORT valide, False sinon.
    """
    if indicators.get('price_momentum') != 'BEARISH':
        return False

    current = indicators.get('current_price')
    ema21 = indicators.get('ema21')
    if current is None or ema21 is None or current >= ema21:
        return False

    adx = indicators.get('adx')
    if adx is not None and adx < ADX_MIN_FOR_TREND:
        return False

    rsi = indicators.get('rsi14')
    rsi_prev = indicators.get('rsi14_prev')
    if rsi is None:
        return False
    if rsi < RSI_SHORT_MIN:  # Pas de short en zone rebond (oversold)
        return False
    if rsi >= 55 and (rsi_prev is None or rsi >= rsi_prev):  # Pas de force acheteuse
        return False
    # Pas de short si RSI remonte fort (rebond en cours)
    if rsi_prev is not None and rsi > rsi_prev + 5:
        return False

    # Bougie baissière
    is_bearish = indicators.get('is_bearish_candle', False)
    open_p = indicators.get('open_price')
    if open_p is not None and current is not None and open_p > 0:
        if current < open_p:
            is_bearish = True
    if not is_bearish:
        return False

    vol_ratio = indicators.get('volume_ratio')
    if vol_ratio is None or vol_ratio < volume_ratio_min:
        return False

    return True


def position_size_usdt(balance_usdt, risk_pct=0.01, sl_pct=1.0, leverage=10, max_pct_balance=0.25, min_usdt=10):
    """
    Taille de position SHORT (marge en USDT) selon le risque par trade.
    Risque max = risk_pct du capital. Perte si SL = marge * leverage * (sl_pct/100).
    => marge = (balance * risk_pct) / (leverage * sl_pct/100)
    """
    if balance_usdt <= 0:
        return 0.0
    risk_amount = balance_usdt * risk_pct
    margin_by_risk = risk_amount * 100 / (leverage * sl_pct)
    margin_by_cap = balance_usdt * max_pct_balance
    margin = min(margin_by_risk, margin_by_cap)
    return max(min_usdt, min(margin, balance_usdt * 0.98))


def score_short_opportunity(indicators, spread_pct, atr_pct, momentum_15m='BEARISH', momentum_1h='BEARISH',
                           momentum_4h=None, stop_loss_pct=1.0, take_profit_pct=2.0):
    """
    Calcule un score de 0 à 100 pour une opportunité SHORT.
    Critères: RSI, volume, MACD, ADX, Bollinger, tendances 15m/1h/4h, spread, ATR.
    """
    score = 0.0
    rsi = indicators.get('rsi14')
    if rsi is None:
        rsi = 50
    # RSI: zone 30-50 idéale pour continuation baissière (pas oversold = pas rebond)
    if 35 <= rsi < 45:
        score += 25
    elif 30 <= rsi < 35:
        score += 20
    elif 45 <= rsi < 50:
        score += 15
    elif 50 <= rsi < 55:
        score += 8

    vol_ratio = indicators.get('volume_ratio') or 0
    if vol_ratio >= 2.0:
        score += 20
    elif vol_ratio >= 1.5:
        score += 15
    elif vol_ratio >= 1.2:
        score += 10
    elif vol_ratio >= 1.0:
        score += 5

    if momentum_15m == 'BEARISH':
        score += 15
    if momentum_1h == 'BEARISH':
        score += 15
    elif momentum_1h == 'NEUTRAL':
        score += 7
    if momentum_4h == 'BEARISH':
        score += 10
    elif momentum_4h == 'NEUTRAL':
        score += 5

    # MACD bearish (momentum baissier) → +5 pts
    macd_hist = indicators.get('macd_hist')
    if macd_hist is not None and macd_hist < 0:
        score += 5

    # ADX: tendance forte = meilleure qualité de setup → +2 à +5 pts
    adx = indicators.get('adx')
    if adx is not None:
        if adx >= 25:
            score += 5
        elif adx >= 20:
            score += 2

    # Bollinger: prix en zone haute (potentiel short) → +3 pts si au-dessus du milieu
    bb_percent = indicators.get('bb_percent')
    if bb_percent is not None and bb_percent >= 0.6:
        score += 3

    # Spread faible = bougie propre → +0 à +10 pts (spread < 0.05% = 10, < 0.1% = 7, < 0.15% = 4)
    if spread_pct < 0.05:
        score += 10
    elif spread_pct < 0.10:
        score += 7
    elif spread_pct < 0.15:
        score += 4

    # ATR modéré (pas trop de bruit) → +0 à +10 pts (ATR 1-3% = 10, 3-4% = 5)
    if atr_pct is None:
        atr_pct = 2.0
    if 1.0 <= atr_pct <= 3.0:
        score += 10
    elif atr_pct <= 4.0:
        score += 5

    # Prix sous EMA21 (déjà requis pour le signal) → +5 pts
    current = indicators.get('current_price')
    ema21 = indicators.get('ema21')
    if current and ema21 and ema21 > 0 and current < ema21:
        dist_pct = ((ema21 - current) / ema21) * 100
        if dist_pct > 1.0:
            score += 5  # bien en dessous

    score = min(100, round(score, 1))
    rr_ratio = take_profit_pct / stop_loss_pct if stop_loss_pct else 0
    return {
        'score': score,
        'rsi': round(rsi, 1),
        'volume_ratio': round(vol_ratio, 2),
        'momentum_15m': momentum_15m or '-',
        'momentum_1h': momentum_1h or '-',
        'momentum_4h': momentum_4h or '-',
        'spread_pct': round(spread_pct, 2),
        'atr_pct': round(atr_pct, 2),
        'rr_ratio': round(rr_ratio, 1),
        'adx': round(adx, 1) if adx is not None else None,
        'macd_bearish': macd_hist is not None and macd_hist < 0,
    }
