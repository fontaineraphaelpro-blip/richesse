"""
Module pour détecter les signaux d'entrée et de sortie pour le scalping.
Adapté pour les données réelles (Binance) avec des seuils réalistes.

V2: Utilise la stratégie PULLBACK en priorité (meilleur timing d'entrée).
"""

import pandas as pd
from typing import Dict, Optional, Tuple

# Import de la nouvelle stratégie pullback
try:
    from entry_strategy import get_entry_signal as get_pullback_signal
    HAS_PULLBACK_STRATEGY = True
except ImportError:
    HAS_PULLBACK_STRATEGY = False


def calculate_entry_exit_signals(indicators: Dict, support: Optional[float], resistance: Optional[float]) -> Dict:
    """
    Calcule les signaux d'entrée et de sortie.
    
    V2: Utilise la stratégie PULLBACK en priorité pour un meilleur timing.
    Fallback sur l'ancienne stratégie momentum si pas de pullback.
    """
    # === STRATÉGIE PULLBACK (PRIORITAIRE) ===
    # Meilleur timing: on attend les retracements vers EMA au lieu de chasser les breakouts
    if HAS_PULLBACK_STRATEGY:
        pullback_result = get_pullback_signal(indicators, support, resistance)
        if pullback_result.get('entry_signal') != 'NEUTRAL':
            return pullback_result
    
    # === FALLBACK: ANCIENNE STRATÉGIE MOMENTUM ===
    return _calculate_momentum_signals(indicators, support, resistance)


