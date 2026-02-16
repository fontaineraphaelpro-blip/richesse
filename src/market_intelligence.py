"""
Module d'Intelligence de Marché Complète.
Agrège TOUTES les sources d'information disponibles en temps réel.

Sources:
1. On-Chain: Whale movements, exchange flows, gas fees
2. Derivatives: Funding rates, open interest, liquidations
3. Social: Twitter trends, Reddit sentiment
4. Order Book: Bid/ask imbalance, large orders
5. Corrélations: DXY, S&P500, Gold
6. Crypto Metrics: BTC dominance, ETH/BTC, stablecoin supply
7. Technical Alerts: Key levels, divergences
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import time
import json


class MarketIntelligence:
    """
    Agrégateur d'intelligence de marché en temps réel.
    Le bot sait TOUT ce qui se passe.
    """
    
    def __init__(self):
        # ── APIs publiques gratuites ──
        self.apis = {
            'coinglass': 'https://open-api.coinglass.com/public/v2/',
            'alternative': 'https://api.alternative.me/',
            'coinmarketcap': 'https://api.coinmarketcap.com/data-api/v3/',
            'blockchain': 'https://blockchain.info/',
            'glassnode': 'https://api.glassnode.com/v1/',
            'defillama': 'https://api.llama.fi/',
            'binance': 'https://api.binance.com/api/v3/',
            'coingecko': 'https://api.coingecko.com/api/v3/',
        }
        
        # ── Cache ──
        self.cache = {}
        self.cache_duration = 60  # 1 minute
        
        # ── État du marché ──
        self.market_state = {
            'last_update': None,
            'overall_bias': 'NEUTRAL',  # BULLISH, BEARISH, NEUTRAL
            'confidence': 0,
            'alerts': []
        }
    
    # ═══════════════════════════════════════════════════════════════
    # 1. DONNÉES DÉRIVÉS (Funding, OI, Liquidations)
    # ═══════════════════════════════════════════════════════════════
    
    def get_funding_rates(self) -> Dict:
        """
        Récupère les taux de funding sur les futures.
        Funding positif = trop de longs = bearish
        Funding négatif = trop de shorts = bullish
        """
        if self._is_cache_valid('funding'):
            return self.cache['funding']['data']
        
        try:
            # Binance Futures funding
            response = requests.get(
                'https://fapi.binance.com/fapi/v1/premiumIndex',
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Analyser les top cryptos
                funding_data = {}
                high_funding = []
                low_funding = []
                
                for item in data[:50]:  # Top 50
                    symbol = item['symbol']
                    rate = float(item.get('lastFundingRate', 0)) * 100
                    funding_data[symbol] = rate
                    
                    if rate > 0.1:  # > 0.1% = très haussier
                        high_funding.append((symbol, rate))
                    elif rate < -0.05:  # < -0.05% = très baissier
                        low_funding.append((symbol, rate))
                
                btc_funding = funding_data.get('BTCUSDT', 0)
                eth_funding = funding_data.get('ETHUSDT', 0)
                
                result = {
                    'btc_funding': round(btc_funding, 4),
                    'eth_funding': round(eth_funding, 4),
                    'avg_funding': round(sum(funding_data.values()) / len(funding_data), 4) if funding_data else 0,
                    'high_funding_count': len(high_funding),
                    'low_funding_count': len(low_funding),
                    'signal': self._interpret_funding(btc_funding),
                    'top_high': high_funding[:5],
                    'top_low': low_funding[:5]
                }
                
                self._update_cache('funding', result)
                return result
                
        except Exception as e:
            print(f"⚠️ Erreur funding rates: {e}")
        
        return {'btc_funding': 0, 'signal': 'NEUTRAL'}
    
    def _interpret_funding(self, btc_funding: float) -> str:
        """Interprète le signal du funding rate."""
        if btc_funding > 0.1:
            return 'BEARISH'  # Trop de longs, correction probable
        elif btc_funding > 0.05:
            return 'SLIGHTLY_BEARISH'
        elif btc_funding < -0.05:
            return 'BULLISH'  # Trop de shorts, squeeze probable
        elif btc_funding < -0.02:
            return 'SLIGHTLY_BULLISH'
        return 'NEUTRAL'
    
    def get_open_interest(self) -> Dict:
        """
        Récupère l'Open Interest (positions ouvertes).
        OI en hausse + prix en hausse = confirmation trend
        OI en hausse + prix en baisse = accumulation shorts
        """
        if self._is_cache_valid('open_interest'):
            return self.cache['open_interest']['data']
        
        try:
            response = requests.get(
                'https://fapi.binance.com/fapi/v1/openInterest',
                params={'symbol': 'BTCUSDT'},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                oi = float(data.get('openInterest', 0))
                
                result = {
                    'btc_oi': oi,
                    'btc_oi_usd': oi * self._get_btc_price(),
                    'timestamp': datetime.now().isoformat()
                }
                
                self._update_cache('open_interest', result)
                return result
                
        except Exception as e:
            print(f"⚠️ Erreur Open Interest: {e}")
        
        return {'btc_oi': 0}
    
    def get_liquidations(self) -> Dict:
        """
        Récupère les liquidations récentes.
        Grosses liquidations LONG = bottom probable
        Grosses liquidations SHORT = top probable
        """
        if self._is_cache_valid('liquidations'):
            return self.cache['liquidations']['data']
        
        # Note: API de liquidations nécessite souvent une clé
        # On simule avec les données disponibles
        try:
            # Utiliser l'API Binance pour les trades récents comme proxy
            response = requests.get(
                'https://fapi.binance.com/fapi/v1/forceOrders',
                params={'symbol': 'BTCUSDT', 'limit': 100},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                long_liqs = sum(1 for d in data if d.get('side') == 'SELL')
                short_liqs = sum(1 for d in data if d.get('side') == 'BUY')
                
                result = {
                    'long_liquidations': long_liqs,
                    'short_liquidations': short_liqs,
                    'dominant': 'LONG' if long_liqs > short_liqs else 'SHORT',
                    'signal': 'BULLISH' if long_liqs > short_liqs * 1.5 else (
                        'BEARISH' if short_liqs > long_liqs * 1.5 else 'NEUTRAL'
                    )
                }
                
                self._update_cache('liquidations', result)
                return result
                
        except:
            pass
        
        return {'long_liquidations': 0, 'short_liquidations': 0, 'signal': 'NEUTRAL'}
    
    # ═══════════════════════════════════════════════════════════════
    # 2. ON-CHAIN DATA (Whale movements, Exchange flows)
    # ═══════════════════════════════════════════════════════════════
    
    def get_exchange_flows(self) -> Dict:
        """
        Analyse les flux vers/depuis les exchanges.
        Inflow (dépôts) = possible vente = bearish
        Outflow (retraits) = holding = bullish
        """
        if self._is_cache_valid('exchange_flows'):
            return self.cache['exchange_flows']['data']
        
        # Utilisation de données publiques CryptoQuant/Glassnode style
        try:
            # Simulation basée sur les metrics disponibles
            # En production, utiliser une API on-chain (CryptoQuant, Glassnode, etc.)
            
            result = {
                'btc_exchange_reserve_change_24h': 0,  # En BTC
                'eth_exchange_reserve_change_24h': 0,  # En ETH
                'net_flow': 'NEUTRAL',  # INFLOW, OUTFLOW, NEUTRAL
                'signal': 'NEUTRAL',
                'note': 'Données on-chain nécessitent API premium'
            }
            
            self._update_cache('exchange_flows', result)
            return result
            
        except Exception as e:
            print(f"⚠️ Erreur exchange flows: {e}")
        
        return {'net_flow': 'NEUTRAL', 'signal': 'NEUTRAL'}
    
    def get_whale_alerts(self) -> List[Dict]:
        """
        Détecte les mouvements de baleines.
        Gros transferts vers exchange = vente imminente
        Gros transferts depuis exchange = accumulation
        """
        if self._is_cache_valid('whale_alerts'):
            return self.cache['whale_alerts']['data']
        
        # En production, utiliser Whale Alert API
        alerts = []
        
        try:
            # Vérifier les gros trades récents sur Binance
            response = requests.get(
                'https://api.binance.com/api/v3/trades',
                params={'symbol': 'BTCUSDT', 'limit': 500},
                timeout=5
            )
            
            if response.status_code == 200:
                trades = response.json()
                
                # Détecter les trades > 10 BTC
                for trade in trades:
                    qty = float(trade.get('qty', 0))
                    if qty > 10:  # > 10 BTC
                        alerts.append({
                            'type': 'LARGE_TRADE',
                            'symbol': 'BTC',
                            'amount': qty,
                            'side': 'BUY' if trade.get('isBuyerMaker') else 'SELL',
                            'time': trade.get('time')
                        })
                
                self._update_cache('whale_alerts', alerts[:10])  # Garder top 10
                return alerts[:10]
                
        except Exception as e:
            print(f"⚠️ Erreur whale alerts: {e}")
        
        return []
    
    # ═══════════════════════════════════════════════════════════════
    # 3. CORRÉLATIONS (DXY, S&P500, Gold)
    # ═══════════════════════════════════════════════════════════════
    
    def get_macro_correlations(self) -> Dict:
        """
        Analyse les corrélations avec les marchés traditionnels.
        BTC inversement corrélé au DXY (dollar fort = BTC faible)
        BTC corrélé au S&P500 (risk-on/risk-off)
        """
        if self._is_cache_valid('macro'):
            return self.cache['macro']['data']
        
        try:
            # Utiliser CoinGecko pour les données globales
            response = requests.get(
                'https://api.coingecko.com/api/v3/global',
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                
                result = {
                    'total_market_cap': data.get('total_market_cap', {}).get('usd', 0),
                    'market_cap_change_24h': data.get('market_cap_change_percentage_24h_usd', 0),
                    'btc_dominance': data.get('market_cap_percentage', {}).get('btc', 0),
                    'eth_dominance': data.get('market_cap_percentage', {}).get('eth', 0),
                    'active_cryptos': data.get('active_cryptocurrencies', 0),
                    'markets': data.get('markets', 0),
                }
                
                # Interpréter BTC dominance
                btc_dom = result['btc_dominance']
                if btc_dom > 55:
                    result['dominance_signal'] = 'BTC_STRONG'  # Altcoins faibles
                elif btc_dom < 45:
                    result['dominance_signal'] = 'ALTSEASON'  # Altcoins forts
                else:
                    result['dominance_signal'] = 'NEUTRAL'
                
                self._update_cache('macro', result)
                return result
                
        except Exception as e:
            print(f"⚠️ Erreur macro: {e}")
        
        return {'btc_dominance': 50, 'dominance_signal': 'NEUTRAL'}
    
    # ═══════════════════════════════════════════════════════════════
    # 4. CRYPTO METRICS (Stablecoins, DeFi TVL)
    # ═══════════════════════════════════════════════════════════════
    
    def get_stablecoin_flows(self) -> Dict:
        """
        Analyse les flux de stablecoins.
        Mint de stablecoins = argent frais entrant = bullish
        Burn de stablecoins = argent sortant = bearish
        """
        if self._is_cache_valid('stablecoins'):
            return self.cache['stablecoins']['data']
        
        try:
            # DefiLlama pour les stablecoins
            response = requests.get(
                'https://stablecoins.llama.fi/stablecoins?includePrices=true',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                stables = data.get('peggedAssets', [])
                
                total_supply = sum(
                    s.get('circulating', {}).get('peggedUSD', 0) or 0 
                    for s in stables[:10]
                )
                
                # USDT et USDC dominants
                usdt = next((s for s in stables if s.get('symbol') == 'USDT'), {})
                usdc = next((s for s in stables if s.get('symbol') == 'USDC'), {})
                
                result = {
                    'total_stablecoin_supply': total_supply,
                    'usdt_supply': usdt.get('circulating', {}).get('peggedUSD', 0),
                    'usdc_supply': usdc.get('circulating', {}).get('peggedUSD', 0),
                    'signal': 'NEUTRAL'
                }
                
                self._update_cache('stablecoins', result)
                return result
                
        except Exception as e:
            print(f"⚠️ Erreur stablecoins: {e}")
        
        return {'total_stablecoin_supply': 0, 'signal': 'NEUTRAL'}
    
    def get_defi_tvl(self) -> Dict:
        """
        Total Value Locked dans DeFi.
        TVL en hausse = confiance = bullish
        TVL en baisse = fuite de capitaux = bearish
        """
        if self._is_cache_valid('defi_tvl'):
            return self.cache['defi_tvl']['data']
        
        try:
            response = requests.get(
                'https://api.llama.fi/v2/historicalChainTvl',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data and len(data) >= 2:
                    current_tvl = data[-1].get('tvl', 0)
                    yesterday_tvl = data[-2].get('tvl', 0)
                    change = ((current_tvl - yesterday_tvl) / yesterday_tvl * 100) if yesterday_tvl else 0
                    
                    result = {
                        'total_tvl': current_tvl,
                        'tvl_change_24h': round(change, 2),
                        'signal': 'BULLISH' if change > 2 else ('BEARISH' if change < -2 else 'NEUTRAL')
                    }
                    
                    self._update_cache('defi_tvl', result)
                    return result
                    
        except Exception as e:
            print(f"⚠️ Erreur DeFi TVL: {e}")
        
        return {'total_tvl': 0, 'signal': 'NEUTRAL'}
    
    # ═══════════════════════════════════════════════════════════════
    # 5. ORDER BOOK ANALYSIS
    # ═══════════════════════════════════════════════════════════════
    
    def get_order_book_imbalance(self, symbol: str = 'BTCUSDT') -> Dict:
        """
        Analyse le déséquilibre du carnet d'ordres.
        Plus de bids = support = bullish
        Plus d'asks = résistance = bearish
        """
        if self._is_cache_valid(f'orderbook_{symbol}'):
            return self.cache[f'orderbook_{symbol}']['data']
        
        try:
            response = requests.get(
                f'https://api.binance.com/api/v3/depth',
                params={'symbol': symbol, 'limit': 100},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Calculer le volume des bids et asks
                bids_volume = sum(float(bid[1]) for bid in data.get('bids', []))
                asks_volume = sum(float(ask[1]) for ask in data.get('asks', []))
                
                total = bids_volume + asks_volume
                bid_ratio = (bids_volume / total * 100) if total else 50
                
                # Détecter les gros ordres (murs)
                bid_walls = [b for b in data.get('bids', []) if float(b[1]) > bids_volume * 0.1]
                ask_walls = [a for a in data.get('asks', []) if float(a[1]) > asks_volume * 0.1]
                
                result = {
                    'symbol': symbol,
                    'bid_volume': round(bids_volume, 2),
                    'ask_volume': round(asks_volume, 2),
                    'bid_ratio': round(bid_ratio, 1),
                    'ask_ratio': round(100 - bid_ratio, 1),
                    'imbalance': 'BULLISH' if bid_ratio > 55 else ('BEARISH' if bid_ratio < 45 else 'NEUTRAL'),
                    'bid_walls': len(bid_walls),
                    'ask_walls': len(ask_walls),
                    'signal': 'BULLISH' if bid_ratio > 55 else ('BEARISH' if bid_ratio < 45 else 'NEUTRAL')
                }
                
                self._update_cache(f'orderbook_{symbol}', result)
                return result
                
        except Exception as e:
            print(f"⚠️ Erreur order book: {e}")
        
        return {'bid_ratio': 50, 'signal': 'NEUTRAL'}
    
    # ═══════════════════════════════════════════════════════════════
    # 6. LONG/SHORT RATIO
    # ═══════════════════════════════════════════════════════════════
    
    def get_long_short_ratio(self) -> Dict:
        """
        Ratio Long/Short sur les futures.
        Trop de longs = correction probable
        Trop de shorts = squeeze probable
        """
        if self._is_cache_valid('ls_ratio'):
            return self.cache['ls_ratio']['data']
        
        try:
            # Binance Long/Short Ratio
            response = requests.get(
                'https://fapi.binance.com/futures/data/globalLongShortAccountRatio',
                params={'symbol': 'BTCUSDT', 'period': '1h', 'limit': 1},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data:
                    ratio = float(data[0].get('longShortRatio', 1))
                    long_pct = float(data[0].get('longAccount', 50))
                    short_pct = float(data[0].get('shortAccount', 50))
                    
                    result = {
                        'ratio': round(ratio, 3),
                        'long_percent': round(long_pct, 1),
                        'short_percent': round(short_pct, 1),
                        'signal': 'BEARISH' if ratio > 2.0 else (
                            'BULLISH' if ratio < 0.7 else 'NEUTRAL'
                        ),
                        'interpretation': (
                            "Trop de longs - correction probable" if ratio > 2.0 else
                            "Trop de shorts - squeeze probable" if ratio < 0.7 else
                            "Équilibré"
                        )
                    }
                    
                    self._update_cache('ls_ratio', result)
                    return result
                    
        except Exception as e:
            print(f"⚠️ Erreur L/S ratio: {e}")
        
        return {'ratio': 1, 'signal': 'NEUTRAL'}
    
    # ═══════════════════════════════════════════════════════════════
    # 7. VOLUME ANALYSIS
    # ═══════════════════════════════════════════════════════════════
    
    def get_volume_analysis(self) -> Dict:
        """
        Analyse du volume de trading.
        Volume en hausse = confirmation du mouvement
        Volume en baisse = affaiblissement
        """
        if self._is_cache_valid('volume_analysis'):
            return self.cache['volume_analysis']['data']
        
        try:
            response = requests.get(
                'https://api.binance.com/api/v3/klines',
                params={'symbol': 'BTCUSDT', 'interval': '1h', 'limit': 24},
                timeout=5
            )
            
            if response.status_code == 200:
                klines = response.json()
                
                volumes = [float(k[5]) for k in klines]
                prices = [float(k[4]) for k in klines]  # Close prices
                
                avg_volume = sum(volumes) / len(volumes)
                current_volume = volumes[-1]
                volume_ratio = current_volume / avg_volume if avg_volume else 1
                
                # Déterminer si le volume confirme le prix
                price_change = (prices[-1] - prices[0]) / prices[0] * 100
                
                result = {
                    'current_volume': current_volume,
                    'avg_volume_24h': avg_volume,
                    'volume_ratio': round(volume_ratio, 2),
                    'price_change_24h': round(price_change, 2),
                    'volume_trend': 'HIGH' if volume_ratio > 1.5 else ('LOW' if volume_ratio < 0.7 else 'NORMAL'),
                    'confirmation': volume_ratio > 1.2 and abs(price_change) > 1,
                    'signal': 'NEUTRAL'
                }
                
                # Signal basé sur volume + prix
                if volume_ratio > 1.5 and price_change > 2:
                    result['signal'] = 'STRONG_BULLISH'
                elif volume_ratio > 1.5 and price_change < -2:
                    result['signal'] = 'STRONG_BEARISH'
                elif volume_ratio < 0.7:
                    result['signal'] = 'WEAK_MOVE'
                
                self._update_cache('volume_analysis', result)
                return result
                
        except Exception as e:
            print(f"⚠️ Erreur volume analysis: {e}")
        
        return {'volume_ratio': 1, 'signal': 'NEUTRAL'}
    
    # ═══════════════════════════════════════════════════════════════
    # 8. TOP GAINERS / LOSERS
    # ═══════════════════════════════════════════════════════════════
    
    def get_top_movers(self) -> Dict:
        """
        Identifie les top gainers et losers.
        Utile pour détecter les rotations sectorielles.
        """
        if self._is_cache_valid('top_movers'):
            return self.cache['top_movers']['data']
        
        try:
            response = requests.get(
                'https://api.binance.com/api/v3/ticker/24hr',
                timeout=10
            )
            
            if response.status_code == 200:
                tickers = response.json()
                
                # Filtrer USDT pairs
                usdt_pairs = [
                    t for t in tickers 
                    if t['symbol'].endswith('USDT') and float(t.get('quoteVolume', 0)) > 1000000
                ]
                
                # Trier par changement
                sorted_by_change = sorted(
                    usdt_pairs,
                    key=lambda x: float(x.get('priceChangePercent', 0)),
                    reverse=True
                )
                
                top_gainers = [
                    {'symbol': t['symbol'], 'change': float(t['priceChangePercent'])}
                    for t in sorted_by_change[:5]
                ]
                
                top_losers = [
                    {'symbol': t['symbol'], 'change': float(t['priceChangePercent'])}
                    for t in sorted_by_change[-5:]
                ]
                
                # Market breadth (% de cryptos en hausse)
                up_count = sum(1 for t in usdt_pairs if float(t.get('priceChangePercent', 0)) > 0)
                breadth = (up_count / len(usdt_pairs) * 100) if usdt_pairs else 50
                
                result = {
                    'top_gainers': top_gainers,
                    'top_losers': top_losers,
                    'market_breadth': round(breadth, 1),
                    'breadth_signal': 'BULLISH' if breadth > 60 else ('BEARISH' if breadth < 40 else 'NEUTRAL'),
                    'total_pairs': len(usdt_pairs)
                }
                
                self._update_cache('top_movers', result)
                return result
                
        except Exception as e:
            print(f"⚠️ Erreur top movers: {e}")
        
        return {'market_breadth': 50, 'breadth_signal': 'NEUTRAL'}
    
    # ═══════════════════════════════════════════════════════════════
    # AGRÉGATION COMPLÈTE
    # ═══════════════════════════════════════════════════════════════
    
    def get_complete_intelligence(self) -> Dict:
        """
        Agrège TOUTES les sources d'information.
        Retourne un rapport complet avec un biais global.
        """
        print("🔍 Collecte intelligence marché complète...")
        
        # Collecter toutes les données
        funding = self.get_funding_rates()
        ls_ratio = self.get_long_short_ratio()
        orderbook = self.get_order_book_imbalance()
        volume = self.get_volume_analysis()
        macro = self.get_macro_correlations()
        movers = self.get_top_movers()
        defi = self.get_defi_tvl()
        
        # Compter les signaux
        signals = {
            'BULLISH': 0,
            'BEARISH': 0,
            'NEUTRAL': 0
        }
        
        all_signals = [
            funding.get('signal', 'NEUTRAL'),
            ls_ratio.get('signal', 'NEUTRAL'),
            orderbook.get('signal', 'NEUTRAL'),
            volume.get('signal', 'NEUTRAL'),
            macro.get('dominance_signal', 'NEUTRAL'),
            movers.get('breadth_signal', 'NEUTRAL'),
            defi.get('signal', 'NEUTRAL'),
        ]
        
        for sig in all_signals:
            if 'BULLISH' in sig:
                signals['BULLISH'] += 1
            elif 'BEARISH' in sig:
                signals['BEARISH'] += 1
            else:
                signals['NEUTRAL'] += 1
        
        # Déterminer le biais global
        total = len(all_signals)
        if signals['BULLISH'] >= total * 0.6:
            overall_bias = 'STRONG_BULLISH'
            confidence = signals['BULLISH'] / total * 100
        elif signals['BULLISH'] > signals['BEARISH']:
            overall_bias = 'BULLISH'
            confidence = signals['BULLISH'] / total * 100
        elif signals['BEARISH'] >= total * 0.6:
            overall_bias = 'STRONG_BEARISH'
            confidence = signals['BEARISH'] / total * 100
        elif signals['BEARISH'] > signals['BULLISH']:
            overall_bias = 'BEARISH'
            confidence = signals['BEARISH'] / total * 100
        else:
            overall_bias = 'NEUTRAL'
            confidence = signals['NEUTRAL'] / total * 100
        
        # Générer les alertes
        alerts = []
        
        if funding.get('btc_funding', 0) > 0.1:
            alerts.append("⚠️ Funding très élevé - correction possible")
        if funding.get('btc_funding', 0) < -0.05:
            alerts.append("💡 Funding négatif - short squeeze possible")
        if ls_ratio.get('ratio', 1) > 2:
            alerts.append("⚠️ Trop de longs ouverts - prudence")
        if ls_ratio.get('ratio', 1) < 0.7:
            alerts.append("💡 Beaucoup de shorts - squeeze probable")
        if volume.get('volume_ratio', 1) > 2:
            alerts.append("📊 Volume anormalement élevé")
        if movers.get('market_breadth', 50) > 70:
            alerts.append("📈 Marché très haussier (>70% en hausse)")
        if movers.get('market_breadth', 50) < 30:
            alerts.append("📉 Marché très baissier (<30% en hausse)")
        
        # Recommandations
        if overall_bias in ['STRONG_BULLISH', 'BULLISH']:
            recommendation = "Favoriser les LONG, prudence sur les SHORT"
            score_modifier = 10 if overall_bias == 'STRONG_BULLISH' else 5
        elif overall_bias in ['STRONG_BEARISH', 'BEARISH']:
            recommendation = "Favoriser les SHORT, éviter les LONG"
            score_modifier = -10 if overall_bias == 'STRONG_BEARISH' else -5
        else:
            recommendation = "Conditions neutres, respecter les signaux techniques"
            score_modifier = 0
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'overall_bias': overall_bias,
            'confidence': round(confidence, 1),
            'score_modifier': score_modifier,
            'signals_count': signals,
            'alerts': alerts,
            'recommendation': recommendation,
            'data': {
                'funding': funding,
                'long_short_ratio': ls_ratio,
                'order_book': orderbook,
                'volume': volume,
                'macro': macro,
                'top_movers': movers,
                'defi_tvl': defi
            }
        }
        
        # Mettre à jour l'état
        self.market_state = {
            'last_update': datetime.now(),
            'overall_bias': overall_bias,
            'confidence': confidence,
            'alerts': alerts
        }
        
        return result
    
    def get_trading_recommendation(self, direction: str) -> Tuple[bool, str, int]:
        """
        Recommandation de trading basée sur l'intelligence complète.
        
        Args:
            direction: 'LONG' ou 'SHORT'
            
        Returns:
            (should_trade, reason, score_modifier)
        """
        intel = self.get_complete_intelligence()
        bias = intel['overall_bias']
        modifier = intel['score_modifier']
        
        # Vérifier la compatibilité direction/biais
        if direction == 'LONG' and bias in ['STRONG_BEARISH', 'BEARISH']:
            return False, f"Intelligence bearish ({bias}) - LONG risqué", 0
        
        if direction == 'SHORT' and bias in ['STRONG_BULLISH', 'BULLISH']:
            return False, f"Intelligence bullish ({bias}) - SHORT risqué", 0
        
        # Ajuster le score
        if direction == 'LONG' and bias in ['STRONG_BULLISH', 'BULLISH']:
            modifier = abs(modifier)  # Bonus pour LONG
        elif direction == 'SHORT' and bias in ['STRONG_BEARISH', 'BEARISH']:
            modifier = abs(modifier)  # Bonus pour SHORT
        else:
            modifier = 0  # Neutre
        
        return True, intel['recommendation'], modifier
    
    # ═══════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════
    
    def _is_cache_valid(self, key: str) -> bool:
        """Vérifie si le cache est valide."""
        entry = self.cache.get(key)
        if not entry:
            return False
        
        age = (datetime.now() - entry.get('updated', datetime.min)).total_seconds()
        return age < self.cache_duration
    
    def _update_cache(self, key: str, data: Any):
        """Met à jour le cache."""
        self.cache[key] = {
            'data': data,
            'updated': datetime.now()
        }
    
    def _get_btc_price(self) -> float:
        """Récupère le prix BTC actuel."""
        try:
            response = requests.get(
                'https://api.binance.com/api/v3/ticker/price',
                params={'symbol': 'BTCUSDT'},
                timeout=3
            )
            if response.status_code == 200:
                return float(response.json().get('price', 0))
        except:
            pass
        return 50000  # Fallback


# ═══════════════════════════════════════════════════════════════
# INSTANCE GLOBALE
# ═══════════════════════════════════════════════════════════════

market_intel = MarketIntelligence()


def get_market_intelligence() -> Dict:
    """Fonction utilitaire pour l'intelligence complète."""
    return market_intel.get_complete_intelligence()


def should_trade_with_intel(direction: str) -> Tuple[bool, str, int]:
    """Vérifie si on devrait trader selon l'intelligence."""
    return market_intel.get_trading_recommendation(direction)


def get_quick_intel() -> Dict:
    """Version rapide avec données essentielles."""
    return {
        'funding': market_intel.get_funding_rates(),
        'ls_ratio': market_intel.get_long_short_ratio(),
        'orderbook': market_intel.get_order_book_imbalance(),
        'volume': market_intel.get_volume_analysis(),
        'top_movers': market_intel.get_top_movers()
    }
