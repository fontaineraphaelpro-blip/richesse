"""
Module pour calculer le score d'opportunité (0-100) pour chaque paire.
"""

from typing import Dict, Optional


def calculate_opportunity_score(indicators: Dict, support_distance: Optional[float]) -> Dict:
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
    if current_volume is not None and volume_ma is not None and volume_ma > 0:
        volume_ratio = current_volume / volume_ma
        if volume_ratio > 1.5:
            score += 20
            details.append(f"Volume élevé ({volume_ratio:.2f}x)")
        else:
            details.append(f"Volume normal ({volume_ratio:.2f}x)")
    else:
        details.append("Volume indisponible")
    
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
    
    signal = " + ".join(signal_parts) if signal_parts else "Neutre"
    
    return {
        'score': score,
        'signal': signal,
        'details': details,
        'rsi': rsi,
        'trend': 'Bullish' if (sma20 and sma50 and sma20 > sma50) else 'Bearish'
    }

