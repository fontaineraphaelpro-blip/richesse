"""
Module pour calculer le score d'opportunité adapté au scalping (0-100).
"""

from typing import Dict, Optional
from scalping_signals import calculate_entry_exit_signals, find_resistance


def detect_trend(indicators: Dict) -> str:
    """
    Détecte la tendance avec plusieurs confirmations pour plus de fiabilité.
    
    Utilise:
    - EMA9 vs EMA21
    - SMA20 vs SMA50
    - MACD
    - Position du prix vs moyennes mobiles
    - Momentum
    - Position dans Bollinger Bands
    
    Returns:
        'Bullish', 'Bearish', ou 'NEUTRAL'
    """
    bullish_signals = 0
    bearish_signals = 0
    
    ema9 = indicators.get('ema9')
    ema21 = indicators.get('ema21')
    sma20 = indicators.get('sma20')
    sma50 = indicators.get('sma50')
    current_price = indicators.get('current_price')
    macd = indicators.get('macd')
    macd_signal = indicators.get('macd_signal')
    momentum = indicators.get('momentum')
    bb_middle = indicators.get('bb_middle')
    
    # 1. EMA9 vs EMA21 (tendance court terme)
    if ema9 and ema21:
        if ema9 > ema21:
            bullish_signals += 1
        elif ema9 < ema21:
            bearish_signals += 1
    
    # 2. SMA20 vs SMA50 (tendance moyen terme)
    if sma20 and sma50:
        if sma20 > sma50:
            bullish_signals += 1
        elif sma20 < sma50:
            bearish_signals += 1
    
    # 3. Position du prix vs EMA21 (confirmation)
    if current_price and ema21:
        if current_price > ema21:
            bullish_signals += 1
        elif current_price < ema21:
            bearish_signals += 1
    
    # 4. Position du prix vs SMA50 (tendance plus large)
    if current_price and sma50:
        if current_price > sma50:
            bullish_signals += 1
        elif current_price < sma50:
            bearish_signals += 1
    
    # 5. MACD (confirmation de tendance)
    if macd and macd_signal:
        if macd > macd_signal:
            bullish_signals += 1
        elif macd < macd_signal:
            bearish_signals += 1
    
    # 6. Momentum (direction du mouvement)
    if momentum:
        if momentum > 0:
            bullish_signals += 1
        elif momentum < 0:
            bearish_signals += 1
    
    # 7. Position vs Bollinger Middle (tendance générale)
    if current_price and bb_middle:
        if current_price > bb_middle:
            bullish_signals += 1
        elif current_price < bb_middle:
            bearish_signals += 1
    
    # Décision: nécessite au moins 4 confirmations sur 7 pour une tendance claire
    if bullish_signals >= 4:
        return 'Bullish'
    elif bearish_signals >= 4:
        return 'Bearish'
    else:
        # Si égalité ou pas assez de confirmations = tendance neutre
        if bullish_signals > bearish_signals:
            return 'Bullish'  # Légèrement bullish mais pas assez confirmé
        elif bearish_signals > bullish_signals:
            return 'Bearish'  # Légèrement bearish mais pas assez confirmé
        else:
            return 'NEUTRAL'


