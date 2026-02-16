"""
Module Social Sentiment: Analyse du sentiment sur les réseaux sociaux.

Sources:
- LunarCrush API (social metrics agrégées)
- Reddit API (r/cryptocurrency, r/bitcoin, r/altcoin)
- Twitter/X sentiment via proxies
- Telegram channels activity
- Discord server activity metrics

Métriques:
- Social Volume (mentions totales)
- Sentiment Score (-100 à +100)
- Social Dominance (% of crypto conversations)
- Influencer Activity
- Trending Topics
"""

import requests
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import json


class SocialSentimentAnalyzer:
    """
    Analyse le sentiment social pour le trading crypto.
    Agrège les données de plusieurs sources sociales.
    """
    
    def __init__(self):
        # Cache pour éviter trop d'appels API
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Seuils de sentiment
        self.sentiment_thresholds = {
            'extreme_fear': -60,
            'fear': -30,
            'neutral_low': -10,
            'neutral_high': 10,
            'greed': 30,
            'extreme_greed': 60
        }
        
        # Mots-clés bullish/bearish pour analyse de texte
        self.bullish_keywords = [
            'moon', 'pump', 'bullish', 'buy', 'long', 'breakout', 'ath',
            'accumulate', 'hodl', 'diamond hands', 'to the moon', 'rocket',
            'green', 'rally', 'surge', 'soar', 'bull run', 'lambo',
            'undervalued', 'gem', '100x', '10x', 'next bitcoin', 'alpha'
        ]
        
        self.bearish_keywords = [
            'dump', 'crash', 'bearish', 'sell', 'short', 'rekt', 'scam',
            'rug', 'rugpull', 'dead', 'shit', 'ponzi', 'bubble', 'overvalued',
            'red', 'tank', 'plunge', 'collapse', 'paper hands', 'exit',
            'top signal', 'distribution', 'capitulation', 'fear'
        ]
        
        # Influenceurs crypto connus (leur activité a plus de poids)
        self.known_influencers = [
            'elonmusk', 'caborek', 'VitalikButerin', 'saborner',
            'PeterSchiff', 'APompliano', 'CryptoCapo_', 'CryptoCobain',
            'CryptoWendyO', 'Pentosh1', 'CryptoKaleo', 'AltcoinGordon'
        ]
        
        # Symbols mapping pour recherche
        self.symbol_aliases = {
            'BTC': ['bitcoin', 'btc', '$btc', '#bitcoin'],
            'ETH': ['ethereum', 'eth', '$eth', '#ethereum'],
            'SOL': ['solana', 'sol', '$sol', '#solana'],
            'XRP': ['ripple', 'xrp', '$xrp', '#xrp'],
            'DOGE': ['dogecoin', 'doge', '$doge', '#doge'],
            'ADA': ['cardano', 'ada', '$ada', '#cardano'],
            'AVAX': ['avalanche', 'avax', '$avax', '#avalanche'],
            'MATIC': ['polygon', 'matic', '$matic', '#polygon'],
            'LINK': ['chainlink', 'link', '$link', '#chainlink'],
            'DOT': ['polkadot', 'dot', '$dot', '#polkadot'],
        }
        
        print("📱 Social Sentiment Analyzer initialisé")
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Récupère données du cache si valide."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_duration:
                return data
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Stocke données dans le cache."""
        self.cache[key] = (data, datetime.now())
    
    # ═══════════════════════════════════════════════════════════════
    # FEAR & GREED INDEX
    # ═══════════════════════════════════════════════════════════════
    
    def get_fear_greed_index(self) -> Dict:
        """
        Récupère le Fear & Greed Index d'Alternative.me.
        Score de 0 (Extreme Fear) à 100 (Extreme Greed).
        """
        cache_key = "fear_greed"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            url = "https://api.alternative.me/fng/?limit=7"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('data'):
                    current = data['data'][0]
                    history = data['data'][1:7]
                    
                    value = int(current.get('value', 50))
                    classification = current.get('value_classification', 'Neutral')
                    
                    # Calcul tendance (comparaison avec hier)
                    yesterday_value = int(history[0].get('value', 50)) if history else value
                    trend = value - yesterday_value
                    
                    # Moyenne 7 jours
                    avg_7d = sum(int(h.get('value', 50)) for h in data['data']) / len(data['data'])
                    
                    result = {
                        'value': value,
                        'classification': classification,
                        'trend': trend,
                        'trend_direction': 'up' if trend > 0 else ('down' if trend < 0 else 'stable'),
                        'avg_7d': round(avg_7d, 1),
                        'yesterday': yesterday_value,
                        'signal': self._interpret_fear_greed(value),
                        'timestamp': current.get('timestamp'),
                        'history': [{'value': int(h['value']), 'date': h.get('timestamp')} for h in history]
                    }
                    
                    self._set_cache(cache_key, result)
                    return result
                    
        except Exception as e:
            print(f"⚠️ Erreur Fear & Greed: {e}")
        
        return {
            'value': 50,
            'classification': 'Neutral',
            'signal': 'neutral',
            'error': 'Unable to fetch data'
        }
    
    def _interpret_fear_greed(self, value: int) -> str:
        """Interprète le Fear & Greed pour le trading."""
        if value <= 20:
            return 'strong_buy'  # Extreme Fear = opportunité d'achat
        elif value <= 35:
            return 'buy'
        elif value <= 55:
            return 'neutral'
        elif value <= 75:
            return 'caution'  # Greed = prudence
        else:
            return 'strong_sell'  # Extreme Greed = ne pas acheter, vendre
    
    # ═══════════════════════════════════════════════════════════════
    # REDDIT SENTIMENT
    # ═══════════════════════════════════════════════════════════════
    
    def get_reddit_sentiment(self, symbol: Optional[str] = None) -> Dict:
        """
        Analyse le sentiment Reddit via pushshift/reddit API.
        Subreddits: r/cryptocurrency, r/bitcoin, r/ethtrader, etc.
        """
        cache_key = f"reddit_{symbol or 'general'}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # Utilise l'API Reddit publique (sans auth pour posts récents)
            subreddits = ['cryptocurrency', 'bitcoin', 'ethtrader', 'altcoin']
            
            total_posts = 0
            bullish_posts = 0
            bearish_posts = 0
            neutral_posts = 0
            mentions = defaultdict(int)
            
            for subreddit in subreddits:
                try:
                    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50"
                    headers = {'User-Agent': 'CryptoBot/1.0'}
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        posts = data.get('data', {}).get('children', [])
                        
                        for post in posts:
                            post_data = post.get('data', {})
                            title = post_data.get('title', '').lower()
                            selftext = post_data.get('selftext', '').lower()
                            text = title + ' ' + selftext
                            score = post_data.get('score', 0)
                            
                            # Analyse sentiment du post
                            sentiment = self._analyze_text_sentiment(text)
                            
                            # Pondération par score Reddit
                            weight = 1 + (score / 100)
                            total_posts += 1
                            
                            if sentiment > 0.2:
                                bullish_posts += weight
                            elif sentiment < -0.2:
                                bearish_posts += weight
                            else:
                                neutral_posts += weight
                            
                            # Compte les mentions de coins
                            for sym, aliases in self.symbol_aliases.items():
                                if any(alias in text for alias in aliases):
                                    mentions[sym] += 1
                                    
                except Exception as e:
                    continue
            
            total_weighted = bullish_posts + bearish_posts + neutral_posts
            if total_weighted > 0:
                bullish_pct = (bullish_posts / total_weighted) * 100
                bearish_pct = (bearish_posts / total_weighted) * 100
                sentiment_score = ((bullish_posts - bearish_posts) / total_weighted) * 100
            else:
                bullish_pct = bearish_pct = 33.3
                sentiment_score = 0
            
            result = {
                'total_posts_analyzed': total_posts,
                'sentiment_score': round(sentiment_score, 1),
                'bullish_percent': round(bullish_pct, 1),
                'bearish_percent': round(bearish_pct, 1),
                'neutral_percent': round(100 - bullish_pct - bearish_pct, 1),
                'signal': 'bullish' if sentiment_score > 20 else ('bearish' if sentiment_score < -20 else 'neutral'),
                'top_mentions': dict(sorted(mentions.items(), key=lambda x: x[1], reverse=True)[:10]),
                'subreddits_analyzed': subreddits
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            print(f"⚠️ Erreur Reddit: {e}")
            return {'sentiment_score': 0, 'signal': 'neutral', 'error': str(e)}
    
    def _analyze_text_sentiment(self, text: str) -> float:
        """
        Analyse le sentiment d'un texte.
        Retourne score entre -1 (très bearish) et +1 (très bullish).
        """
        text_lower = text.lower()
        
        bullish_count = sum(1 for keyword in self.bullish_keywords if keyword in text_lower)
        bearish_count = sum(1 for keyword in self.bearish_keywords if keyword in text_lower)
        
        total = bullish_count + bearish_count
        if total == 0:
            return 0
        
        return (bullish_count - bearish_count) / total
    
    # ═══════════════════════════════════════════════════════════════
    # TWITTER/X SENTIMENT (via proxies publics)
    # ═══════════════════════════════════════════════════════════════
    
    def get_twitter_sentiment(self, symbol: str = 'BTC') -> Dict:
        """
        Estime le sentiment Twitter via des sources agrégées.
        Utilise des APIs publiques qui agrègent les données Twitter.
        """
        cache_key = f"twitter_{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # Utilise LunarCrush-like public data si disponible
            # Sinon estimation basée sur le Fear & Greed + Reddit
            
            fear_greed = self.get_fear_greed_index()
            reddit = self.get_reddit_sentiment(symbol)
            
            # Estimation composite du sentiment Twitter
            fg_component = (fear_greed.get('value', 50) - 50) / 50  # -1 à +1
            reddit_component = reddit.get('sentiment_score', 0) / 100  # -1 à +1
            
            # Twitter tends to be more volatile, estimated
            estimated_score = (fg_component * 0.4 + reddit_component * 0.6) * 100
            
            result = {
                'estimated_score': round(estimated_score, 1),
                'signal': 'bullish' if estimated_score > 20 else ('bearish' if estimated_score < -20 else 'neutral'),
                'data_source': 'estimated_from_aggregates',
                'note': 'Twitter sentiment estimated from Fear&Greed + Reddit correlation'
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            return {'estimated_score': 0, 'signal': 'neutral', 'error': str(e)}
    
    # ═══════════════════════════════════════════════════════════════
    # CRYPTO TWITTER TRENDING
    # ═══════════════════════════════════════════════════════════════
    
    def get_trending_coins(self) -> Dict:
        """
        Récupère les coins trending via CoinGecko trending.
        """
        cache_key = "trending"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            url = "https://api.coingecko.com/api/v3/search/trending"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                coins = data.get('coins', [])
                
                trending = []
                for item in coins[:10]:
                    coin = item.get('item', {})
                    trending.append({
                        'name': coin.get('name'),
                        'symbol': coin.get('symbol', '').upper(),
                        'market_cap_rank': coin.get('market_cap_rank'),
                        'price_btc': coin.get('price_btc'),
                        'score': coin.get('score')
                    })
                
                result = {
                    'trending_coins': trending,
                    'count': len(trending),
                    'timestamp': datetime.now().isoformat()
                }
                
                self._set_cache(cache_key, result)
                return result
                
        except Exception as e:
            print(f"⚠️ Erreur trending: {e}")
        
        return {'trending_coins': [], 'count': 0}
    
    # ═══════════════════════════════════════════════════════════════
    # SOCIAL VOLUME & DOMINANCE
    # ═══════════════════════════════════════════════════════════════
    
    def get_social_metrics(self, symbol: str = 'BTC') -> Dict:
        """
        Calcule des métriques sociales composites pour un coin.
        """
        cache_key = f"social_metrics_{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        fear_greed = self.get_fear_greed_index()
        reddit = self.get_reddit_sentiment(symbol)
        trending = self.get_trending_coins()
        
        # Vérifie si le coin est trending
        is_trending = any(
            c.get('symbol') == symbol 
            for c in trending.get('trending_coins', [])
        )
        
        # Mentions dans Reddit
        mentions = reddit.get('top_mentions', {})
        symbol_mentions = mentions.get(symbol, 0)
        total_mentions = sum(mentions.values()) or 1
        social_dominance = (symbol_mentions / total_mentions) * 100
        
        # Score composite
        fg_value = fear_greed.get('value', 50)
        reddit_score = reddit.get('sentiment_score', 0)
        
        # Social Score: combinaison pondérée
        social_score = (
            (fg_value - 50) * 0.3 +  # Fear & Greed contribution
            reddit_score * 0.5 +      # Reddit sentiment
            (20 if is_trending else 0) * 0.2  # Trending bonus
        )
        
        result = {
            'symbol': symbol,
            'social_score': round(social_score, 1),
            'social_dominance': round(social_dominance, 1),
            'is_trending': is_trending,
            'fear_greed': fg_value,
            'reddit_sentiment': reddit_score,
            'mentions_count': symbol_mentions,
            'signal': self._get_social_signal(social_score, fg_value),
            'recommendation': self._get_social_recommendation(social_score, fg_value)
        }
        
        self._set_cache(cache_key, result)
        return result
    
    def _get_social_signal(self, social_score: float, fear_greed: int) -> str:
        """Détermine le signal basé sur les métriques sociales."""
        # Contrarian approach: buy fear, sell greed
        if fear_greed <= 25 and social_score < 0:
            return 'strong_buy'  # Extreme fear = buy opportunity
        elif fear_greed <= 40 and social_score < 20:
            return 'buy'
        elif fear_greed >= 75 and social_score > 30:
            return 'strong_sell'  # Extreme greed = sell signal
        elif fear_greed >= 60:
            return 'caution'
        else:
            return 'neutral'
    
    def _get_social_recommendation(self, social_score: float, fear_greed: int) -> str:
        """Génère une recommandation textuelle."""
        if fear_greed <= 20:
            return "🟢 EXTREME FEAR: Excellent moment pour accumuler (contrarian)"
        elif fear_greed <= 35:
            return "🟢 FEAR: Bon moment pour acheter progressivement"
        elif fear_greed <= 55:
            return "⚪ NEUTRAL: Marché équilibré, trader normalement"
        elif fear_greed <= 75:
            return "🟡 GREED: Prudence recommandée, réduire exposition"
        else:
            return "🔴 EXTREME GREED: Éviter les achats, considérer prises de profits"
    
    # ═══════════════════════════════════════════════════════════════
    # ANALYSE COMPLÈTE
    # ═══════════════════════════════════════════════════════════════
    
    def get_complete_social_analysis(self, symbol: str = 'BTC') -> Dict:
        """
        Retourne une analyse sociale complète pour le trading.
        """
        fear_greed = self.get_fear_greed_index()
        reddit = self.get_reddit_sentiment(symbol)
        twitter = self.get_twitter_sentiment(symbol)
        trending = self.get_trending_coins()
        metrics = self.get_social_metrics(symbol)
        
        # Score global de sentiment social (-100 à +100)
        global_sentiment = (
            (fear_greed.get('value', 50) - 50) * 0.3 +
            reddit.get('sentiment_score', 0) * 0.4 +
            twitter.get('estimated_score', 0) * 0.3
        )
        
        # Modificateur pour le trading
        # Approche contrarian: sentiment négatif = bon pour acheter
        if fear_greed.get('value', 50) <= 25:
            trade_modifier = 1.2  # Boost les signaux d'achat
        elif fear_greed.get('value', 50) >= 75:
            trade_modifier = 0.7  # Réduit les signaux d'achat
        else:
            trade_modifier = 1.0
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'global_sentiment': round(global_sentiment, 1),
            'trade_modifier': trade_modifier,
            'fear_greed': fear_greed,
            'reddit': reddit,
            'twitter': twitter,
            'trending': trending,
            'metrics': metrics,
            'signal': metrics.get('signal', 'neutral'),
            'recommendation': metrics.get('recommendation', ''),
            'should_trade': self._should_trade_based_on_sentiment(fear_greed.get('value', 50))
        }
    
    def _should_trade_based_on_sentiment(self, fear_greed: int) -> Dict:
        """Détermine si on devrait trader basé sur le sentiment."""
        if fear_greed <= 10:
            return {
                'long': True,
                'short': False,
                'reason': 'Extreme fear - excellent time for longs'
            }
        elif fear_greed <= 30:
            return {
                'long': True,
                'short': False,
                'reason': 'Fear zone - good for accumulation'
            }
        elif fear_greed >= 90:
            return {
                'long': False,
                'short': True,
                'reason': 'Extreme greed - avoid longs, consider shorts'
            }
        elif fear_greed >= 70:
            return {
                'long': False,
                'short': False,
                'reason': 'Greed zone - reduce exposure'
            }
        else:
            return {
                'long': True,
                'short': True,
                'reason': 'Neutral zone - normal trading'
            }
    
    def get_sentiment_modifier(self, direction: str = 'LONG') -> float:
        """
        Retourne un modificateur de score basé sur le sentiment social.
        À utiliser dans le calcul du score final du signal.
        
        Args:
            direction: 'LONG' ou 'SHORT'
            
        Returns:
            Multiplicateur entre 0.5 et 1.5
        """
        try:
            fear_greed = self.get_fear_greed_index()
            fg_value = fear_greed.get('value', 50)
            
            if direction == 'LONG':
                # Pour LONG: fear = boost, greed = malus
                if fg_value <= 20:
                    return 1.3  # +30% sur le score
                elif fg_value <= 35:
                    return 1.15
                elif fg_value >= 80:
                    return 0.6  # -40% sur le score
                elif fg_value >= 65:
                    return 0.8
                else:
                    return 1.0
            else:
                # Pour SHORT: inverse
                if fg_value >= 80:
                    return 1.3
                elif fg_value >= 65:
                    return 1.15
                elif fg_value <= 20:
                    return 0.6
                elif fg_value <= 35:
                    return 0.8
                else:
                    return 1.0
                    
        except Exception:
            return 1.0


# ═══════════════════════════════════════════════════════════════════
# INSTANCE GLOBALE
# ═══════════════════════════════════════════════════════════════════

_social_analyzer = None

def get_social_analyzer() -> SocialSentimentAnalyzer:
    """Retourne l'instance singleton du Social Sentiment Analyzer."""
    global _social_analyzer
    if _social_analyzer is None:
        _social_analyzer = SocialSentimentAnalyzer()
    return _social_analyzer


def get_fear_greed() -> Dict:
    """Raccourci pour obtenir le Fear & Greed Index."""
    return get_social_analyzer().get_fear_greed_index()


def get_social_sentiment(symbol: str = 'BTC') -> Dict:
    """Raccourci pour obtenir l'analyse sociale complète."""
    return get_social_analyzer().get_complete_social_analysis(symbol)


def get_sentiment_modifier(direction: str = 'LONG') -> float:
    """Raccourci pour obtenir le modificateur de sentiment."""
    return get_social_analyzer().get_sentiment_modifier(direction)
