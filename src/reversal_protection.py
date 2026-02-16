"""
Module de Protection contre les Changements Soudains de Tendance.
Évite les faux signaux et les whipsaws lors de retournements brusques du marché.

Stratégies:
1. Détection de divergence entre tendance d'entrée et tendance actuelle
2. Filtrage par volatilité extrême (Bollinger Bands width)
3. ADX faible = pas d'ouverture de position
4. Confirmation multi-candle avant fermeture SL
5. Circuit breaker : pause après perte de 2+ positions consécutives
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
import pandas as pd


class ReversalProtector:
    """
    Gère la protection contre les changements soudains de tendance.
    """
    
    def __init__(self):
        # Historique des positions fermées par SL (pour circuit breaker)
        self.recent_sl_closes = []  # [(timestamp, symbol), ...]
        self.max_recent_sl = 3  # Nombre de SL avant circuit breaker
        self.circuit_breaker_duration = 300  # 5 minutes en secondes
        
        # Tolérance de volatilité (pourcentage)
        self.max_bb_width = 8.0  # Ne pas ouvrir si BB Width > 8%
        self.min_adx = 20  # ADX minimum pour trend confirmation
        
        # Confirmation avant SL
        self.sl_bounce_threshold = 0.3  # 0.3% de rebound requis pour confirmer une inversion

    # ─────────────────────────────────────────────────────────────
    # DÉTECTION DE TENDANCE
    # ─────────────────────────────────────────────────────────────

    def get_position_entry_trend(self, position_data: Dict) -> str:
        """
        Récupère la tendance qui était active lors de l'ouverture.
        Stockée dans les métadonnées de la position lors de place_buy_order.
        """
        return position_data.get('entry_trend', 'UNKNOWN')
    
    def detect_current_trend(self, indicators: Dict) -> str:
        """Détecte la tendance actuelle basée sur les indicateurs."""
        bullish_signals = 0
        bearish_signals = 0
        
        # EMA crossover
        ema9 = indicators.get('ema9')
        ema21 = indicators.get('ema21')
        if ema9 and ema21:
            if ema9 > ema21:
                bullish_signals += 2
            elif ema9 < ema21:
                bearish_signals += 2
        
        # MACD
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                bullish_signals += 1
            elif macd < macd_signal:
                bearish_signals += 1
        
        # ADX strength
        adx = indicators.get('adx', 0)
        if adx < 20:
            return 'WEAK'  # Tendance très faible
        
        # Résultat
        if bullish_signals > bearish_signals:
            return 'Bullish'
        elif bearish_signals > bullish_signals:
            return 'Bearish'
        else:
            return 'NEUTRAL'

    # ─────────────────────────────────────────────────────────────
    # FILTRES D'OUVERTURE
    # ─────────────────────────────────────────────────────────────

    def is_volatility_extreme(self, indicators: Dict) -> Tuple[bool, float]:
        """
        Vérifie si la volatilité est extrême.
        
        Return:
            (is_extreme, bb_width_percent)
        """
        bb_width = indicators.get('bb_width', 0)
        if bb_width is None:
            return False, 0
        
        bb_width_pct = bb_width * 100
        is_extreme = bb_width_pct > self.max_bb_width
        
        return is_extreme, bb_width_pct

    def is_trend_strong_enough(self, indicators: Dict) -> Tuple[bool, float]:
        """
        Vérifie si la tendance est assez forte (ADX > 20).
        
        Return:
            (is_strong, adx_value)
        """
        adx = indicators.get('adx', 0)
        is_strong = adx >= self.min_adx
        return is_strong, adx

    def can_open_position(self, indicators: Dict) -> Tuple[bool, str]:
        """
        Vérifie si les conditions permettent d'ouvrir une position.
        
        Return:
            (can_open, reason)
        """
        # Vérifier volatilité
        is_extreme, bb_width = self.is_volatility_extreme(indicators)
        if is_extreme:
            return False, f"Volatilité extrême détectée (BB Width: {bb_width:.1f}%)"
        
        # Vérifier force de tendance
        is_strong, adx = self.is_trend_strong_enough(indicators)
        if not is_strong:
            return False, f"Tendance faible (ADX: {adx:.1f} < {self.min_adx})"
        
        return True, "✅ Conditions d'ouverture acceptables"

    # ─────────────────────────────────────────────────────────────
    # PROTECTION DE POSITION
    # ─────────────────────────────────────────────────────────────

    def detect_trend_reversal(
        self,
        entry_trend: str,
        current_indicators: Dict,
        entry_price: float,
        current_price: float,
        direction: str = 'LONG'
    ) -> Tuple[bool, str]:
        """
        Détecte si la tendance s'est vraiment inversée (pas un simple retracement).
        
        Args:
            entry_trend: Tendance à l'ouverture ('Bullish', 'Bearish', etc.)
            current_indicators: Indicateurs actuels
            entry_price: Prix d'entrée
            current_price: Prix actuel
            direction: 'LONG' ou 'SHORT'
        
        Return:
            (is_reversed, reason)
        """
        current_trend = self.detect_current_trend(current_indicators)
        
        # Si même tendance, peu de risque
        if current_trend == entry_trend:
            return False, "Tendance inchangée"
        
        # Si la tendance est trop faible pour confirmer un mouvement
        if current_trend == 'NEUTRAL' or current_trend == 'WEAK':
            return False, "Tendance incertaine (mouvement temporaire probable)"
        
        # Vérifier la divergence par ADX (< 25 = possible retournement)
        adx = current_indicators.get('adx', 0)
        if adx < 25:
            return False, f"ADX faible ({adx:.1f}) - Trend faible, SL prévention"
        
        # Cas : entrée LONG, maintenant Bearish + ADX fort = vrai reversal
        if direction == 'LONG' and entry_trend == 'Bullish' and current_trend == 'Bearish':
            return True, "REVERSAL CONFIRMÉ: Bullish → Bearish (ADX > 25)"
        
        # Cas : entrée SHORT, maintenant Bullish + ADX fort = vrai reversal
        if direction == 'SHORT' and entry_trend == 'Bearish' and current_trend == 'Bullish':
            return True, "REVERSAL CONFIRMÉ: Bearish → Bullish (ADX > 25)"
        
        return False, "Pas de reversal confirmé"

    # ─────────────────────────────────────────────────────────────
    # AJUSTEMENT DYNAMIQUE DU SL
    # ─────────────────────────────────────────────────────────────

    def calculate_dynamic_sl(
        self,
        entry_price: float,
        initial_sl: float,
        indicators: Dict,
        direction: str = 'LONG'
    ) -> float:
        """
        Élargit le SL dynamiquement en cas de haute volatilité.
        Empêche les fermetures prématurées sur bruit.
        
        Return:
            adjusted_sl_price
        """
        # Obtenir l'ATR pour la volatilité
        atr = indicators.get('atr', 0)
        if not atr or atr == 0:
            return initial_sl
        
        bb_width = indicators.get('bb_width', 0)
        
        # Élargissement du SL basé sur volatilité  
        # Si BB Width > 4%, ajouter 0.5x ATR au SL (pour LONG, soustraire)
        adjustment_factor = 0
        if bb_width and bb_width > 0.04:
            # Volatilité élevée : augmenter l'espace
            adjustment_factor = 0.5 * atr
        elif bb_width and bb_width < 0.02:
            # Volatilité très basse : peut resserrer (cautieusement)
            adjustment_factor = -0.25 * atr
        
        if direction == 'LONG':
            # Pour LONG, SL est en dessous, on le baisse (augmente la distance)
            adjusted_sl = initial_sl - adjustment_factor
        else:
            # Pour SHORT, SL est au-dessus, on le monte (augmente la distance)
            adjusted_sl = initial_sl + adjustment_factor
        
        return adjusted_sl

    def calculate_emergency_sl(
        self,
        entry_price: float,
        current_price: float,
        indicators: Dict,
        direction: str = 'LONG'
    ) -> float:
        """
        Calcule un SL d'urgence si reversal CONFIRMÉ.
        Place le SL à proximité du prix courant pour limiter les dégâts.
        
        Return:
            emergency_sl_price
        """
        atr = indicators.get('atr', 0)
        if not atr:
            # Utiliser 1% du prix comme buffer minimal
            if direction == 'LONG':
                return current_price * 0.99
            else:
                return current_price * 1.01
        
        if direction == 'LONG':
            # Pour LONG, mettre SL à 1x ATR sous le prix courant
            return current_price - atr
        else:
            # Pour SHORT, mettre SL à 1x ATR au-dessus du prix courant
            return current_price + atr
    
    # ─────────────────────────────────────────────────────────────
    # STRATÉGIES DE GESTION DES POSITIONS EXISTANTES
    # ─────────────────────────────────────────────────────────────

    def analyze_position_risk(
        self,
        position_data: Dict,
        current_indicators: Dict,
        current_price: float
    ) -> Dict:
        """
        Analyse complète du risque d'une position existante lors d'un reversal.
        
        Return:
            {
                'entry_trend': str,
                'current_trend': str,
                'is_reversed': bool,
                'is_danger_zone': bool,
                'distance_to_sl_pct': float,
                'unrealized_pnl': float,
                'risk_level': str,  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
                'recommendation': str,
            }
        """
        entry_price = position_data.get('entry_price', 0)
        entry_trend = position_data.get('entry_trend', 'UNKNOWN')
        direction = position_data.get('direction', 'LONG')
        stop_loss = position_data.get('stop_loss', 0)
        
        current_trend = self.detect_current_trend(current_indicators)
        is_reversed, reason = self.detect_trend_reversal(
            entry_trend, current_indicators, entry_price, current_price, direction
        )
        
        # Calcul du PnL non réalisé
        if direction == 'LONG':
            unrealized_pnl = (current_price - entry_price) / entry_price * 100
            distance_to_sl = (current_price - stop_loss) / stop_loss * 100
        else:  # SHORT
            unrealized_pnl = (entry_price - current_price) / entry_price * 100
            distance_to_sl = (stop_loss - current_price) / current_price * 100
        
        # Position en danger si SL est proche (< 2%)
        is_danger_zone = abs(distance_to_sl) < 2.0
        
        # Évaluation du risque
        if is_reversed and is_danger_zone:
            risk_level = 'CRITICAL'
            recommendation = "⚠️ FERMER IMMÉDIATEMENT - Reversal confirmé + SL proche"
        elif is_reversed and unrealized_pnl < 0:
            risk_level = 'HIGH'
            recommendation = "🔴 RÉDUIRE 50% - Reversal confirmé et position en perte"
        elif is_reversed:
            risk_level = 'HIGH'
            recommendation = "✂️ PRENDRE 50% - Reversal confirmé, verrouiller les gains"
        elif is_danger_zone and not is_reversed:
            risk_level = 'MEDIUM'
            recommendation = "🛡️ ÉLARGIR SL - SL proche mais tendance inchangée"
        elif abs(distance_to_sl) < 5.0:
            risk_level = 'MEDIUM'
            recommendation = "⏱️ SURVEILLER - SL à 5%, vigilance requise"
        else:
            risk_level = 'LOW'
            recommendation = "✅ CONSERVER - Position stable et protégée"
        
        return {
            'entry_trend': entry_trend,
            'current_trend': current_trend,
            'is_reversed': is_reversed,
            'is_danger_zone': is_danger_zone,
            'distance_to_sl_pct': distance_to_sl,
            'unrealized_pnl_pct': unrealized_pnl,
            'risk_level': risk_level,
            'recommendation': recommendation,
        }

    def get_position_action(
        self,
        position_data: Dict,
        current_indicators: Dict,
        current_price: float
    ) -> Dict:
        """
        Détermine l'action à prendre pour une position existante.
        
        Return:
            {
                'action': 'HOLD' | 'CLOSE' | 'PARTIAL_CLOSE' | 'ADJUST_SL' | 'EMERGENCY_CLOSE',
                'target_close_ratio': float,  # 0.0-1.0, portion à fermer (si partial)
                'new_sl': float,  # Nouveau SL (si adjust)
                'reason': str,
            }
        """
        risk = self.analyze_position_risk(position_data, current_indicators, current_price)
        entry_price = position_data.get('entry_price', 0)
        direction = position_data.get('direction', 'LONG')
        
        # RÈGLE 1 : Reversal CONFIRMÉ + en danger zone = FERMER TOUT
        if risk['is_reversed'] and risk['is_danger_zone']:
            return {
                'action': 'EMERGENCY_CLOSE',
                'target_close_ratio': 1.0,
                'new_sl': None,
                'reason': f"URGENCE: {risk['recommendation']}",
            }
        
        # RÈGLE 2 : Reversal CONFIRMÉ + en perte = Fermer 50%
        if risk['is_reversed'] and risk['unrealized_pnl_pct'] < 0:
            return {
                'action': 'PARTIAL_CLOSE',
                'target_close_ratio': 0.5,
                'new_sl': None,
                'reason': f"Reversal confirmé (perte): {risk['unrealized_pnl_pct']:.1f}% - Réduire moitié",
            }
        
        # RÈGLE 3 : Reversal CONFIRMÉ + en gain = Prendre 50% de profits
        if risk['is_reversed'] and risk['unrealized_pnl_pct'] > 0:
            return {
                'action': 'PARTIAL_CLOSE',
                'target_close_ratio': 0.5,
                'new_sl': entry_price,  # Remplacer SL à break-even
                'reason': f"Reversal confirmé (gain): {risk['unrealized_pnl_pct']:.1f}% - Verrouiller 50%",
            }
        
        # RÈGLE 4 : SL très proche mais pas de reversal confirmé = Élargir SL
        if risk['is_danger_zone'] and not risk['is_reversed']:
            new_sl = self.calculate_dynamic_sl(entry_price, position_data['stop_loss'], current_indicators, direction)
            return {
                'action': 'ADJUST_SL',
                'target_close_ratio': 0.0,
                'new_sl': new_sl,
                'reason': f"SL en danger ({risk['distance_to_sl_pct']:.1f}%) - Élargir pour éviter bruit",
            }
        
        # RÈGLE 5 : Tendance inchangée mais volatilité élevée = Élargir SL légèrement
        bb_width = current_indicators.get('bb_width', 0)
        if bb_width and bb_width > 0.06 and not risk['is_reversed']:
            new_sl = self.calculate_dynamic_sl(entry_price, position_data['stop_loss'], current_indicators, direction)
            return {
                'action': 'ADJUST_SL',
                'target_close_ratio': 0.0,
                'new_sl': new_sl,
                'reason': f"Haute volatilité (BB Width: {bb_width*100:.1f}%) - Ajuster SL dynamiquement",
            }
        
        # DEFAULT : Conserver la position
        return {
            'action': 'HOLD',
            'target_close_ratio': 0.0,
            'new_sl': None,
            'reason': 'Tendance stable, position protégée',
        }

    # ─────────────────────────────────────────────────────────────
    # SUMMARY DE PROTECTION
    # ─────────────────────────────────────────────────────────────

    def should_protect_position(
        self,
        position_data: Dict,
        current_indicators: Dict,
        current_price: float
    ) -> Tuple[bool, str]:
        """
        Vérifie si une position devrait être protégée (ne pas être fermée sur SL).
        
        Return:
            (should_protect, reason)
        """
        action = self.get_position_action(position_data, current_indicators, current_price)
        
        # Protéger si l'action est HOLD ou ADJUST_SL
        should_protect = action['action'] in ['HOLD', 'ADJUST_SL']
        return should_protect, action['reason']

    # ─────────────────────────────────────────────────────────────
    # CIRCUIT BREAKER
    # ─────────────────────────────────────────────────────────────

    def record_sl_close(self, symbol: str):
        """Enregistre une fermeture par stop loss pour le circuit breaker."""
        self.recent_sl_closes.append((datetime.now(), symbol))
        # Garder seulement les dernières fermetures
        self.recent_sl_closes = self.recent_sl_closes[-10:]

    def is_circuit_breaker_active(self) -> Tuple[bool, int]:
        """
        Vérifie si le circuit breaker est actif.
        Active après 2+ SL consécutifs en peu de temps.
        
        Return:
            (is_active, seconds_remaining)
        """
        if not self.recent_sl_closes:
            return False, 0
        
        now = datetime.now()
        recent_window = [
            (ts, sym) for ts, sym in self.recent_sl_closes
            if (now - ts).total_seconds() < self.circuit_breaker_duration
        ]
        
        # Si 2+ SL en moins de 5 min = circuit breaker
        if len(recent_window) >= 2:
            oldest = recent_window[0][0]
            seconds_remaining = int(self.circuit_breaker_duration - (now - oldest).total_seconds())
            return True, max(0, seconds_remaining)
        
        return False, 0

    def get_protection_status(self) -> Dict:
        """Retourne l'état de protection pour le dashboard."""
        is_active, remaining = self.is_circuit_breaker_active()
        
        recent_count = len([
            ts for ts, _ in self.recent_sl_closes
            if (datetime.now() - ts).total_seconds() < self.circuit_breaker_duration
        ])
        
        return {
            'circuit_breaker_active': is_active,
            'circuit_breaker_remaining': remaining,
            'recent_sl_count': recent_count,
            'max_recent_sl': self.max_recent_sl,
        }

    # ─────────────────────────────────────────────────────────────
    # AJUSTEMENT DYNAMIQUE DU SL
    # ─────────────────────────────────────────────────────────────

    def calculate_dynamic_sl(
        self,
        entry_price: float,
        initial_sl: float,
        indicators: Dict,
        direction: str = 'LONG'
    ) -> float:
        """
        Élargit le SL dynamiquement en cas de haute volatilité.
        Empêche les fermetures prématurées sur bruit.
        
        Return:
            adjusted_sl_price
        """
        # Obtenir l'ATR pour la volatilité
        atr = indicators.get('atr', 0)
        if not atr or atr == 0:
            return initial_sl
        
        bb_width = indicators.get('bb_width', 0)
        
        # Élargissement du SL basé sur volatilité  
        # Si BB Width > 4%, ajouter 0.5x ATR au SL (pour LONG, soustraire)
        adjustment_factor = 0
        if bb_width and bb_width > 0.04:
            # Volatilité élevée : augmenter l'espace
            adjustment_factor = 0.5 * atr
        elif bb_width and bb_width < 0.02:
            # Volatilité très basse : peut resserrer (cautieusement)
            adjustment_factor = -0.25 * atr
        
        if direction == 'LONG':
            # Pour LONG, SL est en dessous, on le baisse (augmente la distance)
            adjusted_sl = initial_sl - adjustment_factor
        else:
            # Pour SHORT, SL est au-dessus, on le monte (augmente la distance)
            adjusted_sl = initial_sl + adjustment_factor
        
        return adjusted_sl

    # ─────────────────────────────────────────────────────────────
    # STATISTIQUES ET DEBUG
    # ─────────────────────────────────────────────────────────────

    def get_diagnostics(self) -> str:
        """Retourne un diagnostic complet de l'état de protection."""
        status = self.get_protection_status()
        
        output = "\n" + "="*60
        output += "\n🛡️  DIAGNOSTIC PROTECTION REVERSAL\n"
        output += "="*60 + "\n"
        
        output += f"Circuit Breaker: {'🔴 ACTIF' if status['circuit_breaker_active'] else '🟢 INACTIF'}\n"
        output += f"  - SL récents: {status['recent_sl_count']}/{status['max_recent_sl']}\n"
        output += f"  - Temps restant: {status['circuit_breaker_remaining']}s\n"
        
        output += f"Volatilité filtre:\n"
        output += f"  - Max BB Width: {self.max_bb_width}%\n"
        output += f"  - ADX minimum: {self.min_adx}\n"
        
        output += "="*60 + "\n"
        return output
