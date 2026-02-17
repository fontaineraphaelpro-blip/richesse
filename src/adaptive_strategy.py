"""
Module de Stratégie Adaptative - VERSION 1.0
Adapte dynamiquement la stratégie de trading en fonction de TOUTES les informations reçues:
- Indicateurs techniques (EMA, RSI, MACD, ADX, Volume)
- Momentum du prix (direction récente)
- Sentiment du marché (Fear & Greed)
- Intelligence marché (Funding, L/S ratio, Breadth)
- Données on-chain
- Événements macro

PRINCIPE: Le bot s'adapte au marché au lieu d'appliquer des règles fixes.
"""

from typing import Dict, Tuple, Optional
from datetime import datetime


class AdaptiveStrategy:
    """
    Stratégie adaptative qui ajuste les paramètres selon les conditions du marché.
    """
    
    def __init__(self):
        # Historique des régimes pour lisser les transitions
        self.regime_history = []
        self.max_history = 10
        
    def detect_market_regime(self, market_data: Dict) -> Dict:
        """
        Détecte le régime de marché actuel basé sur toutes les infos disponibles.
        
        Régimes possibles:
        - STRONG_TREND_UP: Forte tendance haussière
        - TREND_UP: Tendance haussière modérée
        - RANGING: Marché sans direction claire
        - TREND_DOWN: Tendance baissière modérée
        - STRONG_TREND_DOWN: Forte tendance baissière
        - HIGH_VOLATILITY: Volatilité extrême, prudence
        - REVERSAL_UP: Possible retournement haussier
        - REVERSAL_DOWN: Possible retournement baissier
        """
        
        # ═══════════════════════════════════════════════════════════
        # EXTRACTION DES DONNÉES
        # ═══════════════════════════════════════════════════════════
        
        # Indicateurs techniques
        indicators = market_data.get('indicators', {})
        adx = indicators.get('adx', 25)
        rsi = indicators.get('rsi14', 50)
        ema9 = indicators.get('ema9', 0)
        ema21 = indicators.get('ema21', 0)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        bb_width = indicators.get('bb_width', 0.03)
        volume_ratio = indicators.get('volume_ratio', 1.0)
        price_momentum = indicators.get('price_momentum', 'NEUTRAL')
        momentum_strength = indicators.get('momentum_strength', 0)
        
        # Sentiment & Intelligence
        sentiment = market_data.get('sentiment', {})
        fear_greed = sentiment.get('fear_greed', 50)
        
        intelligence = market_data.get('intelligence', {})
        funding_rate = intelligence.get('funding', 0)
        ls_ratio = intelligence.get('ls_ratio', 1.0)
        market_breadth = intelligence.get('breadth', 50)
        
        # Stats globales du marché
        market_stats = market_data.get('market_stats', {})
        total_bullish = market_stats.get('total_bullish', 0)
        total_bearish = market_stats.get('total_bearish', 0)
        
        # ═══════════════════════════════════════════════════════════
        # ANALYSE DU RÉGIME
        # ═══════════════════════════════════════════════════════════
        
        regime_scores = {
            'STRONG_TREND_UP': 0,
            'TREND_UP': 0,
            'RANGING': 0,
            'TREND_DOWN': 0,
            'STRONG_TREND_DOWN': 0,
            'HIGH_VOLATILITY': 0,
            'REVERSAL_UP': 0,
            'REVERSAL_DOWN': 0
        }
        
        # ─── 1. FORCE DE LA TENDANCE (ADX) ───
        if adx >= 40:
            # Tendance très forte
            if ema9 > ema21:
                regime_scores['STRONG_TREND_UP'] += 30
            else:
                regime_scores['STRONG_TREND_DOWN'] += 30
        elif adx >= 25:
            # Tendance modérée
            if ema9 > ema21:
                regime_scores['TREND_UP'] += 20
            else:
                regime_scores['TREND_DOWN'] += 20
        elif adx < 20:
            # Pas de tendance claire
            regime_scores['RANGING'] += 25
        
        # ─── 2. MOMENTUM DU PRIX ───
        if price_momentum == 'BULLISH':
            regime_scores['TREND_UP'] += 15
            regime_scores['STRONG_TREND_UP'] += 10
        elif price_momentum == 'BEARISH':
            regime_scores['TREND_DOWN'] += 15
            regime_scores['STRONG_TREND_DOWN'] += 10
        else:
            regime_scores['RANGING'] += 10
        
        # ─── 3. RSI ───
        if rsi > 70:
            regime_scores['STRONG_TREND_UP'] += 10
            regime_scores['REVERSAL_DOWN'] += 15  # Risque de correction
        elif rsi > 55:
            regime_scores['TREND_UP'] += 10
        elif rsi < 30:
            regime_scores['STRONG_TREND_DOWN'] += 10
            regime_scores['REVERSAL_UP'] += 15  # Possible rebond
        elif rsi < 45:
            regime_scores['TREND_DOWN'] += 10
        else:
            regime_scores['RANGING'] += 5
        
        # ─── 4. MACD ───
        macd_diff = macd - macd_signal if macd and macd_signal else 0
        if macd_diff > 0:
            regime_scores['TREND_UP'] += 10
            if macd > 0:
                regime_scores['STRONG_TREND_UP'] += 5
        elif macd_diff < 0:
            regime_scores['TREND_DOWN'] += 10
            if macd < 0:
                regime_scores['STRONG_TREND_DOWN'] += 5
        
        # ─── 5. VOLATILITÉ (Bollinger Width) ───
        bb_width_pct = bb_width * 100 if bb_width else 3
        if bb_width_pct > 8:
            regime_scores['HIGH_VOLATILITY'] += 30
        elif bb_width_pct > 5:
            regime_scores['HIGH_VOLATILITY'] += 15
        elif bb_width_pct < 2:
            regime_scores['RANGING'] += 10  # Compression = range
        
        # ─── 6. VOLUME ───
        if volume_ratio > 2.0:
            # Volume très élevé = mouvement significatif
            if price_momentum == 'BULLISH':
                regime_scores['STRONG_TREND_UP'] += 15
            elif price_momentum == 'BEARISH':
                regime_scores['STRONG_TREND_DOWN'] += 15
            else:
                regime_scores['HIGH_VOLATILITY'] += 10
        elif volume_ratio < 0.5:
            # Volume faible = marché sans conviction
            regime_scores['RANGING'] += 10
        
        # ─── 7. FEAR & GREED ───
        if fear_greed >= 80:
            regime_scores['REVERSAL_DOWN'] += 10
            regime_scores['STRONG_TREND_UP'] += 5
        elif fear_greed >= 60:
            regime_scores['TREND_UP'] += 5
        elif fear_greed <= 20:
            regime_scores['REVERSAL_UP'] += 10
            regime_scores['STRONG_TREND_DOWN'] += 5
        elif fear_greed <= 40:
            regime_scores['TREND_DOWN'] += 5
        
        # ─── 8. FUNDING RATE ───
        if funding_rate > 0.05:  # Très positif = marché surchargé en LONG
            regime_scores['REVERSAL_DOWN'] += 10
        elif funding_rate < -0.03:  # Négatif = marché surchargé en SHORT
            regime_scores['REVERSAL_UP'] += 10
        
        # ─── 9. LONG/SHORT RATIO ───
        if ls_ratio > 1.5:
            regime_scores['TREND_UP'] += 5
            regime_scores['REVERSAL_DOWN'] += 5  # Trop de longs
        elif ls_ratio < 0.7:
            regime_scores['TREND_DOWN'] += 5
            regime_scores['REVERSAL_UP'] += 5  # Trop de shorts
        
        # ─── 10. MARKET BREADTH ───
        if total_bullish > 0 and total_bearish > 0:
            bull_ratio = total_bullish / (total_bullish + total_bearish)
            if bull_ratio > 0.7:
                regime_scores['STRONG_TREND_UP'] += 10
            elif bull_ratio > 0.55:
                regime_scores['TREND_UP'] += 10
            elif bull_ratio < 0.3:
                regime_scores['STRONG_TREND_DOWN'] += 10
            elif bull_ratio < 0.45:
                regime_scores['TREND_DOWN'] += 10
        
        # ═══════════════════════════════════════════════════════════
        # DÉTERMINATION DU RÉGIME FINAL
        # ═══════════════════════════════════════════════════════════
        
        # Trouver le régime dominant
        sorted_regimes = sorted(regime_scores.items(), key=lambda x: x[1], reverse=True)
        primary_regime = sorted_regimes[0][0]
        primary_score = sorted_regimes[0][1]
        
        # Calculer la confiance (différence avec le 2ème régime)
        secondary_regime = sorted_regimes[1][0]
        secondary_score = sorted_regimes[1][1]
        
        confidence = min(100, primary_score)
        if primary_score > 0:
            clarity = (primary_score - secondary_score) / primary_score * 100
        else:
            clarity = 0
        
        # Lisser les transitions
        self.regime_history.append(primary_regime)
        if len(self.regime_history) > self.max_history:
            self.regime_history.pop(0)
        
        return {
            'regime': primary_regime,
            'secondary_regime': secondary_regime,
            'confidence': confidence,
            'clarity': clarity,
            'scores': regime_scores,
            'data_used': {
                'adx': adx,
                'rsi': rsi,
                'momentum': price_momentum,
                'fear_greed': fear_greed,
                'volume_ratio': volume_ratio,
                'bb_width': bb_width_pct
            }
        }
    
    def get_adaptive_parameters(self, regime_info: Dict) -> Dict:
        """
        Retourne les paramètres de trading adaptés au régime actuel.
        """
        
        regime = regime_info['regime']
        confidence = regime_info['confidence']
        
        # Paramètres par défaut
        params = {
            'min_score': 72,
            'position_size_multiplier': 1.0,
            'sl_multiplier': 1.5,
            'tp_multiplier': 3.0,
            'allow_long': True,
            'allow_short': True,
            'max_positions': 5,
            'cooldown_minutes': 30,
            'require_volume_confirmation': True,
            'require_momentum_confirmation': True,
            'trading_mode': 'NORMAL'  # NORMAL, AGGRESSIVE, DEFENSIVE, PAUSE
        }
        
        # ═══════════════════════════════════════════════════════════
        # ADAPTATION SELON LE RÉGIME
        # ═══════════════════════════════════════════════════════════
        
        if regime == 'STRONG_TREND_UP':
            # Tendance haussière forte = LONG agressif
            params['min_score'] = 65  # Plus permissif
            params['position_size_multiplier'] = 1.3
            params['allow_long'] = True
            params['allow_short'] = False  # Éviter SHORT contre la tendance
            params['tp_multiplier'] = 4.0  # Laisser courir les gains
            params['cooldown_minutes'] = 15  # Plus réactif
            params['trading_mode'] = 'AGGRESSIVE'
            
        elif regime == 'TREND_UP':
            # Tendance haussière modérée
            params['min_score'] = 68
            params['position_size_multiplier'] = 1.1
            params['allow_long'] = True
            params['allow_short'] = False
            params['tp_multiplier'] = 3.5
            params['trading_mode'] = 'NORMAL'
            
        elif regime == 'RANGING':
            # Marché sans direction = prudence
            params['min_score'] = 78  # Plus strict
            params['position_size_multiplier'] = 0.7
            params['allow_long'] = True
            params['allow_short'] = True
            params['tp_multiplier'] = 2.0  # TP rapide
            params['sl_multiplier'] = 1.0  # SL serré
            params['cooldown_minutes'] = 60  # Plus lent
            params['trading_mode'] = 'DEFENSIVE'
            
        elif regime == 'TREND_DOWN':
            # Tendance baissière modérée
            params['min_score'] = 68
            params['position_size_multiplier'] = 1.1
            params['allow_long'] = False  # Éviter LONG contre la tendance
            params['allow_short'] = True
            params['tp_multiplier'] = 3.5
            params['trading_mode'] = 'NORMAL'
            
        elif regime == 'STRONG_TREND_DOWN':
            # Tendance baissière forte = SHORT agressif
            params['min_score'] = 65
            params['position_size_multiplier'] = 1.3
            params['allow_long'] = False
            params['allow_short'] = True
            params['tp_multiplier'] = 4.0
            params['cooldown_minutes'] = 15
            params['trading_mode'] = 'AGGRESSIVE'
            
        elif regime == 'HIGH_VOLATILITY':
            # Volatilité extrême = très prudent
            params['min_score'] = 85  # Très strict
            params['position_size_multiplier'] = 0.5  # Petites positions
            params['sl_multiplier'] = 2.0  # SL plus large
            params['tp_multiplier'] = 2.0  # TP rapide
            params['max_positions'] = 2  # Moins de positions
            params['cooldown_minutes'] = 60
            params['trading_mode'] = 'DEFENSIVE'
            
        elif regime == 'REVERSAL_UP':
            # Possible retournement haussier - prudent mais prêt
            params['min_score'] = 75
            params['position_size_multiplier'] = 0.8
            params['allow_long'] = True
            params['allow_short'] = False  # Éviter SHORT si rebond
            params['require_momentum_confirmation'] = True  # Attendre confirmation
            params['trading_mode'] = 'DEFENSIVE'
            
        elif regime == 'REVERSAL_DOWN':
            # Possible retournement baissier - prudent
            params['min_score'] = 75
            params['position_size_multiplier'] = 0.8
            params['allow_long'] = False  # Éviter LONG si correction
            params['allow_short'] = True
            params['require_momentum_confirmation'] = True
            params['trading_mode'] = 'DEFENSIVE'
        
        # ═══════════════════════════════════════════════════════════
        # AJUSTEMENT SELON LA CONFIANCE
        # ═══════════════════════════════════════════════════════════
        
        if confidence < 30:
            # Faible confiance = très prudent
            params['min_score'] = max(params['min_score'], 80)
            params['position_size_multiplier'] *= 0.5
            params['trading_mode'] = 'DEFENSIVE'
        elif confidence < 50:
            # Confiance moyenne
            params['min_score'] = max(params['min_score'], 75)
            params['position_size_multiplier'] *= 0.8
        
        return params
    
    def should_take_trade(self, opportunity: Dict, regime_info: Dict, params: Dict) -> Tuple[bool, str]:
        """
        Décide si on doit prendre un trade basé sur le régime et les paramètres.
        
        Returns:
            (should_trade, reason)
        """
        
        signal = opportunity.get('entry_signal', 'NEUTRAL')
        score = opportunity.get('score', 0)
        momentum = opportunity.get('price_momentum', 'NEUTRAL')
        
        # Vérifier si le signal est autorisé
        if signal == 'LONG' and not params['allow_long']:
            return False, f"LONG bloqué en régime {regime_info['regime']}"
        
        if signal == 'SHORT' and not params['allow_short']:
            return False, f"SHORT bloqué en régime {regime_info['regime']}"
        
        # Vérifier le score minimum
        if score < params['min_score']:
            return False, f"Score {score} < min {params['min_score']}"
        
        # Vérifier la confirmation de momentum si requise
        if params['require_momentum_confirmation']:
            if signal == 'LONG' and momentum == 'BEARISH':
                return False, "LONG sans momentum haussier"
            if signal == 'SHORT' and momentum == 'BULLISH':
                return False, "SHORT sans momentum baissier"
        
        # Trading en pause?
        if params['trading_mode'] == 'PAUSE':
            return False, "Trading en pause"
        
        return True, f"OK - Régime: {regime_info['regime']}, Mode: {params['trading_mode']}"
    
    def get_position_size(self, base_amount: float, params: Dict) -> float:
        """
        Calcule la taille de position adaptée.
        """
        return base_amount * params['position_size_multiplier']
    
    def get_sl_tp_multipliers(self, params: Dict) -> Tuple[float, float]:
        """
        Retourne les multiplicateurs SL/TP adaptés.
        """
        return params['sl_multiplier'], params['tp_multiplier']
    
    def get_regime_summary(self, regime_info: Dict, params: Dict) -> str:
        """
        Retourne un résumé lisible du régime actuel.
        """
        regime = regime_info['regime']
        confidence = regime_info['confidence']
        mode = params['trading_mode']
        
        emoji_map = {
            'STRONG_TREND_UP': '🚀',
            'TREND_UP': '📈',
            'RANGING': '↔️',
            'TREND_DOWN': '📉',
            'STRONG_TREND_DOWN': '💥',
            'HIGH_VOLATILITY': '⚡',
            'REVERSAL_UP': '🔄↑',
            'REVERSAL_DOWN': '🔄↓'
        }
        
        emoji = emoji_map.get(regime, '❓')
        
        directions = []
        if params['allow_long']:
            directions.append('LONG')
        if params['allow_short']:
            directions.append('SHORT')
        
        return (
            f"{emoji} {regime} | Confiance: {confidence:.0f}% | "
            f"Mode: {mode} | Score min: {params['min_score']} | "
            f"Directions: {'/'.join(directions) if directions else 'AUCUNE'}"
        )


# Instance globale
adaptive_strategy = AdaptiveStrategy()


def get_adaptive_strategy() -> AdaptiveStrategy:
    """Retourne l'instance globale de la stratégie adaptative."""
    return adaptive_strategy


def analyze_and_adapt(market_data: Dict) -> Tuple[Dict, Dict, str]:
    """
    Fonction principale: analyse le marché et retourne les paramètres adaptés.
    
    Args:
        market_data: Dictionnaire contenant:
            - indicators: Dict des indicateurs techniques
            - sentiment: Dict sentiment (fear_greed, etc.)
            - intelligence: Dict intelligence marché
            - market_stats: Dict stats globales
    
    Returns:
        (regime_info, parameters, summary)
    """
    strategy = get_adaptive_strategy()
    
    regime_info = strategy.detect_market_regime(market_data)
    params = strategy.get_adaptive_parameters(regime_info)
    summary = strategy.get_regime_summary(regime_info, params)
    
    return regime_info, params, summary
