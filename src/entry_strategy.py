"""
Module de Stratégie d'Entrée Optimisée - PULLBACK STRATEGY
Principe: Entrer sur les RETRACEMENTS dans une tendance établie, pas sur les extensions.

Pourquoi ça marche:
- On achète les creux dans une uptrend (pas les sommets)
- On short les rebonds dans une downtrend (pas les creux)
- Meilleur R/R car on entre près des supports/résistances naturels (EMAs)
- Moins de faux signaux car on attend la confirmation du rebond
"""

from typing import Dict, Optional, Tuple


def detect_pullback_entry(indicators: Dict, support: Optional[float], resistance: Optional[float]) -> Dict:
    """
    Détecte les opportunités d'entrée sur pullback.
    
    STRATÉGIE:
    1. Identifier la tendance de fond (EMA9 > EMA21 = bullish)
    2. Attendre que le prix REVIENNE vers l'EMA21 (pullback)
    3. Confirmer le REBOND sur l'EMA (bougie de retournement)
    4. Entrer avec SL sous le récent swing low
    
    Returns:
        Dictionnaire avec signal, prix, SL, TP, confiance
    """
    # Vérifications de base
    current_price = indicators.get('current_price')
    if current_price is None:
        return _empty_signal()
    
    # === INDICATEURS CLÉS ===
    ema9 = indicators.get('ema9')
    ema21 = indicators.get('ema21')
    ema50 = indicators.get('sma50')  # SMA50 comme tendance long terme
    rsi14 = indicators.get('rsi14')
    atr = indicators.get('atr')
    adx = indicators.get('adx')
    
    # Prix OHLC
    open_price = indicators.get('open_price', current_price)
    high_price = indicators.get('high_price', current_price)
    low_price = indicators.get('low_price', current_price)
    
    # Momentum et volume
    price_momentum = indicators.get('price_momentum', 'NEUTRAL')
    volume_ratio = indicators.get('volume_ratio', 1.0)
    
    # MACD pour confirmation
    macd = indicators.get('macd')
    macd_signal = indicators.get('macd_signal')
    macd_hist = indicators.get('macd_hist')
    macd_hist_prev = indicators.get('macd_hist_prev')
    
    # Bandes de Bollinger
    bb_lower = indicators.get('bb_lower')
    bb_upper = indicators.get('bb_upper')
    
    if ema9 is None or ema21 is None or atr is None:
        return _empty_signal()
    try:
        ema9 = float(ema9)
        ema21 = float(ema21)
        atr = float(atr)
    except Exception:
        return _empty_signal()
    
    # === ÉTAPE 1: IDENTIFIER LA TENDANCE DE FOND ===
    trend = 'NEUTRAL'
    trend_strength = 0
    
    # Tendance EMA
    if ema9 > ema21:
        trend = 'BULLISH'
        trend_strength += 1
        if ema50 and ema21 > ema50:
            trend_strength += 1  # Tendance forte (toutes EMAs alignées)
    elif ema9 < ema21:
        trend = 'BEARISH'
        trend_strength += 1
        if ema50 and ema21 < ema50:
            trend_strength += 1
    
    # ADX confirme la force
    if adx and adx >= 20:
        trend_strength += 1
    elif adx and adx < 18:
        # Pas de tendance claire - éviter
        return _empty_signal()
    
    # MACD confirme
    if macd is not None and macd_signal is not None:
        if trend == 'BULLISH' and macd > macd_signal:
            trend_strength += 1
        elif trend == 'BEARISH' and macd < macd_signal:
            trend_strength += 1
    
    # Tendance trop faible
    if trend_strength < 2:
        return _empty_signal()
    
    # === ÉTAPE 2: DÉTECTER LE PULLBACK ===
    is_pullback = False
    pullback_quality = 0
    
    if trend == 'BULLISH':
        # PULLBACK LONG: Le prix doit être PROCHE de l'EMA21 (revenu du haut)
        # Distance du prix à l'EMA21 en %
        dist_to_ema21 = ((current_price - ema21) / ema21) * 100
        dist_to_ema9 = ((current_price - ema9) / ema9) * 100
        
        # Pullback idéal: prix entre EMA9 et EMA21, ou légèrement sous EMA21
        if -1.5 <= dist_to_ema21 <= 1.0:
            # Prix proche de l'EMA21 (zone de pullback)
            is_pullback = True
            pullback_quality += 2
            
            # Bonus si le prix touche/traverse l'EMA21
            if dist_to_ema21 <= 0.2:
                pullback_quality += 1
        
        elif 1.0 < dist_to_ema21 <= 2.0 and dist_to_ema9 <= 0.5:
            # Prix entre EMA9 et légèrement au-dessus de EMA21
            is_pullback = True
            pullback_quality += 1
        
        # ANTI-CHASING: Si le prix est trop haut (>2% au-dessus de EMA21), c'est trop tard
        if dist_to_ema21 > 2.5:
            is_pullback = False
        
        # Vérifier que le prix n'est pas en chute libre (RSI < 35 = danger)
        if rsi14 and rsi14 < 35:
            is_pullback = False
    
    elif trend == 'BEARISH':
        # PULLBACK SHORT: Le prix doit être PROCHE de l'EMA21 (revenu du bas)
        dist_to_ema21 = ((current_price - ema21) / ema21) * 100
        dist_to_ema9 = ((current_price - ema9) / ema9) * 100
        
        # Pullback idéal: prix entre EMA9 et EMA21, ou légèrement au-dessus EMA21
        if -1.0 <= dist_to_ema21 <= 1.5:
            is_pullback = True
            pullback_quality += 2
            
            if dist_to_ema21 >= -0.2:
                pullback_quality += 1
        
        elif -2.0 <= dist_to_ema21 < -1.0 and dist_to_ema9 >= -0.5:
            is_pullback = True
            pullback_quality += 1
        
        # ANTI-CHASING: Prix trop bas
        if dist_to_ema21 < -2.5:
            is_pullback = False
        
        # Vérifier que le prix n'est pas en pump (RSI > 65 = danger pour short)
        if rsi14 and rsi14 > 65:
            is_pullback = False
    
    if not is_pullback:
        return _empty_signal()
    
    # === ÉTAPE 3: CONFIRMER LE REBOND ===
    is_bounce = False
    bounce_quality = 0
    
    if trend == 'BULLISH':
        # Rebond haussier: bougie verte (close > open) ou wick inférieur long
        is_green_candle = current_price > open_price
        
        # Wick inférieur = rejet du bas (signe de rebond)
        candle_body = abs(current_price - open_price)
        lower_wick = min(open_price, current_price) - low_price
        
        has_rejection_wick = lower_wick > candle_body * 0.5
        
        if is_green_candle:
            bounce_quality += 2
            is_bounce = True
        
        if has_rejection_wick:
            bounce_quality += 1
            is_bounce = True
        
        # Le momentum doit commencer à tourner bullish ou être neutre
        if price_momentum == 'BULLISH':
            bounce_quality += 2
        elif price_momentum == 'NEUTRAL':
            bounce_quality += 1
        elif price_momentum == 'BEARISH':
            # Le prix descend encore - pas de rebond confirmé
            bounce_quality -= 1
        
        # MACD histogram qui remonte = momentum qui tourne
        if macd_hist is not None and macd_hist_prev is not None:
            if macd_hist > macd_hist_prev:
                bounce_quality += 1
    
    elif trend == 'BEARISH':
        # Rebond baissier: bougie rouge (close < open) ou wick supérieur long
        is_red_candle = current_price < open_price
        
        candle_body = abs(current_price - open_price)
        upper_wick = high_price - max(open_price, current_price)
        
        has_rejection_wick = upper_wick > candle_body * 0.5
        
        if is_red_candle:
            bounce_quality += 2
            is_bounce = True
        
        if has_rejection_wick:
            bounce_quality += 1
            is_bounce = True
        
        if price_momentum == 'BEARISH':
            bounce_quality += 2
        elif price_momentum == 'NEUTRAL':
            bounce_quality += 1
        elif price_momentum == 'BULLISH':
            bounce_quality -= 1
        
        if macd_hist is not None and macd_hist_prev is not None:
            if macd_hist < macd_hist_prev:
                bounce_quality += 1
    
    # Bounce pas assez clair
    if bounce_quality < 2:
        return _empty_signal()
    
    # === ÉTAPE 4: VALIDATION RSI ===
    rsi_valid = True
    rsi_bonus = 0
    
    if rsi14:
        if trend == 'BULLISH':
            # RSI idéal pour pullback long: 40-55 (pas suracheté, pas survendu)
            if 40 <= rsi14 <= 55:
                rsi_bonus = 2
            elif 35 <= rsi14 < 40:
                rsi_bonus = 1
            elif 55 < rsi14 <= 60:
                rsi_bonus = 1
            elif rsi14 > 65:
                rsi_valid = False  # Trop haut - risque de correction
            elif rsi14 < 35:
                rsi_valid = False  # Chute en cours
        
        elif trend == 'BEARISH':
            # RSI idéal pour pullback short: 45-60
            if 45 <= rsi14 <= 60:
                rsi_bonus = 2
            elif 40 <= rsi14 < 45:
                rsi_bonus = 1
            elif 60 < rsi14 <= 65:
                rsi_bonus = 1
            elif rsi14 < 35:
                rsi_valid = False  # Trop bas - risque de rebond
            elif rsi14 > 65:
                rsi_valid = False  # Hausse en cours
    
    if not rsi_valid:
        return _empty_signal()
    
    # === ÉTAPE 5: CONFIRMATION VOLUME ===
    volume_bonus = 0
    if volume_ratio >= 1.2:
        volume_bonus = 2
    elif volume_ratio >= 1.0:
        volume_bonus = 1
    elif volume_ratio < 0.7:
        # Volume trop faible - signal peu fiable
        volume_bonus = -1
    
    # === CALCUL CONFIANCE FINALE ===
    confidence = 30  # Base
    confidence += trend_strength * 10
    confidence += pullback_quality * 8
    confidence += bounce_quality * 8
    confidence += rsi_bonus * 5
    confidence += volume_bonus * 5
    
    # Plafond
    confidence = min(confidence, 100)
    
    # Seuil minimum
    if confidence < 55:
        return _empty_signal()
    
    # === GÉNÉRATION DU SIGNAL ===
    entry_signal = 'LONG' if trend == 'BULLISH' else 'SHORT'
    entry_price = current_price
    
    # === CALCUL SL/TP ===
    # SL basé sur ATR et structure
    atr_value = atr
    
    if entry_signal == 'LONG':
        # SL sous le récent low ou 1.5x ATR
        structural_sl = low_price * 0.998  # Juste sous le low
        atr_sl = entry_price - (atr_value * 1.5)
        
        # Prendre le SL le plus protecteur (le plus haut des deux)
        stop_loss = max(structural_sl, atr_sl)
        
        # Si support proche, utiliser le support
        if support and support < entry_price and support > stop_loss:
            stop_loss = support * 0.998
        
        # TP basé sur R/R 2:1 minimum
        risk = entry_price - stop_loss
        tp1 = entry_price + (risk * 2.5)  # R/R 2.5:1
        tp2 = entry_price + (risk * 4.0)  # R/R 4:1 pour le reste
    
    else:  # SHORT
        structural_sl = high_price * 1.002
        atr_sl = entry_price + (atr_value * 1.5)
        
        stop_loss = min(structural_sl, atr_sl)
        
        if resistance and resistance > entry_price and resistance < stop_loss:
            stop_loss = resistance * 1.002
        
        risk = stop_loss - entry_price
        tp1 = entry_price - (risk * 2.5)
        tp2 = entry_price - (risk * 4.0)
    
    # Calcul R/R
    risk_amount = abs(entry_price - stop_loss)
    reward_amount = abs(tp1 - entry_price)
    rr_ratio = round(reward_amount / risk_amount, 2) if risk_amount > 0 else 0
    
    # Vérifier R/R minimum
    if rr_ratio < 2.0:
        return _empty_signal()
    
    return {
        'entry_signal': entry_signal,
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'take_profit_1': tp1,
        'take_profit_2': tp2,
        'risk_reward_ratio': rr_ratio,
        'confidence': confidence,
        'exit_signal': 'HOLD',
        'atr_percent': (atr_value / current_price * 100) if atr_value else 0,
        'strategy': 'PULLBACK',
        'trend': trend,
        'trend_strength': trend_strength,
        'pullback_quality': pullback_quality,
        'bounce_quality': bounce_quality,
    }


def _empty_signal() -> Dict:
    """Signal vide par défaut."""
    return {
        'entry_signal': 'NEUTRAL',
        'entry_price': None,
        'stop_loss': None,
        'take_profit_1': None,
        'take_profit_2': None,
        'risk_reward_ratio': None,
        'confidence': 0,
        'exit_signal': 'N/A',
        'atr_percent': 0,
        'strategy': None,
    }


def get_entry_signal(indicators: Dict, support: Optional[float], resistance: Optional[float]) -> Dict:
    """
    Point d'entrée principal - utilise la stratégie pullback.
    Fallback sur l'ancienne stratégie si aucun pullback détecté.
    """
    # Essayer d'abord la stratégie pullback (meilleure)
    pullback_signal = detect_pullback_entry(indicators, support, resistance)
    
    if pullback_signal['entry_signal'] != 'NEUTRAL':
        return pullback_signal
    
    # Sinon retourner signal neutre (pas de trade)
    return _empty_signal()
