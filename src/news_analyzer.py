"""
Module de News & Sentiment pour le Trading Bot.
Récupère les news crypto et ajuste le trading en fonction du sentiment marché.

Sources:
1. Fear & Greed Index (Alternative.me)
2. CryptoPanic API (news crypto)
3. Calendrier économique (événements majeurs)
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import time


class NewsAnalyzer:
    """
    Analyse les news et le sentiment pour ajuster le trading.
    """
    
    def __init__(self):
        # ── Configuration ──
        self.fear_greed_url = "https://api.alternative.me/fng/"
        self.cryptopanic_url = "https://cryptopanic.com/api/v1/posts/"
        self.cryptopanic_api_key = None  # Optionnel, gratuit avec limites
        
        # ── Cache (pour éviter trop de requêtes) ──
        self.cache = {
            'fear_greed': {'value': None, 'updated': None},
            'news': {'items': [], 'updated': None},
            'events': {'items': [], 'updated': None}
        }
        self.cache_duration = 300  # 5 minutes
        
        # ── Seuils de sentiment ──
        self.extreme_fear_threshold = 20    # En dessous = marché paniqué
        self.fear_threshold = 40            # En dessous = prudent
        self.greed_threshold = 60           # Au dessus = euphorie
        self.extreme_greed_threshold = 80   # Au dessus = bulle potentielle
        
        # ── Événements majeurs (pause trading) ──
        self.major_events = self._load_economic_calendar()
        
        # ── Mots-clés de news importantes ──
        self.bullish_keywords = [
            'etf approved', 'adoption', 'partnership', 'bullish', 
            'all-time high', 'ath', 'breakout', 'institutional',
            'buy signal', 'accumulation', 'halving'
        ]
        self.bearish_keywords = [
            'hack', 'exploit', 'crash', 'bearish', 'sec', 'lawsuit',
            'ban', 'regulation', 'dump', 'sell-off', 'bankruptcy',
            'ftx', 'fraud', 'investigation', 'ponzi'
        ]
        self.pause_keywords = [
            'fomc', 'fed', 'interest rate', 'cpi', 'inflation',
            'powell', 'yellen', 'treasury', 'debt ceiling'
        ]
    
    # ─────────────────────────────────────────────────────────────
    # FEAR & GREED INDEX
    # ─────────────────────────────────────────────────────────────
    
    def get_fear_greed_index(self) -> Dict:
        """
        Récupère le Fear & Greed Index actuel.
        
        Returns:
            Dict avec value (0-100), classification, et recommandation
        """
        # Vérifier le cache
        if self._is_cache_valid('fear_greed'):
            return self.cache['fear_greed']['value']
        
        try:
            response = requests.get(self.fear_greed_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('data'):
                    fg_data = data['data'][0]
                    value = int(fg_data['value'])
                    classification = fg_data['value_classification']
                    
                    # Recommandation basée sur le sentiment
                    recommendation = self._get_fg_recommendation(value)
                    
                    result = {
                        'value': value,
                        'classification': classification,
                        'recommendation': recommendation,
                        'score_modifier': self._get_score_modifier(value),
                        'timestamp': fg_data.get('timestamp', datetime.now().isoformat())
                    }
                    
                    # Mettre en cache
                    self.cache['fear_greed'] = {
                        'value': result,
                        'updated': datetime.now()
                    }
                    
                    return result
                    
        except Exception as e:
            print(f"⚠️ Erreur Fear & Greed API: {e}")
        
        # Valeur par défaut en cas d'erreur
        return {
            'value': 50,
            'classification': 'Neutral',
            'recommendation': 'NORMAL',
            'score_modifier': 0,
            'error': True
        }
    
    def _get_fg_recommendation(self, value: int) -> str:
        """Recommandation basée sur le Fear & Greed Index."""
        if value <= self.extreme_fear_threshold:
            return 'STRONG_BUY'  # "Be greedy when others are fearful"
        elif value <= self.fear_threshold:
            return 'BUY_CAUTIOUS'
        elif value <= self.greed_threshold:
            return 'NORMAL'
        elif value <= self.extreme_greed_threshold:
            return 'SELL_CAUTIOUS'
        else:
            return 'AVOID_LONG'  # Risque de correction
    
    def _get_score_modifier(self, fg_value: int) -> int:
        """
        Modifie le score de trading selon le sentiment.
        
        Returns:
            Modificateur à ajouter au score (-15 à +15)
        """
        if fg_value <= self.extreme_fear_threshold:
            return +10  # Opportunité d'achat
        elif fg_value <= self.fear_threshold:
            return +5
        elif fg_value <= self.greed_threshold:
            return 0   # Neutre
        elif fg_value <= self.extreme_greed_threshold:
            return -5  # Prudence
        else:
            return -15  # Éviter les LONG, favoriser SHORT
    
    # ─────────────────────────────────────────────────────────────
    # NEWS CRYPTO
    # ─────────────────────────────────────────────────────────────
    
    def get_recent_news(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Récupère les news crypto récentes.
        
        Args:
            symbol: Filtrer par crypto (ex: 'BTC', 'ETH')
            
        Returns:
            Liste de news avec sentiment
        """
        # Vérifier le cache
        if self._is_cache_valid('news'):
            news = self.cache['news']['items']
            if symbol:
                return [n for n in news if symbol.upper().replace('USDT', '') in n.get('currencies', '')]
            return news
        
        try:
            params = {
                'auth_token': self.cryptopanic_api_key,
                'public': 'true',
                'kind': 'news'
            }
            
            if symbol:
                params['currencies'] = symbol.upper().replace('USDT', '')
            
            response = requests.get(self.cryptopanic_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                news_items = []
                
                for item in data.get('results', [])[:20]:  # Limiter à 20 news
                    sentiment = self._analyze_news_sentiment(item.get('title', ''))
                    
                    news_items.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'source': item.get('source', {}).get('title', 'Unknown'),
                        'published': item.get('published_at', ''),
                        'currencies': [c.get('code', '') for c in item.get('currencies', [])],
                        'sentiment': sentiment,
                        'votes': item.get('votes', {})
                    })
                
                # Mettre en cache
                self.cache['news'] = {
                    'items': news_items,
                    'updated': datetime.now()
                }
                
                return news_items
                
        except Exception as e:
            print(f"⚠️ Erreur News API: {e}")
        
        return []
    
    def _analyze_news_sentiment(self, title: str) -> str:
        """Analyse le sentiment d'une news basé sur les mots-clés."""
        title_lower = title.lower()
        
        # Vérifier les mots-clés de pause
        for keyword in self.pause_keywords:
            if keyword in title_lower:
                return 'PAUSE'
        
        # Compter les signaux
        bullish_count = sum(1 for kw in self.bullish_keywords if kw in title_lower)
        bearish_count = sum(1 for kw in self.bearish_keywords if kw in title_lower)
        
        if bullish_count > bearish_count:
            return 'BULLISH'
        elif bearish_count > bullish_count:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def get_news_sentiment_score(self, symbol: Optional[str] = None) -> Dict:
        """
        Calcule un score de sentiment global basé sur les news récentes.
        
        Returns:
            Dict avec score (-100 à +100) et détails
        """
        news = self.get_recent_news(symbol)
        
        if not news:
            return {'score': 0, 'bullish': 0, 'bearish': 0, 'neutral': 0, 'pause_events': 0}
        
        bullish = sum(1 for n in news if n['sentiment'] == 'BULLISH')
        bearish = sum(1 for n in news if n['sentiment'] == 'BEARISH')
        neutral = sum(1 for n in news if n['sentiment'] == 'NEUTRAL')
        pause = sum(1 for n in news if n['sentiment'] == 'PAUSE')
        
        total = len(news)
        score = ((bullish - bearish) / total) * 100 if total > 0 else 0
        
        return {
            'score': round(score, 1),
            'bullish': bullish,
            'bearish': bearish,
            'neutral': neutral,
            'pause_events': pause,
            'should_pause': pause > 0
        }
    
    # ─────────────────────────────────────────────────────────────
    # CALENDRIER ÉCONOMIQUE
    # ─────────────────────────────────────────────────────────────
    
    def _load_economic_calendar(self) -> List[Dict]:
        """
        Charge les événements économiques majeurs prévus.
        Ces événements peuvent causer de forte volatilité.
        """
        # Événements récurrents à surveiller
        return [
            {'name': 'FOMC Meeting', 'impact': 'HIGH', 'pause_hours': 4},
            {'name': 'CPI Release', 'impact': 'HIGH', 'pause_hours': 2},
            {'name': 'NFP (Jobs Report)', 'impact': 'HIGH', 'pause_hours': 2},
            {'name': 'Fed Chair Speech', 'impact': 'MEDIUM', 'pause_hours': 1},
            {'name': 'GDP Release', 'impact': 'MEDIUM', 'pause_hours': 1},
            {'name': 'ECB Meeting', 'impact': 'MEDIUM', 'pause_hours': 2},
        ]
    
    def check_economic_events(self) -> Dict:
        """
        Vérifie s'il y a des événements économiques majeurs aujourd'hui.
        
        Returns:
            Dict avec should_pause et event_info
        """
        # Vérifier les news pour des mentions d'événements
        news = self.get_recent_news()
        
        for news_item in news:
            if news_item['sentiment'] == 'PAUSE':
                return {
                    'should_pause': True,
                    'event': news_item['title'],
                    'reason': 'Événement économique majeur détecté dans les news'
                }
        
        return {
            'should_pause': False,
            'event': None,
            'reason': None
        }
    
    # ─────────────────────────────────────────────────────────────
    # ANALYSE COMPLÈTE
    # ─────────────────────────────────────────────────────────────
    
    def get_market_sentiment(self) -> Dict:
        """
        Analyse complète du sentiment marché.
        
        Returns:
            Dict avec toutes les analyses et recommandations
        """
        # Fear & Greed
        fg = self.get_fear_greed_index()
        
        # News sentiment
        news_sentiment = self.get_news_sentiment_score()
        
        # Événements économiques
        events = self.check_economic_events()
        
        # Score combiné
        combined_score = fg.get('score_modifier', 0) + (news_sentiment['score'] / 10)
        
        # Décision trading
        if events['should_pause']:
            trading_action = 'PAUSE'
            reason = events['reason']
        elif fg['value'] >= self.extreme_greed_threshold:
            trading_action = 'AVOID_LONG'
            reason = f"Extreme Greed ({fg['value']}) - Risque de correction"
        elif fg['value'] <= self.extreme_fear_threshold:
            trading_action = 'FAVOR_LONG'
            reason = f"Extreme Fear ({fg['value']}) - Opportunité d'achat"
        elif news_sentiment['bearish'] > news_sentiment['bullish'] * 2:
            trading_action = 'CAUTIOUS'
            reason = f"News majoritairement bearish ({news_sentiment['bearish']} vs {news_sentiment['bullish']})"
        else:
            trading_action = 'NORMAL'
            reason = "Conditions normales"
        
        return {
            'timestamp': datetime.now().isoformat(),
            'fear_greed': fg,
            'news_sentiment': news_sentiment,
            'economic_events': events,
            'combined_score_modifier': round(combined_score, 1),
            'trading_action': trading_action,
            'reason': reason,
            'recommendations': {
                'long_bias': max(0, min(100, 50 + combined_score)),
                'short_bias': max(0, min(100, 50 - combined_score)),
                'position_size_modifier': self._get_position_size_modifier(fg['value'], news_sentiment)
            }
        }
    
    def _get_position_size_modifier(self, fg_value: int, news_sentiment: Dict) -> float:
        """
        Modifie la taille de position selon les conditions.
        
        Returns:
            Multiplicateur (0.5 à 1.5)
        """
        modifier = 1.0
        
        # Fear & Greed ajustement
        if fg_value <= self.extreme_fear_threshold:
            modifier *= 1.2  # Augmenter légèrement
        elif fg_value >= self.extreme_greed_threshold:
            modifier *= 0.7  # Réduire
        
        # News ajustement
        if news_sentiment.get('pause_events', 0) > 0:
            modifier *= 0.5  # Très prudent
        elif news_sentiment.get('bearish', 0) > news_sentiment.get('bullish', 0):
            modifier *= 0.8
        
        return round(min(1.5, max(0.5, modifier)), 2)
    
    def should_adjust_trading(self, direction: str) -> Tuple[bool, str, float]:
        """
        Détermine si le trading devrait être ajusté.
        
        Args:
            direction: 'LONG' ou 'SHORT'
            
        Returns:
            (should_trade, reason, score_modifier)
        """
        sentiment = self.get_market_sentiment()
        action = sentiment['trading_action']
        modifier = sentiment['combined_score_modifier']
        
        if action == 'PAUSE':
            return False, sentiment['reason'], 0
        
        if action == 'AVOID_LONG' and direction == 'LONG':
            return False, "Sentiment trop euphorique pour LONG", 0
        
        if action == 'FAVOR_LONG' and direction == 'SHORT':
            # Possible mais avec prudence
            return True, "Fear élevée, SHORT risqué", modifier - 10
        
        return True, "OK", modifier
    
    # ─────────────────────────────────────────────────────────────
    # UTILITAIRES
    # ─────────────────────────────────────────────────────────────
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Vérifie si le cache est encore valide."""
        cache_entry = self.cache.get(cache_key, {})
        updated = cache_entry.get('updated')
        
        if not updated:
            return False
        
        age = (datetime.now() - updated).total_seconds()
        return age < self.cache_duration


# ─────────────────────────────────────────────────────────────────
# INSTANCE GLOBALE
# ─────────────────────────────────────────────────────────────────

news_analyzer = NewsAnalyzer()


def get_market_sentiment() -> Dict:
    """Fonction utilitaire pour obtenir le sentiment marché."""
    return news_analyzer.get_market_sentiment()


def should_trade(direction: str) -> Tuple[bool, str, float]:
    """Vérifie si on devrait trader dans cette direction."""
    return news_analyzer.should_adjust_trading(direction)


def get_fear_greed() -> Dict:
    """Obtenir le Fear & Greed Index actuel."""
    return news_analyzer.get_fear_greed_index()
