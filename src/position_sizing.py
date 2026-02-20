"""
Module Position Sizing: Gestion optimale de la taille des positions.

Méthodes implémentées:
1. Kelly Criterion - Maximise la croissance du capital à long terme
2. Fixed Fractional - Risque fixe par trade
3. ATR-Based - Ajuste selon la volatilité
4. Score-Based - Ajuste selon la qualité du signal

Formule Kelly: f* = (p × b - q) / b
où p = probabilité de gain, b = ratio gain/perte, q = probabilité de perte
"""

from typing import Dict, Tuple
from datetime import datetime


class PositionSizer:
    """
    Gestionnaire de taille de position intelligent.
    Combine plusieurs méthodes pour optimiser le sizing.
    """
    
    def __init__(self, initial_capital: float = 100):
        self.initial_capital = initial_capital
        
        # Configuration Kelly
        self.kelly_enabled = True
        self.kelly_fraction = 0.25  # Utiliser 25% du Kelly (conservative)
        self.max_position_pct = 20  # Max 20% du capital par trade
        self.min_position_pct = 2   # Min 2% du capital par trade
        
        # Configuration Fixed Fractional
        self.risk_per_trade_pct = 2.0  # Risquer 2% du capital par trade
        
        # Historique pour calcul du win rate
        self.win_history = []  # Liste de True (win) / False (loss)
        self.avg_win = 3.5     # % gain moyen estimé
        self.avg_loss = 2.0    # % perte moyenne estimée
        
        print("💰 Position Sizer initialisé")
    
    def update_stats(self, is_win: bool, pnl_pct: float):
        """
        Met à jour les statistiques après un trade.
        
        Args:
            is_win: True si trade gagnant
            pnl_pct: PnL en pourcentage
        """
        self.win_history.append(is_win)
        
        # Garder les 100 derniers trades
        if len(self.win_history) > 100:
            self.win_history = self.win_history[-100:]
        
        # Mettre à jour les moyennes avec EMA
        alpha = 0.1  # Facteur de lissage
        if is_win:
            self.avg_win = self.avg_win * (1 - alpha) + abs(pnl_pct) * alpha
        else:
            self.avg_loss = self.avg_loss * (1 - alpha) + abs(pnl_pct) * alpha
    
    def get_win_rate(self) -> float:
        """Calcule le win rate actuel."""
        if len(self.win_history) < 5:
            return 0.55  # Default 55% si pas assez de données
        
        wins = sum(1 for w in self.win_history if w)
        return wins / len(self.win_history)
    
    def calculate_kelly(self) -> float:
        """
        Calcule la fraction Kelly optimale.
        
        Kelly = (p × b - q) / b
        où:
        - p = probabilité de gain (win rate)
        - q = probabilité de perte (1 - p)
        - b = ratio gain/perte moyen
        
        Returns:
            Fraction du capital à risquer (0.0 à 1.0)
        """
        p = self.get_win_rate()
        q = 1 - p
        
        # Ratio gain/perte
        if self.avg_loss > 0:
            b = self.avg_win / self.avg_loss
        else:
            b = 1.5  # Default R/R
        
        # Formule Kelly
        kelly = (p * b - q) / b
        
        # Kelly peut être négatif si edge négatif
        kelly = max(0, kelly)
        
        # Appliquer la fraction conservative (quarter Kelly)
        kelly_conservative = kelly * self.kelly_fraction
        
        return kelly_conservative
    
    def calculate_atr_adjustment(self, atr_pct: float) -> float:
        """
        Ajuste la taille de position selon la volatilité (ATR).
        
        - ATR élevé (>5%) → Réduire la position
        - ATR normal (2-5%) → Position normale
        - ATR faible (<2%) → Augmenter légèrement
        
        Args:
            atr_pct: ATR en % du prix
            
        Returns:
            Multiplicateur (0.5 à 1.5)
        """
        if atr_pct > 8:
            return 0.5  # Très volatile, réduire de 50%
        elif atr_pct > 5:
            return 0.7  # Volatile, réduire de 30%
        elif atr_pct > 3:
            return 1.0  # Normal
        elif atr_pct > 1.5:
            return 1.2  # Calme, augmenter de 20%
        else:
            return 1.0  # Trop calme peut être suspect
    
    def calculate_score_adjustment(self, score: int, ml_probability: float = 50) -> float:
        """
        Ajuste la taille selon la qualité du signal.
        
        - Score élevé (>85) + ML >80% → Augmenter
        - Score moyen (70-85) → Normal
        - Score bas (<70) → Réduire
        
        Args:
            score: Score technique (0-100)
            ml_probability: Probabilité ML (0-100)
            
        Returns:
            Multiplicateur (0.5 à 1.5)
        """
        # Combiner score technique et ML
        combined_score = score * 0.6 + ml_probability * 0.4
        
        if combined_score >= 85:
            return 1.4  # Signal très fort
        elif combined_score >= 75:
            return 1.2  # Signal fort
        elif combined_score >= 65:
            return 1.0  # Signal normal
        elif combined_score >= 55:
            return 0.8  # Signal faible
        else:
            return 0.6  # Signal très faible
    
    def calculate_drawdown_adjustment(self, current_capital: float) -> float:
        """
        Réduit la taille en cas de drawdown.
        
        - Drawdown >10% → Réduire significativement
        - Drawdown 5-10% → Réduire modérément
        - Profit → Peut augmenter légèrement
        
        Args:
            current_capital: Capital actuel
            
        Returns:
            Multiplicateur (0.3 à 1.2)
        """
        pnl_pct = ((current_capital - self.initial_capital) / self.initial_capital) * 100
        
        if pnl_pct < -15:
            return 0.3  # Drawdown sévère, très conservateur
        elif pnl_pct < -10:
            return 0.5  # Drawdown important
        elif pnl_pct < -5:
            return 0.7  # Drawdown modéré
        elif pnl_pct < 0:
            return 0.9  # Légère perte
        elif pnl_pct < 10:
            return 1.0  # Profit léger, normal
        elif pnl_pct < 25:
            return 1.1  # Bon profit
        else:
            return 1.2  # Excellent profit, peut augmenter
    
    def calculate_optimal_position(
        self,
        capital: float,
        indicators: Dict,
        score: int,
        ml_probability: float = 50,
        stop_loss_pct: float = 2.5
    ) -> Tuple[float, Dict]:
        """
        Calcule la taille de position optimale en combinant toutes les méthodes.
        
        Args:
            capital: Capital disponible
            indicators: Indicateurs techniques (pour ATR)
            score: Score du signal
            ml_probability: Probabilité ML
            stop_loss_pct: Distance du SL en %
            
        Returns:
            (position_size_usdt, breakdown)
        """
        breakdown = {}
        
        # 1. Base: Kelly Criterion
        if self.kelly_enabled:
            kelly_fraction = self.calculate_kelly()
            base_pct = kelly_fraction * 100  # Convertir en %
            breakdown['kelly_fraction'] = f"{kelly_fraction*100:.1f}%"
            breakdown['win_rate'] = f"{self.get_win_rate()*100:.0f}%"
        else:
            base_pct = self.risk_per_trade_pct
            breakdown['fixed_risk'] = f"{base_pct}%"
        
        # S'assurer d'une base minimum
        base_pct = max(base_pct, self.min_position_pct)
        breakdown['base_position'] = f"{base_pct:.1f}%"
        
        # 2. Ajustement ATR (volatilité)
        atr = indicators.get('atr14', 0)
        close = indicators.get('close', 1)
        atr_pct = (atr / close * 100) if close > 0 else 3
        atr_mult = self.calculate_atr_adjustment(atr_pct)
        breakdown['atr_adjustment'] = f"×{atr_mult:.2f} (ATR:{atr_pct:.1f}%)"
        
        # 3. Ajustement Score/ML
        score_mult = self.calculate_score_adjustment(score, ml_probability)
        breakdown['score_adjustment'] = f"×{score_mult:.2f} (Score:{score}, ML:{ml_probability:.0f}%)"
        
        # 4. Ajustement Drawdown
        dd_mult = self.calculate_drawdown_adjustment(capital)
        pnl_pct = ((capital - self.initial_capital) / self.initial_capital) * 100
        breakdown['drawdown_adjustment'] = f"×{dd_mult:.2f} (PnL:{pnl_pct:+.1f}%)"
        
        # 5. Calcul final
        final_pct = base_pct * atr_mult * score_mult * dd_mult
        
        # Appliquer les limites
        final_pct = max(self.min_position_pct, min(self.max_position_pct, final_pct))
        breakdown['final_position'] = f"{final_pct:.1f}%"
        
        # Convertir en USDT
        position_usdt = capital * (final_pct / 100)
        
        # Minimum absolu de 10 USDT
        position_usdt = max(10, min(position_usdt, capital * 0.4))  # Max 40% en une fois
        
        breakdown['position_usdt'] = f"${position_usdt:.2f}"
        
        return position_usdt, breakdown
    
    def calculate_position_from_risk(
        self,
        capital: float,
        entry_price: float,
        stop_loss_price: float,
        risk_pct: float = None
    ) -> Tuple[float, float]:
        """
        Calcule la taille de position basée sur le risque fixe.
        
        Si je veux risquer X% de mon capital, et que mon SL est à Y%,
        alors ma position doit être: (Capital × Risk%) / SL%
        
        Args:
            capital: Capital total
            entry_price: Prix d'entrée
            stop_loss_price: Prix du stop loss
            risk_pct: % du capital à risquer (défaut: self.risk_per_trade_pct)
            
        Returns:
            (position_usdt, quantity)
        """
        if risk_pct is None:
            risk_pct = self.risk_per_trade_pct
        
        # Calculer la distance du SL en %
        sl_distance_pct = abs((entry_price - stop_loss_price) / entry_price * 100)
        
        if sl_distance_pct < 0.1:
            sl_distance_pct = 2  # Minimum 2%
        
        # Capital à risquer en USDT
        risk_amount = capital * (risk_pct / 100)
        
        # Position nécessaire pour que la perte au SL = risk_amount
        position_usdt = risk_amount / (sl_distance_pct / 100)
        
        # Limiter à un % raisonnable du capital
        max_position = capital * (self.max_position_pct / 100)
        position_usdt = min(position_usdt, max_position)
        
        # Calculer la quantité
        quantity = position_usdt / entry_price
        
        return position_usdt, quantity
    
    def get_recommended_positions(self, capital: float, num_positions: int = 5) -> Dict:
        """
        Recommande comment répartir le capital sur plusieurs positions.
        
        Args:
            capital: Capital total
            num_positions: Nombre de positions max souhaitées
            
        Returns:
            Dict avec recommandations
        """
        kelly = self.calculate_kelly()
        
        # Position moyenne recommandée par Kelly
        avg_position_pct = kelly * 100
        avg_position_pct = max(self.min_position_pct, min(self.max_position_pct, avg_position_pct))
        
        # Nombre optimal de positions selon Kelly
        optimal_positions = int(100 / avg_position_pct) if avg_position_pct > 0 else 5
        optimal_positions = max(3, min(10, optimal_positions))
        
        return {
            'kelly_fraction': f"{kelly*100:.1f}%",
            'optimal_positions': optimal_positions,
            'avg_position_size': f"${capital * avg_position_pct / 100:.2f}",
            'avg_position_pct': f"{avg_position_pct:.1f}%",
            'capital_deployed': f"${capital * avg_position_pct * min(num_positions, optimal_positions) / 100:.2f}",
            'capital_reserve': f"${capital - (capital * avg_position_pct * min(num_positions, optimal_positions) / 100):.2f}"
        }
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du position sizer."""
        return {
            'kelly_enabled': self.kelly_enabled,
            'kelly_fraction_used': f"{self.kelly_fraction*100:.0f}%",
            'calculated_kelly': f"{self.calculate_kelly()*100:.2f}%",
            'win_rate': f"{self.get_win_rate()*100:.1f}%",
            'avg_win': f"{self.avg_win:.2f}%",
            'avg_loss': f"{self.avg_loss:.2f}%",
            'risk_reward': f"{self.avg_win/self.avg_loss:.2f}:1" if self.avg_loss > 0 else "N/A",
            'trades_tracked': len(self.win_history),
            'max_position': f"{self.max_position_pct}%",
            'min_position': f"{self.min_position_pct}%"
        }


# ─────────────────────────────────────────────────────────────
# INSTANCE GLOBALE
# ─────────────────────────────────────────────────────────────
position_sizer = PositionSizer()


def calculate_position_size(
    capital: float,
    indicators: Dict,
    score: int,
    ml_probability: float = 50,
    stop_loss_pct: float = 2.5
) -> Tuple[float, Dict]:
    """Fonction helper pour calculer la taille de position optimale."""
    return position_sizer.calculate_optimal_position(
        capital, indicators, score, ml_probability, stop_loss_pct
    )


def update_position_stats(is_win: bool, pnl_pct: float):
    """Met à jour les statistiques après un trade."""
    position_sizer.update_stats(is_win, pnl_pct)


def get_position_recommendations(capital: float, num_positions: int = 5) -> Dict:
    """Retourne les recommandations de position sizing."""
    return position_sizer.get_recommended_positions(capital, num_positions)
