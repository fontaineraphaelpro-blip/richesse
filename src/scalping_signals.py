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
    sma20 = indicators.get('sma20')
    sma50 = indicators.get('sma50')
    rsi14 = indicators.get('rsi14')
    macd = indicators.get('macd')
    macd_signal = indicators.get('macd_signal')
    macd_histogram = indicators.get('macd_histogram')
    bb_upper = indicators.get('bb_upper')
    bb_lower = indicators.get('bb_lower')
    bb_middle = indicators.get('bb_middle')
    atr = indicators.get('atr')
    atr_percent = indicators.get('atr_percent')
    momentum = indicators.get('momentum')
    momentum_percent = indicators.get('momentum_percent')
    stoch_k = indicators.get('stoch_k')
    stoch_d = indicators.get('stoch_d')
    adx = indicators.get('adx')
    rsi_divergence = indicators.get('rsi_divergence', False)
    rsi_divergence_type = indicators.get('rsi_divergence_type')
    
    # Patterns
    candlestick_bearish = indicators.get('candlestick_bearish_signals', 0)
    chart_bearish = indicators.get('chart_bearish_signals', 0)
    has_bearish_candlestick = indicators.get('has_bearish_candlestick', False)
    has_bearish_chart = indicators.get('has_bearish_chart_pattern', False)
    
    # Zones de liquidité
    nearest_support = indicators.get('nearest_support')
    nearest_resistance = indicators.get('nearest_resistance')
    support_zones = indicators.get('support_zones', [])
    resistance_zones = indicators.get('resistance_zones', [])
    liquidity_clusters = indicators.get('liquidity_clusters', [])
    psychological_levels = indicators.get('psychological_levels', [])
    
    # Fibonacci
    nearest_fibonacci = indicators.get('nearest_fibonacci')
    
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
            if momentum_percent is not None and momentum_percent < -0.5:
                confidence += 5
    
    # 7. Stochastic (confirmation de surachat pour SHORT)
    stoch_ok_bearish = False
    if stoch_k is not None and stoch_d is not None:
        # Pour SHORT: Stochastic > 80 = surachat confirmé
        if stoch_k > 80 and stoch_d > 80:
            if ema_bearish:
                stoch_ok_bearish = True
                bearish_confirmations += 1
                confidence += 15  # Stochastic surachat = confirmation forte
        elif stoch_k > 70 and stoch_d > 70:
            if ema_bearish:
                bearish_confirmations += 1
                confidence += 10
    
    # 8. ADX (force de la tendance - nécessaire pour SHORT valide)
    adx_ok = False
    if adx is not None:
        # ADX > 25 = tendance forte (bon pour SHORT)
        if adx > 25:
            adx_ok = True
            if ema_bearish:
                bearish_confirmations += 1
                confidence += 15  # Tendance forte = signal SHORT plus fiable
        elif adx > 20:
            if ema_bearish:
                bearish_confirmations += 1
                confidence += 8
        else:
            # ADX faible = tendance faible, pénalité
            confidence -= 10
    
    # 9. Divergence RSI bearish (signal très fort pour SHORT)
    if rsi_divergence and rsi_divergence_type == 'bearish':
        if ema_bearish:
            bearish_confirmations += 2  # Divergence = double confirmation
            confidence += 25  # Divergence bearish = signal très fort
    
    # 13. Patterns de chandeliers bearish
    if has_bearish_candlestick and ema_bearish:
        bearish_confirmations += 1
        confidence += candlestick_bearish * 5  # Plus le pattern est fort, plus on ajoute
        if candlestick_bearish >= 3:
            bearish_confirmations += 1  # Pattern très bearish = double confirmation
    
    # 14. Patterns chartistes bearish
    if has_bearish_chart and ema_bearish:
        bearish_confirmations += 1
        confidence += chart_bearish * 8  # Patterns chartistes = très importants
        if chart_bearish >= 3:
            bearish_confirmations += 1  # Pattern très bearish = double confirmation
    
    # 15. Proximité d'une zone de résistance (liquidity zone)
    if nearest_resistance and current_price:
        distance_to_resistance = ((nearest_resistance - current_price) / current_price) * 100
        if 0 <= distance_to_resistance <= 2 and ema_bearish:  # Proche de la résistance
            bearish_confirmations += 1
            confidence += 15  # Proche résistance = bon point d'entrée SHORT
    
    # 16. Niveaux psychologiques (round numbers)
    if psychological_levels and current_price:
        for level in psychological_levels:
            distance = abs((current_price - level) / current_price) * 100
            if distance < 0.5:  # Très proche d'un niveau psychologique
                if current_price < level and ema_bearish:  # En dessous = résistance
                    bearish_confirmations += 1
                    confidence += 10
                break
    
    # 17. Zones de liquidité (clusters de volume)
    if liquidity_clusters and current_price:
        for cluster in liquidity_clusters[:2]:  # Top 2 clusters
            cluster_price = cluster['price']
            distance = abs((current_price - cluster_price) / current_price) * 100
            if distance < 1.0 and cluster['strength'] > 2.0:  # Proche d'une zone de forte liquidité
                if current_price < cluster_price and ema_bearish:
                    bearish_confirmations += 1
                    confidence += 8
    
    # 18. Niveaux Fibonacci (résistance)
    if nearest_fibonacci and current_price:
        distance_to_fib = abs((current_price - nearest_fibonacci) / current_price) * 100
        if distance_to_fib < 0.5:  # Très proche d'un niveau Fibonacci
            if current_price < nearest_fibonacci and ema_bearish:
                bearish_confirmations += 1
                confidence += 12
    
    # 10. SMA20 vs SMA50 (confirmation tendance moyen terme)
    sma_bearish = False
    if sma20 and sma50:
        if sma20 < sma50 and current_price < sma20:
            sma_bearish = True
            if ema_bearish:
                bearish_confirmations += 1
                confidence += 15
    
    # 11. Prix vs toutes les moyennes mobiles (confirmation globale)
    price_below_all_ma = False
    ma_count = 0
    ma_below_count = 0
    if ema9 and current_price < ema9:
        ma_count += 1
        ma_below_count += 1
    if ema21 and current_price < ema21:
        ma_count += 1
        ma_below_count += 1
    if sma20 and current_price < sma20:
        ma_count += 1
        ma_below_count += 1
    if sma50 and current_price < sma50:
        ma_count += 1
        ma_below_count += 1
    
    if ma_count >= 3 and ma_below_count == ma_count:
        price_below_all_ma = True
        if ema_bearish:
            bearish_confirmations += 1
            confidence += 10
    
    # 12. Position dans Bollinger Bands (vérification supplémentaire)
    if bb_middle and current_price:
        if current_price > bb_middle:
            if ema_bearish:
                bearish_confirmations += 1
                confidence += 5
    
    # DÉCISION FINALE: UNIQUEMENT les signaux SHORT
    # Nécessite AU MOINS 8 confirmations bearish pour un signal SHORT valide
    # et confiance minimum de 75 (très strict avec toutes les données)
    # ET ADX > 20 (tendance doit être présente)
    if bearish_confirmations >= 8 and confidence >= 75 and (adx is None or adx > 20):
        entry_signal = 'SHORT'
        entry_price = min(current_price, ema9) * 0.9995 if ema9 else current_price * 0.9995
    elif bearish_confirmations >= 7 and confidence >= 70 and (adx is None or adx > 25):
        # Signal SHORT acceptable mais moins fort
        entry_signal = 'SHORT'
        entry_price = min(current_price, ema9) * 0.9995 if ema9 else current_price * 0.9995
        confidence = min(confidence, 70)  # Limiter la confiance
    elif bearish_confirmations >= 6 and confidence >= 65 and (adx is None or adx > 25):
        # Signal SHORT minimal acceptable
        entry_signal = 'SHORT'
        entry_price = min(current_price, ema9) * 0.9995 if ema9 else current_price * 0.9995
        confidence = min(confidence, 65)
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

