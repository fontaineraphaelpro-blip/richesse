"""
Module pour détecter les signaux d'entrée et de sortie pour le scalping.
Adapté pour les données réelles (Binance) avec des seuils réalistes.
"""

import pandas as pd
from typing import Dict, Optional, Tuple

def calculate_entry_exit_signals(indicators: Dict, support: Optional[float], resistance: Optional[float]) -> Dict:
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

    # --- 4. Analyse du Momentum (RSI) - Améliorée ---
    # Scalping : On cherche les rebonds ou les continuités, mais on évite les extrêmes absolus
    if rsi14 is not None:
        # Logique LONG : On veut un RSI qui a de la marge pour monter (pas > 70)
        # Amélioré: Plus restrictif en zone oversold (30-45) = meilleurs signaux
        if 45 <= rsi14 <= 65: 
            if ema_trend == 'BULLISH':
                bullish_confirmations += 2  # Augmenté de 1 à 2
                confidence += 20  # Augmenté de 15 à 20
        elif 30 <= rsi14 < 45:  # Zone rebond possible
            if ema_trend == 'BULLISH':
                bullish_confirmations += 1
                confidence += 10
        
        # Logique SHORT : On veut un RSI qui a de la marge pour descendre (pas < 30)
        # Amélioré: Plus restrictif en zone overbought (55-70) = meilleurs signaux
        if 35 <= rsi14 <= 55: 
            if ema_trend == 'BEARISH':
                bearish_confirmations += 2  # Augmenté de 1 à 2
                confidence += 20  # Augmenté de 15 à 20
        elif 55 < rsi14 <= 70:  # Zone rebond possible
            if ema_trend == 'BEARISH':
                bearish_confirmations += 1
                confidence += 10
                
        # Divergences (Si calculées)
        div_type = indicators.get('rsi_divergence_type')
        if indicators.get('rsi_divergence'):
            if div_type == 'bearish':
                bearish_confirmations += 2  # Amélioré: signal fort
                confidence += 20  # Augmenté de 15 à 20
            elif div_type == 'bullish':
                bullish_confirmations += 2  # Amélioré: signal fort
                confidence += 20  # Augmenté de 15 à 20

    # --- 5. Analyse MACD (Améliorée - Momentum fort) ---
    if macd is not None and macd_signal is not None:
        macd_diff = macd - macd_signal
        
        # Amélioré: On vérifie que ce n'est pas juste un croisement mou
        if macd > macd_signal:
            confidence += 15  # Augmenté de 10 à 15
            # Bonus si MACD s'éloigne du signal (momentum fort)
            if macd_diff > 0.00005:  # Seuil pour momentum visible
                bullish_confirmations += 2  # Signal fort
                confidence += 10  # Bonus momentum
            else:
                bullish_confirmations += 1  # Juste le croisement
        elif macd < macd_signal:
            confidence += 15  # Augmenté de 10 à 15
            # Bonus si MACD s'éloigne du signal (momentum fort)
            if macd_diff < -0.00005:  # Seuil pour momentum visible
                bearish_confirmations += 2  # Signal fort
                confidence += 10  # Bonus momentum
            else:
                bearish_confirmations += 1  # Juste le croisement

    # --- 6. Analyse Volume (Améliorée pour meilleure qualité) ---
    # Le volume DOIT valider le mouvement (sinon c'est un piège)
    if volume_ratio >= 1.3: # Volume 30% supérieur à la moyenne (était 20%)
        confidence += 15  # Bonus augmenté
        # Le volume confirme la direction de la bougie actuelle
        if ema_trend == 'BULLISH':
            bullish_confirmations += 2  # Augmenté de 1 à 2
        elif ema_trend == 'BEARISH':
            bearish_confirmations += 2  # Augmenté de 1 à 2
    elif volume_ratio >= 1.0:
        confidence += 5  # Petit bonus si volume normal

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
    if candlestick_bearish > 0:
        bearish_confirmations += 1
        confidence += 5
    
    # --- 9. DÉCISION FINALE (Thresholds améliorés pour meilleure qualité) ---
    
    entry_signal = 'NEUTRAL'
    entry_price = None
    
    # Vérification ADX (La tendance existe-t-elle ?)
    # Augmenté de 15 à 20 : On veut une vraie tendance, pas du range
    if adx is not None and adx < 20:
        confidence -= 25 # Pénalité encore plus forte

    # CRITÈRES D'ENTRÉE (AMÉLIORÉS) :
    # 1. Minimum 5 confirmations (était 4) - Plus strict
    # 2. Confiance > 55% (était 50%) - Plus exigeant
    
    if bearish_confirmations >= 5 and confidence >= 55 and ema_trend == 'BEARISH':
        entry_signal = 'SHORT'
        entry_price = current_price
        
    elif bullish_confirmations >= 5 and confidence >= 55 and ema_trend == 'BULLISH':
        entry_signal = 'LONG'
        entry_price = current_price

    # --- 10. Gestion du Risque (Stop Loss & Take Profit) ---
    stop_loss = None
    tp1 = None
    tp2 = None
    rr_ratio = None
    
    if entry_signal != 'NEUTRAL' and atr and entry_price:
        # Stop Loss basé sur ATR (Volatilité)
        # Scalping 15m : SL à 1.5x ATR, TP à 2x et 3x ATR
        atr_sl_multiplier = 2.5
        atr_tp_multiplier = 3.5
        
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
            tp2 = entry_price + (atr_value * 3.0)
            
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
            tp2 = entry_price - (atr_value * 3.0)

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
