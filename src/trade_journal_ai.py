"""
Module Trade Journal AI: Analyse intelligente des trades passés.

Fonctionnalités:
- Enregistrement détaillé de chaque trade (entrée, sortie, contexte marché)
- Analyse ML des patterns de succès/échec
- Identification des erreurs récurrentes
- Recommandations personnalisées basées sur l'historique
- Statistiques de performance avancées (Sharpe, Sortino, Max DD)
- Détection des meilleures/pires conditions de trading
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import statistics


class TradeJournalAI:
    """
    Journal de trading intelligent avec analyse ML des performances.
    Apprend des erreurs passées pour améliorer les futures décisions.
    """
    
    def __init__(self, journal_path: Optional[str] = None):
        if journal_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.journal_path = os.path.join(base_dir, 'trade_journal.json')
        else:
            self.journal_path = journal_path
        
        # Charger ou créer le journal
        self.journal = self._load_journal()
        
        # Statistiques calculées
        self.stats_cache = {}
        self.stats_cache_time = None
        
        # Patterns identifiés
        self.error_patterns = []
        self.success_patterns = []
        
        # Seuils de performance
        self.performance_thresholds = {
            'excellent': 3.0,   # > 3% = excellent
            'good': 1.0,       # 1-3% = bon
            'neutral': 0.0,    # 0-1% = neutre
            'bad': -2.0,       # -2 à 0% = mauvais
            'terrible': -100   # < -2% = terrible
        }
        
        print("📔 Trade Journal AI initialisé")
    
    def _load_journal(self) -> Dict:
        """Charge le journal depuis le fichier JSON."""
        if os.path.exists(self.journal_path):
            try:
                with open(self.journal_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Erreur chargement journal: {e}")
        
        return {
            'trades': [],
            'metadata': {
                'created': datetime.now().isoformat(),
                'version': '1.0',
                'total_trades': 0
            },
            'learned_patterns': {
                'avoid_conditions': [],
                'prefer_conditions': []
            }
        }
    
    def _save_journal(self):
        """Sauvegarde le journal sur disque."""
        try:
            self.journal['metadata']['last_updated'] = datetime.now().isoformat()
            self.journal['metadata']['total_trades'] = len(self.journal['trades'])
            
            with open(self.journal_path, 'w') as f:
                json.dump(self.journal, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde journal: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # ENREGISTREMENT DES TRADES
    # ═══════════════════════════════════════════════════════════════
    
    def record_trade_entry(self, trade_data: Dict) -> str:
        """
        Enregistre l'ouverture d'un trade avec tout le contexte.
        
        Args:
            trade_data: {
                'symbol': 'BTCUSDT',
                'direction': 'LONG',
                'entry_price': 50000,
                'amount': 200,
                'stop_loss': 49000,
                'take_profit': 52000,
                'score': 85,
                'indicators': {...},
                'market_context': {...}
            }
        
        Returns:
            trade_id: Identifiant unique du trade
        """
        trade_id = f"{trade_data.get('symbol', 'UNK')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        trade_entry = {
            'id': trade_id,
            'status': 'OPEN',
            'symbol': trade_data.get('symbol'),
            'direction': trade_data.get('direction', 'LONG'),
            'entry_time': datetime.now().isoformat(),
            'entry_price': trade_data.get('entry_price'),
            'amount': trade_data.get('amount'),
            'stop_loss': trade_data.get('stop_loss'),
            'take_profit': trade_data.get('take_profit'),
            'initial_score': trade_data.get('score'),
            
            # Contexte à l'entrée
            'entry_context': {
                'hour': datetime.now().hour,
                'day_of_week': datetime.now().weekday(),
                'indicators': trade_data.get('indicators', {}),
                'market_sentiment': trade_data.get('market_sentiment'),
                'fear_greed': trade_data.get('fear_greed'),
                'btc_trend': trade_data.get('btc_trend'),
                'volume_profile': trade_data.get('volume_profile'),
                'volatility': trade_data.get('volatility'),
                'timeframe': trade_data.get('timeframe', '15m')
            },
            
            # Sera rempli à la sortie
            'exit_time': None,
            'exit_price': None,
            'exit_reason': None,
            'pnl_percent': None,
            'pnl_value': None,
            'duration_minutes': None,
            'max_drawdown': None,
            'max_profit': None
        }
        
        self.journal['trades'].append(trade_entry)
        self._save_journal()
        
        return trade_id
    
    def record_trade_exit(self, symbol: str, exit_data: Dict) -> Optional[Dict]:
        """
        Enregistre la fermeture d'un trade.
        
        Args:
            symbol: Symbole du trade
            exit_data: {
                'exit_price': 51000,
                'exit_reason': 'TP_HIT' | 'SL_HIT' | 'MANUAL' | 'TRAILING_STOP',
                'pnl_percent': 2.5,
                'pnl_value': 50,
                'max_drawdown': -1.2,
                'max_profit': 3.0
            }
        
        Returns:
            Le trade mis à jour ou None
        """
        # Trouver le trade ouvert pour ce symbole
        for trade in reversed(self.journal['trades']):
            if trade['symbol'] == symbol and trade['status'] == 'OPEN':
                # Mise à jour
                trade['status'] = 'CLOSED'
                trade['exit_time'] = datetime.now().isoformat()
                trade['exit_price'] = exit_data.get('exit_price')
                trade['exit_reason'] = exit_data.get('exit_reason')
                trade['pnl_percent'] = exit_data.get('pnl_percent', 0)
                trade['pnl_value'] = exit_data.get('pnl_value', 0)
                trade['max_drawdown'] = exit_data.get('max_drawdown')
                trade['max_profit'] = exit_data.get('max_profit')
                
                # Calcul durée
                entry_time = datetime.fromisoformat(trade['entry_time'])
                duration = (datetime.now() - entry_time).total_seconds() / 60
                trade['duration_minutes'] = round(duration, 1)
                
                # Classification du trade
                trade['classification'] = self._classify_trade(trade)
                
                # Analyse des leçons apprises
                trade['lessons'] = self._extract_lessons(trade)
                
                self._save_journal()
                self._invalidate_cache()
                
                # Mise à jour des patterns appris
                self._update_learned_patterns(trade)
                
                return trade
        
        return None
    
    def _classify_trade(self, trade: Dict) -> str:
        """Classifie la qualité d'un trade."""
        pnl = trade.get('pnl_percent', 0)
        
        for classification, threshold in self.performance_thresholds.items():
            if pnl >= threshold:
                return classification
        
        return 'terrible'
    
    def _extract_lessons(self, trade: Dict) -> List[str]:
        """Extrait les leçons à retenir d'un trade."""
        lessons = []
        pnl = trade.get('pnl_percent', 0)
        exit_reason = trade.get('exit_reason', '')
        context = trade.get('entry_context', {})
        
        # Analyse de l'heure
        hour = context.get('hour', 12)
        if pnl < 0 and (hour < 7 or hour > 22):
            lessons.append(f"❌ Éviter le trading à {hour}h (hors heures optimales)")
        
        # Analyse du jour
        day = context.get('day_of_week', 0)
        day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        if pnl < -2 and day in [5, 6]:  # Weekend
            lessons.append(f"❌ {day_names[day]}: volatilité weekend mal gérée")
        
        # Analyse du Fear & Greed
        fg = context.get('fear_greed', 50)
        if fg and pnl < 0:
            if fg > 70 and trade.get('direction') == 'LONG':
                lessons.append(f"❌ LONG avec Fear&Greed={fg} (greed zone)")
            elif fg < 30 and trade.get('direction') == 'SHORT':
                lessons.append(f"❌ SHORT avec Fear&Greed={fg} (fear zone)")
        
        # Analyse du score initial
        score = trade.get('initial_score', 0)
        if score < 70 and pnl < 0:
            lessons.append(f"❌ Score {score} trop bas - augmenter seuil minimum")
        
        # Analyse du SL
        if exit_reason == 'SL_HIT':
            duration = trade.get('duration_minutes', 0)
            if duration < 15:
                lessons.append("❌ SL touché en < 15min - entrée mal timée")
            
            volatility = context.get('volatility')
            if volatility and volatility > 4:
                lessons.append(f"❌ SL touché avec volatilité={volatility}% - SL trop serré")
        
        # Succès patterns
        if pnl > 2:
            if 9 <= hour <= 16:
                lessons.append(f"✅ Heure optimale {hour}h confirmée")
            direction = trade.get('direction', '')
            if context.get('btc_trend') == direction.lower():
                lessons.append("✅ Trade aligné avec tendance BTC")
        
        return lessons
    
    def _update_learned_patterns(self, trade: Dict):
        """Met à jour les patterns appris basés sur les trades."""
        context = trade.get('entry_context', {})
        pnl = trade.get('pnl_percent', 0)
        
        pattern = {
            'hour': context.get('hour'),
            'day_of_week': context.get('day_of_week'),
            'direction': trade.get('direction'),
            'score_range': self._get_score_range(trade.get('initial_score', 0)),
            'fear_greed_range': self._get_fg_range(context.get('fear_greed')),
            'result': 'win' if pnl > 0 else 'loss',
            'pnl': pnl
        }
        
        if pnl < -1.5:
            self.journal['learned_patterns']['avoid_conditions'].append(pattern)
            # Garder les 50 derniers
            self.journal['learned_patterns']['avoid_conditions'] = \
                self.journal['learned_patterns']['avoid_conditions'][-50:]
        elif pnl > 2:
            self.journal['learned_patterns']['prefer_conditions'].append(pattern)
            self.journal['learned_patterns']['prefer_conditions'] = \
                self.journal['learned_patterns']['prefer_conditions'][-50:]
        
        self._save_journal()
    
    def _get_score_range(self, score: int) -> str:
        if score >= 90:
            return '90+'
        elif score >= 80:
            return '80-89'
        elif score >= 70:
            return '70-79'
        else:
            return '<70'
    
    def _get_fg_range(self, fg: int) -> str:
        if fg is None:
            return 'unknown'
        if fg <= 25:
            return 'extreme_fear'
        elif fg <= 45:
            return 'fear'
        elif fg <= 55:
            return 'neutral'
        elif fg <= 75:
            return 'greed'
        else:
            return 'extreme_greed'
    
    def _invalidate_cache(self):
        """Invalide le cache des statistiques."""
        self.stats_cache = {}
        self.stats_cache_time = None
    
    # ═══════════════════════════════════════════════════════════════
    # STATISTIQUES DE PERFORMANCE
    # ═══════════════════════════════════════════════════════════════
    
    def get_performance_stats(self, period_days: int = 30) -> Dict:
        """
        Calcule les statistiques de performance détaillées.
        
        Returns:
            Dict avec toutes les métriques de performance
        """
        cache_key = f"stats_{period_days}"
        if self.stats_cache.get(cache_key):
            return self.stats_cache[cache_key]
        
        # Filtrer les trades fermés de la période
        cutoff = datetime.now() - timedelta(days=period_days)
        closed_trades = [
            t for t in self.journal['trades']
            if t.get('status') == 'CLOSED' and
            datetime.fromisoformat(t.get('exit_time', datetime.now().isoformat())) > cutoff
        ]
        
        if not closed_trades:
            return {
                'total_trades': 0,
                'message': 'Pas assez de trades pour calculer les stats'
            }
        
        # Métriques de base
        pnls = [t.get('pnl_percent', 0) for t in closed_trades]
        pnl_values = [t.get('pnl_value', 0) for t in closed_trades]
        
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        total_trades = len(closed_trades)
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        avg_win = statistics.mean(wins) if wins else 0
        avg_loss = statistics.mean(losses) if losses else 0
        
        # Profit Factor
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
        
        # Risk/Reward
        risk_reward = (avg_win / abs(avg_loss)) if avg_loss != 0 else float('inf')
        
        # Expectancy
        expectancy = (win_rate/100 * avg_win) + ((100-win_rate)/100 * avg_loss)
        
        # Max Drawdown
        cumulative_pnl = []
        running_total = 0
        for pnl in pnls:
            running_total += pnl
            cumulative_pnl.append(running_total)
        
        max_dd = 0
        peak = 0
        for value in cumulative_pnl:
            if value > peak:
                peak = value
            dd = peak - value
            if dd > max_dd:
                max_dd = dd
        
        # Sharpe Ratio (simplifié)
        if len(pnls) > 1:
            avg_return = statistics.mean(pnls)
            std_return = statistics.stdev(pnls)
            sharpe = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0
        else:
            sharpe = 0
        
        # Sortino Ratio (downside deviation)
        negative_returns = [p for p in pnls if p < 0]
        if len(negative_returns) > 1:
            downside_std = statistics.stdev(negative_returns)
            sortino = (statistics.mean(pnls) / downside_std) * (252 ** 0.5) if downside_std > 0 else 0
        else:
            sortino = sharpe
        
        # Streaks
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        temp_win = 0
        temp_loss = 0
        
        for pnl in pnls:
            if pnl > 0:
                temp_win += 1
                temp_loss = 0
                max_win_streak = max(max_win_streak, temp_win)
            else:
                temp_loss += 1
                temp_win = 0
                max_loss_streak = max(max_loss_streak, temp_loss)
        
        # Dernier streak
        if pnls:
            last_sign = 1 if pnls[-1] > 0 else -1
            for pnl in reversed(pnls):
                if (pnl > 0) == (last_sign > 0):
                    current_streak += last_sign
                else:
                    break
        
        stats = {
            'period_days': period_days,
            'total_trades': total_trades,
            'wins': win_count,
            'losses': loss_count,
            'win_rate': round(win_rate, 1),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'total_pnl_percent': round(sum(pnls), 2),
            'total_pnl_value': round(sum(pnl_values), 2),
            'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else 'N/A',
            'risk_reward': round(risk_reward, 2) if risk_reward != float('inf') else 'N/A',
            'expectancy': round(expectancy, 2),
            'max_drawdown': round(max_dd, 2),
            'sharpe_ratio': round(sharpe, 2),
            'sortino_ratio': round(sortino, 2),
            'max_win_streak': max_win_streak,
            'max_loss_streak': max_loss_streak,
            'current_streak': current_streak,
            'best_trade': round(max(pnls), 2) if pnls else 0,
            'worst_trade': round(min(pnls), 2) if pnls else 0,
            'last_updated': datetime.now().isoformat()
        }
        
        self.stats_cache[cache_key] = stats
        return stats
    
    # ═══════════════════════════════════════════════════════════════
    # ANALYSE DES ERREURS (AI)
    # ═══════════════════════════════════════════════════════════════
    
    def analyze_errors(self) -> Dict:
        """
        Analyse les patterns d'erreurs récurrentes.
        
        Returns:
            Dict avec les erreurs identifiées et recommandations
        """
        closed_trades = [t for t in self.journal['trades'] if t.get('status') == 'CLOSED']
        losing_trades = [t for t in closed_trades if t.get('pnl_percent', 0) < 0]
        
        if len(losing_trades) < 5:
            return {'message': 'Pas assez de trades perdants pour analyse (min 5)'}
        
        # Analyse par heure
        hour_losses = defaultdict(list)
        for trade in losing_trades:
            hour = trade.get('entry_context', {}).get('hour', 12)
            hour_losses[hour].append(trade.get('pnl_percent', 0))
        
        worst_hours = sorted(
            hour_losses.items(),
            key=lambda x: sum(x[1]) / len(x[1])
        )[:3]
        
        # Analyse par jour
        day_losses = defaultdict(list)
        for trade in losing_trades:
            day = trade.get('entry_context', {}).get('day_of_week', 0)
            day_losses[day].append(trade.get('pnl_percent', 0))
        
        day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        worst_days = sorted(
            day_losses.items(),
            key=lambda x: sum(x[1]) / len(x[1])
        )[:2]
        
        # Analyse par raison de sortie
        exit_reasons = defaultdict(lambda: {'count': 0, 'total_loss': 0})
        for trade in losing_trades:
            reason = trade.get('exit_reason', 'UNKNOWN')
            exit_reasons[reason]['count'] += 1
            exit_reasons[reason]['total_loss'] += trade.get('pnl_percent', 0)
        
        # Analyse par score initial
        score_performance = defaultdict(list)
        for trade in closed_trades:
            score_range = self._get_score_range(trade.get('initial_score', 0))
            score_performance[score_range].append(trade.get('pnl_percent', 0))
        
        score_analysis = {
            score_range: {
                'count': len(pnls),
                'avg_pnl': round(sum(pnls) / len(pnls), 2) if pnls else 0,
                'win_rate': round(len([p for p in pnls if p > 0]) / len(pnls) * 100, 1) if pnls else 0
            }
            for score_range, pnls in score_performance.items()
        }
        
        # Générer recommandations
        recommendations = []
        
        for hour, losses in worst_hours:
            avg_loss = sum(losses) / len(losses)
            if avg_loss < -1 and len(losses) >= 3:
                recommendations.append({
                    'type': 'AVOID_HOUR',
                    'value': hour,
                    'reason': f"Perte moyenne de {avg_loss:.1f}% sur {len(losses)} trades à {hour}h",
                    'priority': 'HIGH'
                })
        
        for day, losses in worst_days:
            avg_loss = sum(losses) / len(losses)
            if avg_loss < -1.5 and len(losses) >= 3:
                recommendations.append({
                    'type': 'AVOID_DAY',
                    'value': day_names[day],
                    'reason': f"Perte moyenne de {avg_loss:.1f}% le {day_names[day]}",
                    'priority': 'MEDIUM'
                })
        
        for score_range, data in score_analysis.items():
            if data['avg_pnl'] < -0.5 and data['win_rate'] < 40:
                recommendations.append({
                    'type': 'MIN_SCORE',
                    'value': score_range,
                    'reason': f"Score {score_range}: Win rate {data['win_rate']}%, PnL moyen {data['avg_pnl']}%",
                    'priority': 'HIGH'
                })
        
        return {
            'total_losing_trades': len(losing_trades),
            'worst_hours': [{'hour': h, 'avg_loss': round(sum(l)/len(l), 2), 'count': len(l)} 
                           for h, l in worst_hours],
            'worst_days': [{'day': day_names[d], 'avg_loss': round(sum(l)/len(l), 2), 'count': len(l)} 
                          for d, l in worst_days],
            'exit_reasons': dict(exit_reasons),
            'score_analysis': score_analysis,
            'recommendations': recommendations,
            'analysis_date': datetime.now().isoformat()
        }
    
    def analyze_successes(self) -> Dict:
        """
        Analyse les patterns de trades gagnants.
        
        Returns:
            Dict avec les conditions optimales identifiées
        """
        closed_trades = [t for t in self.journal['trades'] if t.get('status') == 'CLOSED']
        winning_trades = [t for t in closed_trades if t.get('pnl_percent', 0) > 1]
        
        if len(winning_trades) < 5:
            return {'message': 'Pas assez de trades gagnants pour analyse (min 5)'}
        
        # Analyse par heure
        hour_wins = defaultdict(list)
        for trade in winning_trades:
            hour = trade.get('entry_context', {}).get('hour', 12)
            hour_wins[hour].append(trade.get('pnl_percent', 0))
        
        best_hours = sorted(
            hour_wins.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
            reverse=True
        )[:3]
        
        # Analyse par jour
        day_wins = defaultdict(list)
        for trade in winning_trades:
            day = trade.get('entry_context', {}).get('day_of_week', 0)
            day_wins[day].append(trade.get('pnl_percent', 0))
        
        day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        best_days = sorted(
            day_wins.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
            reverse=True
        )[:2]
        
        # Conditions optimales
        optimal_conditions = []
        
        for hour, wins in best_hours:
            if len(wins) >= 3:
                optimal_conditions.append({
                    'type': 'BEST_HOUR',
                    'value': hour,
                    'avg_win': round(sum(wins) / len(wins), 2),
                    'count': len(wins)
                })
        
        for day, wins in best_days:
            if len(wins) >= 3:
                optimal_conditions.append({
                    'type': 'BEST_DAY',
                    'value': day_names[day],
                    'avg_win': round(sum(wins) / len(wins), 2),
                    'count': len(wins)
                })
        
        return {
            'total_winning_trades': len(winning_trades),
            'best_hours': [{'hour': h, 'avg_win': round(sum(w)/len(w), 2), 'count': len(w)} 
                          for h, w in best_hours],
            'best_days': [{'day': day_names[d], 'avg_win': round(sum(w)/len(w), 2), 'count': len(w)} 
                         for d, w in best_days],
            'optimal_conditions': optimal_conditions,
            'analysis_date': datetime.now().isoformat()
        }
    
    # ═══════════════════════════════════════════════════════════════
    # RECOMMANDATIONS INTELLIGENTES
    # ═══════════════════════════════════════════════════════════════
    
    def should_take_trade(self, trade_context: Dict) -> Tuple[bool, str, float]:
        """
        Détermine si un trade devrait être pris basé sur l'historique.
        
        Args:
            trade_context: {
                'hour': 14,
                'day_of_week': 2,
                'score': 85,
                'direction': 'LONG',
                'fear_greed': 45
            }
        
        Returns:
            (should_trade, reason, confidence_modifier)
        """
        hour = trade_context.get('hour', 12)
        day = trade_context.get('day_of_week', 0)
        score = trade_context.get('score', 70)
        
        avoid_patterns = self.journal.get('learned_patterns', {}).get('avoid_conditions', [])
        prefer_patterns = self.journal.get('learned_patterns', {}).get('prefer_conditions', [])
        
        # Vérifier patterns à éviter
        avoid_count = 0
        for pattern in avoid_patterns:
            if pattern.get('hour') == hour:
                avoid_count += 1
            if pattern.get('day_of_week') == day:
                avoid_count += 1
            if pattern.get('score_range') == self._get_score_range(score):
                avoid_count += 1
        
        # Vérifier patterns favorables
        prefer_count = 0
        for pattern in prefer_patterns:
            if pattern.get('hour') == hour:
                prefer_count += 1
            if pattern.get('day_of_week') == day:
                prefer_count += 1
        
        # Décision
        if avoid_count >= 3:
            return (False, f"⚠️ Conditions défavorables détectées ({avoid_count} patterns d'échec)", 0.7)
        elif avoid_count >= 2:
            return (True, f"⚡ Prudence: {avoid_count} patterns de risque", 0.85)
        elif prefer_count >= 2:
            return (True, f"✅ Conditions favorables ({prefer_count} patterns de succès)", 1.15)
        else:
            return (True, "➡️ Conditions neutres", 1.0)
    
    def get_trade_modifier(self, trade_context: Dict) -> float:
        """
        Retourne un modificateur de score basé sur l'historique.
        
        Returns:
            Float entre 0.5 et 1.5
        """
        _, _, modifier = self.should_take_trade(trade_context)
        return modifier
    
    # ═══════════════════════════════════════════════════════════════
    # RAPPORTS
    # ═══════════════════════════════════════════════════════════════
    
    def get_daily_report(self) -> Dict:
        """Génère un rapport journalier."""
        today = datetime.now().date()
        
        today_trades = [
            t for t in self.journal['trades']
            if t.get('status') == 'CLOSED' and
            datetime.fromisoformat(t.get('exit_time', datetime.now().isoformat())).date() == today
        ]
        
        if not today_trades:
            return {
                'date': today.isoformat(),
                'trades': 0,
                'message': 'Aucun trade fermé aujourd\'hui'
            }
        
        pnls = [t.get('pnl_percent', 0) for t in today_trades]
        
        return {
            'date': today.isoformat(),
            'trades': len(today_trades),
            'wins': len([p for p in pnls if p > 0]),
            'losses': len([p for p in pnls if p < 0]),
            'total_pnl': round(sum(pnls), 2),
            'best_trade': round(max(pnls), 2),
            'worst_trade': round(min(pnls), 2),
            'trades_details': [
                {
                    'symbol': t.get('symbol'),
                    'direction': t.get('direction'),
                    'pnl': t.get('pnl_percent'),
                    'exit_reason': t.get('exit_reason')
                }
                for t in today_trades
            ]
        }
    
    def get_complete_analysis(self) -> Dict:
        """Retourne une analyse complète pour le dashboard."""
        return {
            'stats_30d': self.get_performance_stats(30),
            'stats_7d': self.get_performance_stats(7),
            'error_analysis': self.analyze_errors(),
            'success_analysis': self.analyze_successes(),
            'daily_report': self.get_daily_report(),
            'total_trades_all_time': len(self.journal['trades']),
            'learned_patterns_count': {
                'avoid': len(self.journal.get('learned_patterns', {}).get('avoid_conditions', [])),
                'prefer': len(self.journal.get('learned_patterns', {}).get('prefer_conditions', []))
            }
        }


# ═══════════════════════════════════════════════════════════════════
# INSTANCE GLOBALE
# ═══════════════════════════════════════════════════════════════════

_journal_ai = None

def get_trade_journal() -> TradeJournalAI:
    """Retourne l'instance singleton du Trade Journal AI."""
    global _journal_ai
    if _journal_ai is None:
        _journal_ai = TradeJournalAI()
    return _journal_ai


def record_entry(trade_data: Dict) -> str:
    """Raccourci pour enregistrer une entrée."""
    return get_trade_journal().record_trade_entry(trade_data)


def record_exit(symbol: str, exit_data: Dict) -> Optional[Dict]:
    """Raccourci pour enregistrer une sortie."""
    return get_trade_journal().record_trade_exit(symbol, exit_data)


def get_journal_stats(days: int = 30) -> Dict:
    """Raccourci pour obtenir les stats."""
    return get_trade_journal().get_performance_stats(days)


def should_trade(context: Dict) -> Tuple[bool, str, float]:
    """Raccourci pour vérifier si on devrait trader."""
    return get_trade_journal().should_take_trade(context)


def get_trade_modifier(context: Dict) -> float:
    """Raccourci pour obtenir le modificateur."""
    return get_trade_journal().get_trade_modifier(context)
