# -*- coding: utf-8 -*-
"""
Dashboard Statistics Calculator
Calcule les statistiques avancees pour le dashboard
"""

from datetime import datetime, timedelta
from collections import defaultdict
import json


def calculate_advanced_stats(history: list) -> dict:
    """
    Calcule toutes les statistiques avancees depuis l'historique des trades.
    
    Args:
        history: Liste des trades fermes
        
    Returns:
        Dict avec toutes les statistiques
    """
    if not history:
        return get_empty_stats()
    
    # Filtrer uniquement les ventes (trades fermes)
    trades = [t for t in history if 'VENTE' in t.get('type', '') or t.get('exit_price')]
    
    if not trades:
        return get_empty_stats()
    
    # Stats de base
    total_trades = len(trades)
    wins = [t for t in trades if t.get('pnl', 0) > 0]
    losses = [t for t in trades if t.get('pnl', 0) <= 0]
    
    winning_count = len(wins)
    losing_count = len(losses)
    
    total_gains = sum(t.get('pnl', 0) for t in wins)
    total_losses = abs(sum(t.get('pnl', 0) for t in losses))
    
    avg_win = total_gains / winning_count if winning_count > 0 else 0
    avg_loss = total_losses / losing_count if losing_count > 0 else 0
    
    # Profit Factor
    profit_factor = total_gains / total_losses if total_losses > 0 else float('inf') if total_gains > 0 else 0
    profit_factor = min(profit_factor, 99.99)  # Cap for display
    
    # Best/Worst trades
    pnls = [t.get('pnl', 0) for t in trades]
    best_trade = max(pnls) if pnls else 0
    worst_trade = min(pnls) if pnls else 0
    
    best_trade_pair = next((t.get('symbol', 'N/A') for t in trades if t.get('pnl') == best_trade), 'N/A')
    worst_trade_pair = next((t.get('symbol', 'N/A') for t in trades if t.get('pnl') == worst_trade), 'N/A')
    
    # Max Drawdown
    cumulative = 0
    peak = 0
    max_dd = 0
    for t in trades:
        cumulative += t.get('pnl', 0)
        peak = max(peak, cumulative)
        dd = (peak - cumulative) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)
    
    # Expectancy (esperance mathematique)
    win_rate = winning_count / total_trades if total_trades > 0 else 0
    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
    
    # Average R/R
    rr_values = [t.get('rr_ratio', 0) for t in trades if t.get('rr_ratio')]
    avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0
    
    # Consecutive wins/losses
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    current_wins = 0
    current_losses = 0
    
    for t in trades:
        if t.get('pnl', 0) > 0:
            current_wins += 1
            current_losses = 0
            max_consecutive_wins = max(max_consecutive_wins, current_wins)
        else:
            current_losses += 1
            current_wins = 0
            max_consecutive_losses = max(max_consecutive_losses, current_losses)
    
    # Duration stats
    durations = []
    for t in trades:
        if t.get('duration_minutes'):
            durations.append(t['duration_minutes'])
        elif t.get('entry_time') and t.get('exit_time'):
            try:
                entry = datetime.fromisoformat(t['entry_time'])
                exit = datetime.fromisoformat(t['exit_time'])
                durations.append((exit - entry).total_seconds() / 60)
            except:
                pass
    
    avg_duration_mins = sum(durations) / len(durations) if durations else 0
    min_duration_mins = min(durations) if durations else 0
    max_duration_mins = max(durations) if durations else 0
    
    # Performance par direction
    long_trades = [t for t in trades if t.get('direction') == 'LONG']
    short_trades = [t for t in trades if t.get('direction') == 'SHORT']
    
    long_wins = sum(1 for t in long_trades if t.get('pnl', 0) > 0)
    short_wins = sum(1 for t in short_trades if t.get('pnl', 0) > 0)
    
    long_winrate = (long_wins / len(long_trades) * 100) if long_trades else 0
    short_winrate = (short_wins / len(short_trades) * 100) if short_trades else 0
    
    long_pnl = sum(t.get('pnl', 0) for t in long_trades)
    short_pnl = sum(t.get('pnl', 0) for t in short_trades)
    
    # Trades par jour
    dates = set()
    for t in trades:
        try:
            if t.get('exit_time'):
                date = datetime.fromisoformat(t['exit_time']).date()
                dates.add(date)
        except:
            pass
    
    trading_days = len(dates) if dates else 1
    trades_per_day = total_trades / trading_days
    
    # Performance par heure
    hourly_pnl = defaultdict(float)
    hourly_count = defaultdict(int)
    
    for t in trades:
        try:
            if t.get('exit_time'):
                hour = datetime.fromisoformat(t['exit_time']).hour
                hourly_pnl[hour] += t.get('pnl', 0)
                hourly_count[hour] += 1
        except:
            pass
    
    best_hour = max(hourly_pnl.keys(), key=lambda x: hourly_pnl[x]) if hourly_pnl else 0
    worst_hour = min(hourly_pnl.keys(), key=lambda x: hourly_pnl[x]) if hourly_pnl else 0
    
    # Top pairs - using dict instead of defaultdict for type safety
    pair_stats: dict = {}
    for t in trades:
        symbol = t.get('symbol', 'UNKNOWN')
        pnl = t.get('pnl', 0)
        if symbol not in pair_stats:
            pair_stats[symbol] = {'pnl': 0.0, 'count': 0, 'wins': 0, 'trades': []}
        pair_stats[symbol]['pnl'] += pnl
        pair_stats[symbol]['count'] += 1
        pair_stats[symbol]['trades'].append(pnl)
        if pnl > 0:
            pair_stats[symbol]['wins'] += 1
    
    top_pairs = []
    for symbol, data in sorted(pair_stats.items(), key=lambda x: x[1]['pnl'], reverse=True):
        count = data['count']
        wins = data['wins']
        pnl_total = data['pnl']
        trades_list = data['trades']
        top_pairs.append({
            'symbol': symbol,
            'pnl': pnl_total,
            'count': count,
            'winrate': (wins / count * 100) if count > 0 else 0,
            'avg_pnl': pnl_total / count if count > 0 else 0,
            'best': max(trades_list) if trades_list else 0,
            'worst': min(trades_list) if trades_list else 0
        })
    
    return {
        # Counts
        'winning_count': winning_count,
        'losing_count': losing_count,
        
        # PnL stats
        'total_gains': total_gains,
        'total_losses': total_losses,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'best_trade': best_trade,
        'worst_trade': worst_trade,
        'best_trade_pair': best_trade_pair,
        'worst_trade_pair': worst_trade_pair,
        
        # Risk metrics
        'max_drawdown': max_dd,
        'profit_factor': profit_factor,
        'avg_rr': avg_rr,
        'expectancy': expectancy,
        'max_consecutive_wins': max_consecutive_wins,
        'max_consecutive_losses': max_consecutive_losses,
        
        # Time metrics
        'avg_duration': format_duration(avg_duration_mins),
        'min_duration': format_duration(min_duration_mins),
        'max_duration': format_duration(max_duration_mins),
        'trades_per_day': trades_per_day,
        'best_hour': best_hour,
        'worst_hour': worst_hour,
        
        # Direction performance
        'long_winrate': long_winrate,
        'short_winrate': short_winrate,
        'long_pnl': long_pnl,
        'short_pnl': short_pnl,
        'long_count': len(long_trades),
        'short_count': len(short_trades),
        
        # Top pairs
        'top_pairs': top_pairs
    }


