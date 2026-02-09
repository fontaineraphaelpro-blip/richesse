"""
Module pour valider et filtrer les signaux avec des vérifications de cohérence avancées.
"""

from typing import Dict, Optional, List, Tuple


def validate_signal_coherence(indicators: Dict, entry_signal: str) -> Dict:
    """
    Valide la cohérence globale du signal en vérifiant tous les indicateurs.
    
    Returns:
        Dictionnaire avec 'is_valid', 'coherence_score', 'warnings', 'strengths'
    """
    if entry_signal != 'SHORT':
        return {
            'is_valid': False,
            'coherence_score': 0,
            'warnings': ['Signal non-SHORT'],
            'strengths': []
        }
    
    warnings = []
    strengths = []
    coherence_score = 0
    max_score = 0
    
    current_price = indicators.get('current_price')
    ema9 = indicators.get('ema9')
    ema21 = indicators.get('ema21')
    sma20 = indicators.get('sma20')
    sma50 = indicators.get('sma50')
    rsi14 = indicators.get('rsi14')
    macd = indicators.get('macd')
    macd_signal = indicators.get('macd_signal')
    macd_histogram = indicators.get('macd_histogram')
    stoch_k = indicators.get('stoch_k')
    stoch_d = indicators.get('stoch_d')
    adx = indicators.get('adx')
    bb_upper = indicators.get('bb_upper')
    bb_lower = indicators.get('bb_lower')
    bb_middle = indicators.get('bb_middle')
    volume_ratio = None
    if indicators.get('current_volume') and indicators.get('volume_ma20') and indicators.get('volume_ma20') > 0:
        volume_ratio = indicators.get('current_volume') / indicators.get('volume_ma20')
    
    # 1. Vérification EMA (obligatoire)
    max_score += 20
    if ema9 and ema21 and current_price:
        if ema9 < ema21 and current_price < ema9:
            coherence_score += 20
            strengths.append("EMA bearish confirmé")
        else:
            warnings.append("EMA ne confirme pas SHORT")
    
    # 2. Vérification SMA (tendance moyen terme)
    max_score += 15
    if sma20 and sma50 and current_price:
        if sma20 < sma50 and current_price < sma20:
            coherence_score += 15
            strengths.append("SMA bearish confirmé")
        else:
            warnings.append("SMA ne confirme pas SHORT")
    
    # 3. Vérification RSI (zone optimale)
    max_score += 15
    if rsi14 is not None:
        if 50 <= rsi14 <= 75:
            coherence_score += 15
            strengths.append(f"RSI optimal ({rsi14:.1f})")
        elif 40 <= rsi14 < 50:
            coherence_score += 10
            strengths.append(f"RSI modéré ({rsi14:.1f})")
        elif rsi14 < 40:
            warnings.append(f"RSI trop bas ({rsi14:.1f}) - risque rebond")
        else:
            warnings.append(f"RSI extrême ({rsi14:.1f})")
    
    # 4. Vérification MACD
    max_score += 15
    if macd is not None and macd_signal is not None:
        if macd < macd_signal:
            coherence_score += 15
            strengths.append("MACD bearish")
            if macd_histogram and macd_histogram < -0.001:
                coherence_score += 5
                strengths.append("MACD histogram négatif fort")
        else:
            warnings.append("MACD ne confirme pas SHORT")
    
    # 5. Vérification Stochastic
    max_score += 10
    if stoch_k is not None and stoch_d is not None:
        if stoch_k > 70 and stoch_d > 70:
            coherence_score += 10
            strengths.append("Stochastic surachat")
        elif stoch_k > 60 and stoch_d > 60:
            coherence_score += 5
        else:
            warnings.append("Stochastic pas en surachat")
    
    # 6. Vérification ADX (force tendance)
    max_score += 15
    if adx is not None:
        if adx > 25:
            coherence_score += 15
            strengths.append(f"ADX fort ({adx:.1f})")
        elif adx > 20:
            coherence_score += 10
            strengths.append(f"ADX modéré ({adx:.1f})")
        else:
            warnings.append(f"ADX faible ({adx:.1f}) - tendance faible")
    
    # 7. Vérification Volume
    max_score += 10
    if volume_ratio:
        if volume_ratio > 1.5:
            coherence_score += 10
            strengths.append(f"Volume élevé ({volume_ratio:.2f}x)")
        elif volume_ratio > 1.2:
            coherence_score += 5
        else:
            warnings.append(f"Volume insuffisant ({volume_ratio:.2f}x)")
    
    # 8. Vérification Bollinger Bands
    max_score += 10
    if bb_upper and bb_lower and current_price:
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
        if bb_position > 0.6:
            coherence_score += 10
            strengths.append("Prix proche bande supérieure")
        elif bb_position > 0.4:
            coherence_score += 5
        else:
            warnings.append("Prix trop bas dans Bollinger")
    
    # 9. Vérification Patterns
    max_score += 10
    candlestick_bearish = indicators.get('candlestick_bearish_signals', 0)
    chart_bearish = indicators.get('chart_bearish_signals', 0)
    if candlestick_bearish > 0 or chart_bearish > 0:
        coherence_score += min(10, (candlestick_bearish + chart_bearish) * 2)
        strengths.append(f"Patterns bearish détectés")
    else:
        warnings.append("Aucun pattern bearish")
    
    # 10. Vérification Divergence RSI
    max_score += 10
    rsi_divergence = indicators.get('rsi_divergence', False)
    if rsi_divergence:
        coherence_score += 10
        strengths.append("Divergence RSI bearish")
    
    # Calcul du score de cohérence (0-100%)
    coherence_percent = (coherence_score / max_score * 100) if max_score > 0 else 0
    
    # Signal valide si cohérence >= 70%
    is_valid = coherence_percent >= 70 and len(warnings) <= 2
    
    return {
        'is_valid': is_valid,
        'coherence_score': coherence_percent,
        'warnings': warnings,
        'strengths': strengths,
        'max_score': max_score,
        'actual_score': coherence_score
    }


