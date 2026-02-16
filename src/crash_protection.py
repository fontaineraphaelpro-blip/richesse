"""
Module de Protection Anti-Crash du Marché.
Détecte les crashs de marché et protège le portefeuille en temps réel.

Stratégies:
1. Monitor BTC comme indicateur leader (si BTC crash, tout crash)
2. Détection de chute brutale multi-assets
3. Volume anormal + prix en chute = alerte crash
4. Fermeture d'urgence de toutes les positions
5. Pause automatique du trading post-crash
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time


class CrashProtector:
    """
    Protège le portefeuille contre les crashs de marché.
    """
    
    def __init__(self):
        # ── Seuils de détection de crash ──
        self.btc_crash_threshold_1h = -5.0    # BTC -5% en 1h = CRASH
        self.btc_crash_threshold_15m = -3.0   # BTC -3% en 15min = CRASH FLASH
        self.alt_crash_threshold = -8.0       # Altcoin -8% = crash individuel
        
        # Multi-asset crash: si X% des assets monitorés sont en chute
        self.multi_asset_crash_ratio = 0.7    # 70% des assets en chute = crash
        self.multi_asset_drop_threshold = -3.0  # Chute de -3% minimum par asset
        
        # ── État du système ──
        self.crash_detected = False
        self.crash_type = None  # 'BTC_CRASH', 'FLASH_CRASH', 'MULTI_ASSET_CRASH'
        self.crash_start_time = None
        self.trading_paused = False
        self.pause_until = None
        
        # ── Durées de pause ──
        self.pause_duration_minor = 3600      # 1h pour crash mineur
        self.pause_duration_major = 14400     # 4h pour crash majeur
        self.pause_duration_flash = 7200      # 2h pour flash crash
        
        # ── Historique des prix pour détection ──
        self.btc_price_history = []  # [(timestamp, price), ...]
        self.price_history_max = 60  # Garder 60 points max
        
        # ── Actions d'urgence ──
        self.emergency_actions_log = []
        
    # ─────────────────────────────────────────────────────────────
    # MONITORING BTC (Indicateur Leader)
    # ─────────────────────────────────────────────────────────────
    
    def update_btc_price(self, current_price: float):
        """Met à jour l'historique des prix BTC."""
        now = datetime.now()
        self.btc_price_history.append((now, current_price))
        
        # Nettoyer l'historique (garder seulement les 60 dernières minutes)
        cutoff = now - timedelta(minutes=60)
        self.btc_price_history = [
            (ts, price) for ts, price in self.btc_price_history 
            if ts > cutoff
        ]
    
    def check_btc_crash(self, current_btc_price: float) -> Tuple[bool, Optional[str], float]:
        """
        Vérifie si BTC est en crash.
        
        Returns:
            (is_crash, crash_type, drop_percent)
        """
        if not self.btc_price_history:
            self.update_btc_price(current_btc_price)
            return False, None, 0.0
        
        now = datetime.now()
        
        # Vérifier le prix il y a 15 minutes
        price_15m_ago = self._get_price_at_time(now - timedelta(minutes=15))
        if price_15m_ago:
            drop_15m = ((current_btc_price - price_15m_ago) / price_15m_ago) * 100
            if drop_15m <= self.btc_crash_threshold_15m:
                return True, 'FLASH_CRASH', drop_15m
        
        # Vérifier le prix il y a 1 heure
        price_1h_ago = self._get_price_at_time(now - timedelta(minutes=60))
        if price_1h_ago:
            drop_1h = ((current_btc_price - price_1h_ago) / price_1h_ago) * 100
            if drop_1h <= self.btc_crash_threshold_1h:
                return True, 'BTC_CRASH', drop_1h
        
        self.update_btc_price(current_btc_price)
        return False, None, 0.0
    
    def _get_price_at_time(self, target_time: datetime) -> Optional[float]:
        """Récupère le prix le plus proche d'un moment donné."""
        if not self.btc_price_history:
            return None
        
        # Trouver le prix le plus proche (avec tolérance de 5 minutes)
        tolerance = timedelta(minutes=5)
        closest_price = None
        closest_diff = timedelta(hours=24)
        
        for ts, price in self.btc_price_history:
            diff = abs(ts - target_time)
            if diff < closest_diff and diff <= tolerance:
                closest_diff = diff
                closest_price = price
        
        return closest_price
    
    # ─────────────────────────────────────────────────────────────
    # DÉTECTION CRASH MULTI-ASSETS
    # ─────────────────────────────────────────────────────────────
    
    def check_multi_asset_crash(self, price_changes: Dict[str, float]) -> Tuple[bool, float]:
        """
        Vérifie si plusieurs assets sont en chute simultanée.
        
        Args:
            price_changes: Dict {symbol: change_percent_15m}
            
        Returns:
            (is_crash, ratio_of_assets_dropping)
        """
        if not price_changes:
            return False, 0.0
        
        # Compter les assets en chute significative
        dropping_assets = sum(
            1 for change in price_changes.values() 
            if change <= self.multi_asset_drop_threshold
        )
        
        total_assets = len(price_changes)
        drop_ratio = dropping_assets / total_assets
        
        is_crash = drop_ratio >= self.multi_asset_crash_ratio
        return is_crash, drop_ratio
    
    # ─────────────────────────────────────────────────────────────
    # DÉTECTION VOLUME ANORMAL
    # ─────────────────────────────────────────────────────────────
    
    def check_panic_selling(self, 
                            current_volume: float, 
                            avg_volume: float, 
                            price_change: float) -> bool:
        """
        Détecte les ventes paniques (volume élevé + chute de prix).
        
        Returns:
            True si panic selling détecté
        """
        if avg_volume == 0:
            return False
        
        volume_ratio = current_volume / avg_volume
        
        # Panic = Volume 3x+ supérieur à la moyenne ET prix en chute de -2%+
        return volume_ratio >= 3.0 and price_change <= -2.0
    
    # ─────────────────────────────────────────────────────────────
    # ACTIONS D'URGENCE
    # ─────────────────────────────────────────────────────────────
    
    def trigger_crash_response(self, crash_type: str, drop_percent: float) -> Dict:
        """
        Déclenche la réponse au crash.
        
        Returns:
            Dict avec les actions à effectuer
        """
        self.crash_detected = True
        self.crash_type = crash_type
        self.crash_start_time = datetime.now()
        
        # Déterminer la durée de pause
        if crash_type == 'FLASH_CRASH':
            pause_seconds = self.pause_duration_flash
            severity = 'HIGH'
        elif crash_type == 'BTC_CRASH':
            pause_seconds = self.pause_duration_major
            severity = 'CRITICAL'
        else:  # MULTI_ASSET_CRASH
            pause_seconds = self.pause_duration_minor
            severity = 'MEDIUM'
        
        self.trading_paused = True
        self.pause_until = datetime.now() + timedelta(seconds=pause_seconds)
        
        response = {
            'action': 'EMERGENCY_CLOSE_ALL',
            'crash_type': crash_type,
            'severity': severity,
            'drop_percent': round(drop_percent, 2),
            'pause_until': self.pause_until.isoformat(),
            'pause_duration_hours': pause_seconds / 3600,
            'timestamp': datetime.now().isoformat(),
            'message': self._get_crash_message(crash_type, drop_percent)
        }
        
        self.emergency_actions_log.append(response)
        
        return response
    
    def _get_crash_message(self, crash_type: str, drop_percent: float) -> str:
        """Génère un message d'alerte pour le crash."""
        messages = {
            'FLASH_CRASH': f"⚡ FLASH CRASH détecté! BTC -{abs(drop_percent):.1f}% en 15min. Fermeture d'urgence.",
            'BTC_CRASH': f"🔴 CRASH MAJEUR! BTC -{abs(drop_percent):.1f}% en 1h. Toutes positions fermées.",
            'MULTI_ASSET_CRASH': f"💥 CRASH MULTI-ASSETS! {abs(drop_percent)*100:.0f}% du marché en chute. Protection activée."
        }
        return messages.get(crash_type, "⚠️ Crash détecté. Protection activée.")
    
    def is_trading_allowed(self) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si le trading est autorisé.
        
        Returns:
            (allowed, reason_if_paused)
        """
        if not self.trading_paused:
            return True, None
        
        now = datetime.now()
        
        if self.pause_until and now >= self.pause_until:
            # Pause terminée
            self.trading_paused = False
            self.crash_detected = False
            self.crash_type = None
            return True, None
        
        # Encore en pause
        if self.pause_until:
            remaining = self.pause_until - now
            minutes_left = int(remaining.total_seconds() / 60)
            reason = f"Trading pausé suite à {self.crash_type}. Reprise dans {minutes_left} minutes."
        else:
            reason = "Trading pausé"
        
        return False, reason
    
    def force_resume_trading(self):
        """Force la reprise du trading (bypass manuel)."""
        self.trading_paused = False
        self.crash_detected = False
        self.pause_until = None
    
    # ─────────────────────────────────────────────────────────────
    # PROTECTION POSITIONS EXISTANTES
    # ─────────────────────────────────────────────────────────────
    
    def get_emergency_sl_distance(self, crash_type: str) -> float:
        """
        Retourne la distance SL d'urgence selon le type de crash.
        Plus le crash est violent, plus le SL est serré.
        
        Returns:
            Pourcentage de distance SL (ex: 0.5 = 0.5%)
        """
        if crash_type == 'FLASH_CRASH':
            return 0.3  # SL très serré
        elif crash_type == 'BTC_CRASH':
            return 0.5  # SL serré
        else:
            return 0.8  # SL modéré
    
    def calculate_emergency_sl(self, 
                               current_price: float, 
                               direction: str, 
                               crash_type: str) -> float:
        """
        Calcule un nouveau SL d'urgence en cas de crash.
        
        Args:
            current_price: Prix actuel
            direction: 'LONG' ou 'SHORT'
            crash_type: Type de crash détecté
            
        Returns:
            Nouveau prix de stop loss
        """
        sl_distance = self.get_emergency_sl_distance(crash_type)
        
        if direction == 'LONG':
            return current_price * (1 - sl_distance / 100)
        else:  # SHORT
            return current_price * (1 + sl_distance / 100)
    
    # ─────────────────────────────────────────────────────────────
    # ANALYSE COMPLÈTE
    # ─────────────────────────────────────────────────────────────
    
    def analyze_market_crash_risk(self, 
                                   btc_price: float,
                                   price_changes: Dict[str, float],
                                   btc_volume: float = 0,
                                   btc_avg_volume: float = 0) -> Dict:
        """
        Analyse complète du risque de crash.
        
        Args:
            btc_price: Prix actuel de BTC
            price_changes: Dict {symbol: change_percent_15m}
            btc_volume: Volume BTC actuel (optionnel)
            btc_avg_volume: Volume BTC moyen (optionnel)
            
        Returns:
            Dict avec l'analyse complète
        """
        # Vérifier si trading est déjà pausé
        trading_allowed, pause_reason = self.is_trading_allowed()
        if not trading_allowed:
            return {
                'crash_detected': self.crash_detected,
                'crash_type': self.crash_type,
                'trading_allowed': False,
                'reason': pause_reason,
                'action': 'WAIT'
            }
        
        # 1. Check BTC crash
        btc_crash, btc_crash_type, btc_drop = self.check_btc_crash(btc_price)
        
        if btc_crash and btc_crash_type:
            response = self.trigger_crash_response(btc_crash_type, btc_drop)
            return {
                'crash_detected': True,
                'crash_type': btc_crash_type,
                'trading_allowed': False,
                'drop_percent': btc_drop,
                'action': 'EMERGENCY_CLOSE_ALL',
                'response': response
            }
        
        # 2. Check multi-asset crash
        multi_crash, drop_ratio = self.check_multi_asset_crash(price_changes)
        
        if multi_crash:
            response = self.trigger_crash_response('MULTI_ASSET_CRASH', drop_ratio)
            return {
                'crash_detected': True,
                'crash_type': 'MULTI_ASSET_CRASH',
                'trading_allowed': False,
                'drop_ratio': drop_ratio,
                'action': 'EMERGENCY_CLOSE_ALL',
                'response': response
            }
        
        # 3. Check panic selling (si volume fourni)
        if btc_volume > 0 and btc_avg_volume > 0:
            btc_change = price_changes.get('BTCUSDT', 0)
            if self.check_panic_selling(btc_volume, btc_avg_volume, btc_change):
                response = self.trigger_crash_response('PANIC_SELLING', btc_change)
                return {
                    'crash_detected': True,
                    'crash_type': 'PANIC_SELLING',
                    'trading_allowed': False,
                    'action': 'EMERGENCY_CLOSE_ALL',
                    'response': response
                }
        
        # Pas de crash détecté
        return {
            'crash_detected': False,
            'crash_type': None,
            'trading_allowed': True,
            'action': 'CONTINUE',
            'btc_price': btc_price
        }
    
    # ─────────────────────────────────────────────────────────────
    # STATISTIQUES
    # ─────────────────────────────────────────────────────────────
    
    def get_crash_stats(self) -> Dict:
        """Retourne les statistiques des crashs détectés."""
        return {
            'total_crashes_detected': len(self.emergency_actions_log),
            'currently_paused': self.trading_paused,
            'current_crash_type': self.crash_type,
            'pause_until': self.pause_until.isoformat() if self.pause_until else None,
            'recent_crashes': self.emergency_actions_log[-5:] if self.emergency_actions_log else []
        }


# ─────────────────────────────────────────────────────────────────
# INSTANCE GLOBALE
# ─────────────────────────────────────────────────────────────────

crash_protector = CrashProtector()


def check_for_crash(btc_price: float, price_changes: Dict[str, float]) -> Dict:
    """
    Fonction utilitaire pour vérifier les crashs.
    À appeler à chaque cycle de scan.
    """
    return crash_protector.analyze_market_crash_risk(btc_price, price_changes)


def is_crash_mode() -> bool:
    """Vérifie si on est actuellement en mode crash (trading pausé)."""
    return crash_protector.crash_detected


def get_crash_status() -> Dict:
    """Retourne le statut actuel du système crash."""
    allowed, reason = crash_protector.is_trading_allowed()
    return {
        'trading_allowed': allowed,
        'reason': reason,
        'crash_detected': crash_protector.crash_detected,
        'crash_type': crash_protector.crash_type
    }
