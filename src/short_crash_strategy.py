# -*- coding: utf-8 -*-
"""
Stratégie DAY TRADING PRO — LONG et SHORT (SUIVI DE TENDANCE).

Le bot suit la tendance et n'entre pas sur les rebonds (pas d'achat oversold, pas de short oversold).
- LONG: continuation haussière (prix au-dessus de l'EMA, RSI dans la zone tendance).
- SHORT: continuation baissière (prix sous EMA, RSI pas en zone rebond).
"""


# === CONFIG PRO DAY TRADER — Qualité maximale ===
ADX_MIN_FOR_TREND = 28     # ADX 28+ = tendance TRÈS forte (était 25)
RSI_LONG_MIN = 52          # Zone continuation stricte (52-60)
RSI_LONG_MAX = 60          # Éviter surachat
RSI_SHORT_MIN = 38         # Pas de short sous 38 (trop oversold = rebond)
RSI_SHORT_MAX = 48         # Short zone stricte: 38-48
LONG_PRICE_ABOVE_EMA_PCT = 0.08   # Prix clairement au-dessus EMA21 (éviter faux signaux)

# SL/TP mieux positionnés: SL plus large pour éviter stop-out sur le bruit crypto
# Crypto 15m: ATR typique 1.5-3% — SL 1.0-2.0% évite les faux stop-out
ATR_SL_MULTIPLIER = 1.2    # SL = ATR * 1.2 (plus de marge)
ATR_TP_MULTIPLIER = 1.5    # TP = ATR * 1.5
ATR_TP_RR_RATIO = None
ATR_SL_MIN_PCT = 1.0       # Min 1.0% (était 0.7% = trop serré, stop-out fréquents)
ATR_SL_MAX_PCT = 2.0       # Max 2.0% (crypto volatile)
ATR_TP_MIN_PCT = 1.0
ATR_TP_MAX_PCT = 3.0
MIN_RR_RATIO = 1.8         # R:R 1.8:1 PRO (gain systématiquement > risque)


def compute_sl_tp_from_chart(price, indicators, direction, sl_atr_mult=None, rr_ratio=None):
    """
    Calcule SL et TP independamment depuis l'ATR.
    rr_ratio: si fourni, utilise ce R:R min au lieu de MIN_RR_RATIO (ex: 1.8 en tendance forte).
    """
    if price is None or price <= 0:
        return None, None, None
    sl_mult = sl_atr_mult if sl_atr_mult is not None else ATR_SL_MULTIPLIER
    tp_mult = ATR_TP_MULTIPLIER
    atr = indicators.get('atr')
    atr_pct = indicators.get('atr_percent')
    if atr is None and atr_pct is not None and atr_pct > 0:
        atr = price * (atr_pct / 100.0)
    if atr is None or atr <= 0:
        atr = price * (ATR_SL_MIN_PCT / 100.0)
    # SL distance
    sl_distance = atr * sl_mult
    sl_pct = (sl_distance / price) * 100
    sl_pct = max(ATR_SL_MIN_PCT, min(ATR_SL_MAX_PCT, sl_pct))
    sl_distance = price * (sl_pct / 100.0)
    # TP distance: au moins min_rr * sl_distance (rr_ratio passé en param ou MIN_RR_RATIO)
    min_rr = rr_ratio if rr_ratio is not None else MIN_RR_RATIO
    tp_distance = atr * tp_mult
    tp_pct = (tp_distance / price) * 100
    tp_pct = max(ATR_TP_MIN_PCT, min(ATR_TP_MAX_PCT, tp_pct))
    tp_distance = price * (tp_pct / 100.0)
    min_tp_distance = sl_distance * min_rr
    if tp_distance < min_tp_distance:
        tp_distance = min_tp_distance
        tp_pct = (tp_distance / price) * 100

    if direction == 'LONG':
        stop_loss = price - sl_distance
        take_profit = price + tp_distance
    else:
        stop_loss = price + sl_distance
        take_profit = price - tp_distance
    return stop_loss, take_profit, sl_pct


# ─── LONG (continuation haussière, pas d'achat de rebond) ────────────────────

SIGNAL_MIN_CONDITIONS = 8  # 8/10 conditions = PRO — qualité maximale, zéro faille

