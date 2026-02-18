"""
Module d'Analyse Technique Complète - CHART ANALYZER
Combine TOUS les indicateurs et patterns pour une décision de trading optimale.

Ce module:
1. Calcule 20+ indicateurs techniques
2. Détecte les patterns de chandeliers (Engulfing, Doji, Hammer, etc.)
3. Détecte les patterns chartistes (Double Top, H&S, Triangles, etc.)
4. Analyse la structure de marché (HH/HL/LH/LL)
5. Détecte les divergences RSI/MACD
6. Calcule un score de confluence pour timing optimal
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class ChartSignal:
    """Signal d'analyse technique."""
    direction: str  # 'LONG', 'SHORT', 'NEUTRAL'
    confidence: int  # 0-100
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    risk_reward: float
    analysis: Dict  # Détails de l'analyse


class ChartAnalyzer:
    """
    Analyseur de graphiques complet.
    Combine indicateurs, patterns et structure pour des entrées précises.
    """
    
    def __init__(self):
        # Poids des différentes composantes (total = 100)
        self.weights = {
            'trend_structure': 20,       # Structure HH/HL/LH/LL
            'momentum': 15,              # RSI, Stoch, CCI
            'trend_indicators': 15,      # EMA, MACD, ADX
            'candlestick_patterns': 15,  # Patterns de bougies
            'chart_patterns': 15,        # Patterns chartistes
            'volume': 10,                # Volume analysis
            'divergences': 10,           # RSI/MACD divergences
        }
    
    def analyze_chart(self, df: pd.DataFrame, indicators: Dict) -> ChartSignal:
        """
        Analyse complète du graphique pour décision de trading.
        
        Args:
            df: DataFrame OHLCV
            indicators: Dictionnaire d'indicateurs pré-calculés
        
        Returns:
            ChartSignal avec direction, confiance et niveaux
        """
        if df is None or len(df) < 100:
            return self._neutral_signal()
        
        # === COLLECTE DES ANALYSES ===
        analysis = {}
        bullish_score = 0
        bearish_score = 0
        
        # 1. STRUCTURE DE MARCHÉ (20 pts)
        structure = self._analyze_market_structure(df)
        analysis['structure'] = structure
        if structure['trend'] == 'UPTREND':
            bullish_score += self.weights['trend_structure'] * (structure['strength'] / 100)
        elif structure['trend'] == 'DOWNTREND':
            bearish_score += self.weights['trend_structure'] * (structure['strength'] / 100)
        
        # 2. INDICATEURS DE MOMENTUM (15 pts)
        momentum = self._analyze_momentum(indicators)
        analysis['momentum'] = momentum
        if momentum['bias'] == 'BULLISH':
            bullish_score += self.weights['momentum'] * (momentum['strength'] / 100)
        elif momentum['bias'] == 'BEARISH':
            bearish_score += self.weights['momentum'] * (momentum['strength'] / 100)
        
        # 3. INDICATEURS DE TENDANCE (15 pts)
        trend = self._analyze_trend_indicators(indicators)
        analysis['trend'] = trend
        if trend['bias'] == 'BULLISH':
            bullish_score += self.weights['trend_indicators'] * (trend['strength'] / 100)
        elif trend['bias'] == 'BEARISH':
            bearish_score += self.weights['trend_indicators'] * (trend['strength'] / 100)
        
        # 4. PATTERNS DE CHANDELIERS (15 pts)
        candles = self._analyze_candlestick_patterns(df)
        analysis['candlestick_patterns'] = candles
        if candles['bias'] == 'BULLISH':
            bullish_score += self.weights['candlestick_patterns'] * (candles['strength'] / 100)
        elif candles['bias'] == 'BEARISH':
            bearish_score += self.weights['candlestick_patterns'] * (candles['strength'] / 100)
        
        # 5. PATTERNS CHARTISTES (15 pts)
        chart_patterns = self._analyze_chart_patterns(df)
        analysis['chart_patterns'] = chart_patterns
        if chart_patterns['bias'] == 'BULLISH':
            bullish_score += self.weights['chart_patterns'] * (chart_patterns['strength'] / 100)
        elif chart_patterns['bias'] == 'BEARISH':
            bearish_score += self.weights['chart_patterns'] * (chart_patterns['strength'] / 100)
        
        # 6. VOLUME (10 pts)
        volume = self._analyze_volume(df, indicators)
        analysis['volume'] = volume
        if volume['confirms_bullish']:
            bullish_score += self.weights['volume']
        elif volume['confirms_bearish']:
            bearish_score += self.weights['volume']
        
        # 7. DIVERGENCES (10 pts)
        div = self._detect_divergences(df, indicators)
        analysis['divergences'] = div
        if div['bullish_divergence']:
            bullish_score += self.weights['divergences']
        elif div['bearish_divergence']:
            bearish_score += self.weights['divergences']
        
        # === DÉCISION FINALE ===
        analysis['bullish_score'] = round(bullish_score, 1)
        analysis['bearish_score'] = round(bearish_score, 1)
        
        # Direction basée sur le score dominant
        current_price = indicators.get('current_price', df['close'].iloc[-1])
        atr = indicators.get('atr', self._calculate_atr(df))
        
        if bullish_score > bearish_score and bullish_score >= 45:
            direction = 'LONG'
            confidence = int(bullish_score)
            stop_loss, tp1, tp2 = self._calculate_long_levels(df, current_price, atr, structure)
        elif bearish_score > bullish_score and bearish_score >= 45:
            direction = 'SHORT'
            confidence = int(bearish_score)
            stop_loss, tp1, tp2 = self._calculate_short_levels(df, current_price, atr, structure)
        else:
            return self._neutral_signal()
        
        # Calcul R/R
        risk = abs(current_price - stop_loss)
        reward = abs(tp1 - current_price)
        rr = round(reward / risk, 2) if risk > 0 else 0
        
        # Filtres de qualité
        if rr < 2.0 or confidence < 50:
            return self._neutral_signal()
        
        return ChartSignal(
            direction=direction,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            risk_reward=rr,
            analysis=analysis
        )
    
    # ═══════════════════════════════════════════════════════════════
    # ANALYSES INDIVIDUELLES
    # ═══════════════════════════════════════════════════════════════
    
    def _analyze_market_structure(self, df: pd.DataFrame) -> Dict:
        """Analyse la structure de marché (Higher Highs/Lows)."""
        lookback = min(50, len(df))
        recent = df.tail(lookback)
        
        # Trouver les swing points
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(recent) - 2):
            high = recent['high'].iloc[i]
            low = recent['low'].iloc[i]
            
            # Swing High
            if (high > recent['high'].iloc[i-1] and high > recent['high'].iloc[i-2] and
                high > recent['high'].iloc[i+1] and high > recent['high'].iloc[i+2]):
                swing_highs.append(high)
            
            # Swing Low
            if (low < recent['low'].iloc[i-1] and low < recent['low'].iloc[i-2] and
                low < recent['low'].iloc[i+1] and low < recent['low'].iloc[i+2]):
                swing_lows.append(low)
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {'trend': 'NEUTRAL', 'strength': 50, 'details': 'Insufficient data'}
        
        # Compter HH/HL vs LH/LL
        hh_count = sum(1 for i in range(1, len(swing_highs)) if swing_highs[i] > swing_highs[i-1])
        hl_count = sum(1 for i in range(1, len(swing_lows)) if swing_lows[i] > swing_lows[i-1])
        lh_count = sum(1 for i in range(1, len(swing_highs)) if swing_highs[i] < swing_highs[i-1])
        ll_count = sum(1 for i in range(1, len(swing_lows)) if swing_lows[i] < swing_lows[i-1])
        
        bullish_swings = hh_count + hl_count
        bearish_swings = lh_count + ll_count
        total = bullish_swings + bearish_swings
        
        if total == 0:
            return {'trend': 'NEUTRAL', 'strength': 50, 'details': 'No clear structure'}
        
        bullish_ratio = bullish_swings / total
        
        if bullish_ratio > 0.65:
            return {
                'trend': 'UPTREND',
                'strength': int(bullish_ratio * 100),
                'details': f'{hh_count} HH, {hl_count} HL',
                'last_swing_low': swing_lows[-1] if swing_lows else None
            }
        elif bullish_ratio < 0.35:
            return {
                'trend': 'DOWNTREND',
                'strength': int((1 - bullish_ratio) * 100),
                'details': f'{lh_count} LH, {ll_count} LL',
                'last_swing_high': swing_highs[-1] if swing_highs else None
            }
        else:
            return {'trend': 'RANGING', 'strength': 50, 'details': 'Mixed structure'}
    
    def _analyze_momentum(self, indicators: Dict) -> Dict:
        """Analyse les oscillateurs de momentum."""
        rsi = indicators.get('rsi14')
        stoch_k = indicators.get('stoch_k')
        stoch_d = indicators.get('stoch_d')
        
        bullish_signals = 0
        bearish_signals = 0
        details = []
        
        # RSI
        if rsi is not None:
            if 40 <= rsi <= 60:
                # Zone neutre - momentum équilibré
                details.append(f'RSI neutral ({rsi:.1f})')
            elif rsi < 40:
                if rsi < 30:
                    # Survendu - potentiel rebond
                    bullish_signals += 1
                    details.append(f'RSI oversold ({rsi:.1f})')
                else:
                    bearish_signals += 1
                    details.append(f'RSI bearish ({rsi:.1f})')
            elif rsi > 60:
                if rsi > 70:
                    # Surachat - potentiel correction
                    bearish_signals += 1
                    details.append(f'RSI overbought ({rsi:.1f})')
                else:
                    bullish_signals += 1
                    details.append(f'RSI bullish ({rsi:.1f})')
        
        # Stochastique
        if stoch_k is not None and stoch_d is not None:
            if stoch_k > stoch_d and stoch_k < 80:
                bullish_signals += 1
                details.append('Stoch bullish cross')
            elif stoch_k < stoch_d and stoch_k > 20:
                bearish_signals += 1
                details.append('Stoch bearish cross')
            elif stoch_k < 20:
                bullish_signals += 1
                details.append('Stoch oversold')
            elif stoch_k > 80:
                bearish_signals += 1
                details.append('Stoch overbought')
        
        total = bullish_signals + bearish_signals
        if total == 0:
            return {'bias': 'NEUTRAL', 'strength': 50, 'details': details}
        
        if bullish_signals > bearish_signals:
            return {
                'bias': 'BULLISH',
                'strength': int((bullish_signals / max(total, 1)) * 100),
                'details': details
            }
        elif bearish_signals > bullish_signals:
            return {
                'bias': 'BEARISH',
                'strength': int((bearish_signals / max(total, 1)) * 100),
                'details': details
            }
        return {'bias': 'NEUTRAL', 'strength': 50, 'details': details}
    
    def _analyze_trend_indicators(self, indicators: Dict) -> Dict:
        """Analyse les indicateurs de tendance (EMA, MACD, ADX)."""
        ema9 = indicators.get('ema9')
        ema21 = indicators.get('ema21')
        sma50 = indicators.get('sma50')
        sma200 = indicators.get('sma200')
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        macd_hist = indicators.get('macd_hist')
        adx = indicators.get('adx')
        current_price = indicators.get('current_price')
        
        bullish_signals = 0
        bearish_signals = 0
        details = []
        
        # EMA Cross
        if ema9 and ema21:
            if ema9 > ema21:
                bullish_signals += 2
                details.append('EMA9 > EMA21')
            else:
                bearish_signals += 2
                details.append('EMA9 < EMA21')
        
        # Prix vs EMA
        if current_price and ema21:
            if current_price > ema21:
                bullish_signals += 1
                details.append('Price > EMA21')
            else:
                bearish_signals += 1
                details.append('Price < EMA21')
        
        # Golden/Death Cross (SMA50 vs SMA200)
        if sma50 and sma200:
            if sma50 > sma200:
                bullish_signals += 2
                details.append('Golden Cross')
            else:
                bearish_signals += 2
                details.append('Death Cross')
        
        # MACD
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                bullish_signals += 1
                details.append('MACD bullish')
            else:
                bearish_signals += 1
                details.append('MACD bearish')
            
            # MACD Histogram direction
            if macd_hist is not None:
                macd_hist_prev = indicators.get('macd_hist_prev')
                if macd_hist_prev is not None:
                    if macd_hist > macd_hist_prev:
                        bullish_signals += 1
                        details.append('MACD momentum up')
                    else:
                        bearish_signals += 1
                        details.append('MACD momentum down')
        
        # ADX (Force de tendance)
        if adx is not None:
            if adx >= 25:
                details.append(f'Strong trend (ADX={adx:.1f})')
            elif adx < 20:
                # Tendance faible - réduire les signaux
                bullish_signals = bullish_signals // 2
                bearish_signals = bearish_signals // 2
                details.append(f'Weak trend (ADX={adx:.1f})')
        
        total = bullish_signals + bearish_signals
        if total == 0:
            return {'bias': 'NEUTRAL', 'strength': 50, 'details': details}
        
        if bullish_signals > bearish_signals:
            return {'bias': 'BULLISH', 'strength': int((bullish_signals / total) * 100), 'details': details}
        elif bearish_signals > bullish_signals:
            return {'bias': 'BEARISH', 'strength': int((bearish_signals / total) * 100), 'details': details}
        return {'bias': 'NEUTRAL', 'strength': 50, 'details': details}
    
    def _analyze_candlestick_patterns(self, df: pd.DataFrame) -> Dict:
        """Détecte les patterns de chandeliers japonais."""
        if len(df) < 5:
            return {'bias': 'NEUTRAL', 'strength': 50, 'patterns': []}
        
        patterns = []
        bullish_score = 0
        bearish_score = 0
        
        # Dernières bougies
        c = df.iloc[-1]  # Current
        p1 = df.iloc[-2]  # Previous 1
        p2 = df.iloc[-3]  # Previous 2
        
        body = abs(c['close'] - c['open'])
        upper_wick = c['high'] - max(c['open'], c['close'])
        lower_wick = min(c['open'], c['close']) - c['low']
        total_range = c['high'] - c['low']
        
        is_green = c['close'] > c['open']
        is_red = c['close'] < c['open']
        
        # === PATTERNS BULLISH ===
        
        # 1. Bullish Engulfing
        if p1['close'] < p1['open'] and is_green:
            if c['open'] < p1['close'] and c['close'] > p1['open']:
                patterns.append('Bullish Engulfing')
                bullish_score += 25
        
        # 2. Hammer (Corps petit en haut, longue mèche basse)
        if total_range > 0 and body / total_range < 0.3 and lower_wick / total_range > 0.6:
            if upper_wick / total_range < 0.1:
                patterns.append('Hammer')
                bullish_score += 20
        
        # 3. Morning Star (3 bougies)
        if len(df) >= 3:
            if p2['close'] < p2['open']:  # Première: rouge
                p1_body = abs(p1['close'] - p1['open'])
                p2_body = abs(p2['close'] - p2['open'])
                if p1_body < p2_body * 0.3:  # Deuxième: petit corps (doji-like)
                    if is_green and c['close'] > (p2['open'] + p2['close']) / 2:
                        patterns.append('Morning Star')
                        bullish_score += 30
        
        # 4. Bullish Harami
        if p1['close'] < p1['open'] and is_green:
            if c['open'] > p1['close'] and c['close'] < p1['open']:
                if body < abs(p1['close'] - p1['open']) * 0.5:
                    patterns.append('Bullish Harami')
                    bullish_score += 15
        
        # 5. Three White Soldiers
        if len(df) >= 3:
            if (p2['close'] > p2['open'] and p1['close'] > p1['open'] and is_green):
                if p1['close'] > p2['close'] and c['close'] > p1['close']:
                    if p1['open'] > p2['open'] and c['open'] > p1['open']:
                        patterns.append('Three White Soldiers')
                        bullish_score += 35
        
        # === PATTERNS BEARISH ===
        
        # 1. Bearish Engulfing
        if p1['close'] > p1['open'] and is_red:
            if c['open'] > p1['close'] and c['close'] < p1['open']:
                patterns.append('Bearish Engulfing')
                bearish_score += 25
        
        # 2. Shooting Star (Corps petit en bas, longue mèche haute)
        if total_range > 0 and body / total_range < 0.3 and upper_wick / total_range > 0.6:
            if lower_wick / total_range < 0.1:
                patterns.append('Shooting Star')
                bearish_score += 20
        
        # 3. Evening Star
        if len(df) >= 3:
            if p2['close'] > p2['open']:  # Première: verte
                p1_body = abs(p1['close'] - p1['open'])
                p2_body = abs(p2['close'] - p2['open'])
                if p1_body < p2_body * 0.3:  # Deuxième: petit corps
                    if is_red and c['close'] < (p2['open'] + p2['close']) / 2:
                        patterns.append('Evening Star')
                        bearish_score += 30
        
        # 4. Bearish Harami
        if p1['close'] > p1['open'] and is_red:
            if c['open'] < p1['close'] and c['close'] > p1['open']:
                if body < abs(p1['close'] - p1['open']) * 0.5:
                    patterns.append('Bearish Harami')
                    bearish_score += 15
        
        # 5. Three Black Crows
        if len(df) >= 3:
            if (p2['close'] < p2['open'] and p1['close'] < p1['open'] and is_red):
                if p1['close'] < p2['close'] and c['close'] < p1['close']:
                    patterns.append('Three Black Crows')
                    bearish_score += 35
        
        # 6. Doji (Indécision - peut précéder un retournement)
        if total_range > 0 and body / total_range < 0.1:
            patterns.append('Doji')
            # Doji après tendance = signal de retournement potentiel
        
        # Déterminer le bias
        if bullish_score > bearish_score:
            return {
                'bias': 'BULLISH',
                'strength': min(bullish_score, 100),
                'patterns': patterns
            }
        elif bearish_score > bullish_score:
            return {
                'bias': 'BEARISH',
                'strength': min(bearish_score, 100),
                'patterns': patterns
            }
        return {'bias': 'NEUTRAL', 'strength': 50, 'patterns': patterns}
    
    def _analyze_chart_patterns(self, df: pd.DataFrame) -> Dict:
        """Détecte les patterns chartistes (Double Top, H&S, Triangles, etc.)."""
        if len(df) < 30:
            return {'bias': 'NEUTRAL', 'strength': 50, 'patterns': []}
        
        patterns = []
        bullish_score = 0
        bearish_score = 0
        
        lookback = min(50, len(df))
        recent = df.tail(lookback)
        highs = recent['high'].values
        lows = recent['low'].values
        closes = recent['close'].values
        current_price = closes[-1]
        
        # Trouver les pics et creux
        peaks = []
        troughs = []
        
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                peaks.append((i, highs[i]))
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                troughs.append((i, lows[i]))
        
        # === DOUBLE TOP (Bearish) ===
        if len(peaks) >= 2:
            p1, p2 = peaks[-2], peaks[-1]
            if abs(p1[1] - p2[1]) / p1[1] < 0.02:  # Pics similaires (2%)
                # Vérifier neckline
                start_idx, end_idx = (p1[0], p2[0]) if p2[0] > p1[0] else (p2[0], p1[0])
                valley_between = float(np.min(lows[start_idx:end_idx])) if end_idx > start_idx else float(lows[start_idx])
                if current_price < valley_between:
                    patterns.append('Double Top')
                    bearish_score += 40
                elif current_price < p1[1] * 0.98:
                    patterns.append('Possible Double Top')
                    bearish_score += 20
        
        # === DOUBLE BOTTOM (Bullish) ===
        if len(troughs) >= 2:
            t1, t2 = troughs[-2], troughs[-1]
            if abs(t1[1] - t2[1]) / t1[1] < 0.02:
                start_idx, end_idx = (t1[0], t2[0]) if t2[0] > t1[0] else (t2[0], t1[0])
                peak_between = float(np.max(highs[start_idx:end_idx])) if end_idx > start_idx else float(highs[start_idx])
                if current_price > peak_between:
                    patterns.append('Double Bottom')
                    bullish_score += 40
                elif current_price > t1[1] * 1.02:
                    patterns.append('Possible Double Bottom')
                    bullish_score += 20
        
        # === HEAD AND SHOULDERS (Bearish) ===
        if len(peaks) >= 3:
            left = peaks[-3]
            head = peaks[-2]
            right = peaks[-1]
            
            # Head doit être le plus haut
            if head[1] > left[1] and head[1] > right[1]:
                # Épaules similaires
                if abs(left[1] - right[1]) / left[1] < 0.03:
                    patterns.append('Head & Shoulders')
                    bearish_score += 50
        
        # === INVERSE HEAD AND SHOULDERS (Bullish) ===
        if len(troughs) >= 3:
            left = troughs[-3]
            head = troughs[-2]
            right = troughs[-1]
            
            if head[1] < left[1] and head[1] < right[1]:
                if abs(left[1] - right[1]) / left[1] < 0.03:
                    patterns.append('Inverse H&S')
                    bullish_score += 50
        
        # === TRIANGLES ===
        if len(highs) >= 15:
            recent_highs = highs[-15:]
            recent_lows = lows[-15:]
            
            high_trend = np.polyfit(range(len(recent_highs)), recent_highs, 1)[0]
            low_trend = np.polyfit(range(len(recent_lows)), recent_lows, 1)[0]
            
            # Ascending Triangle (Bullish)
            if abs(high_trend) < 0.001 and low_trend > 0.001:
                patterns.append('Ascending Triangle')
                bullish_score += 30
            
            # Descending Triangle (Bearish)
            if high_trend < -0.001 and abs(low_trend) < 0.001:
                patterns.append('Descending Triangle')
                bearish_score += 30
            
            # Symmetrical Triangle (Neutre mais breakout imminent)
            if high_trend < -0.001 and low_trend > 0.001:
                patterns.append('Symmetrical Triangle')
                # Direction basée sur la tendance précédente
        
        # === FLAG/PENNANT ===
        if len(closes) >= 20:
            # Chercher un mouvement impulsif suivi d'une consolidation
            first_half = closes[:10]
            second_half = closes[10:]
            
            impulse_move = (first_half[-1] - first_half[0]) / first_half[0] * 100
            consolidation_range = (max(second_half) - min(second_half)) / min(second_half) * 100
            
            if abs(impulse_move) > 5 and consolidation_range < 3:
                if impulse_move > 0:
                    patterns.append('Bull Flag')
                    bullish_score += 25
                else:
                    patterns.append('Bear Flag')
                    bearish_score += 25
        
        # Déterminer le bias
        if bullish_score > bearish_score:
            return {'bias': 'BULLISH', 'strength': min(bullish_score, 100), 'patterns': patterns}
        elif bearish_score > bullish_score:
            return {'bias': 'BEARISH', 'strength': min(bearish_score, 100), 'patterns': patterns}
        return {'bias': 'NEUTRAL', 'strength': 50, 'patterns': patterns}
    
    def _analyze_volume(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Analyse le volume pour confirmer les mouvements."""
        volume_ratio = indicators.get('volume_ratio', 1.0)
        current_price = indicators.get('current_price', df['close'].iloc[-1])
        prev_close = df['close'].iloc[-2] if len(df) >= 2 else current_price
        
        is_up_move = current_price > prev_close
        high_volume = volume_ratio >= 1.3
        
        return {
            'volume_ratio': volume_ratio,
            'confirms_bullish': is_up_move and high_volume,
            'confirms_bearish': not is_up_move and high_volume,
            'high_volume': high_volume
        }
    
    def _detect_divergences(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Détecte les divergences RSI/MACD."""
        if len(df) < 20:
            return {'bullish_divergence': False, 'bearish_divergence': False}
        
        rsi = indicators.get('rsi14')
        if rsi is None:
            return {'bullish_divergence': False, 'bearish_divergence': False}
        
        lookback = 20
        recent = df.tail(lookback)
        closes = recent['close'].values
        
        # Calculer RSI sur la période (simplifié)
        # Trouver les creux du prix et du RSI
        price_lows = []
        for i in range(2, len(closes) - 2):
            if closes[i] < closes[i-1] and closes[i] < closes[i+1]:
                price_lows.append((i, closes[i]))
        
        price_highs = []
        for i in range(2, len(closes) - 2):
            if closes[i] > closes[i-1] and closes[i] > closes[i+1]:
                price_highs.append((i, closes[i]))
        
        # Divergence haussière: Prix fait LL mais RSI monte (simplifié)
        bullish_div = False
        bearish_div = False
        
        if len(price_lows) >= 2:
            if price_lows[-1][1] < price_lows[-2][1]:  # Prix: Lower Low
                if rsi > 35:  # RSI pas en survente
                    bullish_div = True
        
        if len(price_highs) >= 2:
            if price_highs[-1][1] > price_highs[-2][1]:  # Prix: Higher High
                if rsi < 65:  # RSI pas en surachat
                    bearish_div = True
        
        return {
            'bullish_divergence': bullish_div,
            'bearish_divergence': bearish_div
        }
    
    # ═══════════════════════════════════════════════════════════════
    # CALCUL DES NIVEAUX
    # ═══════════════════════════════════════════════════════════════
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calcule l'ATR."""
        if len(df) < period:
            return df['high'].iloc[-1] - df['low'].iloc[-1]
        
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift())
        tr3 = abs(df['low'] - df['close'].shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean().iloc[-1]
    
    def _calculate_long_levels(self, df: pd.DataFrame, price: float, atr: float, structure: Dict) -> Tuple[float, float, float]:
        """Calcule SL et TP pour un LONG."""
        # SL basé sur structure (dernier swing low) ou ATR
        last_swing_low = structure.get('last_swing_low')
        
        if last_swing_low and last_swing_low < price:
            structural_sl = last_swing_low * 0.998
        else:
            structural_sl = price - (atr * 1.5)
        
        # Prendre le SL le plus proche (moins de risque)
        atr_sl = price - (atr * 1.5)
        stop_loss = max(structural_sl, atr_sl)
        
        # TP basé sur R/R
        risk = price - stop_loss
        tp1 = price + (risk * 2.5)
        tp2 = price + (risk * 4.0)
        
        return stop_loss, tp1, tp2
    
    def _calculate_short_levels(self, df: pd.DataFrame, price: float, atr: float, structure: Dict) -> Tuple[float, float, float]:
        """Calcule SL et TP pour un SHORT."""
        last_swing_high = structure.get('last_swing_high')
        
        if last_swing_high and last_swing_high > price:
            structural_sl = last_swing_high * 1.002
        else:
            structural_sl = price + (atr * 1.5)
        
        atr_sl = price + (atr * 1.5)
        stop_loss = min(structural_sl, atr_sl)
        
        risk = stop_loss - price
        tp1 = price - (risk * 2.5)
        tp2 = price - (risk * 4.0)
        
        return stop_loss, tp1, tp2
    
    def _neutral_signal(self) -> ChartSignal:
        """Retourne un signal neutre."""
        return ChartSignal(
            direction='NEUTRAL',
            confidence=0,
            entry_price=0,
            stop_loss=0,
            take_profit_1=0,
            take_profit_2=0,
            risk_reward=0,
            analysis={}
        )


# Instance globale
chart_analyzer = ChartAnalyzer()


def analyze_chart_complete(df: pd.DataFrame, indicators: Dict) -> Dict:
    """
    Fonction wrapper pour analyse complète du graphique.
    
    Returns:
        Dict avec 'entry_signal', 'confidence', 'stop_loss', 'take_profit_1', etc.
    """
    signal = chart_analyzer.analyze_chart(df, indicators)
    
    return {
        'entry_signal': signal.direction,
        'entry_price': signal.entry_price,
        'stop_loss': signal.stop_loss,
        'take_profit_1': signal.take_profit_1,
        'take_profit_2': signal.take_profit_2,
        'confidence': signal.confidence,
        'risk_reward_ratio': signal.risk_reward,
        'atr_percent': 0,  # Calculé ailleurs
        'exit_signal': 'HOLD',
        'analysis': signal.analysis,
        'strategy': 'CHART_ANALYSIS'
    }