def calculate_chart_data(history: list) -> dict:
    """
    Prepare les donnees pour les graphiques Chart.js
    
    Args:
        history: Liste des trades fermes
        
    Returns:
        Dict avec les donnees de graphiques prets pour JSON
    """
    if not history:
        return get_empty_chart_data()
    
    trades = [t for t in history if 'VENTE' in t.get('type', '') or t.get('exit_price')]
    
    if not trades:
        return get_empty_chart_data()
    
    # Equity curve (PnL cumule)
    equity_labels = []
    equity_data = []
    cumulative = 0
    
    for i, t in enumerate(trades):
        cumulative += t.get('pnl', 0)
        equity_labels.append(f"#{i+1}")
        equity_data.append(round(cumulative, 2))
    
    # Win/Loss count
    wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
    losses = len(trades) - wins
    
    # Daily PnL
    daily_pnl = defaultdict(float)
    for t in trades:
        try:
            if t.get('exit_time'):
                date = datetime.fromisoformat(t['exit_time']).strftime('%d/%m')
                daily_pnl[date] += t.get('pnl', 0)
            elif t.get('time'):
                # Fallback to time field
                daily_pnl[t['time'][:5]] += t.get('pnl', 0)
        except:
            pass
    
    daily_labels = list(daily_pnl.keys())[-14:]  # Last 14 days
    daily_data = [round(daily_pnl[d], 2) for d in daily_labels]
    
    # Performance par paire (top 10)
    pair_pnl = defaultdict(float)
    for t in trades:
        symbol = t.get('symbol', 'UNKNOWN').replace('USDT', '')
        pair_pnl[symbol] += t.get('pnl', 0)
    
    sorted_pairs = sorted(pair_pnl.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
    pairs_labels = [p[0] for p in sorted_pairs]
    pairs_data = [round(p[1], 2) for p in sorted_pairs]
    
    # Hourly distribution
    hourly_count = defaultdict(int)
    for t in trades:
        try:
            if t.get('exit_time'):
                hour = datetime.fromisoformat(t['exit_time']).hour
                hourly_count[hour] += 1
        except:
            pass
    
    hourly_labels = [f"{h}h" for h in range(24)]
    hourly_data = [hourly_count[h] for h in range(24)]
    
    # Direction performance
    long_wins = sum(1 for t in trades if t.get('direction') == 'LONG' and t.get('pnl', 0) > 0)
    long_losses = sum(1 for t in trades if t.get('direction') == 'LONG' and t.get('pnl', 0) <= 0)
    short_wins = sum(1 for t in trades if t.get('direction') == 'SHORT' and t.get('pnl', 0) > 0)
    short_losses = sum(1 for t in trades if t.get('direction') == 'SHORT' and t.get('pnl', 0) <= 0)
    
    return {
        'equity': {
            'labels': equity_labels,
            'data': equity_data
        },
        'winLoss': {
            'wins': wins,
            'losses': losses
        },
        'daily': {
            'labels': daily_labels,
            'data': daily_data
        },
        'pairs': {
            'labels': pairs_labels,
            'data': pairs_data
        },
        'hourly': {
            'labels': hourly_labels,
            'data': hourly_data
        },
        'direction': {
            'wins': [long_wins, short_wins],
            'losses': [long_losses, short_losses]
        }
    }


def format_history_for_display(history: list) -> list:
    """
    Formate l'historique pour l'affichage dans le tableau
    
    Args:
        history: Liste brute des trades
        
    Returns:
        Liste formatee pour le template
    """
    formatted = []
    
    for t in history:
        if 'VENTE' not in t.get('type', '') and not t.get('exit_price'):
            continue
            
        # Calculate duration
        duration = "N/A"
        if t.get('duration_minutes'):
            duration = format_duration(t['duration_minutes'])
        elif t.get('entry_time') and t.get('exit_time'):
            try:
                entry = datetime.fromisoformat(t['entry_time'])
                exit = datetime.fromisoformat(t['exit_time'])
                mins = (exit - entry).total_seconds() / 60
                duration = format_duration(mins)
            except:
                pass
        
        formatted.append({
            'time': t.get('exit_time', t.get('time', 'N/A'))[:16].replace('T', ' '),
            'date': t.get('exit_time', t.get('time', ''))[:10],
            'symbol': t.get('symbol', 'N/A'),
            'direction': t.get('direction', 'LONG'),
            'entry_price': t.get('entry_price', t.get('entry', 0)),
            'exit_price': t.get('exit_price', t.get('price', 0)),
            'amount': t.get('amount', t.get('usdt', 0)),
            'pnl': t.get('pnl', 0),
            'pnl_percent': t.get('pnl_percent', 0),
            'duration': duration,
            'exit_reason': t.get('exit_reason', t.get('reason', 'Manuel'))
        })
    
    return formatted


def get_all_pairs_from_history(history: list) -> list:
    """Extrait la liste unique des paires depuis l'historique"""
    pairs = set()
    for t in history:
        if t.get('symbol'):
            pairs.add(t['symbol'])
    return sorted(list(pairs))


def format_duration(minutes: float) -> str:
    """Formate une duree en minutes vers un string lisible"""
    if minutes < 1:
        return "<1m"
    elif minutes < 60:
        return f"{int(minutes)}m"
    elif minutes < 1440:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h{mins}m"
    else:
        days = int(minutes // 1440)
        hours = int((minutes % 1440) // 60)
        return f"{days}j{hours}h"


def get_empty_stats() -> dict:
    """Retourne des stats vides par defaut"""
    return {
        'winning_count': 0,
        'losing_count': 0,
        'total_gains': 0,
        'total_losses': 0,
        'avg_win': 0,
        'avg_loss': 0,
        'best_trade': 0,
        'worst_trade': 0,
        'best_trade_pair': 'N/A',
        'worst_trade_pair': 'N/A',
        'max_drawdown': 0,
        'profit_factor': 0,
        'avg_rr': 0,
        'expectancy': 0,
        'max_consecutive_wins': 0,
        'max_consecutive_losses': 0,
        'avg_duration': 'N/A',
        'min_duration': 'N/A',
        'max_duration': 'N/A',
        'trades_per_day': 0,
        'best_hour': 0,
        'worst_hour': 0,
        'long_winrate': 0,
        'short_winrate': 0,
        'long_pnl': 0,
        'short_pnl': 0,
        'long_count': 0,
        'short_count': 0,
        'top_pairs': []
    }


def get_empty_chart_data() -> dict:
    """Retourne des donnees de graphiques vides"""
    return {
        'equity': {'labels': ['Aucun trade'], 'data': [0]},
        'winLoss': {'wins': 0, 'losses': 0},
        'daily': {'labels': [], 'data': []},
        'pairs': {'labels': [], 'data': []},
        'hourly': {'labels': [f"{h}h" for h in range(24)], 'data': [0]*24},
        'direction': {'wins': [0, 0], 'losses': [0, 0]}
    }
