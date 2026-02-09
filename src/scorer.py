"""
Module pour calculer le score d'opportunité (0-100).
"""

from typing import Dict, Optional


def calculate_opportunity_score(indicators: Dict, support_distance: Optional[float]) -> Dict:
    """
    Calcule le score d'opportunité (0-100) basé sur plusieurs critères.
    
    Critères de scoring:
    - Trend bullish (SMA20 > SMA50) → +30
    - RSI entre 35 et 50 → +25
    - Prix proche support (<2%) → +25
    - Volume actuel > 1.5× volume moyen → +20
    
    Args:
        indicators: Dictionnaire avec les indicateurs techniques
        support_distance: Distance en % entre prix actuel et support
    
    Returns:
        Dictionnaire avec le score et les détails
    """
    score = 0
    details = []
    
    sma20 = indicators.get('sma20')
    sma50 = indicators.get('sma50')
    rsi14 = indicators.get('rsi14')
    current_volume = indicators.get('current_volume')
    volume_ma20 = indicators.get('volume_ma20')
    
    # 1. Trend bullish (SMA20 > SMA50) → +30
    if sma20 is not None and sma50 is not None:
        if sma20 > sma50:
            score += 30
            details.append("Trend bullish")
        else:
            details.append("Trend bearish")
    else:
        details.append("Trend indéterminé")
    
    # 2. RSI entre 35 et 50 → +25
    if rsi14 is not None:
        if 35 <= rsi14 <= 50:
            score += 25
            details.append(f"RSI optimal ({rsi14:.1f})")
        elif rsi14 < 35:
            details.append(f"RSI très bas ({rsi14:.1f})")
        else:
            details.append(f"RSI élevé ({rsi14:.1f})")
    else:
        details.append("RSI N/A")
    
    # 3. Prix proche support (<2%) → +25
    if support_distance is not None:
        if 0 <= support_distance < 2:
            score += 25
            details.append(f"Proche support ({support_distance:.2f}%)")
        elif support_distance < 0:
            details.append(f"Sous support ({abs(support_distance):.2f}%)")
        else:
            details.append(f"Loin du support ({support_distance:.2f}%)")
    else:
        details.append("Support N/A")
    
    # 4. Volume actuel > 1.5× volume moyen → +20
    if current_volume is not None and volume_ma20 is not None and volume_ma20 > 0:
        volume_ratio = current_volume / volume_ma20
        if volume_ratio > 1.5:
            score += 20
            details.append(f"Volume élevé ({volume_ratio:.2f}x)")
        else:
            details.append(f"Volume normal ({volume_ratio:.2f}x)")
    else:
        details.append("Volume N/A")
    
    # Déterminer le signal
    if score >= 80:
        signal = "Opportunité forte"
    elif score >= 60:
        signal = "Opportunité modérée"
    elif score >= 40:
        signal = "Surveillance"
    else:
        signal = "Faible opportunité"
    
    return {
        'score': score,
        'signal': signal,
        'details': ' | '.join(details),
        'trend': 'Bullish' if (sma20 and sma50 and sma20 > sma50) else 'Bearish'
    }