def signal_long_buy_dip(df, indicators, volume_ratio_min=1.0):
    """
    Signal LONG ultra-strict: 10 conditions, 7 requises.
    Objectif: 60%+ win rate.
    """
    conditions_met = 0

    current = indicators.get('current_price')
    ema21 = indicators.get('ema21')
    if current is None or ema21 is None or current <= 0 or ema21 <= 0:
        return False

    # HARD STOPS (disqualifient immediatement)
    rsi = indicators.get('rsi14')
    if rsi is not None and rsi >= RSI_LONG_MAX:
        return False  # surachat = trop tard
    adx = indicators.get('adx')
    if adx is not None and adx < 22:
        return False  # tendance trop faible (était 20)
    regime = indicators.get('market_regime')
    if regime == 'VOLATILE':
        return False  # trop imprévisible
    if regime == 'RANGING':
        return False  # PRO: pas de LONG en ranging (trop de faux signaux)

    # 1. Momentum haussier
    if indicators.get('price_momentum') == 'BULLISH':
        conditions_met += 1

    # 2. Prix au-dessus de l'EMA21
    if current >= ema21 * (1 + LONG_PRICE_ABOVE_EMA_PCT / 100):
        conditions_met += 1

    # 3. ADX >= 25 (tendance forte)
    if adx is not None and adx >= ADX_MIN_FOR_TREND:
        conditions_met += 1

    # 4. RSI zone continuation (52-60)
    if rsi is not None and RSI_LONG_MIN <= rsi < RSI_LONG_MAX:
        conditions_met += 1

    # 5. Bougie haussiere
    open_p = indicators.get('open_price')
    if open_p is not None and current > open_p:
        conditions_met += 1

    # 6. Volume au-dessus de la moyenne
    vol_ratio = indicators.get('volume_ratio')
    if vol_ratio is not None and vol_ratio >= volume_ratio_min:
        conditions_met += 1

    # 7. Stochastic bullish (K > D) et pas en zone surachat
    stoch_k = indicators.get('stoch_k')
    stoch_d = indicators.get('stoch_d')
    if stoch_k is not None and stoch_d is not None and stoch_k > stoch_d and stoch_k < 80:
        conditions_met += 1

    # 8. MACD histogramme positif (momentum haussier confirme)
    macd_hist = indicators.get('macd_hist')
    if macd_hist is not None and macd_hist > 0:
        conditions_met += 1

    # 9. Bollinger: prix entre 45% et 65% (zone optimale, pas extrêmes)
    bb_pct = indicators.get('bb_percent')
    if bb_pct is not None and 0.45 <= bb_pct <= 0.65:
        conditions_met += 1

    # 10. Marche en tendance (regime TRENDING)
    if regime == 'TRENDING':
        conditions_met += 1

    # 11. DI+ > DI- (momentum directionnel confirmé)
    di_plus = indicators.get('di_plus')
    di_minus = indicators.get('di_minus')
    if di_plus is not None and di_minus is not None and di_plus > di_minus + 2:
        conditions_met += 1

    return conditions_met >= SIGNAL_MIN_CONDITIONS


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
        if adx >= 35:
            score += 10   # tendance TRES forte = gros bonus
        elif adx >= 28:
            score += 7
        elif adx >= 22:
            score += 4

    bb_percent = indicators.get('bb_percent')
    if bb_percent is not None and 0.3 <= bb_percent <= 0.6:
        score += 3

    if spread_pct < 0.05:
        score += 12   # spread ultra serre = execution parfaite
    elif spread_pct < 0.08:
        score += 8
    elif spread_pct < 0.10:
        score += 5

    if atr_pct is None:
        atr_pct = 2.0
    if 1.0 <= atr_pct <= 2.5:
        score += 12   # volatilite ideale pour day trading
    elif atr_pct <= 3.5:
        score += 6

    current = indicators.get('current_price')
    ema21 = indicators.get('ema21')
    if current and ema21 and ema21 > 0 and current > ema21:
        dist_pct = ((current - ema21) / ema21) * 100
        if 0.3 < dist_pct < 2.0:
            score += 7   # proche de l'EMA mais au-dessus = meilleur R:R

    # Stochastic K/D crossover bullish: K > D et K_prev <= D_prev
    stoch_k = indicators.get('stoch_k')
    stoch_d = indicators.get('stoch_d')
    stoch_k_prev = indicators.get('stoch_k_prev')
    stoch_d_prev = indicators.get('stoch_d_prev')
    if all(v is not None for v in [stoch_k, stoch_d, stoch_k_prev, stoch_d_prev]):
        if stoch_k > stoch_d and stoch_k_prev <= stoch_d_prev:
            score += 8
        elif stoch_k > stoch_d:
            score += 4

    # Ichimoku: Tenkan > Kijun = tendance haussiere confirmee
    tenkan = indicators.get('tenkan')
    kijun = indicators.get('kijun')
    if tenkan is not None and kijun is not None:
        if tenkan > kijun and current and current > tenkan:
            score += 8
        elif tenkan > kijun:
            score += 4

    # RSI divergence bullish: prix lower low, RSI higher low -> retournement
    if indicators.get('rsi_bullish_divergence'):
        score += 7

    # Volume Profile: prix pres du POC = support fort
    poc = indicators.get('volume_poc')
    va_low = indicators.get('value_area_low')
    if poc and current and va_low:
        if current >= va_low and current <= poc * 1.01:
            score += 5

    # Regime trending = meilleur pour trend-following
    regime = indicators.get('market_regime')
    if regime == 'TRENDING':
        score += 5
    elif regime == 'RANGING':
        score -= 3

    # VWAP: prix sous VWAP = bon point d'entree LONG
    vwap_dist = indicators.get('vwap_distance_pct')
    if vwap_dist is not None:
        if -1.0 <= vwap_dist <= 0:
            score += 8
        elif 0 < vwap_dist <= 0.5:
            score += 4
        elif vwap_dist > 2.0:
            score -= 3

    # Volatility cluster: penaliser si vol extreme
    if indicators.get('in_vol_cluster'):
        score -= 5

    # Intraday pattern: bonus si heure historiquement bullish
    if indicators.get('intraday_bias') == 'BULLISH':
        score += 5
    elif indicators.get('intraday_bias') == 'BEARISH':
        score -= 3

    score = min(100, max(0, round(score, 1)))
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
        'regime': regime or 'UNKNOWN',
    }