def _calculate_momentum_signals(indicators: Dict, support: Optional[float], resistance: Optional[float]) -> Dict:
    """
    Calcule les signaux d'entrée et de sortie basés sur une convergence d'indicateurs.
    
    Args:
        indicators: Dictionnaire avec les indicateurs techniques calculés
        support: Niveau de support identifié
        resistance: Niveau de résistance identifié
    
    Returns:
        Dictionnaire contenant: entry_signal, entry_price, stop_loss, take_profits, confidence
    """
    # Vérification de base
    current_price = indicators.get('current_price')
    if current_price is None:
        return _empty_signal_result()
    
    # --- 1. Extraction des indicateurs clés ---
    ema9 = indicators.get('ema9')
    ema21 = indicators.get('ema21')
    rsi14 = indicators.get('rsi14')
    macd = indicators.get('macd')
    macd_signal = indicators.get('macd_signal')
    atr = indicators.get('atr')
    
    # Indicateurs secondaires
    volume_current = indicators.get('current_volume')
    volume_ma = indicators.get('volume_ma20')
    adx = indicators.get('adx')
    
    # Bandes de Bollinger
    bb_upper = indicators.get('bb_upper')
    bb_lower = indicators.get('bb_lower')
    
    # Patterns
    candlestick_bearish = indicators.get('candlestick_bearish_signals', 0)
    # On suppose que tu pourrais avoir des patterns bullish à l'avenir
    # candlestick_bullish = indicators.get('candlestick_bullish_signals', 0) 
    
    # MOMENTUM CONFIRMATION (direction récente du prix)
    price_momentum = indicators.get('price_momentum', 'NEUTRAL')
    momentum_strength = indicators.get('momentum_strength', 0)
    
    # Ratio Volume (Force du mouvement)
    volume_ratio = 1.0
    if volume_current and volume_ma and volume_ma > 0:
        volume_ratio = volume_current / volume_ma

    # --- 2. Initialisation des scores ---
    bullish_confirmations = 0
    bearish_confirmations = 0
    confidence = 0
    
    # --- 3. Analyse de Tendance (EMA) ---
    # C'est le "King Indicator" pour le scalping
    ema_trend = 'NEUTRAL'
    if ema9 and ema21:
        if ema9 > ema21:
            ema_trend = 'BULLISH'
            if current_price > ema9: # Prix au-dessus des EMAs (Force)
                bullish_confirmations += 2 
                confidence += 20
        elif ema9 < ema21:
            ema_trend = 'BEARISH'
            if current_price < ema9: # Prix en-dessous des EMAs (Faiblesse)
                bearish_confirmations += 2 
                confidence += 20

    # --- 4. Analyse du Momentum (RSI) --- TREND FOLLOWING (pas contrarian!)
    # PRINCIPE: On trade AVEC la tendance, pas contre elle
    # RSI < 35 = marché en CHUTE = NE PAS ACHETER
    # RSI > 65 = marché en HAUSSE = NE PAS SHORTER
    if rsi14 is not None:
        # LONG: RSI en zone de momentum HAUSSIER (40-65) avec tendance confirmée
        # On évite les extrêmes (< 35 = trop risqué, > 65 = surachat)
        if 40 <= rsi14 <= 65 and ema_trend == 'BULLISH':
            bullish_confirmations += 2
            confidence += 20
        elif 35 <= rsi14 < 40 and ema_trend == 'BULLISH':
            # Zone transition - momentum faible mais tendance OK
            bullish_confirmations += 1
            confidence += 10
        
        # FILTRE ANTI-PIÈGE: RSI < 35 = marché en CHUTE LIBRE = DANGER pour LONG
        if rsi14 < 35:
            bullish_confirmations -= 1  # Pénaliser les LONG en oversold
            bearish_confirmations += 1  # Favoriser SHORT (tendance baissière)
            confidence -= 5
        
        # SHORT: RSI en zone de momentum BAISSIER (35-60) avec tendance confirmée
        if 35 <= rsi14 <= 60 and ema_trend == 'BEARISH':
            bearish_confirmations += 2
            confidence += 20
        elif 60 < rsi14 <= 65 and ema_trend == 'BEARISH':
            # Zone transition - correction imminente
            bearish_confirmations += 1
            confidence += 10
        
        # FILTRE ANTI-PIÈGE: RSI > 65 = marché en HAUSSE FORTE = DANGER pour SHORT
        if rsi14 > 65:
            bearish_confirmations -= 1  # Pénaliser les SHORT en overbought
            bullish_confirmations += 1  # Favoriser LONG (tendance haussière)
            confidence -= 5
                
        # Divergences (Si calculées)
        div_type = indicators.get('rsi_divergence_type')
        if indicators.get('rsi_divergence'):
            if div_type == 'bearish':
                bearish_confirmations += 2
                confidence += 15
            elif div_type == 'bullish':
                bullish_confirmations += 2
                confidence += 15

    # --- 5. Analyse MACD ---
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            bullish_confirmations += 1
            confidence += 10
        elif macd < macd_signal:
            bearish_confirmations += 1
            confidence += 10

    # --- 6. Analyse Volume ---
    # Le volume valide le mouvement
    if volume_ratio >= 1.2: # Volume 20% supérieur à la moyenne
        confidence += 10
        # Le volume confirme la direction de la bougie actuelle
        if ema_trend == 'BULLISH':
            bullish_confirmations += 1
        elif ema_trend == 'BEARISH':
            bearish_confirmations += 1

    # --- 7. Analyse Bollinger ---
    if bb_upper and bb_lower:
        # Position relative dans les bandes (0 = bas, 1 = haut)
        bb_range = bb_upper - bb_lower
        if bb_range > 0:
            bb_pos = (current_price - bb_lower) / bb_range
            
            # Stratégie de suivi de tendance (Breakout ou Ride the bands)
            if bb_pos > 0.7 and ema_trend == 'BULLISH': 
                # Prix fort dans une tendance haussière
                bullish_confirmations += 1
            elif bb_pos < 0.3 and ema_trend == 'BEARISH':
                # Prix faible dans une tendance baissière
                bearish_confirmations += 1

    # --- 8. Patterns (Bonus) ---
    candlestick_bullish = indicators.get('candlestick_bullish_signals', 0)
    if candlestick_bearish > 0:
        bearish_confirmations += 1
        confidence += 10
    if candlestick_bullish > 0:
        bullish_confirmations += 1
        confidence += 10
    
    # --- 9. MOMENTUM CONFIRMATION (CRUCIAL - Trade AVEC le marché!) ---
    # On ne trade que si le prix VA DÉJÀ dans notre direction
    if price_momentum == 'BULLISH':
        bullish_confirmations += 2  # Bonus important - le prix monte!
        confidence += 15
        # Pénaliser les SHORT contre le momentum
        bearish_confirmations -= 1
    elif price_momentum == 'BEARISH':
        bearish_confirmations += 2  # Bonus important - le prix descend!
        confidence += 15
        # Pénaliser les LONG contre le momentum
        bullish_confirmations -= 1
    
    # S'assurer que les confirmations ne sont pas négatives
    bullish_confirmations = max(0, bullish_confirmations)
    bearish_confirmations = max(0, bearish_confirmations)
    
    # --- 10. DÉCISION FINALE (TREND FOLLOWING - Trade AVEC le marché!) ---
    
    entry_signal = 'NEUTRAL'
    entry_price = None
    
    # Vérification ADX (La tendance existe-t-elle ?)
    # Si ADX < 15, le marché est en range (plat), scalping dangereux avec cette stratégie
    if adx is not None and adx < 15:
        confidence -= 20 # Pénalité forte

    # CRITÈRES D'ENTRÉE TREND FOLLOWING:
    # 1. Minimum 4 confirmations
    # 2. Confiance >= 50%
    # 3. Tendance EMA alignée
    # 4. MOMENTUM aligné (le prix va DÉJÀ dans notre direction!)
    # 5. Écart minimum de 2 entre bullish et bearish
    # 6. ADX > 18 (tendance présente)
    
    # Calcul de l'écart entre signaux
    signal_strength_diff = abs(bullish_confirmations - bearish_confirmations)
    
    # Filtre ADX - tendance présente (plus strict pour éviter de trader le bruit)
    adx_valid = adx is None or adx >= 20
    if adx is not None and adx < 22:
        confidence -= 5  # légère pénalité si la force de tendance est faible

    # FILTRE MOMENTUM - Ne trader que dans la direction active (plus de neutre toléré)
    momentum_aligned_long = price_momentum == 'BULLISH'
    momentum_aligned_short = price_momentum == 'BEARISH'

    # Anti-chasing: éviter d'acheter trop haut ou de shorter trop bas
    ema_ref = ema21 or ema9
    chasing_long = False
    chasing_short = False
    if ema_ref:
        if current_price > ema_ref * 1.02 and rsi14 and rsi14 > 65:
            chasing_long = True
        if current_price < ema_ref * 0.98 and rsi14 and rsi14 < 35:
            chasing_short = True

    if bullish_confirmations > bearish_confirmations and not chasing_long:
        # Signal FORT: plus de confirmations et confiance élevée, momentum impératif
        if bullish_confirmations >= 5 and confidence >= 60 and signal_strength_diff >= 3 and momentum_aligned_long and adx_valid:
            entry_signal = 'LONG'
            entry_price = current_price
        # Signal VALIDE: seuils relevés pour réduire les entrées tardives
        elif bullish_confirmations >= 4 and confidence >= 55 and ema_trend == 'BULLISH' and signal_strength_diff >= 2 and adx_valid and momentum_aligned_long:
            entry_signal = 'LONG'
            entry_price = current_price
            
    elif bearish_confirmations > bullish_confirmations and not chasing_short:
        # Signal FORT
        if bearish_confirmations >= 5 and confidence >= 60 and signal_strength_diff >= 3 and momentum_aligned_short and adx_valid:
            entry_signal = 'SHORT'
            entry_price = current_price
        # Signal VALIDE
        elif bearish_confirmations >= 4 and confidence >= 55 and ema_trend == 'BEARISH' and signal_strength_diff >= 2 and adx_valid and momentum_aligned_short:
            entry_signal = 'SHORT'
            entry_price = current_price

    # --- 11. Gestion du Risque (Stop Loss & Take Profit) ---
    stop_loss = None
    tp1 = None
    tp2 = None
    rr_ratio = None
    
    if entry_signal != 'NEUTRAL' and atr and entry_price:
        # Stop Loss basé sur ATR (Volatilité) - REALISTE R/R 2:1
        # SL à 1.5x ATR (assez serré mais évite le bruit)
        # TP à 3.0x ATR = R/R de 2:1 solide
        # Ce ratio permet d'être rentable avec 40% de win rate
        atr_sl_multiplier = 1.5
        atr_tp_multiplier = 3.0
        
        atr_value = atr
        
        if entry_signal == 'LONG':
            # SL sous le prix
            sl_dist = atr_value * atr_sl_multiplier
            stop_loss = entry_price - sl_dist
            
            # Si support proche, on place le SL juste sous le support pour être plus safe
            if support and support < entry_price:
                # On vérifie que le support n'est pas trop loin (max 2% de distance)
                if (entry_price - support) / entry_price < 0.02:
                    support_sl = support * 0.995
                    # On prend le stop le plus logique (souvent le support est mieux que l'ATR pur)
                    if support_sl > stop_loss: 
                        stop_loss = support_sl
            
            tp1 = entry_price + (atr_value * atr_tp_multiplier)
            tp2 = entry_price + (atr_value * 4.5)  # TP2 plus loin que TP1 pour partial TP
            
        elif entry_signal == 'SHORT':
            # SL au-dessus du prix
            sl_dist = atr_value * atr_sl_multiplier
            stop_loss = entry_price + sl_dist
            
            # Si résistance proche
            if resistance and resistance > entry_price:
                if (resistance - entry_price) / entry_price < 0.02:
                    res_sl = resistance * 1.005
                    if res_sl < stop_loss:
                        stop_loss = res_sl
            
            tp1 = entry_price - (atr_value * atr_tp_multiplier)
            tp2 = entry_price - (atr_value * 4.5)  # TP2 plus loin que TP1 pour partial TP

        # Calcul Ratio Risque/Récompense (Risk/Reward)
        risk = abs(entry_price - stop_loss)
        reward = abs(tp1 - entry_price)
        
        # Éviter division par zéro
        if risk > 0:
            rr_ratio = round(reward / risk, 2)
        else:
            rr_ratio = 0

    # Signal de sortie (Indicatif pour l'affichage)
    exit_signal = 'HOLD'
    if entry_signal == 'LONG' and rsi14 and rsi14 > 75:
        exit_signal = 'SELL (RSI Overbought)'
    elif entry_signal == 'SHORT' and rsi14 and rsi14 < 25:
        exit_signal = 'COVER (RSI Oversold)'

    # Plafonner la confiance à 100 pour l'affichage
    confidence = min(confidence, 100)
    confidence = max(confidence, 0)

    return {
        'entry_signal': entry_signal,
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'take_profit_1': tp1,
        'take_profit_2': tp2,
        'risk_reward_ratio': rr_ratio,
        'exit_signal': exit_signal,
        'confidence': confidence,
        'atr_percent': (atr / current_price * 100) if atr and current_price else 0
    }

def _empty_signal_result() -> Dict:
    """Retourne une structure vide par défaut pour éviter les erreurs."""
    return {
        'entry_signal': 'NEUTRAL',
        'entry_price': None,
        'stop_loss': None,
        'take_profit_1': None,
        'take_profit_2': None,
        'risk_reward_ratio': None,
        'exit_signal': 'N/A',
        'confidence': 0,
        'atr_percent': 0
    }

def find_resistance(df: pd.DataFrame, lookback: int = 30) -> Optional[float]:
    """
    Trouve le niveau de résistance (plus haut local) récent.
    """
    if df is None or len(df) < lookback:
        return None
    recent_data = df.tail(lookback)
    return float(recent_data['high'].max())
