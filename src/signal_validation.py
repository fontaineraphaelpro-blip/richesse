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

    # 3. RSI (25 pts) - TREND FOLLOWING (pas contrarian!)
    # PRINCIPE: Trader AVEC la tendance, pas anticiper les retournements
    max_score += 25
    if rsi is not None:
        if entry_signal == 'LONG':
            # LONG valide si RSI en zone de MOMENTUM HAUSSIER (40-65)
            # RSI < 35 = marché en chute = DANGER pour LONG
            # RSI > 70 = surachat = risque de correction
            if 45 <= rsi <= 60:
                coherence_score += 25  # Zone IDEALE pour LONG (momentum sain)
                strengths.append("RSI Momentum Haussier Optimal")
            elif 40 <= rsi < 45:
                coherence_score += 20
                strengths.append("RSI Momentum Haussier")
            elif 60 < rsi <= 70:
                coherence_score += 15  # Encore OK mais prudence
                warnings.append("RSI élevé - proche surachat")
            elif rsi < 40:
                coherence_score += 5  # Marché faible - LONG risqué
                warnings.append("RSI faible - momentum baissier!")
            else:  # RSI > 70
                coherence_score += 0
                warnings.append("RSI SURACHAT - éviter LONG")
        elif entry_signal == 'SHORT':
            # SHORT valide si RSI en zone de MOMENTUM BAISSIER (35-55)
            # RSI > 65 = marché en hausse = DANGER pour SHORT
            # RSI < 30 = survente = risque de rebond
            if 40 <= rsi <= 55:
                coherence_score += 25  # Zone IDEALE pour SHORT (momentum baissier)
                strengths.append("RSI Momentum Baissier Optimal")
            elif 55 < rsi <= 60:
                coherence_score += 20
                strengths.append("RSI Pré-correction")
            elif 30 <= rsi < 40:
                coherence_score += 15  # Encore OK mais prudence
                warnings.append("RSI bas - proche survente")
            elif rsi > 60:
                coherence_score += 5  # Marché fort - SHORT risqué
                warnings.append("RSI élevé - momentum haussier!")
            else:  # RSI < 30
                coherence_score += 0
                warnings.append("RSI SURVENTE - éviter SHORT")

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
    
    # Validation EQUILIBREE : 60% de cohérence minimum
    # Permet ~5 trades/jour tout en filtrant les mauvais signaux
    is_valid = coherence_percent >= 60

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
