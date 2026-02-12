"""
Module pour valider et filtrer les signaux (LONG et SHORT).
"""

from typing import Dict, List

def validate_signal_coherence(indicators: Dict, entry_signal: str) -> Dict:
    """
    Valide la cohérence du signal (Achat ou Vente).
    Seuil de validation assoupli à 50% pour les données réelles.
    """
    if entry_signal not in ['LONG', 'SHORT']:
        return {'is_valid': False, 'coherence_score': 0, 'warnings': ['Signal neutre'], 'strengths': []}
    
    warnings = []
    strengths = []
    coherence_score = 0
    max_score = 0
    
    # Données
    price = indicators.get('current_price')
    ema9 = indicators.get('ema9')
    ema21 = indicators.get('ema21')
    rsi = indicators.get('rsi14')
    macd = indicators.get('macd')
    macd_signal = indicators.get('macd_signal')
    adx = indicators.get('adx')
    
    # 1. EMA (25 pts)
    max_score += 25
    if ema9 and ema21 and price:
        if entry_signal == 'LONG':
            if ema9 > ema21:
                coherence_score += 25
                strengths.append("EMA Haussier")
            else:
                warnings.append("EMA Baissier (Danger Long)")
        elif entry_signal == 'SHORT':
            if ema9 < ema21:
                coherence_score += 25
                strengths.append("EMA Baissier")
            else:
                warnings.append("EMA Haussier (Danger Short)")

    # 2. MACD (25 pts)
    max_score += 25
    if macd is not None and macd_signal is not None:
        if entry_signal == 'LONG':
            if macd > macd_signal:
                coherence_score += 25
                strengths.append("MACD croisement Achat")
            else:
                warnings.append("MACD Vente")
        elif entry_signal == 'SHORT':
            if macd < macd_signal:
                coherence_score += 25
                strengths.append("MACD croisement Vente")
            else:
                warnings.append("MACD Achat")

    # 3. RSI (25 pts)
    max_score += 25
    if rsi is not None:
        if entry_signal == 'LONG':
            if 40 <= rsi <= 70:
                coherence_score += 25
                strengths.append("RSI Zone Achat")
            elif rsi > 70:
                warnings.append("RSI Surachat (Risqué)")
                coherence_score += 10 # Possible momentum fort
            else:
                warnings.append("RSI trop faible pour Achat")
        elif entry_signal == 'SHORT':
            if 30 <= rsi <= 60:
                coherence_score += 25
                strengths.append("RSI Zone Vente")
            elif rsi < 30:
                warnings.append("RSI Survente (Risqué)")
                coherence_score += 10
            else:
                warnings.append("RSI trop haut pour Vente")

    # 4. ADX (25 pts)
    max_score += 25
    if adx is not None:
        if adx > 20:
            coherence_score += 25
            strengths.append("Tendance présente")
        else:
            # On ne penalise pas trop, on met juste un warning
            warnings.append("Marché mou (ADX faible)")
            coherence_score += 10

    # Calcul final
    coherence_percent = (coherence_score / max_score * 100) if max_score > 0 else 0
    
    # Validation stricte : 65% de cohérence minimum (au lieu de 50%)
    # Cela améliore la qualité des signaux et augmente le taux de réussite
    is_valid = coherence_percent >= 65

    return {
        'is_valid': is_valid,
        'coherence_score': coherence_percent,
        'warnings': warnings,
        'strengths': strengths
    }

def calculate_signal_strength(indicators: Dict, entry_signal: str, confidence: int) -> Dict:
    """Calcul simplifié de la force du signal"""
    
    # On utilise la validation pour avoir le score de cohérence
    val = validate_signal_coherence(indicators, entry_signal)
    coherence = val['coherence_score']
    
    strength_score = (confidence + coherence) / 2
    
    if strength_score >= 80: quality = 'EXCELLENT'
    elif strength_score >= 60: quality = 'VERY_GOOD'
    elif strength_score >= 40: quality = 'GOOD'
    else: quality = 'WEAK'
    
    return {
        'strength': strength_score,
        'quality': quality,
        'risk_level': 'LOW' if strength_score > 60 else 'MEDIUM'
    }


def calculate_position_size(balance_usdt: float, entry_price: float, stop_loss: float, risk_per_trade: float = 0.01, min_usdt: float = 5.0) -> Dict:
    """
    Calcule la taille de position (en USDT et en quantité) basée sur le risque par trade.

    Args:
        balance_usdt: Solde disponible en USDT
        entry_price: Prix d'entrée
        stop_loss: Prix du stop loss
        risk_per_trade: Fraction du solde à risquer (ex: 0.01 = 1%)
        min_usdt: Taille minimale d'investissement acceptée

    Returns:
        Dictionnaire avec 'risk_amount_usdt', 'position_usdt', 'quantity' et 'notes'
    """
    notes = []

    # Validation basique
    if not entry_price or not stop_loss or entry_price == stop_loss:
        return {'risk_amount_usdt': 0, 'position_usdt': 0, 'quantity': 0, 'notes': ['Invalid price or stop_loss']}

    # Calcul du risque en USDT (ce qu'on est prêt à perdre)
    risk_amount = balance_usdt * float(risk_per_trade)

    # Distance en prix
    risk_dist = abs(entry_price - stop_loss)
    if risk_dist == 0:
        return {'risk_amount_usdt': 0, 'position_usdt': 0, 'quantity': 0, 'notes': ['Zero risk distance']}

    # Position size en quantité = risk_amount / risk_dist
    quantity = risk_amount / risk_dist

    # Montant à investir approximatif
    position_usdt = quantity * entry_price

    # Si la position est trop petite (frais / minimum), on lève une note
    if position_usdt < min_usdt:
        notes.append(f'Position too small (${position_usdt:.2f} < ${min_usdt})')

    return {
        'risk_amount_usdt': round(risk_amount, 6),
        'position_usdt': round(position_usdt, 6),
        'quantity': round(quantity, 8),
        'notes': notes
    }