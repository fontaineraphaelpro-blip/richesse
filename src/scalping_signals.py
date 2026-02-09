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
    
    # Calculer le signal d'entrée avec critères STRICTS
    entry_signal = 'NEUTRAL'
    confidence = 0
    entry_price = current_price
    
    # Compteurs de confirmations (nécessaires pour un signal valide)
    bullish_confirmations = 0
    bearish_confirmations = 0
    
    # 1. Croisement EMA (nécessaire mais pas suffisant seul)
    # UNIQUEMENT pour SHORT: EMA9 < EMA21 ET prix < EMA9
    ema_bearish = False
    if ema9 and ema21:
        if ema9 < ema21 and current_price < ema9:
            # Vérifier que l'écart est significatif (au moins 0.1%)
            ema_gap = ((ema21 - ema9) / ema9) * 100
            price_below_ema = ((ema9 - current_price) / ema9) * 100
            if ema_gap > 0.1 and price_below_ema > 0.05:  # Écart significatif
                ema_bearish = True
                bearish_confirmations += 1
                confidence += 20  # Plus de poids pour EMA bearish
    
    # 2. RSI (filtre important pour SHORT - éviter survente)
    rsi_ok_bearish = False
    if rsi14 is not None:
        # Pour SHORT: RSI entre 50-75 (zone de surachat à survente modérée)
        # Éviter RSI < 30 (survente extrême = risque de rebond)
        if 50 <= rsi14 <= 75:
            if ema_bearish:
                rsi_ok_bearish = True
                bearish_confirmations += 1
                confidence += 20  # RSI élevé confirme SHORT
        elif 40 <= rsi14 < 50:
            if ema_bearish:
                # RSI modéré mais bearish = confirmation faible
                bearish_confirmations += 1
                confidence += 10
    
    # 3. MACD (confirmation de tendance bearish)
    macd_bearish = False
    if macd is not None and macd_signal is not None:
        if macd < macd_signal:
            macd_bearish = True
            if ema_bearish:
                bearish_confirmations += 1
                confidence += 20  # MACD bearish = confirmation forte
                # Histogramme négatif = confirmation supplémentaire
                if macd_histogram and macd_histogram < 0:
                    bearish_confirmations += 1
                    confidence += 10
    
    # 4. Bollinger Bands (filtre de volatilité et position pour SHORT)
    bb_ok_bearish = False
    if bb_lower and bb_upper and (bb_upper - bb_lower) > 0:
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
        # Pour SHORT: prix proche ou au-dessus bande supérieure (surachat)
        # OU prix au-dessus de la bande moyenne (tendance bearish)
        if bb_position > 0.6 and ema_bearish:
            bb_ok_bearish = True
            bearish_confirmations += 1
            confidence += 15
            # Entrer légèrement en dessous de la bande supérieure ou au prix actuel
            if bb_position > 0.8:
                entry_price = min(current_price, bb_upper * 0.999)
            else:
                entry_price = min(current_price, bb_upper * 0.998)
    
    # 5. Volume (confirmation importante pour SHORT - minimum 1.5x)
    volume_ok = False
    if volume_ratio:
        if volume_ratio > 1.5 and ema_bearish:
            volume_ok = True
            bearish_confirmations += 1
            confidence += 15  # Volume élevé confirme la pression vendeuse
            if volume_ratio > 2.0:
                confidence += 10  # Volume très élevé = signal SHORT très fort
    
    # 6. Momentum (confirmation de direction bearish)
    momentum_ok = False
    if momentum:
        if momentum < 0 and ema_bearish:
            # Momentum négatif = pression vendeuse
            momentum_ok = True
            bearish_confirmations += 1
            confidence += 10
            # Momentum très négatif = signal plus fort
            if momentum_percent and momentum_percent < -0.5:
                confidence += 5
    
    # DÉCISION FINALE: UNIQUEMENT les signaux SHORT
    # Nécessite AU MOINS 4 confirmations bearish pour un signal SHORT valide
    # et confiance minimum de 60 (plus strict pour SHORT)
    if bearish_confirmations >= 4 and confidence >= 60:
        entry_signal = 'SHORT'
        entry_price = min(current_price, ema9) * 0.9995 if ema9 else current_price * 0.9995
    else:
        # Pas assez de confirmations ou pas bearish = pas de signal
        entry_signal = 'NEUTRAL'
        confidence = 0
    
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

