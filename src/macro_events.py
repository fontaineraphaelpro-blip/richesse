"""
Module Macro Events: Calendrier économique temps réel et alertes régulations.

Sources utilisées:
- Investing.com Calendar (scraping léger)
- ForexFactory Calendar
- FED Calendar officiel
- ECB Calendar officiel  
- CoinDesk/CoinTelegraph pour régulations crypto
- RSS feeds pour alertes

Événements surveillés:
- FOMC, CPI, NFP, GDP, PPI (US)
- ECB, BCE décisions (EU)
- Régulations MiCA, SEC, CFTC
- Halving Bitcoin, Upgrades réseau
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import json
import re
import os
from xml.etree import ElementTree


class MacroEventsAnalyzer:
    """
    Analyseur d'événements macroéconomiques et réglementaires.
    Surveille les événements qui peuvent impacter les marchés crypto.
    """
    
    def __init__(self):
        # Cache
        self.cache = {}
        self.cache_duration = 1800  # 30 minutes
        
        # Fichier pour stocker les événements personnalisés
        self.custom_events_file = 'custom_events.json'
        
        # URLs des sources
        self.fed_calendar_url = "https://www.federalreserve.gov"
        self.ecb_calendar_url = "https://www.ecb.europa.eu"
        
        # Événements économiques majeurs (impact HIGH sur crypto)
        self.high_impact_events = {
            'FOMC': {'impact': 'CRITICAL', 'pause_hours': 4, 'volatility': 'extreme'},
            'CPI': {'impact': 'HIGH', 'pause_hours': 2, 'volatility': 'high'},
            'NFP': {'impact': 'HIGH', 'pause_hours': 2, 'volatility': 'high'},
            'GDP': {'impact': 'MEDIUM', 'pause_hours': 1, 'volatility': 'medium'},
            'PPI': {'impact': 'MEDIUM', 'pause_hours': 1, 'volatility': 'medium'},
            'PCE': {'impact': 'HIGH', 'pause_hours': 2, 'volatility': 'high'},
            'Unemployment': {'impact': 'MEDIUM', 'pause_hours': 1, 'volatility': 'medium'},
            'Retail Sales': {'impact': 'MEDIUM', 'pause_hours': 1, 'volatility': 'medium'},
            'ECB Rate': {'impact': 'HIGH', 'pause_hours': 3, 'volatility': 'high'},
            'ECB Press': {'impact': 'MEDIUM', 'pause_hours': 2, 'volatility': 'medium'},
            'BoJ Rate': {'impact': 'MEDIUM', 'pause_hours': 2, 'volatility': 'medium'},
            'BoE Rate': {'impact': 'MEDIUM', 'pause_hours': 2, 'volatility': 'medium'},
        }
        
        # Mots-clés pour régulations crypto
        self.regulation_keywords = [
            'sec', 'cftc', 'regulation', 'ban', 'lawsuit', 'legal',
            'mica', 'mifid', 'eu regulation', 'european union',
            'binance', 'coinbase', 'kraken', 'lawsuit', 'settlement',
            'stablecoin', 'cbdc', 'digital currency', 'crypto bill',
            'etf approve', 'etf reject', 'etf delay',
            'money laundering', 'aml', 'kyc', 'sanctions',
            'tax', 'taxation', 'irs', 'treasury',
        ]
        
        # Événements crypto spécifiques
        self.crypto_events = {
            'halving': {'impact': 'CRITICAL', 'effect': 'bullish_long_term'},
            'upgrade': {'impact': 'MEDIUM', 'effect': 'neutral'},
            'fork': {'impact': 'HIGH', 'effect': 'volatile'},
            'listing': {'impact': 'HIGH', 'effect': 'bullish_short'},
            'delisting': {'impact': 'HIGH', 'effect': 'bearish'},
            'hack': {'impact': 'CRITICAL', 'effect': 'bearish'},
            'bankruptcy': {'impact': 'CRITICAL', 'effect': 'bearish'},
        }
        
        # Calendrier statique 2026 (événements récurrents)
        self.static_calendar_2026 = self._build_2026_calendar()
        
        print("📅 Macro Events Analyzer initialisé")
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Récupère une donnée du cache si valide."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_duration:
                return data
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Stocke une donnée dans le cache."""
        self.cache[key] = (data, datetime.now())
    
    def _build_2026_calendar(self) -> List[Dict]:
        """
        Construit le calendrier des événements économiques majeurs pour 2026.
        Basé sur les patterns historiques de la FED et ECB.
        """
        events = []
        
        # FOMC Meetings 2026 (estimation basée sur pattern historique)
        # La FED se réunit ~8 fois par an
        fomc_dates = [
            '2026-01-28', '2026-03-18', '2026-05-06', '2026-06-17',
            '2026-07-29', '2026-09-16', '2026-11-04', '2026-12-16'
        ]
        for date in fomc_dates:
            events.append({
                'date': date,
                'time': '19:00',  # 14:00 EST = 19:00 UTC
                'name': 'FOMC Rate Decision',
                'type': 'FOMC',
                'impact': 'CRITICAL',
                'region': 'US',
                'pause_hours': 4
            })
        
        # CPI Release (généralement 2ème semaine du mois)
        for month in range(1, 13):
            # Approximation: 10-14 du mois
            day = 12 if month not in [2, 5, 8, 11] else 13
            events.append({
                'date': f'2026-{month:02d}-{day:02d}',
                'time': '13:30',  # 8:30 EST = 13:30 UTC
                'name': 'US CPI Release',
                'type': 'CPI',
                'impact': 'HIGH',
                'region': 'US',
                'pause_hours': 2
            })
        
        # NFP - Non-Farm Payrolls (1er vendredi du mois)
        nfp_dates = [
            '2026-01-02', '2026-02-06', '2026-03-06', '2026-04-03',
            '2026-05-01', '2026-06-05', '2026-07-03', '2026-08-07',
            '2026-09-04', '2026-10-02', '2026-11-06', '2026-12-04'
        ]
        for date in nfp_dates:
            events.append({
                'date': date,
                'time': '13:30',
                'name': 'Non-Farm Payrolls',
                'type': 'NFP',
                'impact': 'HIGH',
                'region': 'US',
                'pause_hours': 2
            })
        
        # ECB Meetings 2026
        ecb_dates = [
            '2026-01-22', '2026-03-05', '2026-04-16', '2026-06-04',
            '2026-07-23', '2026-09-10', '2026-10-29', '2026-12-10'
        ]
        for date in ecb_dates:
            events.append({
                'date': date,
                'time': '13:15',  # 14:15 CET = 13:15 UTC
                'name': 'ECB Rate Decision',
                'type': 'ECB Rate',
                'impact': 'HIGH',
                'region': 'EU',
                'pause_hours': 3
            })
        
        # GDP Releases (fin de chaque trimestre)
        gdp_dates = ['2026-01-29', '2026-04-29', '2026-07-30', '2026-10-29']
        for date in gdp_dates:
            events.append({
                'date': date,
                'time': '13:30',
                'name': 'US GDP Release',
                'type': 'GDP',
                'impact': 'MEDIUM',
                'region': 'US',
                'pause_hours': 1
            })
        
        # PCE (Personal Consumption Expenditure - indicateur inflation préféré de la Fed)
        for month in range(1, 13):
            day = 28 if month not in [2] else 26
            events.append({
                'date': f'2026-{month:02d}-{day:02d}',
                'time': '13:30',
                'name': 'US PCE Price Index',
                'type': 'PCE',
                'impact': 'HIGH',
                'region': 'US',
                'pause_hours': 2
            })
        
        return sorted(events, key=lambda x: x['date'])
    
    def get_upcoming_events(self, days_ahead: int = 7) -> List[Dict]:
        """
        Retourne les événements économiques des N prochains jours.
        
        Args:
            days_ahead: Nombre de jours à regarder
            
        Returns:
            Liste des événements à venir
        """
        cache_key = f"upcoming_{days_ahead}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        upcoming = []
        
        for event in self.static_calendar_2026:
            try:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                if today <= event_date <= end_date:
                    days_until = (event_date - today).days
                    upcoming.append({
                        **event,
                        'days_until': days_until,
                        'is_today': days_until == 0,
                        'is_tomorrow': days_until == 1
                    })
            except ValueError:
                continue
        
        # Ajouter les événements personnalisés
        custom_events = self._load_custom_events()
        for event in custom_events:
            try:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                if today <= event_date <= end_date:
                    days_until = (event_date - today).days
                    upcoming.append({
                        **event,
                        'days_until': days_until,
                        'is_today': days_until == 0,
                        'is_tomorrow': days_until == 1,
                        'custom': True
                    })
            except ValueError:
                continue
        
        # Trier par date
        upcoming = sorted(upcoming, key=lambda x: (x['date'], x.get('time', '00:00')))
        
        self._set_cache(cache_key, upcoming)
        return upcoming
    
    def get_today_events(self) -> List[Dict]:
        """Retourne les événements du jour."""
        return [e for e in self.get_upcoming_events(1) if e.get('is_today')]
    
    def check_event_proximity(self) -> Dict:
        """
        Vérifie si un événement majeur est proche.
        
        Returns:
            Dict avec should_pause, event_info, etc.
        """
        now = datetime.utcnow()
        today = now.date()
        current_hour = now.hour
        current_minute = now.minute
        
        today_events = self.get_today_events()
        
        for event in today_events:
            event_time = event.get('time', '00:00')
            try:
                event_hour, event_minute = map(int, event_time.split(':'))
            except:
                event_hour, event_minute = 0, 0
            
            # Convertir en minutes depuis minuit
            current_minutes = current_hour * 60 + current_minute
            event_minutes = event_hour * 60 + event_minute
            
            # Minutes avant l'événement
            minutes_until = event_minutes - current_minutes
            
            # Pause si dans les 2 heures avant ou 2 heures après un événement HIGH/CRITICAL
            if event.get('impact') in ['HIGH', 'CRITICAL']:
                if -120 <= minutes_until <= 120:  # 2h avant et 2h après
                    return {
                        'should_pause': True,
                        'event': event['name'],
                        'time': event_time,
                        'impact': event['impact'],
                        'minutes_until': minutes_until,
                        'reason': f"⚠️ {event['name']} dans {minutes_until}min" if minutes_until > 0 
                                  else f"⚠️ {event['name']} en cours/récent",
                        'pause_hours': event.get('pause_hours', 2)
                    }
            
            # Alerte si événement MEDIUM dans l'heure
            elif event.get('impact') == 'MEDIUM':
                if -30 <= minutes_until <= 60:
                    return {
                        'should_pause': False,
                        'should_warn': True,
                        'event': event['name'],
                        'time': event_time,
                        'impact': event['impact'],
                        'minutes_until': minutes_until,
                        'reason': f"📊 {event['name']} proche ({minutes_until}min)"
                    }
        
        # Vérifier événements demain (alerte préventive)
        tomorrow_events = [e for e in self.get_upcoming_events(2) if e.get('is_tomorrow')]
        critical_tomorrow = [e for e in tomorrow_events if e.get('impact') == 'CRITICAL']
        
        if critical_tomorrow:
            return {
                'should_pause': False,
                'should_warn': True,
                'event': critical_tomorrow[0]['name'],
                'time': critical_tomorrow[0].get('time'),
                'impact': 'CRITICAL',
                'days_until': 1,
                'reason': f"⚠️ DEMAIN: {critical_tomorrow[0]['name']}"
            }
        
        return {
            'should_pause': False,
            'should_warn': False,
            'event': None,
            'reason': 'Pas d\'événement majeur proche'
        }
    
    # ─────────────────────────────────────────────────────────────
    # RÉGULATIONS ET NEWS
    # ─────────────────────────────────────────────────────────────
    
    def fetch_regulation_news(self) -> List[Dict]:
        """
        Récupère les news liées aux régulations crypto.
        Utilise CryptoPanic et d'autres sources.
        """
        cache_key = "regulation_news"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        news = []
        
        try:
            # CryptoPanic API (filtre régulations)
            response = requests.get(
                "https://cryptopanic.com/api/v1/posts/",
                params={
                    'auth_token': 'DEMO',  # Token demo limité
                    'filter': 'important',
                    'kind': 'news',
                    'regions': 'en'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('results', [])[:30]:
                    title = item.get('title', '').lower()
                    
                    # Vérifier si c'est une news régulation
                    is_regulation = any(kw in title for kw in self.regulation_keywords)
                    
                    if is_regulation:
                        # Analyser le sentiment
                        sentiment = 'neutral'
                        if any(w in title for w in ['ban', 'lawsuit', 'reject', 'fine', 'fraud']):
                            sentiment = 'bearish'
                        elif any(w in title for w in ['approve', 'allow', 'legal', 'adopt']):
                            sentiment = 'bullish'
                        
                        news.append({
                            'title': item.get('title'),
                            'source': item.get('source', {}).get('title'),
                            'url': item.get('url'),
                            'published': item.get('published_at'),
                            'sentiment': sentiment,
                            'type': 'regulation',
                            'impact': 'HIGH' if any(w in title for w in ['sec', 'ban', 'etf']) else 'MEDIUM'
                        })
        except Exception as e:
            print(f"⚠️ Erreur fetch regulation news: {e}")
        
        self._set_cache(cache_key, news)
        return news
    
    def check_regulation_alerts(self) -> Dict:
        """
        Vérifie s'il y a des alertes régulation importantes.
        
        Returns:
            Dict avec has_alert, alerts, sentiment_impact
        """
        news = self.fetch_regulation_news()
        
        if not news:
            return {
                'has_alert': False,
                'alerts': [],
                'sentiment_impact': 0,
                'should_pause': False
            }
        
        # Filtrer les news des dernières 24h
        recent_news = []
        now = datetime.now()
        
        for item in news:
            try:
                pub_date = datetime.fromisoformat(item['published'].replace('Z', '+00:00'))
                if (now - pub_date.replace(tzinfo=None)).total_seconds() < 86400:  # 24h
                    recent_news.append(item)
            except:
                recent_news.append(item)  # Inclure si date invalide
        
        if not recent_news:
            return {
                'has_alert': False,
                'alerts': [],
                'sentiment_impact': 0,
                'should_pause': False
            }
        
        # Calculer l'impact
        bearish_count = sum(1 for n in recent_news if n['sentiment'] == 'bearish')
        bullish_count = sum(1 for n in recent_news if n['sentiment'] == 'bullish')
        high_impact = [n for n in recent_news if n.get('impact') == 'HIGH']
        
        sentiment_impact = (bullish_count - bearish_count) * 5
        
        # Pause si news très négative HIGH impact
        should_pause = len([n for n in high_impact if n['sentiment'] == 'bearish']) >= 2
        
        return {
            'has_alert': len(recent_news) > 0,
            'alert_count': len(recent_news),
            'alerts': recent_news[:5],  # Top 5
            'bearish_count': bearish_count,
            'bullish_count': bullish_count,
            'sentiment_impact': sentiment_impact,
            'should_pause': should_pause,
            'reason': 'Multiples news régulation négatives' if should_pause else None
        }
    
    # ─────────────────────────────────────────────────────────────
    # ÉVÉNEMENTS CRYPTO SPÉCIFIQUES
    # ─────────────────────────────────────────────────────────────
    
    def get_crypto_events(self) -> List[Dict]:
        """
        Retourne les événements crypto majeurs à venir.
        (Halvings, upgrades, forks...)
        """
        # Événements crypto 2026 (à mettre à jour)
        events = [
            {
                'date': '2026-04-15',  # Estimation
                'name': 'Bitcoin Halving #5',
                'type': 'halving',
                'asset': 'BTC',
                'impact': 'CRITICAL',
                'effect': 'bullish_long_term',
                'note': 'Block reward: 3.125 → 1.5625 BTC'
            },
            {
                'date': '2026-03-01',
                'name': 'Ethereum Dencun+ Upgrade',
                'type': 'upgrade',
                'asset': 'ETH',
                'impact': 'MEDIUM',
                'effect': 'neutral',
                'note': 'Amélioration scalabilité L2'
            },
        ]
        
        # Filtrer les événements futurs
        today = datetime.now().date()
        future_events = []
        
        for event in events:
            try:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                if event_date >= today:
                    days_until = (event_date - today).days
                    future_events.append({
                        **event,
                        'days_until': days_until
                    })
            except:
                continue
        
        return sorted(future_events, key=lambda x: x['days_until'])
    
    # ─────────────────────────────────────────────────────────────
    # ÉVÉNEMENTS PERSONNALISÉS
    # ─────────────────────────────────────────────────────────────
    
    def _load_custom_events(self) -> List[Dict]:
        """Charge les événements personnalisés."""
        if os.path.exists(self.custom_events_file):
            try:
                with open(self.custom_events_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def add_custom_event(self, date: str, name: str, impact: str = 'MEDIUM', 
                        event_type: str = 'CUSTOM', pause_hours: int = 1) -> bool:
        """
        Ajoute un événement personnalisé.
        
        Args:
            date: Date au format YYYY-MM-DD
            name: Nom de l'événement
            impact: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
            event_type: Type d'événement
            pause_hours: Heures de pause recommandées
        """
        try:
            # Valider la date
            datetime.strptime(date, '%Y-%m-%d')
            
            events = self._load_custom_events()
            events.append({
                'date': date,
                'name': name,
                'type': event_type,
                'impact': impact,
                'pause_hours': pause_hours,
                'created': datetime.now().isoformat()
            })
            
            with open(self.custom_events_file, 'w') as f:
                json.dump(events, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Erreur ajout événement: {e}")
            return False
    
    # ─────────────────────────────────────────────────────────────
    # ANALYSE COMPLÈTE
    # ─────────────────────────────────────────────────────────────
    
    def get_complete_macro_analysis(self) -> Dict:
        """
        Retourne une analyse macro complète.
        
        Returns:
            Dict avec tous les événements, alertes et recommandations
        """
        # Événements économiques
        upcoming = self.get_upcoming_events(7)
        event_proximity = self.check_event_proximity()
        
        # Régulations
        regulation = self.check_regulation_alerts()
        
        # Crypto events
        crypto_events = self.get_crypto_events()
        
        # Décision trading
        should_pause = event_proximity.get('should_pause', False) or regulation.get('should_pause', False)
        
        # Score macro (impact sur sentiment)
        macro_score = 0
        
        # Impact événements proches
        if event_proximity.get('should_pause'):
            macro_score -= 20
        elif event_proximity.get('should_warn'):
            macro_score -= 5
        
        # Impact régulations
        macro_score += regulation.get('sentiment_impact', 0)
        
        # Limiter entre -50 et +50
        macro_score = max(-50, min(50, macro_score))
        
        # Signal global
        if macro_score > 20:
            macro_signal = 'bullish'
        elif macro_score < -20:
            macro_signal = 'bearish'
        else:
            macro_signal = 'neutral'
        
        return {
            'timestamp': datetime.now().isoformat(),
            'should_pause_trading': should_pause,
            'pause_reason': event_proximity.get('reason') if event_proximity.get('should_pause') 
                           else (regulation.get('reason') if regulation.get('should_pause') else None),
            
            'economic_events': {
                'upcoming_7d': len(upcoming),
                'today': [e for e in upcoming if e.get('is_today')],
                'tomorrow': [e for e in upcoming if e.get('is_tomorrow')],
                'this_week': upcoming[:10],
                'proximity_check': event_proximity
            },
            
            'regulation': regulation,
            
            'crypto_events': crypto_events[:5],
            
            'macro_score': macro_score,
            'macro_signal': macro_signal,
            
            'trading_recommendation': 'PAUSE' if should_pause else (
                'CAUTIOUS' if macro_score < -10 else (
                    'FAVORABLE' if macro_score > 10 else 'NORMAL'
                )
            )
        }
    
    def get_trading_adjustment(self) -> Tuple[bool, int, str]:
        """
        Retourne l'ajustement pour le trading.
        
        Returns:
            (should_trade, score_modifier, reason)
        """
        analysis = self.get_complete_macro_analysis()
        
        if analysis['should_pause_trading']:
            return False, -50, analysis['pause_reason']
        
        return True, analysis['macro_score'], analysis['trading_recommendation']


# ─────────────────────────────────────────────────────────────
# INSTANCE GLOBALE
# ─────────────────────────────────────────────────────────────
macro_analyzer = MacroEventsAnalyzer()


def get_macro_analysis() -> Dict:
    """Fonction helper pour obtenir l'analyse macro complète."""
    return macro_analyzer.get_complete_macro_analysis()


def check_macro_events() -> Tuple[bool, int, str]:
    """Vérifie les événements macro et retourne l'ajustement."""
    return macro_analyzer.get_trading_adjustment()


def get_upcoming_economic_events(days: int = 7) -> List[Dict]:
    """Retourne les événements économiques à venir."""
    return macro_analyzer.get_upcoming_events(days)
