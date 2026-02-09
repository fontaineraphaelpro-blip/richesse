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
    entry_price = current_price
    
    # 1. Croisement EMA (signal fort pour scalping)
    if ema9 and ema21:
        if ema9 > ema21:
            confidence += 20
            if current_price > ema9:
                confidence += 10
                entry_signal = 'LONG'
        else:
            if current_price < ema9:
                confidence += 10
                entry_signal = 'SHORT'
    
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
    
    # 4. Bollinger Bands (rebond ou breakout)
    if bb_lower and bb_upper:
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
        if bb_position < 0.2 and entry_signal == 'LONG':
            confidence += 10  # Rebound depuis bande inférieure
            entry_price = bb_lower * 1.001  # Entrée légèrement au-dessus
        elif bb_position > 0.8 and entry_signal == 'SHORT':
            confidence += 10  # Rebound depuis bande supérieure
            entry_price = bb_upper * 0.999  # Entrée légèrement en dessous
    
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
    
    if atr and atr > 0:
        # Stop-loss: 1.5x ATR pour scalping
        atr_stop = atr * 1.5
        
        if entry_signal == 'LONG':
            stop_loss = entry_price - atr_stop
            # Take-profit 1: 2x ATR (objectif rapide)
            take_profit_1 = entry_price + (atr * 2)
            # Take-profit 2: 3x ATR (objectif étendu)
            take_profit_2 = entry_price + (atr * 3)
        elif entry_signal == 'SHORT':
            stop_loss = entry_price + atr_stop
            # Take-profit 1: 2x ATR
            take_profit_1 = entry_price - (atr * 2)
            # Take-profit 2: 3x ATR
            take_profit_2 = entry_price - (atr * 3)
        
        # Calculer ratio risque/récompense
        if stop_loss and take_profit_1:
            if entry_signal == 'LONG':
                risk = entry_price - stop_loss
                reward = take_profit_1 - entry_price
            else:
                risk = stop_loss - entry_price
                reward = entry_price - take_profit_1
            
            if risk > 0:
                risk_reward_ratio = round(reward / risk, 2)
    
    # Ajuster stop-loss avec support/résistance si disponible
    if entry_signal == 'LONG' and support:
        if stop_loss is None or stop_loss < support * 0.995:
            stop_loss = support * 0.995  # Juste en dessous du support
    
    if entry_signal == 'SHORT' and resistance:
        if stop_loss is None or stop_loss > resistance * 1.005:
            stop_loss = resistance * 1.005  # Juste au-dessus de la résistance
    
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

