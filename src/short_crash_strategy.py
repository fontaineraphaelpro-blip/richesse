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


def position_size_usdt(balance_usdt, risk_pct=0.02, max_pct_balance=0.25):
    """
    Taille de position SHORT en USDT.

    Args:
        balance_usdt: solde disponible.
        risk_pct: risque par trade (ex: 0.02 = 2%).
        max_pct_balance: plafond en % du solde (ex: 0.25 = 25%).

    Returns:
        Montant USDT à engager pour le short.
    """
    if balance_usdt <= 0:
        return 0.0
    by_risk = balance_usdt * risk_pct
    by_cap = balance_usdt * max_pct_balance
    return min(by_risk * 5, by_cap)  # 5x risk as size, plafonné
