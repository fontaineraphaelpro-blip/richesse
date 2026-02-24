# -*- coding: utf-8 -*-
"""
Stratégie SHORT uniquement — Trader les grandes baisses.

Le bot n'ouvre que des positions SHORT quand une forte baisse est détectée:
  - Tendance baissière (prix sous EMA21, momentum BEARISH).
  - RSI confirme (sous 50 ou en chute depuis suracheté).
  - Bougie baissière + volume suffisant.
  - Optionnel: tendance 15m aussi baissière pour confirmer.

TP/SL: pour un SHORT, le stop loss est au-dessus du prix, le take profit en dessous.
"""


def signal_short_big_drop(df, indicators, volume_ratio_min=1.0):
    """
    Détecte une opportunité SHORT sur une grande baisse.

    Conditions (toutes requises):
      1. Tendance baissière: price_momentum == 'BEARISH'.
      2. Prix sous EMA21 (confirmation tendance).
      3. RSI < 55 (pas d'achat fort) ou RSI en baisse (rsi14 < rsi14_prev).
      4. Dernière bougie baissière (close < open) ou pattern bearish.
      5. Volume >= volume_ratio_min × moyenne (confirmation).

    Returns:
        True si signal SHORT valide, False sinon.
    """
    if indicators.get('price_momentum') != 'BEARISH':
        return False

    current = indicators.get('current_price')
    ema21 = indicators.get('ema21')
    if current is None or ema21 is None or current >= ema21:
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
    Calcule un score de 0 à 100 pour une opportunité SHORT (plus c'est haut, mieux c'est).
    Critères: RSI bas, volume élevé, tendances 15m/1h baissières, spread faible, ATR modéré.
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
    # Tendance 1h baissière → +15 pts
    if momentum_1h == 'BEARISH':
        score += 15

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
    }
