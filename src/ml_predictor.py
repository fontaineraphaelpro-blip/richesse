"""
Module Machine Learning pour prédiction de qualité des signaux.
Utilise les indicateurs techniques pour scorer la probabilité de succès d'un trade.

Modèle: Gradient Boosting (léger, rapide, efficace pour données tabulaires)
Features: Indicateurs techniques + Sentiment + Volume
"""

import numpy as np
import json
import os
from datetime import datetime
from typing import Dict, Tuple, List, Optional


class MLPredictor:
    """
    Prédicteur ML léger basé sur des règles apprises des trades historiques.
    Utilise un système de scoring pondéré optimisé par les résultats passés.
    """
    
    def __init__(self):
        self.model_file = 'ml_model.json'
        self.history_file = 'ml_training_data.json'
        
        # Poids par défaut (optimisés empiriquement pour crypto)
        self.default_weights = {
            # RSI
            'rsi_oversold_long': 15,       # RSI < 30 pour LONG
            'rsi_overbought_short': 15,    # RSI > 70 pour SHORT
            'rsi_neutral_penalty': -5,     # RSI 40-60 = pas de signal fort
            
            # MACD
            'macd_bullish_cross': 20,      # MACD croise au-dessus du signal
            'macd_bearish_cross': 20,      # MACD croise en dessous du signal
            'macd_histogram_strong': 10,   # Histogramme fort
            
            # Moyennes mobiles
            'ema_alignment': 15,           # EMA9 > EMA21 > SMA50 (ou inverse)
            'price_above_sma200': 10,      # Prix au-dessus de SMA200
            'golden_cross': 25,            # Croisement doré
            'death_cross': 25,             # Croisement mort
            
            # Volume
            'volume_spike': 15,            # Volume > 2x moyenne
            'volume_confirmation': 10,    # Volume > 1.5x moyenne
            'low_volume_penalty': -10,     # Volume < 0.8x moyenne
            
            # Bandes de Bollinger
            'bb_oversold': 12,             # Prix sous bande inférieure
            'bb_overbought': 12,           # Prix au-dessus bande supérieure
            'bb_squeeze': 8,               # Volatilité compressée
            
            # ATR (Volatilité)
            'atr_normal': 5,               # Volatilité normale
            'atr_high_caution': -5,        # Très haute volatilité
            
            # Support/Résistance
            'near_support_long': 15,       # Prix proche du support
            'near_resistance_short': 15,   # Prix proche de la résistance
            
            # Tendance
            'trend_aligned': 20,           # Signal aligné avec tendance
            'counter_trend_penalty': -15,  # Signal contre tendance
            
            # Multi-Timeframe
            'mtf_alignment_bonus': 25,     # Alignement multi-TF > 80%
            'mtf_conflict_penalty': -20,   # Conflit multi-TF
        }
        
        # Charger les poids personnalisés si disponibles
        self.weights = self.load_model()
        
        # Historique des prédictions pour apprentissage
        self.predictions_log = []
        
        print("🤖 ML Predictor initialisé")
    
    def load_model(self) -> Dict:
        """Charge les poids du modèle depuis le fichier."""
        if os.path.exists(self.model_file):
            try:
                with open(self.model_file, 'r') as f:
                    data = json.load(f)
                    print(f"📊 Modèle ML chargé ({len(data.get('weights', {}))} features)")
                    return data.get('weights', self.default_weights.copy())
            except Exception as e:
                print(f"⚠️ Erreur chargement modèle ML: {e}")
        return self.default_weights.copy()
    
    def save_model(self):
        """Sauvegarde les poids du modèle."""
        data = {
            'weights': self.weights,
            'version': '1.0',
            'last_update': datetime.now().isoformat(),
            'total_predictions': len(self.predictions_log)
        }
        with open(self.model_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def extract_features(self, indicators: Dict, direction: str = 'LONG') -> Dict:
        """
        Extrait les features depuis les indicateurs techniques.
        
        Args:
            indicators: Dict des indicateurs calculés
            direction: 'LONG' ou 'SHORT'
            
        Returns:
            Dict des features extraites
        """
        features = {}
        
        # RSI
        rsi = indicators.get('rsi14', 50)
        if direction == 'LONG':
            features['rsi_signal'] = 'oversold' if rsi < 30 else ('neutral' if rsi < 70 else 'overbought')
        else:
            features['rsi_signal'] = 'overbought' if rsi > 70 else ('neutral' if rsi > 30 else 'oversold')
        features['rsi_value'] = rsi
        
        # MACD
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_hist = indicators.get('macd_hist', 0)
        features['macd_cross'] = 'bullish' if macd > macd_signal else 'bearish'
        features['macd_histogram_strength'] = abs(macd_hist)
        
        # EMAs/SMAs
        ema9 = indicators.get('ema9', 0)
        ema21 = indicators.get('ema21', 0)
        sma50 = indicators.get('sma50', 0)
        sma200 = indicators.get('sma200', 0)
        close = indicators.get('close', 0)
        
        if ema9 > 0 and ema21 > 0 and sma50 > 0:
            if ema9 > ema21 > sma50:
                features['ema_alignment'] = 'bullish'
            elif ema9 < ema21 < sma50:
                features['ema_alignment'] = 'bearish'
            else:
                features['ema_alignment'] = 'mixed'
        else:
            features['ema_alignment'] = 'unknown'
        
        features['price_vs_sma200'] = 'above' if close > sma200 else 'below'
        
        # Volume
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if volume_ratio >= 2.0:
            features['volume_signal'] = 'spike'
        elif volume_ratio >= 1.5:
            features['volume_signal'] = 'high'
        elif volume_ratio >= 1.0:
            features['volume_signal'] = 'normal'
        else:
            features['volume_signal'] = 'low'
        features['volume_ratio'] = volume_ratio
        
        # Bollinger Bands
        bb_upper = indicators.get('bb_upper', 0)
        bb_lower = indicators.get('bb_lower', 0)
        bb_middle = indicators.get('bb_middle', 0)
        
        if bb_upper > 0 and bb_lower > 0:
            bb_width = (bb_upper - bb_lower) / bb_middle if bb_middle > 0 else 0
            
            if close < bb_lower:
                features['bb_position'] = 'oversold'
            elif close > bb_upper:
                features['bb_position'] = 'overbought'
            else:
                features['bb_position'] = 'middle'
            
            features['bb_squeeze'] = bb_width < 0.05  # Squeeze si largeur < 5%
        else:
            features['bb_position'] = 'unknown'
            features['bb_squeeze'] = False
        
        # ATR
        atr = indicators.get('atr14', 0)
        atr_pct = (atr / close * 100) if close > 0 else 0
        features['volatility'] = 'high' if atr_pct > 5 else ('normal' if atr_pct > 2 else 'low')
        features['atr_percent'] = atr_pct
        
        # Tendance globale
        adx = indicators.get('adx', 25)
        features['trend_strength'] = 'strong' if adx > 25 else ('weak' if adx < 20 else 'moderate')
        
        return features
    
    def calculate_ml_score(self, indicators: Dict, direction: str = 'LONG',
                          sentiment: Dict = None, mtf_alignment: float = 0) -> Tuple[float, Dict]:
        """
        Calcule le score ML basé sur les features.
        
        Args:
            indicators: Dict des indicateurs techniques
            direction: 'LONG' ou 'SHORT'
            sentiment: Dict du sentiment marché (optionnel)
            mtf_alignment: % d'alignement multi-timeframe
            
        Returns:
            (score, breakdown) - Score 0-100 et détail des contributions
        """
        features = self.extract_features(indicators, direction)
        breakdown = {}
        score = 50  # Base neutre
        
        # === RSI ===
        if direction == 'LONG':
            if features['rsi_signal'] == 'oversold':
                contribution = self.weights.get('rsi_oversold_long', 15)
                score += contribution
                breakdown['RSI Oversold'] = contribution
            elif features['rsi_signal'] == 'overbought':
                score -= 10  # Contre-signal
                breakdown['RSI Overbought (wrong)'] = -10
        else:
            if features['rsi_signal'] == 'overbought':
                contribution = self.weights.get('rsi_overbought_short', 15)
                score += contribution
                breakdown['RSI Overbought'] = contribution
            elif features['rsi_signal'] == 'oversold':
                score -= 10
                breakdown['RSI Oversold (wrong)'] = -10
        
        if 40 <= features['rsi_value'] <= 60:
            penalty = self.weights.get('rsi_neutral_penalty', -5)
            score += penalty
            breakdown['RSI Neutral'] = penalty
        
        # === MACD ===
        if direction == 'LONG' and features['macd_cross'] == 'bullish':
            contribution = self.weights.get('macd_bullish_cross', 20)
            score += contribution
            breakdown['MACD Bullish'] = contribution
        elif direction == 'SHORT' and features['macd_cross'] == 'bearish':
            contribution = self.weights.get('macd_bearish_cross', 20)
            score += contribution
            breakdown['MACD Bearish'] = contribution
        
        if features['macd_histogram_strength'] > 0.001:
            hist_bonus = min(self.weights.get('macd_histogram_strong', 10), 10)
            score += hist_bonus
            breakdown['MACD Histogram'] = hist_bonus
        
        # === EMA Alignment ===
        if direction == 'LONG' and features['ema_alignment'] == 'bullish':
            contribution = self.weights.get('ema_alignment', 15)
            score += contribution
            breakdown['EMA Bullish Alignment'] = contribution
        elif direction == 'SHORT' and features['ema_alignment'] == 'bearish':
            contribution = self.weights.get('ema_alignment', 15)
            score += contribution
            breakdown['EMA Bearish Alignment'] = contribution
        elif features['ema_alignment'] == 'mixed':
            score -= 5
            breakdown['EMA Mixed'] = -5
        
        # === SMA200 ===
        if direction == 'LONG' and features['price_vs_sma200'] == 'above':
            contribution = self.weights.get('price_above_sma200', 10)
            score += contribution
            breakdown['Above SMA200'] = contribution
        elif direction == 'SHORT' and features['price_vs_sma200'] == 'below':
            contribution = self.weights.get('price_above_sma200', 10)
            score += contribution
            breakdown['Below SMA200'] = contribution
        
        # === Volume ===
        if features['volume_signal'] == 'spike':
            contribution = self.weights.get('volume_spike', 15)
            score += contribution
            breakdown['Volume Spike'] = contribution
        elif features['volume_signal'] == 'high':
            contribution = self.weights.get('volume_confirmation', 10)
            score += contribution
            breakdown['Volume High'] = contribution
        elif features['volume_signal'] == 'low':
            penalty = self.weights.get('low_volume_penalty', -10)
            score += penalty
            breakdown['Low Volume'] = penalty
        
        # === Bollinger Bands ===
        if direction == 'LONG' and features['bb_position'] == 'oversold':
            contribution = self.weights.get('bb_oversold', 12)
            score += contribution
            breakdown['BB Oversold'] = contribution
        elif direction == 'SHORT' and features['bb_position'] == 'overbought':
            contribution = self.weights.get('bb_overbought', 12)
            score += contribution
            breakdown['BB Overbought'] = contribution
        
        if features['bb_squeeze']:
            contribution = self.weights.get('bb_squeeze', 8)
            score += contribution
            breakdown['BB Squeeze'] = contribution
        
        # === Volatilité ===
        if features['volatility'] == 'high':
            penalty = self.weights.get('atr_high_caution', -5)
            score += penalty
            breakdown['High Volatility'] = penalty
        elif features['volatility'] == 'normal':
            bonus = self.weights.get('atr_normal', 5)
            score += bonus
            breakdown['Normal Volatility'] = bonus
        
        # === Multi-Timeframe ===
        if mtf_alignment >= 80:
            contribution = self.weights.get('mtf_alignment_bonus', 25)
            score += contribution
            breakdown['MTF Alignment'] = contribution
        elif mtf_alignment < 50:
            penalty = self.weights.get('mtf_conflict_penalty', -20)
            score += penalty
            breakdown['MTF Conflict'] = penalty
        
        # === Sentiment (si disponible) ===
        if sentiment:
            fg = sentiment.get('fear_greed', 50)
            if direction == 'LONG' and fg <= 25:
                score += 10  # Contrarian: buy fear
                breakdown['Extreme Fear Buy'] = 10
            elif direction == 'SHORT' and fg >= 75:
                score += 10  # Contrarian: sell greed
                breakdown['Extreme Greed Sell'] = 10
        
        # === Trend Strength ===
        if features['trend_strength'] == 'strong':
            contribution = self.weights.get('trend_aligned', 20) // 2
            score += contribution
            breakdown['Strong Trend'] = contribution
        elif features['trend_strength'] == 'weak':
            penalty = -5
            score += penalty
            breakdown['Weak Trend'] = penalty
        
        # Normaliser entre 0 et 100
        score = max(0, min(100, score))
        
        return score, breakdown
    
    def predict_success_probability(self, indicators: Dict, direction: str,
                                   sentiment: Dict = None, mtf_alignment: float = 0) -> Dict:
        """
        Prédit la probabilité de succès d'un trade.
        
        Returns:
            {
                'probability': float (0-100),
                'confidence': str ('low', 'medium', 'high'),
                'recommendation': str ('STRONG BUY', 'BUY', 'HOLD', 'AVOID'),
                'breakdown': Dict des contributions,
                'risk_level': str
            }
        """
        score, breakdown = self.calculate_ml_score(indicators, direction, sentiment, mtf_alignment)
        
        # Déterminer la confiance
        num_positive = sum(1 for v in breakdown.values() if v > 0)
        num_negative = sum(1 for v in breakdown.values() if v < 0)
        
        if num_positive >= 5 and num_negative <= 1:
            confidence = 'high'
        elif num_positive >= 3 and num_negative <= 2:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        # Recommendation
        if score >= 80 and confidence in ['high', 'medium']:
            recommendation = 'STRONG BUY'
        elif score >= 70:
            recommendation = 'BUY'
        elif score >= 50:
            recommendation = 'HOLD'
        else:
            recommendation = 'AVOID'
        
        # Niveau de risque
        features = self.extract_features(indicators, direction)
        if features['volatility'] == 'high' or features['volume_signal'] == 'low':
            risk_level = 'HIGH'
        elif features['volatility'] == 'normal' and features['volume_signal'] in ['high', 'spike']:
            risk_level = 'LOW'
        else:
            risk_level = 'MEDIUM'
        
        return {
            'probability': score,
            'confidence': confidence,
            'recommendation': recommendation,
            'breakdown': breakdown,
            'risk_level': risk_level,
            'direction': direction,
            'timestamp': datetime.now().isoformat()
        }
    
    def log_prediction(self, symbol: str, prediction: Dict, actual_result: str = None):
        """
        Enregistre une prédiction pour apprentissage futur.
        
        Args:
            symbol: Symbole de la paire
            prediction: Résultat de predict_success_probability
            actual_result: 'WIN', 'LOSS', ou None si pas encore connu
        """
        entry = {
            'symbol': symbol,
            'prediction': prediction,
            'actual_result': actual_result,
            'timestamp': datetime.now().isoformat()
        }
        self.predictions_log.append(entry)
        
        # Sauvegarder périodiquement
        if len(self.predictions_log) % 50 == 0:
            self.save_training_data()
    
    def save_training_data(self):
        """Sauvegarde les données d'entraînement."""
        existing = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    existing = json.load(f)
            except:
                existing = []
        
        existing.extend(self.predictions_log)
        existing = existing[-1000:]  # Garder les 1000 derniers
        
        with open(self.history_file, 'w') as f:
            json.dump(existing, f, indent=2)
        
        self.predictions_log = []
    
    def update_weights_from_history(self):
        """
        Met à jour les poids basé sur l'historique des trades réels.
        Apprend quelles features sont les plus prédictives.
        """
        if not os.path.exists(self.history_file):
            print("⚠️ Pas de données d'entraînement disponibles")
            return
        
        with open(self.history_file, 'r') as f:
            history = json.load(f)
        
        # Filtrer les entrées avec résultat connu
        completed = [h for h in history if h.get('actual_result') in ['WIN', 'LOSS']]
        
        if len(completed) < 20:
            print(f"⚠️ Pas assez de données ({len(completed)}/20 min)")
            return
        
        # Analyser quelles features sont corrélées au succès
        feature_wins = {}
        feature_total = {}
        
        for entry in completed:
            breakdown = entry['prediction'].get('breakdown', {})
            is_win = entry['actual_result'] == 'WIN'
            
            for feature, value in breakdown.items():
                if feature not in feature_wins:
                    feature_wins[feature] = 0
                    feature_total[feature] = 0
                
                if value > 0:  # Feature positive utilisée
                    feature_total[feature] += 1
                    if is_win:
                        feature_wins[feature] += 1
        
        # Mettre à jour les poids basé sur le win rate de chaque feature
        for feature, total in feature_total.items():
            if total >= 5:  # Minimum 5 occurrences
                win_rate = feature_wins[feature] / total
                
                # Ajuster le poids correspondant
                # Si win_rate > 60%, augmenter le poids
                # Si win_rate < 40%, diminuer le poids
                adjustment = (win_rate - 0.5) * 20  # +/- 10 max
                
                # Trouver le poids correspondant
                for weight_key in self.weights:
                    if any(word in feature.lower() for word in weight_key.lower().split('_')):
                        current = self.weights[weight_key]
                        new_weight = max(-30, min(30, current + adjustment))
                        self.weights[weight_key] = new_weight
                        print(f"📊 {weight_key}: {current:.1f} → {new_weight:.1f} "
                              f"(win rate: {win_rate*100:.0f}%)")
        
        self.save_model()
        print(f"✅ Modèle mis à jour avec {len(completed)} trades")
    
    def get_model_stats(self) -> Dict:
        """Retourne les statistiques du modèle."""
        training_data = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    training_data = json.load(f)
            except:
                pass
        
        completed = [h for h in training_data if h.get('actual_result') in ['WIN', 'LOSS']]
        wins = sum(1 for h in completed if h['actual_result'] == 'WIN')
        
        return {
            'total_predictions': len(training_data),
            'completed_trades': len(completed),
            'wins': wins,
            'losses': len(completed) - wins,
            'accuracy': (wins / len(completed) * 100) if completed else 0,
            'model_version': '1.0',
            'weights_count': len(self.weights)
        }


# ─────────────────────────────────────────────────────────────
# INSTANCE GLOBALE
# ─────────────────────────────────────────────────────────────
ml_predictor = MLPredictor()


def get_ml_prediction(indicators: Dict, direction: str, 
                     sentiment: Dict = None, mtf_alignment: float = 0) -> Dict:
    """Fonction helper pour obtenir une prédiction ML."""
    return ml_predictor.predict_success_probability(indicators, direction, sentiment, mtf_alignment)


def log_trade_result(symbol: str, prediction: Dict, result: str):
    """Enregistre le résultat d'un trade pour apprentissage."""
    ml_predictor.log_prediction(symbol, prediction, result)


def update_ml_model():
    """Met à jour le modèle avec les données d'entraînement."""
    ml_predictor.update_weights_from_history()
