"""
Module de Filtrage Avancé pour Améliorer la Rentabilité.
Contient les filtres de:
- Volume
- Heures de Trading
- Score Dynamique
- Risk/Reward Minimum
"""

from datetime import datetime
from typing import Dict, Tuple


class TradeFilters:
    """Gère tous les filtres de qualité des trades."""
    
    def __init__(self):
        # Configuration Volume STRICT
        self.volume_filter_enabled = True
        self.min_volume_ratio = 1.5  # Volume doit être 1.5x la moyenne (augmente de 1.2)
        
        # Configuration Heures de Trading (UTC) - HEURES OPTIMALES
        self.trading_hours_enabled = True
        self.trading_start_hour = 8   # 8h UTC (meilleure liquidité)
        self.trading_end_hour = 20    # 20h UTC (éviter fin de session)
        self.avoid_weekends = True
        
        # Configuration Score Dynamique ULTRA-STRICT
        self.dynamic_score_enabled = True
        self.score_bullish_market = 80   # STRICT
        self.score_bearish_market = 90   # TRES STRICT
        self.score_neutral_market = 85   # STRICT
        
        # Configuration Risk/Reward ULTRA-STRICT
        self.min_risk_reward = 3.0  # R/R minimum de 3:1 (qualité maximale)

    # ─────────────────────────────────────────────────────────────
    # FILTRE VOLUME
    # ─────────────────────────────────────────────────────────────

    def check_volume_filter(self, indicators: Dict) -> Tuple[bool, str]:
        """
        Vérifie si le volume est suffisant pour entrer en position.
        
        Args:
            indicators: Dict contenant 'volume_ratio'
        
        Returns:
            (is_valid, reason)
        """
        if not self.volume_filter_enabled:
            return True, "Volume filter désactivé"
        
        volume_ratio = indicators.get('volume_ratio', 0)
        
        if volume_ratio is None or volume_ratio == 0:
            return False, "Volume ratio non disponible"
        
        if volume_ratio >= self.min_volume_ratio:
            return True, f"✅ Volume OK: {volume_ratio:.2f}x moyenne"
        else:
            return False, f"❌ Volume faible: {volume_ratio:.2f}x (min: {self.min_volume_ratio}x)"

    # ─────────────────────────────────────────────────────────────
    # FILTRE HEURES DE TRADING
    # ─────────────────────────────────────────────────────────────

    def check_trading_hours(self) -> Tuple[bool, str]:
        """
        Vérifie si on est dans les heures de trading optimales.
        
        Returns:
            (is_valid, reason)
        """
        if not self.trading_hours_enabled:
            return True, "Trading hours filter désactivé"
        
        now = datetime.utcnow()
        current_hour = now.hour
        current_weekday = now.weekday()  # 0=Lundi, 6=Dimanche
        
        # Vérifier le week-end
        if self.avoid_weekends and current_weekday >= 5:
            return False, f"❌ Week-end (jour {current_weekday}) - Trading suspendu"
        
        # Vérifier les heures
        if self.trading_start_hour <= current_hour < self.trading_end_hour:
            return True, f"✅ Heure OK: {current_hour}h UTC (session active)"
        else:
            return False, f"❌ Hors heures: {current_hour}h UTC (actif: {self.trading_start_hour}h-{self.trading_end_hour}h)"

    # ─────────────────────────────────────────────────────────────
    # SCORE DYNAMIQUE SELON MARCHÉ
    # ─────────────────────────────────────────────────────────────

    def get_dynamic_min_score(self, market_stats: Dict) -> Tuple[int, str]:
        """
        Retourne le score minimum dynamique selon le sentiment du marché.
        
        Args:
            market_stats: Dict contenant 'total_bullish', 'total_bearish', 'total_neutral'
        
        Returns:
            (min_score, reason)
        """
        if not self.dynamic_score_enabled:
            return 70, "Score dynamique désactivé (défaut: 70)"
        
        bullish = market_stats.get('total_bullish', 0)
        bearish = market_stats.get('total_bearish', 0)
        
        if bullish > bearish * 1.5:
            # Marché très haussier - on peut être moins strict
            return self.score_bullish_market, f"🟢 Marché haussier (score min: {self.score_bullish_market})"
        elif bearish > bullish * 1.5:
            # Marché baissier - on doit être plus strict
            return self.score_bearish_market, f"🔴 Marché baissier (score min: {self.score_bearish_market})"
        else:
            # Marché neutre
            return self.score_neutral_market, f"⚪ Marché neutre (score min: {self.score_neutral_market})"

    # ─────────────────────────────────────────────────────────────
    # FILTRE RISK/REWARD
    # ─────────────────────────────────────────────────────────────

    def check_risk_reward(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        direction: str = 'LONG'
    ) -> Tuple[bool, float, str]:
        """
        Vérifie si le ratio Risk/Reward est acceptable.
        
        Args:
            entry_price: Prix d'entrée
            stop_loss: Prix du stop loss
            take_profit: Prix du take profit
            direction: 'LONG' ou 'SHORT'
        
        Returns:
            (is_valid, rr_ratio, reason)
        """
        if entry_price <= 0 or stop_loss <= 0 or take_profit <= 0:
            return False, 0, "Prix invalides"
        
        if direction == 'LONG':
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:  # SHORT
            risk = stop_loss - entry_price
            reward = entry_price - take_profit
        
        if risk <= 0:
            return False, 0, "Risk calculé <= 0"
        
        rr_ratio = reward / risk
        
        if rr_ratio >= self.min_risk_reward:
            return True, rr_ratio, f"✅ R/R OK: {rr_ratio:.2f}:1"
        else:
            return False, rr_ratio, f"❌ R/R faible: {rr_ratio:.2f}:1 (min: {self.min_risk_reward}:1)"

    # ─────────────────────────────────────────────────────────────
    # VALIDATION COMPLÈTE
    # ─────────────────────────────────────────────────────────────

    def validate_trade(
        self,
        indicators: Dict,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        score: int,
        market_stats: Dict,
        direction: str = 'LONG'
    ) -> Tuple[bool, list]:
        """
        Valide un trade avec tous les filtres.
        
        Returns:
            (is_valid, list_of_reasons)
        """
        reasons = []
        all_valid = True
        
        # 1. Volume
        vol_valid, vol_reason = self.check_volume_filter(indicators)
        if not vol_valid:
            all_valid = False
        reasons.append(vol_reason)
        
        # 2. Heures de trading
        hours_valid, hours_reason = self.check_trading_hours()
        if not hours_valid:
            all_valid = False
        reasons.append(hours_reason)
        
        # 3. Score dynamique
        min_score, score_reason = self.get_dynamic_min_score(market_stats)
        if score < min_score:
            all_valid = False
            reasons.append(f"❌ Score {score} < {min_score} requis")
        else:
            reasons.append(f"✅ Score OK: {score} >= {min_score}")
        
        # 4. Risk/Reward
        rr_valid, rr_ratio, rr_reason = self.check_risk_reward(
            entry_price, stop_loss, take_profit, direction
        )
        if not rr_valid:
            all_valid = False
        reasons.append(rr_reason)
        
        return all_valid, reasons


# Instance globale pour utilisation facile
trade_filters = TradeFilters()