def calculate_signal_strength(indicators: Dict, entry_signal: str, confidence: int) -> Dict:
    """
    Calcule la force relative du signal basée sur tous les facteurs.
    
    Returns:
        Dictionnaire avec 'strength', 'quality', 'risk_level'
    """
    if entry_signal != 'SHORT':
        return {
            'strength': 0,
            'quality': 'INVALID',
            'risk_level': 'HIGH'
        }
    
    # Validation de cohérence
    validation = validate_signal_coherence(indicators, entry_signal)
    
    if not validation['is_valid']:
        return {
            'strength': 0,
            'quality': 'INVALID',
            'risk_level': 'HIGH',
            'reason': 'Cohérence insuffisante'
        }
    
    # Facteurs de force
    strength_factors = []
    strength_score = 0
    
    # 1. Confiance du signal
    if confidence >= 80:
        strength_score += 30
        strength_factors.append("Confiance très élevée")
    elif confidence >= 70:
        strength_score += 20
        strength_factors.append("Confiance élevée")
    elif confidence >= 60:
        strength_score += 10
        strength_factors.append("Confiance modérée")
    
    # 2. Cohérence globale
    coherence = validation['coherence_score']
    if coherence >= 85:
        strength_score += 25
        strength_factors.append("Cohérence excellente")
    elif coherence >= 75:
        strength_score += 15
        strength_factors.append("Cohérence bonne")
    elif coherence >= 70:
        strength_score += 10
        strength_factors.append("Cohérence acceptable")
    
    # 3. Patterns forts
    candlestick_bearish = indicators.get('candlestick_bearish_signals', 0)
    chart_bearish = indicators.get('chart_bearish_signals', 0)
    if candlestick_bearish >= 3 or chart_bearish >= 3:
        strength_score += 20
        strength_factors.append("Patterns très bearish")
    elif candlestick_bearish > 0 or chart_bearish > 0:
        strength_score += 10
        strength_factors.append("Patterns bearish")
    
    # 4. Divergence RSI
    if indicators.get('rsi_divergence', False):
        strength_score += 15
        strength_factors.append("Divergence RSI")
    
    # 5. ADX fort
    adx = indicators.get('adx')
    if adx and adx > 30:
        strength_score += 10
        strength_factors.append("Tendance très forte")
    
    # 6. Volume très élevé
    volume_ratio = None
    if indicators.get('current_volume') and indicators.get('volume_ma20') and indicators.get('volume_ma20') > 0:
        volume_ratio = indicators.get('current_volume') / indicators.get('volume_ma20')
    if volume_ratio and volume_ratio > 2.0:
        strength_score += 10
        strength_factors.append("Volume exceptionnel")
    
    # Déterminer la qualité
    if strength_score >= 80:
        quality = 'EXCELLENT'
        risk_level = 'LOW'
    elif strength_score >= 60:
        quality = 'VERY_GOOD'
        risk_level = 'LOW'
    elif strength_score >= 40:
        quality = 'GOOD'
        risk_level = 'MEDIUM'
    elif strength_score >= 20:
        quality = 'MODERATE'
        risk_level = 'MEDIUM'
    else:
        quality = 'WEAK'
        risk_level = 'HIGH'
    
    return {
        'strength': strength_score,
        'quality': quality,
        'risk_level': risk_level,
        'factors': strength_factors,
        'coherence': coherence
    }


def filter_weak_signals(opportunities: List[Dict]) -> List[Dict]:
    """
    Filtre les signaux faibles avec des critères stricts supplémentaires.
    
    Returns:
        Liste filtrée des opportunités
    """
    
    filtered = []
    
    for opp in opportunities:
        if opp.get('entry_signal') != 'SHORT':
            continue
        
        # Reconstruire les indicateurs depuis les données de l'opportunité
        indicators = {
            'current_price': opp.get('price'),
            'ema9': opp.get('ema9'),
            'ema21': opp.get('ema21'),
            'rsi14': opp.get('rsi'),
            'confidence': opp.get('confidence', 0),
            'candlestick_bearish_signals': 0,  # À récupérer si disponible
            'chart_bearish_signals': 0,
            'rsi_divergence': False,
            'adx': None,
            'current_volume': None,
            'volume_ma20': None
        }
        
        # Validation de cohérence
        validation = validate_signal_coherence(indicators, 'SHORT')
        
        # Calcul de la force
        strength_data = calculate_signal_strength(indicators, 'SHORT', opp.get('confidence', 0))
        
        # Filtrer selon critères stricts
        if (validation['is_valid'] and 
            strength_data['quality'] in ['EXCELLENT', 'VERY_GOOD', 'GOOD'] and
            strength_data['risk_level'] in ['LOW', 'MEDIUM'] and
            opp.get('score', 0) >= 60 and
            opp.get('confidence', 0) >= 70):
            
            # Ajouter les métadonnées de validation
            opp['signal_quality'] = strength_data['quality']
            opp['risk_level'] = strength_data['risk_level']
            opp['coherence_score'] = validation['coherence_score']
            opp['signal_strength'] = strength_data['strength']
            
            filtered.append(opp)
    
    return filtered

