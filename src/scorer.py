"""
Module pour calculer le score d'opportunité (0-100) pour chaque paire.
Amélioré avec détection de breakout, pullback et divergence RSI.
"""

from typing import Dict, Optional


def calculate_opportunity_score(indicators: Dict, support_distance: Optional[float],
                               breakout_signals: Optional[Dict] = None,
                               multi_timeframe_confirmation: Optional[str] = None) -> Dict:
    """
    Calcule le score d'opportunité selon les critères définis.
    
    Critères de scoring:
    - Trend bullish (SMA20 > SMA50) → +30 points
    - RSI entre 35 et 50 → +25 points
    - Prix proche support (<2%) → +25 points
    - Volume actuel > 1.5× volume moyen → +20 points
    
    Args:
        indicators: Dictionnaire avec les indicateurs techniques
        support_distance: Distance au support en pourcentage
    
    Returns:
        Dictionnaire avec le score total et les détails
    """
    score = 0
    details = []
    
    # 1. Trend bullish (SMA20 > SMA50) → +30
    sma20 = indicators.get('sma20')
    sma50 = indicators.get('sma50')
    if sma20 is not None and sma50 is not None:
        if sma20 > sma50:
            score += 30
            details.append("Trend bullish")
        else:
            details.append("Trend bearish")
    else:
        details.append("Trend indéterminé")
    
    # 2. RSI entre 35 et 50 → +25
    rsi = indicators.get('rsi14')
    if rsi is not None:
        if 35 <= rsi <= 50:
            score += 25
            details.append(f"RSI favorable ({rsi:.1f})")
        elif rsi < 35:
            details.append(f"RSI très bas ({rsi:.1f})")
        elif rsi > 70:
            details.append(f"RSI sur-acheté ({rsi:.1f})")
        else:
            details.append(f"RSI neutre ({rsi:.1f})")
    else:
        details.append("RSI indisponible")
    
    # 3. Prix proche support (<2%) → +25
    if support_distance is not None:
        if 0 <= support_distance < 2:
            score += 25
            details.append(f"Près du support ({support_distance:.2f}%)")
        elif support_distance < 0:
            details.append(f"Sous le support ({support_distance:.2f}%)")
        else:
            details.append(f"Loin du support ({support_distance:.2f}%)")
    else:
        details.append("Support non détecté")
    
    # 4. Volume actuel > 1.5× volume moyen → +20
    current_volume = indicators.get('current_volume')
    volume_ma = indicators.get('volume_ma20')
    volume_ratio = None
    if current_volume is not None and volume_ma is not None and volume_ma > 0:
        volume_ratio = current_volume / volume_ma
        if volume_ratio > 1.5:
            score += 20
            details.append(f"Volume élevé ({volume_ratio:.2f}x)")
        else:
            details.append(f"Volume normal ({volume_ratio:.2f}x)")
    else:
        details.append("Volume indisponible")
    
    # 5. Détection de breakout → +15 points supplémentaires
    if breakout_signals:
        breakout = breakout_signals.get('breakout', {})
        if breakout.get('breakout_detected', False):
            score += 15
            details.append(f"Breakout détecté ({breakout.get('breakout_type', 'N/A')})")
    
    # 6. Détection de pullback → +10 points supplémentaires
    if breakout_signals:
        pullback = breakout_signals.get('pullback', {})
        if pullback.get('pullback_detected', False):
            score += 10
            details.append(f"Pullback détecté ({pullback.get('pullback_type', 'N/A')})")
    
    # 7. Divergence RSI haussière → +10 points supplémentaires
    rsi_divergence = indicators.get('rsi_divergence', {})
    if rsi_divergence and rsi_divergence.get('divergence_detected', False):
        div_type = rsi_divergence.get('divergence_type', '')
        if 'Bullish' in div_type:
            score += 10
            details.append(f"Divergence RSI haussière ({rsi_divergence.get('strength', 'N/A')})")
        elif 'Bearish' in div_type:
            # Divergence baissière réduit légèrement le score
            score = max(0, score - 5)
            details.append(f"Divergence RSI baissière ({rsi_divergence.get('strength', 'N/A')})")
    
    # 8. Confirmation multi-timeframe → +5 points
    if multi_timeframe_confirmation:
        if multi_timeframe_confirmation == 'Bullish':
            score += 5
            details.append("Confirmation multi-timeframe bullish")
        elif multi_timeframe_confirmation == 'Bearish':
            score = max(0, score - 3)
            details.append("Confirmation multi-timeframe bearish")
    
    # Limiter le score à 100
    score = min(100, score)
    
    # Générer un signal textuel
    signal_parts = []
    if "Trend bullish" in details[0]:
        signal_parts.append("Bullish")
    if "RSI favorable" in " ".join(details):
        signal_parts.append("RSI OK")
    if "Près du support" in " ".join(details):
        signal_parts.append("Near support")
    if "Volume élevé" in " ".join(details):
        signal_parts.append("Volume spike")
    if breakout_signals and breakout_signals.get('breakout', {}).get('breakout_detected', False):
        signal_parts.append("Breakout")
    if breakout_signals and breakout_signals.get('pullback', {}).get('pullback_detected', False):
        signal_parts.append("Pullback")
    if rsi_divergence and rsi_divergence.get('divergence_detected', False) and 'Bullish' in rsi_divergence.get('divergence_type', ''):
        signal_parts.append("RSI Divergence")
    
    signal = " + ".join(signal_parts) if signal_parts else "Neutre"
    
    # Déterminer la confirmation de tendance
    trend_confirmation = "Strong"
    if multi_timeframe_confirmation == 'Bullish' and sma20 and sma50 and sma20 > sma50:
        trend_confirmation = "Very Strong"
    elif sma20 and sma50 and sma20 > sma50:
        trend_confirmation = "Confirmed"
    elif sma20 and sma50 and sma20 <= sma50:
        trend_confirmation = "Weak"
    else:
        trend_confirmation = "Unconfirmed"
    
    return {
        'score': score,
        'signal': signal,
        'details': details,
        'rsi': rsi,
        'trend': 'Bullish' if (sma20 and sma50 and sma20 > sma50) else 'Bearish',
        'volume_ratio': volume_ratio,
        'trend_confirmation': trend_confirmation
    }