def position_size_long_usdt(balance_usdt, risk_pct=0.01, sl_pct=1.0, leverage=10, max_pct_balance=0.25, min_usdt=10):
    """
    Taille de position LONG (marge en USDT) avec levier.
    Meme formule que SHORT: marge = (balance * risk_pct) / (leverage * sl_pct/100)
    """
    if balance_usdt <= 0:
        return 0.0
    risk_amount = balance_usdt * risk_pct
    margin_by_risk = risk_amount * 100 / (leverage * sl_pct)
    margin_by_cap = balance_usdt * max_pct_balance
    margin = min(margin_by_risk, margin_by_cap)
    return max(min_usdt, min(margin, balance_usdt * 0.98))


# ─── SHORT (continuation baissière, pas de short sur rebond) ───────────────────

def signal_short_big_drop(df, indicators, volume_ratio_min=1.0):
    """
    Signal SHORT ultra-strict: 10 conditions, 7 requises.
    Objectif: 60%+ win rate.
    """
    conditions_met = 0

    current = indicators.get('current_price')
    ema21 = indicators.get('ema21')
    if current is None or ema21 is None:
        return False

    # HARD STOPS
    rsi = indicators.get('rsi14')
    if rsi is not None and rsi < RSI_SHORT_MIN:
        return False  # oversold = rebond probable
    rsi_prev = indicators.get('rsi14_prev')
    if rsi_prev is not None and rsi is not None and rsi > rsi_prev + 5:
        return False  # RSI remonte = rebond en cours (était 6)
    adx = indicators.get('adx')
    if adx is not None and adx < 22:
        return False  # tendance trop faible
    regime = indicators.get('market_regime')
    if regime == 'VOLATILE':
        return False
    if regime == 'RANGING':
        return False  # PRO: pas de SHORT en ranging

    # 1. Momentum baissier
    if indicators.get('price_momentum') == 'BEARISH':
        conditions_met += 1

    # 2. Prix sous EMA21
    if current < ema21:
        conditions_met += 1

    # 3. ADX >= 25 (tendance forte)
    if adx is not None and adx >= ADX_MIN_FOR_TREND:
        conditions_met += 1

    # 4. RSI zone continuation (38-48)
    if rsi is not None and RSI_SHORT_MIN <= rsi <= RSI_SHORT_MAX:
        conditions_met += 1

    # 5. Bougie baissiere
    open_p = indicators.get('open_price')
    if open_p is not None and current is not None and open_p > 0 and current < open_p:
        conditions_met += 1

    # 6. Volume au-dessus de la moyenne
    vol_ratio = indicators.get('volume_ratio')
    if vol_ratio is not None and vol_ratio >= volume_ratio_min:
        conditions_met += 1

    # 7. Stochastic bearish (K < D) et pas en zone survente
    stoch_k = indicators.get('stoch_k')
    stoch_d = indicators.get('stoch_d')
    if stoch_k is not None and stoch_d is not None and stoch_k < stoch_d and stoch_k > 20:
        conditions_met += 1

    # 8. MACD histogramme negatif
    macd_hist = indicators.get('macd_hist')
    if macd_hist is not None and macd_hist < 0:
        conditions_met += 1

    # 9. Bollinger: prix entre 35% et 55% (tendance baissière, pas de rebond)
    bb_pct = indicators.get('bb_percent')
    if bb_pct is not None and 0.35 <= bb_pct <= 0.55:
        conditions_met += 1

    # 10. Marche en tendance
    if regime == 'TRENDING':
        conditions_met += 1

    # 11. DI- > DI+ (momentum baissier confirmé)
    di_plus = indicators.get('di_plus')
    di_minus = indicators.get('di_minus')
    if di_plus is not None and di_minus is not None and di_minus > di_plus + 2:
        conditions_met += 1

    return conditions_met >= SIGNAL_MIN_CONDITIONS


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

    adx = indicators.get('adx')
    if adx is not None:
        if adx >= 35:
            score += 10
        elif adx >= 28:
            score += 7
        elif adx >= 22:
            score += 4

    bb_percent = indicators.get('bb_percent')
    if bb_percent is not None and bb_percent >= 0.6:
        score += 3

    if spread_pct < 0.05:
        score += 12
    elif spread_pct < 0.08:
        score += 8
    elif spread_pct < 0.10:
        score += 5

    if atr_pct is None:
        atr_pct = 2.0
    if 1.0 <= atr_pct <= 2.5:
        score += 12
    elif atr_pct <= 3.5:
        score += 6

    current = indicators.get('current_price')
    ema21 = indicators.get('ema21')
    if current and ema21 and ema21 > 0 and current < ema21:
        dist_pct = ((ema21 - current) / ema21) * 100
        if 0.3 < dist_pct < 2.0:
            score += 7

    # Stochastic K/D crossover bearish: K < D et K_prev >= D_prev
    stoch_k = indicators.get('stoch_k')
    stoch_d = indicators.get('stoch_d')
    stoch_k_prev = indicators.get('stoch_k_prev')
    stoch_d_prev = indicators.get('stoch_d_prev')
    if all(v is not None for v in [stoch_k, stoch_d, stoch_k_prev, stoch_d_prev]):
        if stoch_k < stoch_d and stoch_k_prev >= stoch_d_prev:
            score += 8
        elif stoch_k < stoch_d:
            score += 4

    # Ichimoku: Tenkan < Kijun = tendance baissiere confirmee
    tenkan = indicators.get('tenkan')
    kijun = indicators.get('kijun')
    if tenkan is not None and kijun is not None:
        if tenkan < kijun and current and current < tenkan:
            score += 8
        elif tenkan < kijun:
            score += 4

    # RSI divergence bearish: prix higher high, RSI lower high -> retournement
    if indicators.get('rsi_bearish_divergence'):
        score += 7

    # Volume Profile: prix pres du POC par le haut = resistance
    poc = indicators.get('volume_poc')
    va_high = indicators.get('value_area_high')
    if poc and current and va_high:
        if current <= va_high and current >= poc * 0.99:
            score += 5

    # Regime trending = meilleur pour trend-following
    regime = indicators.get('market_regime')
    if regime == 'TRENDING':
        score += 5
    elif regime == 'RANGING':
        score -= 3

    # VWAP: prix au-dessus du VWAP = bon point d'entree SHORT
    vwap_dist = indicators.get('vwap_distance_pct')
    if vwap_dist is not None:
        if 0 <= vwap_dist <= 1.0:
            score += 8
        elif -0.5 <= vwap_dist < 0:
            score += 4
        elif vwap_dist < -2.0:
            score -= 3

    # Volatility cluster: penaliser si vol extreme
    if indicators.get('in_vol_cluster'):
        score -= 5

    # Intraday pattern: bonus si heure historiquement bearish
    if indicators.get('intraday_bias') == 'BEARISH':
        score += 5
    elif indicators.get('intraday_bias') == 'BULLISH':
        score -= 3

    score = min(100, max(0, round(score, 1)))
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
        'regime': regime or 'UNKNOWN',
    }
