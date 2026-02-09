"""
Module pour calculer le score d'opportunité adapté au scalping (0-100).
"""

from typing import Dict, Optional
from scalping_signals import calculate_entry_exit_signals, find_resistance


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
    
    # Trouver support et résistance
    support = None
    resistance = None
    if df is not None:
        from support import find_swing_low
        support = find_swing_low(df, lookback=30)
        resistance = find_resistance(df, lookback=30)
    
    # Calculer les signaux d'entrée/sortie
    signals = calculate_entry_exit_signals(indicators, support, resistance)
    
    # 1. Signal d'entrée fort (LONG/SHORT) → +30 (seulement si confiance >= 50)
    entry_signal = signals.get('entry_signal', 'NEUTRAL')
    confidence = signals.get('confidence', 0)
    
    if entry_signal == 'LONG' or entry_signal == 'SHORT':
        if confidence >= 50:
            score += 30
            details.append(f"Signal {entry_signal} (conf: {confidence}%)")
        else:
            # Signal faible = pas de points
            entry_signal = 'NEUTRAL'
            details.append(f"Signal {entry_signal} trop faible (conf: {confidence}%)")
    else:
        details.append("Pas de signal clair")
    
    # 2. RSI optimal pour scalping (40-60) → +20 (seulement si signal valide)
    if rsi14 is not None:
        if entry_signal != 'NEUTRAL':
            if 40 <= rsi14 <= 60:
                score += 20
                details.append(f"RSI optimal ({rsi14:.1f})")
            elif 30 <= rsi14 < 40 and entry_signal == 'LONG':
                score += 15  # Survente pour LONG
                details.append(f"RSI survente ({rsi14:.1f})")
            elif 60 < rsi14 <= 70 and entry_signal == 'SHORT':
                score += 15  # Surachat pour SHORT
                details.append(f"RSI surachat ({rsi14:.1f})")
            else:
                score -= 10  # Pénalité si RSI ne correspond pas au signal
                details.append(f"RSI incompatible ({rsi14:.1f})")
        else:
            details.append(f"RSI {rsi14:.1f} (pas de signal)")
    else:
        details.append("RSI N/A")
    
    # 3. EMA croisement (EMA9 > EMA21) → +20 (seulement si cohérent avec signal)
    if ema9 is not None and ema21 is not None:
        if entry_signal == 'LONG' and ema9 > ema21:
            score += 20
            details.append("EMA bullish ✓")
        elif entry_signal == 'SHORT' and ema9 < ema21:
            score += 20
            details.append("EMA bearish ✓")
        elif entry_signal != 'NEUTRAL':
            score -= 15  # Pénalité si EMA ne correspond pas au signal
            details.append("EMA incompatible ✗")
        else:
            details.append("EMA neutre")
    else:
        details.append("EMA N/A")
    
    # 4. MACD → +15 (seulement si cohérent avec signal)
    if macd is not None and macd_signal is not None:
        if entry_signal == 'LONG' and macd > macd_signal:
            score += 15
            if macd_histogram and macd_histogram > 0:
                score += 5
                details.append("MACD bullish fort ✓")
            else:
                details.append("MACD bullish ✓")
        elif entry_signal == 'SHORT' and macd < macd_signal:
            score += 15
            details.append("MACD bearish ✓")
        elif entry_signal != 'NEUTRAL':
            score -= 10  # Pénalité si MACD ne correspond pas
            details.append("MACD incompatible ✗")
        else:
            details.append("MACD neutre")
    else:
        details.append("MACD N/A")
    
    # 5. Volume élevé (>1.3x) → +10 (obligatoire pour signal valide)
    volume_ratio = None
    if current_volume is not None and volume_ma20 is not None and volume_ma20 > 0:
        volume_ratio = current_volume / volume_ma20
        if entry_signal != 'NEUTRAL':
            if volume_ratio > 1.5:
                score += 10
                details.append(f"Volume élevé ({volume_ratio:.2f}x) ✓")
            elif volume_ratio > 1.3:
                score += 5
                details.append(f"Volume OK ({volume_ratio:.2f}x) ✓")
            else:
                score -= 10  # Pénalité si volume insuffisant
                details.append(f"Volume faible ({volume_ratio:.2f}x) ✗")
        else:
            details.append(f"Volume {volume_ratio:.2f}x")
    else:
        details.append("Volume N/A")
    
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
    if score >= 75 and entry_signal != 'NEUTRAL' and confidence >= 60:
        signal = "🔥 Opportunité scalping EXCELLENTE"
    elif score >= 60 and entry_signal != 'NEUTRAL' and confidence >= 50:
        signal = "✅ Opportunité scalping BONNE"
    elif score >= 45 and entry_signal != 'NEUTRAL':
        signal = "⚠️ Opportunité scalping MODÉRÉE"
    else:
        signal = "❌ Pas d'opportunité valide"
    
    # Déterminer le trend
    trend = 'Bullish'
    if ema9 and ema21:
        trend = 'Bullish' if ema9 > ema21 else 'Bearish'
    elif indicators.get('sma20') and indicators.get('sma50'):
        trend = 'Bullish' if indicators.get('sma20') > indicators.get('sma50') else 'Bearish'
    
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
