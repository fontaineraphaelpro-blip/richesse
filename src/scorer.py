"""
Module pour calculer le score d'opportunité adapté au scalping (0-100).
Gère les signaux LONG et SHORT.
"""

from typing import Dict, Optional
from scalping_signals import calculate_entry_exit_signals, find_resistance
from signal_validation import validate_signal_coherence, calculate_signal_strength


def detect_trend(indicators: Dict) -> str:
    """Détecte la tendance globale."""
    bullish_signals = 0
    bearish_signals = 0
    
    ema9 = indicators.get('ema9')
    ema21 = indicators.get('ema21')
    macd = indicators.get('macd')
    macd_signal = indicators.get('macd_signal')
    
    if ema9 and ema21:
        if ema9 > ema21: bullish_signals += 1
        elif ema9 < ema21: bearish_signals += 1
        
    if macd is not None and macd_signal is not None:
        if macd > macd_signal: bullish_signals += 1
        elif macd < macd_signal: bearish_signals += 1

    if bullish_signals > bearish_signals: return 'Bullish'
    elif bearish_signals > bullish_signals: return 'Bearish'
    return 'NEUTRAL'


def calculate_opportunity_score(indicators: Dict, support_distance: Optional[float], df=None) -> Dict:
    """
    Calcule le score (0-100) pour LONG et SHORT.
    """
    score = 0
    details = []
    
    # Données
    rsi14 = indicators.get('rsi14')
    trend = detect_trend(indicators)
    
    # Support/Résistance
    support = None
    resistance = None
    if df is not None:
        from support import find_swing_low
        support = find_swing_low(df, lookback=30)
        resistance = find_resistance(df, lookback=30)
    
    # Calcul signaux bruts
    signals = calculate_entry_exit_signals(indicators, support, resistance)
    entry_signal = signals.get('entry_signal', 'NEUTRAL')
    confidence = signals.get('confidence', 0)

    # Si le signal est NEUTRAL, on arrête là
    if entry_signal == 'NEUTRAL':
        return {
            'score': 0, 'signal': "⚪ ATTENTE", 'details': "", 'trend': trend,
            'entry_signal': 'NEUTRAL', 'confidence': 0
        }
    
    # FILTRE ADX OBLIGATOIRE - Tendance forte requise
    adx = indicators.get('adx')
    if adx is None or adx < 20:
        return {
            'score': 0, 'signal': "⚪ ADX FAIBLE", 'details': f"ADX {adx:.1f} < 20 requis",
            'trend': trend, 'entry_signal': 'NEUTRAL', 'confidence': 0
        }
    
    # FILTRE CONFIANCE MINIMALE - 70% obligatoire
    if confidence < 70:
        return {
            'score': 0, 'signal': "⚪ CONFIANCE FAIBLE", 'details': f"Confiance {confidence}% < 70%",
            'trend': trend, 'entry_signal': 'NEUTRAL', 'confidence': 0
        }

    # Validation de cohérence
    validation = validate_signal_coherence(indicators, entry_signal)
    
    if not validation['is_valid']:
        return {
            'score': 0, 'signal': "⚪ INVALIDÉ", 'details': "Signal rejeté par validation", 
            'trend': trend, 'entry_signal': 'NEUTRAL', 'confidence': 0
        }
    
    # --- CALCUL DU SCORE ---
    # Base: Confiance du signal (0-40 pts)
    score += min(confidence, 40)
    
    # Cohérence technique (0-30 pts)
    score += min(validation['coherence_score'] * 0.3, 30)
    
    # Bonus Contextuels (0-30 pts)
    
    # 1. RSI favorable - LOGIQUE AMELIOREE (zones optimales)
    if rsi14:
        if entry_signal == 'LONG':
            # LONG: bonus si RSI en zone OPTIMALE (30-50), pas extreme
            if 30 <= rsi14 <= 50:
                score += 15  # Zone ideale pour LONG
                details.append("RSI Zone Optimale LONG")
            elif 50 < rsi14 <= 60:
                score += 10
                details.append("RSI Momentum LONG")
            elif rsi14 < 30:
                score += 5   # Oversold risque mais possible
                details.append("RSI Oversold (risque)")
            # RSI > 60 = pas de bonus pour LONG
        elif entry_signal == 'SHORT':
            # SHORT: bonus si RSI en zone OPTIMALE (50-70), pas extreme
            if 50 <= rsi14 <= 70:
                score += 15  # Zone ideale pour SHORT
                details.append("RSI Zone Optimale SHORT")
            elif 40 <= rsi14 < 50:
                score += 10
                details.append("RSI Pre-correction")
            elif rsi14 > 70:
                score += 5   # Overbought risque mais possible
                details.append("RSI Overbought (risque)")
            # RSI < 40 = pas de bonus pour SHORT
            
    # 2. Alignement Tendance
    if (entry_signal == 'LONG' and trend == 'Bullish') or \
       (entry_signal == 'SHORT' and trend == 'Bearish'):
        score += 10
        details.append("Aligné Tendance")
        
    # 3. Volume
    vol = indicators.get('current_volume')
    vol_ma = indicators.get('volume_ma20')
    if vol and vol_ma and vol > vol_ma:
        score += 10
        details.append("Volume Fort")

    # Plafond score
    score = min(score, 100)
    
    # Texte final
    signal_text = "⚠️ SIGNAL FAIBLE"
    if score >= 75: signal_text = "🔥 OPPORTUNITÉ FORTE"
    elif score >= 50: signal_text = "✅ OPPORTUNITÉ"

    return {
        'score': int(score),
        'signal': signal_text,
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
