"""
Module d'Analyse Technique Avancée pour Crypto Trading.
Intègre de nombreuses stratégies professionnelles et indicateurs avancés.

Stratégies:
1. Multi-Timeframe Analysis (MTF)
2. Smart Money Concepts (SMC) - Order Blocks, FVG, Liquidity
3. Divergences RSI/MACD avec confirmation
4. Structure de marché (HH, HL, LH, LL)
5. Confluence de signaux pondérée
6. Momentum Analysis (ROC, Williams %R, CCI)
7. Volatility Analysis (Keltner, ATR Bands)
8. Trend Strength Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TechnicalSignal:
    """Structure pour un signal technique."""
    name: str
    direction: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    strength: float  # 0-100
    weight: float  # Importance du signal
    description: str


class AdvancedTechnicalAnalyzer:
    """
    Analyseur technique avancé multi-stratégies.
    Combine plusieurs approches pour maximiser la précision des signaux.
    """
    
    def __init__(self):
        # Poids des différentes analyses (total = 1.0)
        self.analysis_weights = {
            'trend_structure': 0.20,      # Structure de tendance (HH/HL/LH/LL)
            'momentum_oscillators': 0.20,  # RSI, Stoch, CCI, Williams %R
            'moving_averages': 0.15,       # EMAs, SMAs, Golden/Death Cross
            'volume_analysis': 0.15,       # Volume profile, OBV, VWAP
            'divergences': 0.10,           # RSI/MACD divergences
            'smart_money': 0.10,           # Order blocks, FVG, liquidity
            'volatility': 0.10,            # BB, Keltner, ATR analysis
        }
        
        print("📈 Advanced Technical Analyzer initialisé")
    
    # ─────────────────────────────────────────────────────────────
    # INDICATEURS SUPPLÉMENTAIRES
    # ─────────────────────────────────────────────────────────────
    
    def calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Williams %R - Momentum oscillator (-100 to 0)."""
        high_max = df['high'].rolling(window=period).max()
        low_min = df['low'].rolling(window=period).min()
        williams_r = -100 * (high_max - df['close']) / (high_max - low_min)
        return williams_r
    
    def calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Commodity Channel Index."""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )
        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
        return cci
    
    def calculate_roc(self, data: pd.Series, period: int = 12) -> pd.Series:
        """Rate of Change - Momentum."""
        roc = ((data - data.shift(period)) / data.shift(period)) * 100
        return roc
    
    def calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """On-Balance Volume."""
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        return pd.Series(obv, index=df.index)
    
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Volume Weighted Average Price."""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap
    
    def calculate_keltner_channels(self, df: pd.DataFrame, period: int = 20, 
                                   atr_multiplier: float = 2.0) -> Dict:
        """Keltner Channels - Volatilité alternative aux BB."""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        middle = typical_price.ewm(span=period, adjust=False).mean()
        
        # ATR
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift())
        tr3 = abs(df['low'] - df['close'].shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        upper = middle + (atr * atr_multiplier)
        lower = middle - (atr * atr_multiplier)
        
        return {'upper': upper, 'middle': middle, 'lower': lower}
    
    def calculate_squeeze_indicator(self, df: pd.DataFrame) -> Dict:
        """
        TTM Squeeze - Détecte les breakouts potentiels.
        Squeeze = BB inside Keltner (faible volatilité avant explosion).
        """
        # Bollinger Bands
        sma20 = df['close'].rolling(20).mean()
        std20 = df['close'].rolling(20).std()
        bb_upper = sma20 + (2 * std20)
        bb_lower = sma20 - (2 * std20)
        
        # Keltner Channels
        keltner = self.calculate_keltner_channels(df, 20, 1.5)
        
        # Squeeze: BB inside Keltner
        squeeze_on = (bb_lower > keltner['lower']) & (bb_upper < keltner['upper'])
        
        # Momentum pour direction
        highest = df['high'].rolling(20).max()
        lowest = df['low'].rolling(20).min()
        mom = df['close'] - ((highest + lowest) / 2 + sma20) / 2
        
        return {
            'squeeze_on': squeeze_on,
            'momentum': mom,
            'current_squeeze': squeeze_on.iloc[-1] if len(squeeze_on) > 0 else False,
            'momentum_direction': 'BULLISH' if mom.iloc[-1] > 0 else 'BEARISH'
        }
    
    # ─────────────────────────────────────────────────────────────
    # ANALYSE DE STRUCTURE DE MARCHÉ
    # ─────────────────────────────────────────────────────────────
    
    def analyze_market_structure(self, df: pd.DataFrame, lookback: int = 50) -> Dict:
        """
        Analyse la structure de marché (Higher Highs/Lows, Lower Highs/Lows).
        Fondamental pour déterminer la tendance réelle.
        """
        if len(df) < lookback:
            return {'structure': 'UNKNOWN', 'strength': 0, 'swing_points': []}
        
        recent = df.tail(lookback)
        highs = recent['high'].values
        lows = recent['low'].values
        
        # Trouver les swing highs et swing lows
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(highs) - 2):
            # Swing High: plus haut que les 2 bougies avant et après
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append((i, highs[i]))
            
            # Swing Low: plus bas que les 2 bougies avant et après
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append((i, lows[i]))
        
        # Analyser la structure
        structure = 'NEUTRAL'
        strength = 0
        
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            # Higher Highs & Higher Lows = UPTREND
            hh_count = 0
            hl_count = 0
            lh_count = 0
            ll_count = 0
            
            for i in range(1, len(swing_highs)):
                if swing_highs[i][1] > swing_highs[i-1][1]:
                    hh_count += 1
                else:
                    lh_count += 1
            
            for i in range(1, len(swing_lows)):
                if swing_lows[i][1] > swing_lows[i-1][1]:
                    hl_count += 1
                else:
                    ll_count += 1
            
            total_swings = hh_count + hl_count + lh_count + ll_count
            
            if total_swings > 0:
                bullish_ratio = (hh_count + hl_count) / total_swings
                bearish_ratio = (lh_count + ll_count) / total_swings
                
                if bullish_ratio > 0.65:
                    structure = 'UPTREND'
                    strength = bullish_ratio * 100
                elif bearish_ratio > 0.65:
                    structure = 'DOWNTREND'
                    strength = bearish_ratio * 100
                else:
                    structure = 'RANGING'
                    strength = 50
        
        return {
            'structure': structure,
            'strength': strength,
            'swing_highs': swing_highs[-5:] if len(swing_highs) >= 5 else swing_highs,
            'swing_lows': swing_lows[-5:] if len(swing_lows) >= 5 else swing_lows,
            'last_swing_high': swing_highs[-1][1] if swing_highs else None,
            'last_swing_low': swing_lows[-1][1] if swing_lows else None,
        }
    
    # ─────────────────────────────────────────────────────────────
    # DÉTECTION DES DIVERGENCES
    # ─────────────────────────────────────────────────────────────
    
    def detect_divergences(self, df: pd.DataFrame, rsi: pd.Series, 
                          macd: pd.Series, lookback: int = 20) -> Dict:
        """
        Détecte les divergences RSI et MACD (signaux de retournement).
        - Divergence haussière: Prix fait LL, RSI/MACD fait HL
        - Divergence baissière: Prix fait HH, RSI/MACD fait LH
        """
        if len(df) < lookback or len(rsi) < lookback:
            return {'rsi_divergence': None, 'macd_divergence': None}
        
        recent_close = df['close'].tail(lookback).values
        recent_rsi = rsi.tail(lookback).values
        recent_macd = macd.tail(lookback).values
        
        # Trouver les points bas et hauts du prix
        price_lows = []
        price_highs = []
        rsi_at_lows = []
        rsi_at_highs = []
        macd_at_lows = []
        macd_at_highs = []
        
        for i in range(2, len(recent_close) - 2):
            # Swing Low
            if recent_close[i] < recent_close[i-1] and recent_close[i] < recent_close[i+1]:
                price_lows.append((i, recent_close[i]))
                rsi_at_lows.append((i, recent_rsi[i]))
                macd_at_lows.append((i, recent_macd[i]))
            
            # Swing High
            if recent_close[i] > recent_close[i-1] and recent_close[i] > recent_close[i+1]:
                price_highs.append((i, recent_close[i]))
                rsi_at_highs.append((i, recent_rsi[i]))
                macd_at_highs.append((i, recent_macd[i]))
        
        rsi_divergence = None
        macd_divergence = None
        
        # Divergence Haussière (bullish): Prix LL, RSI HL
        if len(price_lows) >= 2 and len(rsi_at_lows) >= 2:
            if price_lows[-1][1] < price_lows[-2][1]:  # Prix: Lower Low
                if rsi_at_lows[-1][1] > rsi_at_lows[-2][1]:  # RSI: Higher Low
                    rsi_divergence = 'BULLISH'
                if macd_at_lows[-1][1] > macd_at_lows[-2][1]:  # MACD: Higher Low
                    macd_divergence = 'BULLISH'
        
        # Divergence Baissière (bearish): Prix HH, RSI LH
        if len(price_highs) >= 2 and len(rsi_at_highs) >= 2:
            if price_highs[-1][1] > price_highs[-2][1]:  # Prix: Higher High
                if rsi_at_highs[-1][1] < rsi_at_highs[-2][1]:  # RSI: Lower High
                    rsi_divergence = 'BEARISH'
                if macd_at_highs[-1][1] < macd_at_highs[-2][1]:  # MACD: Lower High
                    macd_divergence = 'BEARISH'
        
        return {
            'rsi_divergence': rsi_divergence,
            'macd_divergence': macd_divergence,
            'has_bullish_div': rsi_divergence == 'BULLISH' or macd_divergence == 'BULLISH',
            'has_bearish_div': rsi_divergence == 'BEARISH' or macd_divergence == 'BEARISH',
        }
    
    # ─────────────────────────────────────────────────────────────
    # SMART MONEY CONCEPTS
    # ─────────────────────────────────────────────────────────────
    
    def find_order_blocks(self, df: pd.DataFrame, lookback: int = 50) -> Dict:
        """
        Trouve les Order Blocks (zones institutionnelles).
        Order Block = dernière bougie avant un mouvement impulsif.
        """
        if len(df) < lookback:
            return {'bullish_ob': [], 'bearish_ob': []}
        
        recent = df.tail(lookback)
        bullish_ob = []
        bearish_ob = []
        
        for i in range(3, len(recent) - 1):
            current = recent.iloc[i]
            prev = recent.iloc[i-1]
            next_candle = recent.iloc[i+1] if i+1 < len(recent) else None
            
            # Calcul du body et de la range
            body = abs(current['close'] - current['open'])
            range_candle = current['high'] - current['low']
            
            # Bougie impulsive = grande bougie (body > 60% de la range)
            if range_candle > 0 and body / range_candle > 0.6:
                # Mouvement impulsif haussier
                if current['close'] > current['open']:
                    move_size = (current['close'] - prev['low']) / prev['low'] * 100
                    if move_size > 1.5:  # Mouvement > 1.5%
                        # Order Block = bougie précédente (baissière idéalement)
                        if prev['close'] < prev['open']:
                            bullish_ob.append({
                                'high': prev['high'],
                                'low': prev['low'],
                                'index': i-1,
                                'strength': min(move_size * 10, 100)
                            })
                
                # Mouvement impulsif baissier
                elif current['close'] < current['open']:
                    move_size = (prev['high'] - current['close']) / prev['high'] * 100
                    if move_size > 1.5:
                        if prev['close'] > prev['open']:
                            bearish_ob.append({
                                'high': prev['high'],
                                'low': prev['low'],
                                'index': i-1,
                                'strength': min(move_size * 10, 100)
                            })
        
        return {
            'bullish_ob': bullish_ob[-3:] if len(bullish_ob) > 3 else bullish_ob,
            'bearish_ob': bearish_ob[-3:] if len(bearish_ob) > 3 else bearish_ob,
        }
    
    def find_fair_value_gaps(self, df: pd.DataFrame, lookback: int = 30) -> Dict:
        """
        Trouve les Fair Value Gaps (FVG) - zones de déséquilibre.
        FVG haussier: Low[i+1] > High[i-1] (gap entre bougies)
        FVG baissier: High[i+1] < Low[i-1]
        """
        if len(df) < lookback:
            return {'bullish_fvg': [], 'bearish_fvg': []}
        
        recent = df.tail(lookback)
        bullish_fvg = []
        bearish_fvg = []
        
        for i in range(1, len(recent) - 1):
            prev = recent.iloc[i-1]
            current = recent.iloc[i]
            next_candle = recent.iloc[i+1]
            
            # FVG Haussier: gap entre la mèche haute de i-1 et la mèche basse de i+1
            if next_candle['low'] > prev['high']:
                gap_size = (next_candle['low'] - prev['high']) / prev['high'] * 100
                if gap_size > 0.2:  # Gap > 0.2%
                    bullish_fvg.append({
                        'top': next_candle['low'],
                        'bottom': prev['high'],
                        'gap_percent': gap_size,
                        'index': i
                    })
            
            # FVG Baissier
            if next_candle['high'] < prev['low']:
                gap_size = (prev['low'] - next_candle['high']) / prev['low'] * 100
                if gap_size > 0.2:
                    bearish_fvg.append({
                        'top': prev['low'],
                        'bottom': next_candle['high'],
                        'gap_percent': gap_size,
                        'index': i
                    })
        
        return {
            'bullish_fvg': bullish_fvg[-5:],
            'bearish_fvg': bearish_fvg[-5:],
        }
    
    # ─────────────────────────────────────────────────────────────
    # ANALYSE VOLUME
    # ─────────────────────────────────────────────────────────────
    
    def analyze_volume_profile(self, df: pd.DataFrame, lookback: int = 50) -> Dict:
        """
        Analyse le profil de volume.
        - Volume climax (très haut volume = possibilité de reversal)
        - Divergence Volume/Prix
        - OBV trend
        """
        if len(df) < lookback:
            return {'analysis': 'NEUTRAL', 'strength': 50}
        
        recent = df.tail(lookback)
        volume = recent['volume'].values
        close = recent['close'].values
        
        # Volume moyen et actuel
        avg_volume = np.mean(volume)
        current_volume = volume[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # OBV (On Balance Volume)
        obv = self.calculate_obv(recent)
        obv_trend = 'NEUTRAL'
        if len(obv) >= 10:
            obv_ma = obv.rolling(10).mean()
            if obv.iloc[-1] > obv_ma.iloc[-1]:
                obv_trend = 'BULLISH'
            elif obv.iloc[-1] < obv_ma.iloc[-1]:
                obv_trend = 'BEARISH'
        
        # Volume Climax (volume extrême = possible reversal)
        volume_std = np.std(volume)
        is_climax = current_volume > (avg_volume + 2 * volume_std)
        
        # Divergence Volume/Prix
        price_up = close[-1] > close[-5] if len(close) >= 5 else False
        volume_up = volume[-1] > np.mean(volume[-5:]) if len(volume) >= 5 else False
        
        volume_confirms_price = (price_up and volume_up) or (not price_up and not volume_up)
        
        # Score
        strength = 50
        analysis = 'NEUTRAL'
        
        if volume_ratio > 1.5 and obv_trend == 'BULLISH' and volume_confirms_price:
            analysis = 'STRONG_BULLISH'
            strength = 80
        elif volume_ratio > 1.5 and obv_trend == 'BEARISH' and volume_confirms_price:
            analysis = 'STRONG_BEARISH'
            strength = 80
        elif obv_trend == 'BULLISH':
            analysis = 'BULLISH'
            strength = 65
        elif obv_trend == 'BEARISH':
            analysis = 'BEARISH'
            strength = 65
        
        return {
            'analysis': analysis,
            'strength': strength,
            'volume_ratio': volume_ratio,
            'obv_trend': obv_trend,
            'is_climax': is_climax,
            'volume_confirms_price': volume_confirms_price,
        }
    
    # ─────────────────────────────────────────────────────────────
    # ANALYSE COMPLÈTE
    # ─────────────────────────────────────────────────────────────
    
    def calculate_advanced_indicators(self, df: pd.DataFrame) -> Dict:
        """
        Calcule tous les indicateurs techniques avancés.
        """
        if df is None or len(df) < 50:
            return {}
        
        close = df['close']
        
        # Indicateurs supplémentaires
        williams_r = self.calculate_williams_r(df)
        cci = self.calculate_cci(df)
        roc = self.calculate_roc(close)
        obv = self.calculate_obv(df)
        vwap = self.calculate_vwap(df)
        keltner = self.calculate_keltner_channels(df)
        squeeze = self.calculate_squeeze_indicator(df)
        
        return {
            'williams_r': williams_r.iloc[-1] if len(williams_r) > 0 else None,
            'cci': cci.iloc[-1] if len(cci) > 0 else None,
            'roc': roc.iloc[-1] if len(roc) > 0 else None,
            'obv': obv.iloc[-1] if len(obv) > 0 else None,
            'obv_change': ((obv.iloc[-1] - obv.iloc[-5]) / abs(obv.iloc[-5]) * 100) if len(obv) >= 5 and obv.iloc[-5] != 0 else 0,
            'vwap': vwap.iloc[-1] if len(vwap) > 0 else None,
            'keltner_upper': keltner['upper'].iloc[-1],
            'keltner_lower': keltner['lower'].iloc[-1],
            'keltner_middle': keltner['middle'].iloc[-1],
            'squeeze_on': squeeze['current_squeeze'],
            'squeeze_momentum': squeeze['momentum_direction'],
        }
    
    def perform_full_analysis(self, df: pd.DataFrame, basic_indicators: Dict) -> Dict:
        """
        Effectue une analyse technique complète et retourne un score pondéré.
        
        Args:
            df: DataFrame OHLCV
            basic_indicators: Indicateurs de base déjà calculés
        
        Returns:
            Dict avec score global, signaux et recommandations
        """
        if df is None or len(df) < 100:
            return {
                'score': 50,
                'direction': 'NEUTRAL',
                'confidence': 0,
                'signals': [],
                'recommendation': 'ATTENDRE'
            }
        
        signals = []
        bullish_score = 0
        bearish_score = 0
        total_weight = 0
        
        # 1. Structure de marché (20%)
        structure = self.analyze_market_structure(df)
        weight = self.analysis_weights['trend_structure']
        total_weight += weight
        
        if structure['structure'] == 'UPTREND':
            bullish_score += structure['strength'] * weight
            signals.append(TechnicalSignal(
                'Market Structure', 'BULLISH', structure['strength'], weight,
                f"Tendance haussière (HH/HL) - Force: {structure['strength']:.0f}%"
            ))
        elif structure['structure'] == 'DOWNTREND':
            bearish_score += structure['strength'] * weight
            signals.append(TechnicalSignal(
                'Market Structure', 'BEARISH', structure['strength'], weight,
                f"Tendance baissière (LH/LL) - Force: {structure['strength']:.0f}%"
            ))
        
        # 2. Momentum Oscillators (20%)
        weight = self.analysis_weights['momentum_oscillators']
        total_weight += weight
        
        rsi = basic_indicators.get('rsi14', 50)
        stoch_k = basic_indicators.get('stoch_k', 50)
        macd = basic_indicators.get('macd', 0)
        macd_signal = basic_indicators.get('macd_signal', 0)
        
        # Calculer indicateurs avancés
        advanced = self.calculate_advanced_indicators(df)
        williams_r = advanced.get('williams_r', -50)
        cci = advanced.get('cci', 0)
        
        momentum_bullish = 0
        momentum_bearish = 0
        
        # RSI
        if rsi and rsi < 35:
            momentum_bullish += 20
        elif rsi and rsi > 65:
            momentum_bearish += 20
        elif rsi and 35 <= rsi <= 45:
            momentum_bullish += 10
        elif rsi and 55 <= rsi <= 65:
            momentum_bearish += 10
        
        # Stochastic
        if stoch_k and stoch_k < 25:
            momentum_bullish += 15
        elif stoch_k and stoch_k > 75:
            momentum_bearish += 15
        
        # Williams %R
        if williams_r and williams_r < -80:
            momentum_bullish += 15
        elif williams_r and williams_r > -20:
            momentum_bearish += 15
        
        # CCI
        if cci and cci < -100:
            momentum_bullish += 15
        elif cci and cci > 100:
            momentum_bearish += 15
        
        # MACD
        if macd and macd_signal and macd > macd_signal:
            momentum_bullish += 20
        elif macd and macd_signal and macd < macd_signal:
            momentum_bearish += 20
        
        # Histogram MACD
        macd_hist = basic_indicators.get('macd_hist', 0)
        macd_hist_prev = basic_indicators.get('macd_hist_prev', 0)
        if macd_hist and macd_hist_prev and macd_hist > macd_hist_prev:
            momentum_bullish += 15
        elif macd_hist and macd_hist_prev and macd_hist < macd_hist_prev:
            momentum_bearish += 15
        
        # Normaliser à 100
        max_momentum = 100
        momentum_bullish = min(momentum_bullish, max_momentum)
        momentum_bearish = min(momentum_bearish, max_momentum)
        
        if momentum_bullish > momentum_bearish:
            bullish_score += momentum_bullish * weight
            signals.append(TechnicalSignal(
                'Momentum', 'BULLISH', momentum_bullish, weight,
                f"Momentum haussier (RSI:{rsi:.0f}, Stoch:{stoch_k:.0f})"
            ))
        elif momentum_bearish > momentum_bullish:
            bearish_score += momentum_bearish * weight
            signals.append(TechnicalSignal(
                'Momentum', 'BEARISH', momentum_bearish, weight,
                f"Momentum baissier (RSI:{rsi:.0f}, Stoch:{stoch_k:.0f})"
            ))
        
        # 3. Moving Averages (15%)
        weight = self.analysis_weights['moving_averages']
        total_weight += weight
        
        ema9 = basic_indicators.get('ema9')
        ema21 = basic_indicators.get('ema21')
        sma50 = basic_indicators.get('sma50')
        sma200 = basic_indicators.get('sma200')
        price = basic_indicators.get('current_price')
        
        ma_bullish = 0
        ma_bearish = 0
        
        if ema9 and ema21:
            if ema9 > ema21:
                ma_bullish += 30
            else:
                ma_bearish += 30
        
        if price and sma50:
            if price > sma50:
                ma_bullish += 20
            else:
                ma_bearish += 20
        
        if price and sma200:
            if price > sma200:
                ma_bullish += 25
            else:
                ma_bearish += 25
        
        # Golden/Death Cross
        if sma50 and sma200:
            if sma50 > sma200:
                ma_bullish += 25  # Golden Cross zone
            else:
                ma_bearish += 25  # Death Cross zone
        
        ma_bullish = min(ma_bullish, 100)
        ma_bearish = min(ma_bearish, 100)
        
        if ma_bullish > ma_bearish:
            bullish_score += ma_bullish * weight
            signals.append(TechnicalSignal(
                'Moving Averages', 'BULLISH', ma_bullish, weight,
                f"MAs haussières (EMA9>EMA21, Prix>SMA50)"
            ))
        elif ma_bearish > ma_bullish:
            bearish_score += ma_bearish * weight
            signals.append(TechnicalSignal(
                'Moving Averages', 'BEARISH', ma_bearish, weight,
                f"MAs baissières (EMA9<EMA21, Prix<SMA50)"
            ))
        
        # 4. Volume Analysis (15%)
        weight = self.analysis_weights['volume_analysis']
        total_weight += weight
        
        volume_analysis = self.analyze_volume_profile(df)
        
        if 'BULLISH' in volume_analysis['analysis']:
            bullish_score += volume_analysis['strength'] * weight
            signals.append(TechnicalSignal(
                'Volume', 'BULLISH', volume_analysis['strength'], weight,
                f"Volume confirme hausse (OBV: {volume_analysis['obv_trend']})"
            ))
        elif 'BEARISH' in volume_analysis['analysis']:
            bearish_score += volume_analysis['strength'] * weight
            signals.append(TechnicalSignal(
                'Volume', 'BEARISH', volume_analysis['strength'], weight,
                f"Volume confirme baisse (OBV: {volume_analysis['obv_trend']})"
            ))
        
        # 5. Divergences (10%)
        weight = self.analysis_weights['divergences']
        total_weight += weight
        
        rsi_series = df['close'].diff()
        rsi_series = rsi_series.fillna(0)
        # On utilise le RSI déjà calculé
        from indicators import calculate_rsi, calculate_macd
        rsi_full = calculate_rsi(df['close'], 14)
        macd_data = calculate_macd(df['close'])
        
        divergences = self.detect_divergences(df, rsi_full, macd_data['macd'])
        
        if divergences['has_bullish_div']:
            bullish_score += 80 * weight
            signals.append(TechnicalSignal(
                'Divergence', 'BULLISH', 80, weight,
                f"Divergence haussière détectée (RSI:{divergences['rsi_divergence']}, MACD:{divergences['macd_divergence']})"
            ))
        elif divergences['has_bearish_div']:
            bearish_score += 80 * weight
            signals.append(TechnicalSignal(
                'Divergence', 'BEARISH', 80, weight,
                f"Divergence baissière détectée (RSI:{divergences['rsi_divergence']}, MACD:{divergences['macd_divergence']})"
            ))
        
        # 6. Smart Money (10%)
        weight = self.analysis_weights['smart_money']
        total_weight += weight
        
        order_blocks = self.find_order_blocks(df)
        fvg = self.find_fair_value_gaps(df)
        
        # Prix proche d'un Order Block?
        if price and order_blocks['bullish_ob']:
            for ob in order_blocks['bullish_ob']:
                if ob['low'] <= price <= ob['high'] * 1.01:  # Dans ou juste au-dessus
                    bullish_score += 70 * weight
                    signals.append(TechnicalSignal(
                        'Smart Money', 'BULLISH', 70, weight,
                        f"Prix sur Bullish Order Block"
                    ))
                    break
        
        if price and order_blocks['bearish_ob']:
            for ob in order_blocks['bearish_ob']:
                if ob['low'] * 0.99 <= price <= ob['high']:
                    bearish_score += 70 * weight
                    signals.append(TechnicalSignal(
                        'Smart Money', 'BEARISH', 70, weight,
                        f"Prix sur Bearish Order Block"
                    ))
                    break
        
        # 7. Volatility (10%)
        weight = self.analysis_weights['volatility']
        total_weight += weight
        
        bb_percent = basic_indicators.get('bb_percent', 0.5)
        squeeze_on = advanced.get('squeeze_on', False)
        squeeze_momentum = advanced.get('squeeze_momentum', 'NEUTRAL')
        
        vol_signal = 'NEUTRAL'
        vol_strength = 50
        
        if squeeze_on:
            # Squeeze = consolidation, direction par momentum
            if squeeze_momentum == 'BULLISH':
                vol_signal = 'BULLISH'
                vol_strength = 75
            elif squeeze_momentum == 'BEARISH':
                vol_signal = 'BEARISH'
                vol_strength = 75
        else:
            # Pas de squeeze, utiliser BB %
            if bb_percent and bb_percent < 0.2:
                vol_signal = 'BULLISH'  # Près du bas des BB
                vol_strength = 65
            elif bb_percent and bb_percent > 0.8:
                vol_signal = 'BEARISH'  # Près du haut des BB
                vol_strength = 65
        
        if vol_signal == 'BULLISH':
            bullish_score += vol_strength * weight
            signals.append(TechnicalSignal(
                'Volatility', 'BULLISH', vol_strength, weight,
                f"Volatilité favorable (BB%:{bb_percent:.2f}, Squeeze:{squeeze_on})"
            ))
        elif vol_signal == 'BEARISH':
            bearish_score += vol_strength * weight
            signals.append(TechnicalSignal(
                'Volatility', 'BEARISH', vol_strength, weight,
                f"Volatilité défavorable (BB%:{bb_percent:.2f}, Squeeze:{squeeze_on})"
            ))
        
        # ─── CALCUL SCORE FINAL ───
        # Normaliser les scores
        if total_weight > 0:
            bullish_score = bullish_score / total_weight
            bearish_score = bearish_score / total_weight
        
        # Score final (0-100)
        if bullish_score > bearish_score:
            final_score = 50 + (bullish_score - bearish_score) / 2
            direction = 'BULLISH'
        elif bearish_score > bullish_score:
            final_score = 50 - (bearish_score - bullish_score) / 2
            direction = 'BEARISH'
        else:
            final_score = 50
            direction = 'NEUTRAL'
        
        final_score = max(0, min(100, final_score))
        
        # Confiance basée sur l'écart entre bull et bear
        confidence = abs(bullish_score - bearish_score)
        
        # Recommandation
        if final_score >= 70 and confidence >= 30:
            recommendation = 'STRONG_BUY' if direction == 'BULLISH' else 'STRONG_SELL'
        elif final_score >= 60 and confidence >= 20:
            recommendation = 'BUY' if direction == 'BULLISH' else 'SELL'
        elif final_score <= 30 and confidence >= 30:
            recommendation = 'STRONG_SELL' if direction == 'BEARISH' else 'STRONG_BUY'
        elif final_score <= 40 and confidence >= 20:
            recommendation = 'SELL' if direction == 'BEARISH' else 'BUY'
        else:
            recommendation = 'HOLD'
        
        return {
            'score': round(final_score, 1),
            'direction': direction,
            'confidence': round(confidence, 1),
            'bullish_score': round(bullish_score, 1),
            'bearish_score': round(bearish_score, 1),
            'signals': [{'name': s.name, 'direction': s.direction, 'strength': s.strength, 
                        'weight': s.weight, 'description': s.description} for s in signals],
            'recommendation': recommendation,
            'advanced_indicators': advanced,
            'market_structure': structure,
            'volume_analysis': volume_analysis,
            'divergences': divergences,
        }


# Instance globale
advanced_ta = AdvancedTechnicalAnalyzer()


def get_advanced_technical_analysis(df: pd.DataFrame, basic_indicators: Dict) -> Dict:
    """
    Fonction wrapper pour obtenir l'analyse technique avancée.
    """
    return advanced_ta.perform_full_analysis(df, basic_indicators)


def get_technical_score_adjustment(analysis: Dict, direction: str) -> int:
    """
    Retourne un ajustement de score basé sur l'analyse technique avancée.
    
    Args:
        analysis: Résultat de perform_full_analysis()
        direction: 'LONG' ou 'SHORT'
    
    Returns:
        Ajustement du score (-20 à +20)
    """
    if not analysis:
        return 0
    
    ta_direction = analysis.get('direction', 'NEUTRAL')
    confidence = analysis.get('confidence', 0)
    recommendation = analysis.get('recommendation', 'HOLD')
    
    adjustment = 0
    
    # Direction alignée?
    if direction == 'LONG' and ta_direction == 'BULLISH':
        adjustment += int(confidence / 5)  # +0 à +20
    elif direction == 'SHORT' and ta_direction == 'BEARISH':
        adjustment += int(confidence / 5)
    elif direction == 'LONG' and ta_direction == 'BEARISH':
        adjustment -= int(confidence / 5)  # -0 à -20
    elif direction == 'SHORT' and ta_direction == 'BULLISH':
        adjustment -= int(confidence / 5)
    
    # Bonus pour recommandations fortes
    if 'STRONG' in recommendation:
        if (direction == 'LONG' and 'BUY' in recommendation) or \
           (direction == 'SHORT' and 'SELL' in recommendation):
            adjustment += 10
        else:
            adjustment -= 10
    
    return max(-20, min(20, adjustment))
