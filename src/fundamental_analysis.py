"""
Module d'Analyse Fondamentale pour Crypto Trading.
Évalue la valeur intrinsèque des cryptos au-delà de l'analyse technique.

Métriques analysées:
1. Tokenomics - Supply, inflation, distribution
2. Développement - Activité GitHub, commits, releases  
3. Adoption - Adresses actives, transactions, holders
4. DeFi/TVL - Total Value Locked pour écosystèmes DeFi
5. Partenariats & Écosystème
6. Équipe & Gouvernance
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json


class FundamentalAnalyzer:
    """
    Analyseur fondamental pour évaluer la valeur intrinsèque des cryptos.
    Utilise des APIs gratuites: CoinGecko, DefiLlama, GitHub.
    """
    
    def __init__(self):
        # APIs gratuites
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        self.defillama_url = "https://api.llama.fi"
        self.github_api_url = "https://api.github.com"
        
        # Cache pour éviter rate limiting
        self.cache = {}
        self.cache_duration = 600  # 10 minutes
        
        # Mapping des symboles vers CoinGecko IDs
        self.symbol_to_id = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin',
            'SOL': 'solana', 'XRP': 'ripple', 'ADA': 'cardano',
            'AVAX': 'avalanche-2', 'DOT': 'polkadot', 'MATIC': 'matic-network',
            'LINK': 'chainlink', 'ATOM': 'cosmos', 'UNI': 'uniswap',
            'LTC': 'litecoin', 'NEAR': 'near', 'APT': 'aptos',
            'ARB': 'arbitrum', 'OP': 'optimism', 'INJ': 'injective-protocol',
            'SUI': 'sui', 'SEI': 'sei-network', 'TIA': 'celestia',
            'DOGE': 'dogecoin', 'SHIB': 'shiba-inu', 'PEPE': 'pepe',
            'FET': 'fetch-ai', 'RNDR': 'render-token', 'AR': 'arweave',
            'FIL': 'filecoin', 'ICP': 'internet-computer', 'HBAR': 'hedera-hashgraph',
            'VET': 'vechain', 'ALGO': 'algorand', 'AAVE': 'aave',
            'MKR': 'maker', 'SNX': 'synthetix-network-token', 'CRV': 'curve-dao-token',
            'LDO': 'lido-dao', 'RPL': 'rocket-pool', 'GMX': 'gmx',
            'DYDX': 'dydx', 'STX': 'stacks', 'IMX': 'immutable-x',
            'SAND': 'the-sandbox', 'MANA': 'decentraland', 'AXS': 'axie-infinity',
            'GALA': 'gala', 'ENS': 'ethereum-name-service', 'APE': 'apecoin',
            'WLD': 'worldcoin-wld', 'BLUR': 'blur', 'JTO': 'jito-governance-token',
            'PYTH': 'pyth-network', 'JUP': 'jupiter-exchange-solana',
        }
        
        # GitHub repos des principaux projets
        self.github_repos = {
            'bitcoin': 'bitcoin/bitcoin',
            'ethereum': 'ethereum/go-ethereum',
            'solana': 'solana-labs/solana',
            'cardano': 'input-output-hk/cardano-node',
            'polkadot': 'paritytech/polkadot',
            'avalanche-2': 'ava-labs/avalanchego',
            'cosmos': 'cosmos/cosmos-sdk',
            'chainlink': 'smartcontractkit/chainlink',
            'uniswap': 'Uniswap/v3-core',
            'aave': 'aave/aave-v3-core',
            'arbitrum': 'OffchainLabs/arbitrum',
            'optimism': 'ethereum-optimism/optimism',
        }
        
        # Poids pour le score fondamental
        self.weights = {
            'market_cap_rank': 0.15,      # Position sur le marché
            'liquidity': 0.15,            # Liquidité et volume
            'tokenomics': 0.20,           # Supply, inflation
            'development': 0.15,          # Activité dev
            'adoption': 0.15,             # Utilisation réseau
            'defi_tvl': 0.10,             # TVL si applicable
            'community': 0.10,            # Taille communauté
        }
        
        print("📊 Fundamental Analyzer initialisé")
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        """Récupère une donnée du cache si valide."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_duration:
                return data
        return None
    
    def _set_cache(self, key: str, data: Dict):
        """Stocke une donnée dans le cache."""
        self.cache[key] = (data, time.time())
    
    def _extract_symbol(self, pair: str) -> str:
        """Extrait le symbole de la paire (ex: BTCUSDT -> BTC)."""
        pair = pair.upper()
        for suffix in ['USDT', 'BUSD', 'USD', 'USDC', 'BTC', 'ETH']:
            if pair.endswith(suffix):
                return pair[:-len(suffix)]
        return pair
    
    def _get_coingecko_id(self, symbol: str) -> Optional[str]:
        """Convertit un symbole en ID CoinGecko."""
        symbol = symbol.upper()
        return self.symbol_to_id.get(symbol)
    
    # ─────────────────────────────────────────────────────────────
    # DONNÉES DE MARCHÉ (CoinGecko)
    # ─────────────────────────────────────────────────────────────
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """
        Récupère les données de marché détaillées depuis CoinGecko.
        """
        coin_id = self._get_coingecko_id(symbol)
        if not coin_id:
            return None
        
        cache_key = f"market_{coin_id}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.coingecko_url}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'true',
                'developer_data': 'true',
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = self._parse_market_data(data)
                self._set_cache(cache_key, result)
                return result
            elif response.status_code == 429:
                # Rate limited, utiliser estimation
                return self._estimate_market_data(symbol)
                
        except Exception as e:
            print(f"⚠️ Erreur CoinGecko {symbol}: {e}")
        
        return self._estimate_market_data(symbol)
    
    def _parse_market_data(self, data: Dict) -> Dict:
        """Parse les données CoinGecko en format utilisable."""
        market = data.get('market_data', {})
        community = data.get('community_data', {})
        developer = data.get('developer_data', {})
        
        # Calcul du score de tokenomics
        circ_supply = market.get('circulating_supply', 0) or 0
        total_supply = market.get('total_supply', 0) or 0
        max_supply = market.get('max_supply')
        
        # Ratio circulation (plus c'est haut, mieux c'est - moins d'inflation future)
        if max_supply and max_supply > 0:
            circulation_ratio = (circ_supply / max_supply) * 100
        elif total_supply and total_supply > 0:
            circulation_ratio = (circ_supply / total_supply) * 100
        else:
            circulation_ratio = 100
        
        # Score d'inflation (basé sur le ratio)
        if circulation_ratio >= 90:
            inflation_score = 100  # Très peu d'inflation restante
        elif circulation_ratio >= 70:
            inflation_score = 80
        elif circulation_ratio >= 50:
            inflation_score = 60
        elif circulation_ratio >= 30:
            inflation_score = 40
        else:
            inflation_score = 20  # Beaucoup d'inflation potentielle
        
        return {
            'name': data.get('name'),
            'symbol': data.get('symbol', '').upper(),
            'market_cap_rank': data.get('market_cap_rank', 999),
            
            # Données de marché
            'market_cap_usd': market.get('market_cap', {}).get('usd', 0),
            'volume_24h_usd': market.get('total_volume', {}).get('usd', 0),
            'price_usd': market.get('current_price', {}).get('usd', 0),
            'price_change_24h': market.get('price_change_percentage_24h', 0),
            'price_change_7d': market.get('price_change_percentage_7d', 0),
            'price_change_30d': market.get('price_change_percentage_30d', 0),
            'ath_change_pct': market.get('ath_change_percentage', {}).get('usd', 0),
            
            # Tokenomics
            'circulating_supply': circ_supply,
            'total_supply': total_supply,
            'max_supply': max_supply,
            'circulation_ratio': circulation_ratio,
            'inflation_score': inflation_score,
            'fdv': market.get('fully_diluted_valuation', {}).get('usd', 0),
            'mcap_fdv_ratio': (market.get('market_cap', {}).get('usd', 0) / 
                              market.get('fully_diluted_valuation', {}).get('usd', 1)) * 100
                              if market.get('fully_diluted_valuation', {}).get('usd', 0) > 0 else 100,
            
            # Communauté
            'twitter_followers': community.get('twitter_followers', 0),
            'reddit_subscribers': community.get('reddit_subscribers', 0),
            'telegram_members': community.get('telegram_channel_user_count', 0),
            
            # Développement
            'github_commits_4w': developer.get('commit_count_4_weeks', 0),
            'github_stars': developer.get('stars', 0),
            'github_forks': developer.get('forks', 0),
            'github_contributors': developer.get('pull_request_contributors', 0),
            
            'last_updated': datetime.now().isoformat()
        }
    
    def _estimate_market_data(self, symbol: str) -> Dict:
        """Estimation des données si API indisponible."""
        # Données de base pour les principales cryptos
        base_scores = {
            'BTC': {'rank': 1, 'liquidity': 100, 'inflation': 95, 'dev': 90, 'adoption': 100},
            'ETH': {'rank': 2, 'liquidity': 100, 'inflation': 85, 'dev': 100, 'adoption': 95},
            'BNB': {'rank': 4, 'liquidity': 90, 'inflation': 80, 'dev': 70, 'adoption': 85},
            'SOL': {'rank': 5, 'liquidity': 85, 'inflation': 60, 'dev': 90, 'adoption': 80},
            'XRP': {'rank': 6, 'liquidity': 80, 'inflation': 70, 'dev': 50, 'adoption': 70},
            'ADA': {'rank': 8, 'liquidity': 70, 'inflation': 75, 'dev': 85, 'adoption': 60},
            'AVAX': {'rank': 10, 'liquidity': 75, 'inflation': 55, 'dev': 80, 'adoption': 70},
            'DOT': {'rank': 12, 'liquidity': 70, 'inflation': 50, 'dev': 85, 'adoption': 65},
            'LINK': {'rank': 14, 'liquidity': 75, 'inflation': 70, 'dev': 90, 'adoption': 80},
            'MATIC': {'rank': 15, 'liquidity': 75, 'inflation': 65, 'dev': 85, 'adoption': 75},
        }
        
        symbol = symbol.upper()
        if symbol in base_scores:
            scores = base_scores[symbol]
        else:
            # Valeurs par défaut pour tokens inconnus
            scores = {'rank': 100, 'liquidity': 50, 'inflation': 50, 'dev': 50, 'adoption': 50}
        
        return {
            'name': symbol,
            'symbol': symbol,
            'market_cap_rank': scores['rank'],
            'estimated': True,
            'inflation_score': scores['inflation'],
            'dev_score': scores['dev'],
            'adoption_score': scores['adoption'],
            'liquidity_score': scores['liquidity'],
        }
    
    # ─────────────────────────────────────────────────────────────
    # TVL & DEFI (DefiLlama)
    # ─────────────────────────────────────────────────────────────
    
    def get_tvl_data(self, protocol: Optional[str] = None, chain: Optional[str] = None) -> Dict:
        """
        Récupère les données TVL depuis DefiLlama.
        """
        cache_key = f"tvl_{protocol or chain or 'all'}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            if protocol:
                url = f"{self.defillama_url}/protocol/{protocol}"
            elif chain:
                url = f"{self.defillama_url}/v2/chains"
            else:
                url = f"{self.defillama_url}/protocols"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if protocol:
                    result = {
                        'name': data.get('name'),
                        'tvl': data.get('tvl', 0),
                        'tvl_change_1d': data.get('change_1d', 0),
                        'tvl_change_7d': data.get('change_7d', 0),
                        'category': data.get('category'),
                        'chains': data.get('chains', []),
                        'mcap_tvl_ratio': data.get('mcap', 0) / data.get('tvl', 1) if data.get('tvl', 0) > 0 else 0,
                    }
                else:
                    # Liste des protocoles
                    result = {'protocols': data[:50] if isinstance(data, list) else data}
                
                self._set_cache(cache_key, result)
                return result
                
        except Exception as e:
            print(f"⚠️ Erreur DefiLlama: {e}")
        
        return {'tvl': 0, 'error': True}
    
    def get_chain_tvl(self, symbol: str) -> Dict:
        """Récupère le TVL d'une chaîne spécifique."""
        chain_map = {
            'ETH': 'ethereum', 'BNB': 'bsc', 'SOL': 'solana',
            'AVAX': 'avalanche', 'MATIC': 'polygon', 'ARB': 'arbitrum',
            'OP': 'optimism', 'FTM': 'fantom', 'NEAR': 'near',
            'ATOM': 'cosmos', 'DOT': 'polkadot', 'ADA': 'cardano',
        }
        
        chain_name = chain_map.get(symbol.upper())
        if not chain_name:
            return {'tvl': 0, 'not_applicable': True}
        
        cache_key = f"chain_tvl_{chain_name}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.defillama_url}/v2/chains"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                chains = response.json()
                for chain in chains:
                    if chain.get('name', '').lower() == chain_name.lower():
                        result = {
                            'chain': chain_name,
                            'tvl': chain.get('tvl', 0),
                            'token_symbol': chain.get('tokenSymbol'),
                            'gecko_id': chain.get('gecko_id'),
                        }
                        self._set_cache(cache_key, result)
                        return result
                        
        except Exception as e:
            print(f"⚠️ Erreur Chain TVL: {e}")
        
        return {'tvl': 0, 'chain': chain_name}
    
    # ─────────────────────────────────────────────────────────────
    # DÉVELOPPEMENT (GitHub)
    # ─────────────────────────────────────────────────────────────
    
    def get_development_activity(self, symbol: str) -> Dict:
        """
        Analyse l'activité de développement via GitHub.
        """
        coin_id = self._get_coingecko_id(symbol)
        if not coin_id:
            return {'commits_30d': 0, 'no_coin_id': True}
        repo = self.github_repos.get(coin_id)
        
        if not repo:
            return {'commits_30d': 0, 'no_repo': True}
        
        cache_key = f"github_{repo}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # Commits récents
            since = (datetime.now() - timedelta(days=30)).isoformat()
            url = f"{self.github_api_url}/repos/{repo}/commits"
            params = {'since': since, 'per_page': 100}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                commits = response.json()
                
                # Stats du repo
                repo_url = f"{self.github_api_url}/repos/{repo}"
                repo_response = requests.get(repo_url, timeout=10)
                repo_data = repo_response.json() if repo_response.status_code == 200 else {}
                
                result = {
                    'repo': repo,
                    'commits_30d': len(commits),
                    'stars': repo_data.get('stargazers_count', 0),
                    'forks': repo_data.get('forks_count', 0),
                    'open_issues': repo_data.get('open_issues_count', 0),
                    'watchers': repo_data.get('watchers_count', 0),
                    'last_push': repo_data.get('pushed_at'),
                    'dev_score': self._calculate_dev_score(len(commits), repo_data),
                }
                
                self._set_cache(cache_key, result)
                return result
                
        except Exception as e:
            print(f"⚠️ Erreur GitHub {repo}: {e}")
        
        return {'commits_30d': 0, 'error': True}
    
    def _calculate_dev_score(self, commits: int, repo_data: Dict) -> int:
        """Calcule un score de développement 0-100."""
        score = 0
        
        # Commits (0-40 points)
        if commits >= 100:
            score += 40
        elif commits >= 50:
            score += 30
        elif commits >= 20:
            score += 20
        elif commits >= 5:
            score += 10
        
        # Stars (0-30 points)
        stars = repo_data.get('stargazers_count', 0)
        if stars >= 10000:
            score += 30
        elif stars >= 5000:
            score += 25
        elif stars >= 1000:
            score += 15
        elif stars >= 100:
            score += 10
        
        # Activité récente (0-30 points)
        last_push = repo_data.get('pushed_at')
        if last_push:
            try:
                push_date = datetime.fromisoformat(last_push.replace('Z', '+00:00'))
                days_since = (datetime.now(push_date.tzinfo) - push_date).days
                if days_since <= 1:
                    score += 30
                elif days_since <= 7:
                    score += 25
                elif days_since <= 30:
                    score += 15
                elif days_since <= 90:
                    score += 5
            except:
                pass
        
        return min(score, 100)
    
    # ─────────────────────────────────────────────────────────────
    # SCORE FONDAMENTAL GLOBAL
    # ─────────────────────────────────────────────────────────────
    
    def calculate_fundamental_score(self, pair: str) -> Dict:
        """
        Calcule un score fondamental global (0-100) pour une crypto.
        
        Returns:
            Dict avec score, composants, et recommandation
        """
        symbol = self._extract_symbol(pair)
        
        # Récupérer toutes les données
        market_data = self.get_market_data(symbol)
        tvl_data = self.get_chain_tvl(symbol)
        dev_data = self.get_development_activity(symbol)
        
        if not market_data:
            return {
                'score': 50,  # Score neutre par défaut
                'symbol': symbol,
                'error': 'Données non disponibles',
                'recommendation': 'NEUTRAL'
            }
        
        components = {}
        
        # 1. Score de rang marché (0-100)
        rank = market_data.get('market_cap_rank', 999)
        if rank <= 10:
            components['market_position'] = 100
        elif rank <= 25:
            components['market_position'] = 85
        elif rank <= 50:
            components['market_position'] = 70
        elif rank <= 100:
            components['market_position'] = 55
        elif rank <= 200:
            components['market_position'] = 40
        else:
            components['market_position'] = 25
        
        # 2. Score liquidité (volume/mcap ratio)
        volume = market_data.get('volume_24h_usd', 0)
        mcap = market_data.get('market_cap_usd', 1)
        vol_mcap_ratio = (volume / mcap) * 100 if mcap > 0 else 0
        
        if vol_mcap_ratio >= 20:
            components['liquidity'] = 100
        elif vol_mcap_ratio >= 10:
            components['liquidity'] = 80
        elif vol_mcap_ratio >= 5:
            components['liquidity'] = 60
        elif vol_mcap_ratio >= 2:
            components['liquidity'] = 40
        else:
            components['liquidity'] = 20
        
        # 3. Score tokenomics
        components['tokenomics'] = market_data.get('inflation_score', 50)
        
        # Bonus si mcap/fdv ratio élevé (moins de dilution future)
        mcap_fdv = market_data.get('mcap_fdv_ratio', 100)
        if mcap_fdv >= 90:
            components['tokenomics'] = min(100, components['tokenomics'] + 10)
        elif mcap_fdv < 50:
            components['tokenomics'] = max(0, components['tokenomics'] - 15)
        
        # 4. Score développement
        if market_data.get('estimated'):
            components['development'] = market_data.get('dev_score', 50)
        else:
            commits_4w = market_data.get('github_commits_4w', 0)
            stars = market_data.get('github_stars', 0)
            
            dev_score = 0
            if commits_4w >= 50:
                dev_score += 50
            elif commits_4w >= 20:
                dev_score += 35
            elif commits_4w >= 5:
                dev_score += 20
            
            if stars >= 5000:
                dev_score += 50
            elif stars >= 1000:
                dev_score += 35
            elif stars >= 100:
                dev_score += 20
            
            components['development'] = min(dev_score, 100)
        
        # 5. Score adoption (basé sur communauté + prix performance)
        twitter = market_data.get('twitter_followers', 0)
        reddit = market_data.get('reddit_subscribers', 0)
        
        community_score = 0
        if twitter >= 1000000:
            community_score += 50
        elif twitter >= 500000:
            community_score += 40
        elif twitter >= 100000:
            community_score += 25
        
        if reddit >= 100000:
            community_score += 50
        elif reddit >= 50000:
            community_score += 35
        elif reddit >= 10000:
            community_score += 20
        
        components['adoption'] = min(community_score, 100) if community_score > 0 else 50
        
        # 6. Score TVL/DeFi (si applicable)
        tvl = tvl_data.get('tvl', 0)
        if tvl_data.get('not_applicable'):
            components['defi_tvl'] = 50  # Neutre si pas applicable
        elif tvl >= 10_000_000_000:  # 10B+
            components['defi_tvl'] = 100
        elif tvl >= 1_000_000_000:   # 1B+
            components['defi_tvl'] = 85
        elif tvl >= 100_000_000:     # 100M+
            components['defi_tvl'] = 70
        elif tvl >= 10_000_000:      # 10M+
            components['defi_tvl'] = 50
        else:
            components['defi_tvl'] = 30
        
        # 7. Score communauté global
        components['community'] = components['adoption']  # Réutiliser
        
        # Calcul du score pondéré
        final_score = 0
        for key, weight in self.weights.items():
            component_score = components.get(key, 50)
            final_score += component_score * weight
        
        final_score = round(final_score, 1)
        
        # Recommandation basée sur le score
        if final_score >= 80:
            recommendation = 'STRONG_BUY'
            signal_modifier = 15
        elif final_score >= 65:
            recommendation = 'BUY'
            signal_modifier = 10
        elif final_score >= 50:
            recommendation = 'NEUTRAL'
            signal_modifier = 0
        elif final_score >= 35:
            recommendation = 'CAUTION'
            signal_modifier = -10
        else:
            recommendation = 'AVOID'
            signal_modifier = -20
        
        return {
            'symbol': symbol,
            'score': final_score,
            'components': components,
            'recommendation': recommendation,
            'signal_modifier': signal_modifier,
            'market_cap_rank': rank,
            'price_change_30d': market_data.get('price_change_30d', 0),
            'tvl': tvl_data.get('tvl', 0),
            'circulation_ratio': market_data.get('circulation_ratio', 0),
            'summary': self._generate_summary(final_score, components, recommendation),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_summary(self, score: float, components: Dict, recommendation: str) -> str:
        """Génère un résumé textuel de l'analyse."""
        strengths = []
        weaknesses = []
        
        for key, value in components.items():
            name_map = {
                'market_position': 'Position marché',
                'liquidity': 'Liquidité',
                'tokenomics': 'Tokenomics',
                'development': 'Développement',
                'adoption': 'Adoption',
                'defi_tvl': 'TVL DeFi',
                'community': 'Communauté'
            }
            name = name_map.get(key, key)
            
            if value >= 70:
                strengths.append(f"{name} ({value})")
            elif value <= 40:
                weaknesses.append(f"{name} ({value})")
        
        summary = f"Score: {score}/100 | "
        if strengths:
            summary += f"Forces: {', '.join(strengths[:3])} | "
        if weaknesses:
            summary += f"Faiblesses: {', '.join(weaknesses[:2])}"
        
        return summary.strip(' |')
    
    # ─────────────────────────────────────────────────────────────
    # FILTRAGE PAR FONDAMENTAUX
    # ─────────────────────────────────────────────────────────────
    
    def should_trade_fundamentally(self, pair: str, direction: str = 'LONG') -> Tuple[bool, int, str]:
        """
        Détermine si un trade est valide du point de vue fondamental.
        
        Returns:
            (can_trade, score_modifier, reason)
        """
        analysis = self.calculate_fundamental_score(pair)
        score = analysis['score']
        recommendation = analysis['recommendation']
        
        # Règles de filtrage
        if recommendation == 'AVOID':
            return False, -25, f"Fondamentaux faibles ({score}/100)"
        
        if direction == 'LONG':
            if recommendation in ['STRONG_BUY', 'BUY']:
                return True, analysis['signal_modifier'], f"Fondamentaux solides ({score}/100)"
            elif recommendation == 'NEUTRAL':
                return True, 0, f"Fondamentaux neutres ({score}/100)"
            else:  # CAUTION
                return True, -5, f"Prudence fondamentale ({score}/100)"
        
        else:  # SHORT
            # Pour SHORT, on veut des fondamentaux faibles
            if recommendation in ['CAUTION', 'AVOID']:
                return True, 5, f"Fondamentaux faibles favorisent SHORT ({score}/100)"
            elif recommendation == 'NEUTRAL':
                return True, 0, f"Fondamentaux neutres ({score}/100)"
            else:
                # SHORT sur fundamentals forts = risqué
                return True, -10, f"Attention: fondamentaux forts ({score}/100)"
    
    def get_top_fundamental_picks(self, pairs: List[str], limit: int = 10) -> List[Dict]:
        """
        Analyse une liste de paires et retourne les meilleures fondamentalement.
        """
        results = []
        
        for pair in pairs:
            try:
                analysis = self.calculate_fundamental_score(pair)
                results.append(analysis)
            except Exception as e:
                print(f"⚠️ Erreur analyse {pair}: {e}")
        
        # Trier par score décroissant
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return results[:limit]


# ─────────────────────────────────────────────────────────────
# INSTANCE GLOBALE & FONCTIONS HELPER
# ─────────────────────────────────────────────────────────────

fundamental_analyzer = FundamentalAnalyzer()

def get_fundamental_score(pair: str) -> Dict:
    """Raccourci pour obtenir le score fondamental d'une paire."""
    return fundamental_analyzer.calculate_fundamental_score(pair)

def should_trade_fundamentally(pair: str, direction: str = 'LONG') -> Tuple[bool, int, str]:
    """Raccourci pour vérifier si un trade est valide fondamentalement."""
    return fundamental_analyzer.should_trade_fundamentally(pair, direction)

def get_fundamental_modifier(pair: str, direction: str = 'LONG') -> int:
    """Retourne le modificateur de score basé sur les fondamentaux."""
    can_trade, modifier, reason = fundamental_analyzer.should_trade_fundamentally(pair, direction)
    return modifier if can_trade else -25
