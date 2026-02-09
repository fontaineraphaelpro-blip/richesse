"""
Module pour détecter les signaux d'entrée et de sortie pour le scalping.
"""

import pandas as pd
from typing import Dict, Optional, Tuple


def calculate_entry_exit_signals(indicators: Dict, support: Optional[float], resistance: Optional[float]) -> Dict:
    """
    Calcule les signaux d'entrée et de sortie pour le scalping.
    
    Args:
        indicators: Dictionnaire avec les indicateurs techniques
        support: Niveau de support
        resistance: Niveau de résistance
    
    Returns:
        Dictionnaire avec les signaux d'entrée/sortie, prix recommandés, stop-loss, take-profit
    """
    current_price = indicators.get('current_price')
    if current_price is None:
        return {
            'entry_signal': 'N/A',
            'entry_price': None,
            'stop_loss': None,
            'take_profit_1': None,
            'take_profit_2': None,
            'risk_reward_ratio': None,
            'exit_signal': 'N/A',
            'confidence': 0
        }
    
    # Récupérer les indicateurs
    ema9 = indicators.get('ema9')
    ema21 = indicators.get('ema21')
    rsi14 = indicators.get('rsi14')
    macd = indicators.get('macd')
    macd_signal = indicators.get('macd_signal')
    macd_histogram = indicators.get('macd_histogram')
    bb_upper = indicators.get('bb_upper')
    bb_lower = indicators.get('bb_lower')
    atr = indicators.get('atr')
    atr_percent = indicators.get('atr_percent')
    momentum = indicators.get('momentum')
    volume_ratio = None
    if indicators.get('current_volume') and indicators.get('volume_ma20') and indicators.get('volume_ma20') > 0:
        volume_ratio = indicators.get('current_volume') / indicators.get('volume_ma20')
    
    # Calculer le signal d'entrée
    entry_signal = 'NEUTRAL'
    confidence = 0
    # Le prix d'entrée doit toujours être proche du prix actuel (max 0.5% d'écart)
    entry_price = current_price
    
    # 1. Croisement EMA (signal fort pour scalping)
    if ema9 and ema21:
        if ema9 > ema21:
            confidence += 20
            if current_price > ema9:
                confidence += 10
                entry_signal = 'LONG'
                # Pour LONG, entrer légèrement au-dessus du prix actuel ou au niveau EMA9
                entry_price = max(current_price, ema9) * 1.0005  # +0.05% pour éviter les slippages
        else:
            if current_price < ema9:
                confidence += 10
                entry_signal = 'SHORT'
                # Pour SHORT, entrer légèrement en dessous du prix actuel ou au niveau EMA9
                entry_price = min(current_price, ema9) * 0.9995  # -0.05% pour éviter les slippages
    
    # 2. RSI (zone optimale pour scalping: 40-60)
    if rsi14 is not None:
        if 40 <= rsi14 <= 60:
            confidence += 15
        elif 30 <= rsi14 < 40 and entry_signal == 'LONG':
            confidence += 10  # Survente pour long
        elif 60 < rsi14 <= 70 and entry_signal == 'SHORT':
            confidence += 10  # Surachat pour short
    
    # 3. MACD (croisement)
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            confidence += 15
            if macd_histogram and macd_histogram > 0:
                confidence += 5
        elif macd < macd_signal:
            if entry_signal == 'SHORT':
                confidence += 15
    
    # 4. Bollinger Bands (rebond ou breakout) - ajuster le prix d'entrée si opportunité
    if bb_lower and bb_upper and (bb_upper - bb_lower) > 0:
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
        if bb_position < 0.2 and entry_signal == 'LONG':
            confidence += 10  # Rebound depuis bande inférieure
            # Entrer légèrement au-dessus de la bande inférieure ou au prix actuel
            entry_price = max(current_price, bb_lower * 1.001)  # +0.1% au-dessus de la bande
        elif bb_position > 0.8 and entry_signal == 'SHORT':
            confidence += 10  # Rebound depuis bande supérieure
            # Entrer légèrement en dessous de la bande supérieure ou au prix actuel
            entry_price = min(current_price, bb_upper * 0.999)  # -0.1% en dessous de la bande
    
    # 5. Volume (confirmation)
    if volume_ratio and volume_ratio > 1.5:
        confidence += 10
    
    # 6. Momentum
    if momentum and momentum > 0 and entry_signal == 'LONG':
        confidence += 5
    elif momentum and momentum < 0 and entry_signal == 'SHORT':
        confidence += 5
    
    # Calculer stop-loss et take-profit basés sur ATR
    stop_loss = None
    take_profit_1 = None
    take_profit_2 = None
    risk_reward_ratio = None
    
    if atr and atr > 0 and entry_signal != 'NEUTRAL':
        # Stop-loss: 1.5x ATR pour scalping (mais minimum 0.5% et maximum 3%)
        atr_stop = atr * 1.5
        min_stop = entry_price * 0.005  # 0.5% minimum
        max_stop = entry_price * 0.03   # 3% maximum
        atr_stop = max(min_stop, min(atr_stop, max_stop))
        
        if entry_signal == 'LONG':
            stop_loss = entry_price - atr_stop
            # S'assurer que le stop-loss est en dessous du prix actuel
            stop_loss = min(stop_loss, current_price * 0.98)  # Max 2% en dessous du prix actuel
            
            # Take-profit 1: 2x ATR (objectif rapide) mais minimum 1% de gain
            tp1_atr = max(atr * 2, entry_price * 0.01)
            take_profit_1 = entry_price + tp1_atr
            
            # Take-profit 2: 3x ATR (objectif étendu) mais minimum 1.5% de gain
            tp2_atr = max(atr * 3, entry_price * 0.015)
            take_profit_2 = entry_price + tp2_atr
            
        elif entry_signal == 'SHORT':
            stop_loss = entry_price + atr_stop
            # S'assurer que le stop-loss est au-dessus du prix actuel
            stop_loss = max(stop_loss, current_price * 1.02)  # Max 2% au-dessus du prix actuel
            
            # Take-profit 1: 2x ATR mais minimum 1% de gain
            tp1_atr = max(atr * 2, entry_price * 0.01)
            take_profit_1 = entry_price - tp1_atr
            
            # Take-profit 2: 3x ATR mais minimum 1.5% de gain
            tp2_atr = max(atr * 3, entry_price * 0.015)
            take_profit_2 = entry_price - tp2_atr
        
        # Calculer ratio risque/récompense
        if stop_loss and take_profit_1:
            if entry_signal == 'LONG':
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit_1 - entry_price)
            else:
                risk = abs(stop_loss - entry_price)
                reward = abs(entry_price - take_profit_1)
            
            if risk > 0:
                risk_reward_ratio = round(reward / risk, 2)
    
    # Ajuster stop-loss avec support/résistance si disponible (mais garder les limites ATR)
    if entry_signal == 'LONG' and support and support < current_price:
        # Stop-loss juste en dessous du support, mais pas trop loin
        support_stop = support * 0.995
        if stop_loss is None or support_stop < stop_loss:
            # Utiliser le stop le plus proche (le plus protecteur)
            stop_loss = max(support_stop, current_price * 0.97)  # Min 3% en dessous
    
    if entry_signal == 'SHORT' and resistance and resistance > current_price:
        # Stop-loss juste au-dessus de la résistance, mais pas trop loin
        resistance_stop = resistance * 1.005
        if stop_loss is None or resistance_stop > stop_loss:
            # Utiliser le stop le plus proche (le plus protecteur)
            stop_loss = min(resistance_stop, current_price * 1.03)  # Max 3% au-dessus
    
    # Déterminer le signal de sortie
    exit_signal = 'HOLD'
    if entry_signal == 'LONG':
        if rsi14 and rsi14 > 70:
            exit_signal = 'SELL (RSI surachat)'
        elif macd and macd_signal and macd < macd_signal:
            exit_signal = 'SELL (MACD bearish)'
        elif ema9 and ema21 and ema9 < ema21:
            exit_signal = 'SELL (EMA croisement)'
    elif entry_signal == 'SHORT':
        if rsi14 and rsi14 < 30:
            exit_signal = 'COVER (RSI survente)'
        elif macd and macd_signal and macd > macd_signal:
            exit_signal = 'COVER (MACD bullish)'
        elif ema9 and ema21 and ema9 > ema21:
            exit_signal = 'COVER (EMA croisement)'
    
    # Limiter la confiance à 100
    confidence = min(confidence, 100)
    
    return {
        'entry_signal': entry_signal,
        'entry_price': round(entry_price, 8) if entry_price else None,
        'stop_loss': round(stop_loss, 8) if stop_loss else None,
        'take_profit_1': round(take_profit_1, 8) if take_profit_1 else None,
        'take_profit_2': round(take_profit_2, 8) if take_profit_2 else None,
        'risk_reward_ratio': risk_reward_ratio,
        'exit_signal': exit_signal,
        'confidence': confidence,
        'atr_percent': round(atr_percent, 2) if atr_percent else None
    }


def find_resistance(df, lookback: int = 30) -> Optional[float]:
    """
    Trouve le niveau de résistance (swing high).
    """
    if df is None or len(df) < lookback:
        return None
    
    recent_data = df.tail(lookback)
    swing_high = recent_data['high'].max()
    
    return float(swing_high)