def calculate_opportunity_score(indicators: Dict, support_distance: Optional[float], df=None) -> Dict:
    """
    Calcule le score d'opportunité (0-100) adapté au scalping.
    
    Critères de scoring pour scalping:
    - Signal d'entrée fort (LONG/SHORT) → +30
    - RSI optimal pour scalping (40-60) → +20
    - EMA croisement (EMA9 > EMA21) → +20
    - MACD bullish → +15
    - Volume élevé (>1.5x) → +10
    - Prix proche support/résistance → +5
    
    Args:
        indicators: Dictionnaire avec les indicateurs techniques
        support_distance: Distance en % entre prix actuel et support
        df: DataFrame OHLCV (optionnel, pour trouver résistance)
    
    Returns:
        Dictionnaire avec le score, les détails et les signaux
    """
    score = 0
    details = []
    
    # Récupérer les indicateurs
    ema9 = indicators.get('ema9')
    ema21 = indicators.get('ema21')
    rsi14 = indicators.get('rsi14')
    macd = indicators.get('macd')
    macd_signal = indicators.get('macd_signal')
    macd_histogram = indicators.get('macd_histogram')
    current_volume = indicators.get('current_volume')
    volume_ma20 = indicators.get('volume_ma20')
    atr_percent = indicators.get('atr_percent')
    momentum_percent = indicators.get('momentum_percent')
    current_price = indicators.get('current_price')  # Prix actuel
    
    # Trouver support et résistance
    support = None
    resistance = None
    if df is not None:
        from support import find_swing_low
        support = find_swing_low(df, lookback=30)
        resistance = find_resistance(df, lookback=30)
    
    # Calculer les signaux d'entrée/sortie
    signals = calculate_entry_exit_signals(indicators, support, resistance)
    
    # Déterminer le trend AVANT de calculer le score (pour vérifier la cohérence)
    trend = detect_trend(indicators)
    
    # 1. Signal d'entrée fort (LONG/SHORT) → +30 (seulement si confiance >= 50)
    entry_signal = signals.get('entry_signal', 'NEUTRAL')
    confidence = signals.get('confidence', 0)
    
    # UNIQUEMENT les signaux SHORT sont acceptés
    if entry_signal == 'SHORT':
        if confidence >= 65:  # Confiance minimum encore plus élevée pour SHORT
            # Bonus si le signal SHORT est cohérent avec tendance Bearish
            if trend == 'Bearish':
                score += 40  # Bonus important pour SHORT + tendance Bearish
                details.append(f"Signal SHORT ✓ (conf: {confidence}%, tendance: {trend})")
            elif trend == 'NEUTRAL':
                score += 30  # Pas de bonus mais pas de pénalité
                details.append(f"Signal SHORT (conf: {confidence}%, tendance: {trend})")
            else:
                score += 15  # Pénalité si signal SHORT avec tendance Bullish
                details.append(f"Signal SHORT ⚠️ (conf: {confidence}%, contre-tendance: {trend})")
        else:
            # Signal faible = pas de points
            entry_signal = 'NEUTRAL'
            details.append(f"Signal SHORT trop faible (conf: {confidence}%)")
    else:
        # Ignorer les signaux LONG
        entry_signal = 'NEUTRAL'
        details.append("Pas de signal SHORT")
    
    # 2. RSI pour SHORT (50-75 = zone favorable)
    if rsi14 is not None:
        if entry_signal == 'SHORT':
            if 60 <= rsi14 <= 75:
                score += 25  # RSI élevé = excellent pour SHORT
                details.append(f"RSI surachat ({rsi14:.1f}) ✓")
            elif 50 <= rsi14 < 60:
                score += 15  # RSI modéré-élevé = bon pour SHORT
                details.append(f"RSI élevé ({rsi14:.1f}) ✓")
            elif 40 <= rsi14 < 50:
                score += 5  # RSI neutre = faible confirmation
                details.append(f"RSI neutre ({rsi14:.1f})")
            else:
                score -= 15  # Pénalité si RSI trop bas (risque de rebond)
                details.append(f"RSI trop bas ({rsi14:.1f}) ✗")
        else:
            details.append(f"RSI {rsi14:.1f} (pas de signal SHORT)")
    else:
        details.append("RSI N/A")
    
    # 3. EMA croisement bearish (EMA9 < EMA21) → +25 pour SHORT
    if ema9 is not None and ema21 is not None:
        if entry_signal == 'SHORT' and ema9 < ema21:
            # Vérifier l'écart significatif
            ema_gap = ((ema21 - ema9) / ema9) * 100
            if ema_gap > 0.2:
                score += 25  # Écart important = signal fort
                details.append(f"EMA bearish fort ✓ (écart: {ema_gap:.2f}%)")
            else:
                score += 20
                details.append("EMA bearish ✓")
        elif entry_signal == 'SHORT':
            score -= 20  # Pénalité importante si EMA ne confirme pas SHORT
            details.append("EMA incompatible ✗")
        else:
            details.append("EMA neutre")
    else:
        details.append("EMA N/A")
    
    # 4. MACD bearish → +20 pour SHORT
    if macd is not None and macd_signal is not None:
        if entry_signal == 'SHORT' and macd < macd_signal:
            score += 20
            if macd_histogram and macd_histogram < -0.001:  # Histogramme négatif significatif
                score += 10
                details.append("MACD bearish très fort ✓")
            else:
                details.append("MACD bearish ✓")
        elif entry_signal == 'SHORT':
            score -= 15  # Pénalité si MACD ne confirme pas SHORT
            details.append("MACD incompatible ✗")
        else:
            details.append("MACD neutre")
    else:
        details.append("MACD N/A")
    
    # 5. Volume élevé (>1.5x) → +15 pour SHORT (obligatoire)
    volume_ratio = None
    if current_volume is not None and volume_ma20 is not None and volume_ma20 > 0:
        volume_ratio = current_volume / volume_ma20
        if entry_signal == 'SHORT':
            if volume_ratio > 2.0:
                score += 20  # Volume très élevé = pression vendeuse forte
                details.append(f"Volume très élevé ({volume_ratio:.2f}x) ✓✓")
            elif volume_ratio > 1.5:
                score += 15
                details.append(f"Volume élevé ({volume_ratio:.2f}x) ✓")
            else:
                score -= 15  # Pénalité importante si volume insuffisant pour SHORT
                details.append(f"Volume faible ({volume_ratio:.2f}x) ✗")
        else:
            details.append(f"Volume {volume_ratio:.2f}x")
    else:
        details.append("Volume N/A")
    
    # 9. Stochastic (surachat) → +15 pour SHORT
    stoch_k = indicators.get('stoch_k')
    stoch_d = indicators.get('stoch_d')
    if stoch_k is not None and stoch_d is not None:
        if entry_signal == 'SHORT':
            if stoch_k > 80 and stoch_d > 80:
                score += 20  # Stochastic surachat extrême = excellent pour SHORT
                details.append(f"Stoch surachat ({stoch_k:.1f}/{stoch_d:.1f}) ✓✓")
            elif stoch_k > 70 and stoch_d > 70:
                score += 15
                details.append(f"Stoch élevé ({stoch_k:.1f}/{stoch_d:.1f}) ✓")
            else:
                score -= 10  # Pénalité si Stochastic pas en surachat
                details.append(f"Stoch modéré ({stoch_k:.1f}/{stoch_d:.1f}) ✗")
    
    # 10. ADX (force de la tendance) → +15 pour SHORT
    adx = indicators.get('adx')
    if adx is not None:
        if entry_signal == 'SHORT':
            if adx > 30:
                score += 20  # Tendance très forte = signal SHORT très fiable
                details.append(f"ADX très fort ({adx:.1f}) ✓✓")
            elif adx > 25:
                score += 15
                details.append(f"ADX fort ({adx:.1f}) ✓")
            elif adx > 20:
                score += 10
                details.append(f"ADX modéré ({adx:.1f})")
            else:
                score -= 15  # Pénalité si tendance faible
                details.append(f"ADX faible ({adx:.1f}) ✗")
    
    # 11. Divergence RSI bearish → +25 pour SHORT (signal très fort)
    rsi_divergence = indicators.get('rsi_divergence', False)
    rsi_divergence_type = indicators.get('rsi_divergence_type')
    if rsi_divergence and rsi_divergence_type == 'bearish':
        if entry_signal == 'SHORT':
            score += 25  # Divergence bearish = signal très fort
            details.append("Divergence RSI bearish ✓✓✓")
    
    # 12. Patterns de chandeliers bearish → +20 pour SHORT
    candlestick_bearish = indicators.get('candlestick_bearish_signals', 0)
    has_bearish_candlestick = indicators.get('has_bearish_candlestick', False)
    if has_bearish_candlestick and entry_signal == 'SHORT':
        score += min(candlestick_bearish * 7, 25)  # Max 25 points
        details.append(f"Pattern chandelier bearish ({candlestick_bearish}) ✓")
    
    # 13. Patterns chartistes bearish → +30 pour SHORT (très fort)
    chart_bearish = indicators.get('chart_bearish_signals', 0)
    has_bearish_chart = indicators.get('has_bearish_chart_pattern', False)
    if has_bearish_chart and entry_signal == 'SHORT':
        score += min(chart_bearish * 10, 30)  # Max 30 points
        details.append(f"Pattern chartiste bearish ({chart_bearish}) ✓✓")
    
    # 14. Proximité zone de résistance → +15 pour SHORT
    nearest_resistance = indicators.get('nearest_resistance')
    if nearest_resistance and entry_signal == 'SHORT' and current_price:
        distance = ((nearest_resistance - current_price) / current_price) * 100
        if 0 <= distance <= 2:
            score += 15
            details.append(f"Proche résistance ({distance:.2f}%) ✓")
    
    # 15. Niveaux psychologiques → +10 pour SHORT
    psychological_levels = indicators.get('psychological_levels', [])
    if psychological_levels and entry_signal == 'SHORT' and current_price:
        for level in psychological_levels:
            distance = abs((current_price - level) / current_price) * 100
            if distance < 0.5:
                score += 10
                details.append(f"Niveau psychologique ${level:.2f} ✓")
                break
    
    # 16. Zones de liquidité → +12 pour SHORT
    liquidity_clusters = indicators.get('liquidity_clusters', [])
    if liquidity_clusters and entry_signal == 'SHORT' and current_price:
        for cluster in liquidity_clusters[:2]:
            distance = abs((current_price - cluster['price']) / current_price) * 100
            if distance < 1.0 and cluster['strength'] > 2.0:
                score += 12
                details.append(f"Zone liquidité (force: {cluster['strength']:.1f}) ✓")
                break
    
    # 17. Niveaux Fibonacci → +10 pour SHORT
    nearest_fibonacci = indicators.get('nearest_fibonacci')
    if nearest_fibonacci and entry_signal == 'SHORT' and current_price:
        distance = abs((current_price - nearest_fibonacci) / current_price) * 100
        if distance < 0.5:
            fib_ratio = indicators.get('nearest_fib_ratio')
            score += 10
            details.append(f"Fibonacci {fib_ratio} ({distance:.2f}%) ✓")
    
    # 6. Prix proche support/résistance → +5
    if support_distance is not None:
        if 0 <= support_distance < 1:
            score += 5
            details.append(f"Proche support ({support_distance:.2f}%)")
        else:
            details.append(f"Loin support ({support_distance:.2f}%)")
    
    # 7. Volatilité (ATR) adaptée au scalping → +5
    if atr_percent is not None:
        if 0.5 <= atr_percent <= 3.0:  # Volatilité modérée pour scalping
            score += 5
            details.append(f"Volatilité OK ({atr_percent:.2f}%)")
        else:
            details.append(f"Volatilité {atr_percent:.2f}%")
    
    # 8. Momentum positif → +5
    if momentum_percent is not None:
        if momentum_percent > 0:
            score += 5
            details.append(f"Momentum +{momentum_percent:.2f}%")
        else:
            details.append(f"Momentum {momentum_percent:.2f}%")
    
    # Déterminer le signal (seuils plus stricts)
    # Score minimum de 60 pour être considéré comme opportunité
    # Bonus si signal cohérent avec tendance
    trend_bonus = 0
    if (entry_signal == 'LONG' and trend == 'Bullish') or (entry_signal == 'SHORT' and trend == 'Bearish'):
        trend_bonus = 5
        score += trend_bonus
    
    if score >= 75 and entry_signal != 'NEUTRAL' and confidence >= 60:
        signal = "🔥 Opportunité scalping EXCELLENTE"
    elif score >= 60 and entry_signal != 'NEUTRAL' and confidence >= 50:
        signal = "✅ Opportunité scalping BONNE"
    elif score >= 45 and entry_signal != 'NEUTRAL':
        signal = "⚠️ Opportunité scalping MODÉRÉE"
    else:
        signal = "❌ Pas d'opportunité valide"
    
    return {
        'score': score,
        'signal': signal,
        'details': ' | '.join(details),
        'trend': trend,
        'entry_signal': entry_signal,
        'confidence': confidence,
        'entry_price': signals.get('entry_price'),
        'stop_loss': signals.get('stop_loss'),
        'take_profit_1': signals.get('take_profit_1'),
        'take_profit_2': signals.get('take_profit_2'),
        'risk_reward_ratio': signals.get('risk_reward_ratio'),
        'exit_signal': signals.get('exit_signal'),
        'atr_percent': signals.get('atr_percent')
    }
