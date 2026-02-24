# -*- coding: utf-8 -*-
"""
Stratégie DAY TRADING PRO — LONG et SHORT.

Risk management optimal: analyse technique + filtres qualité (ADX, volume, tendance 15m/1h)
pour maximiser les gains sur la durée tout en protégeant le capital.
"""


# Seuil ADX minimum (risk mgt: tendance claire = meilleure qualité des setups)
ADX_MIN_FOR_TREND = 18


# ─── LONG (acheter les dips / momentum haussier) ─────────────────────────────

def signal_long_buy_dip(df, indicators, volume_ratio_min=1.0):
    """
    Détecte une opportunité LONG (achat sur force haussière ou rebond).

    Conditions (toutes requises):
      1. Tendance haussière: price_momentum == 'BULLISH'.
      2. Prix au-dessus ou proche EMA21 (confirmation tendance).
      3. ADX >= 18 (tendance présente).
      4. RSI pas en surchauffe: RSI < 70 et (RSI > 40 ou RSI en hausse).
      5. Dernière bougie haussière (close > open).
      6. Volume >= volume_ratio_min × moyenne.
    """
    if indicators.get('price_momentum') != 'BULLISH':
        return False

    current = indicators.get('current_price')
    ema21 = indicators.get('ema21')
    if current is None or ema21 is None or current <= 0:
        return False
    if current < ema21 * 0.995:  # Légèrement sous EMA21 OK (dip), pas trop
        return False

    adx = indicators.get('adx')
    if adx is not None and adx < ADX_MIN_FOR_TREND:
        return False

    rsi = indicators.get('rsi14')
    rsi_prev = indicators.get('rsi14_prev')
    if rsi is None:
        return False
    if rsi >= 70:  # Surchauffé
        return False
    if rsi < 40 and (rsi_prev is None or rsi <= rsi_prev):  # Encore trop faible sans rebond
        return False

    is_bullish = indicators.get('open_price') is not None and current > indicators.get('open_price')
    if not is_bullish:
        return False

    vol_ratio = indicators.get('volume_ratio')
    if vol_ratio is None or vol_ratio < volume_ratio_min:
        return False

    return True


def score_long_opportunity(indicators, spread_pct, atr_pct, momentum_15m='BULLISH', momentum_1h='BULLISH',
                           stop_loss_pct=1.0, take_profit_pct=2.0):
    """Score 0-100 pour une opportunité LONG (analyse technique poussée)."""
    score = 0.0
    rsi = indicators.get('rsi14') or 50
    # RSI: zone 45-65 idéale pour long (momentum sans surchauffe) → +8 à +25
    if 50 <= rsi < 60:
        score += 25
    elif 45 <= rsi < 50:
        score += 20
    elif 40 <= rsi < 45:
        score += 15
    elif 60 <= rsi < 70:
        score += 10
    elif 35 <= rsi < 40:
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

    if momentum_15m == 'BULLISH':
        score += 15
    elif momentum_15m == 'NEUTRAL':
        score += 7
    if momentum_1h == 'BULLISH':
        score += 15
    elif momentum_1h == 'NEUTRAL':
        score += 7

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
    if bb_percent is not None and bb_percent <= 0.4:  # Zone basse = bon point d'entrée long
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


# ─── SHORT (vendre les rallies / grandes baisses) ─────────────────────────────

def signal_short_big_drop(df, indicators, volume_ratio_min=1.0):
    """
    Détecte une opportunité SHORT sur une grande baisse.

    Conditions (toutes requises):
      1. Tendance baissière: price_momentum == 'BEARISH'.
      2. Prix sous EMA21 (confirmation tendance).
      3. ADX >= 18 (tendance présente, pas de range plat).
      4. RSI < 55 (pas d'achat fort) ou RSI en baisse (rsi14 < rsi14_prev).
      5. Dernière bougie baissière (close < open) ou pattern bearish.
      6. Volume >= volume_ratio_min × moyenne (confirmation).

    Returns:
        True si signal SHORT valide, False sinon.
    """
    if indicators.get('price_momentum') != 'BEARISH':
        return False

    current = indicators.get('current_price')
    ema21 = indicators.get('ema21')
    if current is None or ema21 is None or current >= ema21:
        return False

    # Analyse technique poussée: tendance suffisamment marquée (ADX)
    adx = indicators.get('adx')
    if adx is not None and adx < ADX_MIN_FOR_TREND:
        return False

    rsi = indicators.get('rsi14')
    rsi_prev = indicators.get('rsi14_prev')
    if rsi is None:
        return False
    if rsi >= 55 and (rsi_prev is None or rsi >= rsi_prev):
        return False

    # Bougie baissière ou pattern bearish
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
                           stop_loss_pct=1.0, take_profit_pct=2.0):
    """
    Calcule un score de 0 à 100 pour une opportunité SHORT (analyse technique poussée).
    Critères: RSI, volume, MACD, ADX, Bollinger, tendances 15m/1h, spread, ATR.
    Retourne aussi un dict avec toutes les infos pour l'affichage (ranking).
    """
    score = 0.0
    rsi = indicators.get('rsi14')
    if rsi is None:
        rsi = 50
    # RSI: plus c'est bas, plus c'est bearish → +0 à +25 pts
    if rsi < 35:
        score += 25
    elif rsi < 45:
        score += 20
    elif rsi < 50:
        score += 15
    elif rsi < 55:
        score += 8

    vol_ratio = indicators.get('volume_ratio') or 0
    # Volume: plus c'est élevé, plus la confirmation est forte → +0 à +20 pts
    if vol_ratio >= 2.0:
        score += 20
    elif vol_ratio >= 1.5:
        score += 15
    elif vol_ratio >= 1.2:
        score += 10
    elif vol_ratio >= 1.0:
        score += 5

    # Tendance 15m baissière → +15 pts
    if momentum_15m == 'BEARISH':
        score += 15
    # Tendance 1h baissière → +15 pts ; 1h neutre → +7 pts (pour TREND_1H_ALLOW_NEUTRAL)
    if momentum_1h == 'BEARISH':
        score += 15
    elif momentum_1h == 'NEUTRAL':
        score += 7

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
        'spread_pct': round(spread_pct, 2),
        'atr_pct': round(atr_pct, 2),
        'rr_ratio': round(rr_ratio, 1),
        'adx': round(adx, 1) if adx is not None else None,
        'macd_bearish': macd_hist is not None and macd_hist < 0,
    }
