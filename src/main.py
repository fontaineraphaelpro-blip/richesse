"""
Script principal: Crypto Swing Trader Bot & Dashboard ULTIME.
Version: ULTIMATE v2.0 â€” Scanner complet + Bot Swing + Paper Trading + Dashboard Pro
"""

import sys
import os

# Garantir que le dossier contenant main.py est dans le path (pour Docker /app ou exécution depuis la racine)
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import time
import math
import threading
import json
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request, Response

# Import des modules internes (seulement ceux utilisés par le flux principal + API dashboard)
# Retirés (jamais utilisés dans main): validate_signal_multi_timeframe, find_swing_low, find_resistance,
#   trade_filters, calculate_opportunity_score, check_for_crash, is_crash_mode, get_fear_greed (news),
#   should_trade_with_intel, log_trade_result, get_onchain_signal_adjustment, update_position_stats,
#   check_macro_events, get_sentiment_modifier, record_entry, record_exit, journal_should_trade,
#   get_trade_modifier, fundamental_analyzer/get_fundamental_*, advanced_ta/get_advanced_*,
#   adaptive_strategy/analyze_and_adapt/get_adaptive_strategy
from trader import PaperTrader
from data_fetcher import fetch_multiple_pairs, fetch_current_prices
from minimal_dashboard import get_minimal_dashboard_html
from indicators import calculate_indicators
from crash_protection import crash_protector, get_crash_status
from news_analyzer import news_analyzer, get_market_sentiment
from market_intelligence import market_intel, get_market_intelligence
from ml_predictor import ml_predictor, get_ml_prediction
from onchain_analyzer import onchain_analyzer, get_onchain_analysis
from position_sizing import position_sizer, calculate_position_size, get_position_recommendations
from macro_events import macro_analyzer, get_macro_analysis, get_upcoming_economic_events
from social_sentiment import get_social_analyzer, get_fear_greed as get_social_fear_greed, get_social_sentiment
from trade_journal_ai import get_trade_journal, get_journal_stats

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CONFIGURATION DU BOT
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# STRATÉGIE DAY TRADING PRO — RISK MANAGEMENT OPTIMAL
# ─────────────────────────────────────────────────────────
# Objectif: gagner un max sur la durée en protégeant le capital.
# • Risque par trade 2% (ou Kelly si historique) — croissance optimale sans explosion.
# • Stop après 3 pertes d'affilée + drawdown jour 5% — protection.
# • Cooldown 10 min + score min 68 — qualité des setups, pas de sur-trading.
# • Sentiment Extreme Fear/Greed — éviter les pièges évidents.
# • Taille de position plafonnée 30% — jamais tout dans un seul trade.
# ─────────────────────────────────────────────────────────
TIMEFRAME        = '15m'
CANDLE_LIMIT     = 200
# === CIBLE 30%/mois: levier 10x, sizing agressif, R:R 1.5:1 ===
STOP_LOSS_PCT    = 1.2        # SL controle
TAKE_PROFIT_PCT  = 1.8        # TP 1.5x SL (R:R 1.5:1)
LONG_STOP_LOSS_PCT   = 1.2
LONG_TAKE_PROFIT_PCT = 1.8
SCAN_INTERVAL    = 300
SCAN_INTERVAL_SESSION = 90    # 1.5 min en session (plus d'opportunites)
SCAN_INTERVAL_NIGHT = 900
MAX_POSITIONS    = 999         # Pas de limite (était 4)
MAX_CONSECUTIVE_LOSSES = 2
COOLDOWN_MINUTES = 10          # 10 min entre trades
SPREAD_MAX_PCT   = 0.10
VOLUME_RATIO_MIN = 1.3
VOLATILITY_MAX   = 5.0
TOP_OPPORTUNITIES_DISPLAY = 10
TREND_15M_MUST_BEARISH = True
TREND_1H_MUST_BEARISH = True
TREND_1H_ALLOW_NEUTRAL = True
TREND_15M_LONG_BULLISH = True
TREND_1H_LONG_BULLISH  = True
TREND_1H_LONG_ALLOW_NEUTRAL = True
# Confirmation 4h (optionnel — meilleure qualité)
TREND_4H_ENABLED = True
TREND_4H_LONG_BULLISH_OR_NEUTRAL = True   # LONG si 4h BULLISH ou NEUTRAL
TREND_4H_SHORT_BEARISH_OR_NEUTRAL = True  # SHORT si 4h BEARISH ou NEUTRAL
POSITION_PCT_BALANCE   = 0.35   # 35% par position (levier 10x, equilibre risque/rendement)
SESSION_BONUS_ENABLED = True
SESSION_BONUS_UTC_START = 14
SESSION_BONUS_UTC_END = 22
SESSION_BONUS_PTS = 3
RISK_PCT_CAPITAL       = 0.06   # 6% risk par trade (agressif)
RISK_PCT_SMALL_ACCOUNT = 0.06
SMALL_ACCOUNT_THRESHOLD = 200
MIN_POSITION_USDT      = 10
MAX_DAILY_DRAWDOWN_PCT = 15.0   # Tolerance 15% (levier 10x)

MIN_SCORE_TO_OPEN = 62          # Score 62+ = opportunités adaptatives (multi-indicateurs)
SENTIMENT_FILTER_ENABLED = True # Éviter LONG en Extreme Greed / SHORT en Extreme Fear
FEAR_GREED_MIN_TO_SHORT = 22
FEAR_GREED_MAX_TO_LONG  = 78

# Risk management: utiliser Kelly pour adapter la taille au win rate (max gains long terme)
KELLY_RISK_ENABLED = True
KELLY_RISK_MIN_PCT = 0.02      # Minimum 2%
KELLY_RISK_MAX_PCT = 0.08      # Maximum 8% (levier 10x)

# Nombre de paires à scanner: None = TOUTES les paires (max opportunités). Sinon mettre SCAN_PAIRS_LIMIT=50 en env pour limiter.
_scan_limit = os.environ.get('SCAN_PAIRS_LIMIT', '').strip()
SCAN_PAIRS_LIMIT = int(_scan_limit) if (_scan_limit and _scan_limit.isdigit()) else None
SCAN_INTERVAL = int(os.environ.get('SCAN_INTERVAL', '90'))   # 90s H24 day trader pro

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# NOUVELLES CONFIGURATIONS RENTABILITÃ‰
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# Take Profit Partiel (Scaling Out)
PARTIAL_TP_ENABLED = True    # Prendre 50% a TP1, laisser courir le reste
PARTIAL_TP_RATIO = 0.5       # Prendre 0% Ã  TP1
# Le reste court vers TP2

# Filtrage Volume
VOLUME_FILTER_ENABLED = True
MIN_VOLUME_RATIO = 1.2       # Volume doit Ãªtre 1.2x la moyenne

# Heures de Trading — DAY TRADER PRO 24/7
TRADING_HOURS_ENABLED = False  # DÉSACTIVÉ = trade H24 (crypto ne dort jamais)
TRADING_START_HOUR = 8         # (ignoré si TRADING_HOURS_ENABLED=False)
TRADING_END_HOUR = 22          # (ignoré si TRADING_HOURS_ENABLED=False)
AVOID_WEEKENDS = False         # Crypto trade 7j/7

# Score Dynamique selon Marche
DYNAMIC_SCORE_ENABLED = True
SCORE_BULLISH_MARKET = 75    # Bull: setups corrects
SCORE_BEARISH_MARKET = 82    # Bear: plus strict
SCORE_NEUTRAL_MARKET = 78    # Neutre: equilibre

MIN_RISK_REWARD = 1.2        # R:R 1.2:1 minimum (profitable a 55% WR)

# Configuration News & Sentiment
NEWS_ENABLED = True
SENTIMENT_SCORE_ADJUST = True
PAUSE_ON_EVENTS = True

# Configuration Machine Learning
ML_ENABLED = True
ML_MIN_PROBABILITY = 60
ML_SCORE_ADJUST = True

# Configuration On-Chain
ONCHAIN_ENABLED = False       # DÉSACTIVÉ - trop de bruit
ONCHAIN_SCORE_ADJUST = False  # DÉSACTIVÉ

# Configuration Position Sizing (Kelly)
KELLY_SIZING_ENABLED = True   # Sizing activé (Kelly)
FIXED_TRADE_AMOUNT = None     # Désactivé, calcul dynamique

# Configuration Macro Events (Calendrier économique)
MACRO_EVENTS_ENABLED = False  # DÉSACTIVÉ - trop de bruit
PAUSE_ON_FOMC = False         # DÉSACTIVÉ
PAUSE_ON_CPI = False          # DÉSACTIVÉ
REGULATION_ALERTS = False     # DÉSACTIVÉ

# Social Sentiment
SOCIAL_SENTIMENT_ENABLED = False # DÉSACTIVÉ - trop de bruit
SOCIAL_SCORE_MODIFIER = False    # DÉSACTIVÉ

# Trade Journal AI
TRADE_JOURNAL_ENABLED = True     # Enregistrer tous les trades
JOURNAL_LEARN_PATTERNS = True    # Apprendre des erreurs passees

# ANALYSE FONDAMENTALE
FUNDAMENTAL_ENABLED = False      # DÉSACTIVÉ - trop de bruit
FUNDAMENTAL_SCORE_ADJUST = False # DÉSACTIVÉ
FUNDAMENTAL_MIN_SCORE = 0        # (non utilisé)
FUNDAMENTAL_BLOCK_AVOID = False  # DÉSACTIVÉ

# ANALYSE TECHNIQUE AVANCEE
ADVANCED_TA_ENABLED = False      # DÉSACTIVÉ - garder simple
ADVANCED_TA_SCORE_ADJUST = False # DÉSACTIVÉ
ADVANCED_TA_MIN_SCORE = 0        # (non utilisé)
ADVANCED_TA_WEIGHT = 0.25        # Poids de l'analyse avancee

# Pyramiding (Renforcement de position)
PYRAMIDING_ENABLED = False   # DÃ©sactivÃ© par dÃ©faut (risquÃ©)
MAX_PYRAMIDING = 2           # Max 2 ajouts par position
PYRAMIDING_GAIN_THRESHOLD = 2.0  # Ajouter si position gagne +2%

# Cooldown après Trade
COOLDOWN_ENABLED = True
# COOLDOWN_MINUTES défini ci-dessus (10)

# ═══════════════════════════════════════════════════════════════════════════════

# STRATÉGIE MICRO SCALP 1€ : pas d'adaptatif, logique simple et stricte
ADAPTIVE_STRATEGY_ENABLED = False
ADAPTIVE_OVERRIDE_PARAMS = False

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Ã‰TAT PARTAGÃ‰ (Thread Scanner â†” Serveur Web Flask)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
shared_data = {
    'opportunities': [],        # Top opportunités du dernier scan
    'all_scanned': [],          # Toutes les paires analysées
    'last_prices': {},          # Prix actuels
    'last_indicators': {},      # Derniers indicateurs par symbole (pour API)
    'is_scanning': False,
    'last_update': 'Jamais',
    'scan_count': 0,
    'bot_log': [],              # Journal d'activitÃ© du bot (20 derniers events)
    'market_stats': {
        'total_bullish': 0,
        'total_bearish': 0,
        'total_neutral': 0,
        'avg_rsi': 0,
        'top_volume': [],
    },
    'performance': {
        'total_trades': 0,
        'winning_trades': 0,
        'total_pnl': 0,
        'win_rate': 0,
    },
    'crash_status': {           # Statut protection crash
        'crash_detected': False,
        'crash_type': None,
        'trading_allowed': True,
        'reason': None
    },
    'market_sentiment': {       # Sentiment marchÃ© (News & Fear/Greed)
        'fear_greed': 50,
        'fear_greed_class': 'Neutral',
        'news_bullish': 0,
        'news_bearish': 0,
        'action': 'NORMAL',
        'updated': None
    },
    'market_intelligence': {    # Intelligence complÃ¨te (Funding, L/S, Volume...)
        'bias': 'NEUTRAL',
        'confidence': 0,
        'funding': 0,
        'ls_ratio': 1,
        'breadth': 50,
        'alerts': [],
        'updated': None
    },
    'adaptive_regime': {        # Régime adaptatif (NOUVEAU!)
        'regime': 'UNKNOWN',
        'confidence': 0,
        'trading_mode': 'NORMAL',
        'min_score': 72,
        'allow_long': True,
        'allow_short': True,
        'summary': '',
        'updated': None
    },
    'sentiment_display': None,  # Sentiment marché & réseaux (Fear & Greed, Reddit, trending)
}

app = Flask(__name__)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# FONCTIONS UTILITAIRES
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def add_bot_log(msg: str, level: str = 'INFO'):
    """Ajoute une ligne au journal du bot (visible dans le dashboard)."""
    entry = {
        'time': datetime.now().strftime('%H:%M:%S'),
        'level': level,  # INFO | TRADE | WARN | ERROR
        'msg': msg
    }
    shared_data['bot_log'].insert(0, entry)
    shared_data['bot_log'] = shared_data['bot_log'][:30]  # Garder les 30 derniers
    level_pad = level.ljust(5)
    print("  [{}] [{}] {}".format(entry['time'], level_pad, msg))


def fetch_sentiment_for_dashboard():
    """
    Agrège le sentiment marché et réseaux pour le dashboard (lecture seule).
    Fear & Greed, Reddit, trending coins, news. Ne bloque pas le trading.
    """
    out = {
        'updated': datetime.now().strftime('%H:%M'),
        'fear_greed': None,
        'reddit': None,
        'trending': None,
        'news': None,
    }
    try:
        fg = get_social_fear_greed()
        if fg and not fg.get('error'):
            out['fear_greed'] = {
                'value': fg.get('value', 50),
                'classification': fg.get('classification', 'Neutral'),
                'signal': fg.get('signal', 'neutral'),
                'trend_direction': fg.get('trend_direction', 'stable'),
                'avg_7d': fg.get('avg_7d'),
            }
    except Exception:
        pass
    try:
        social = get_social_analyzer()
        reddit = social.get_reddit_sentiment('BTC')
        if reddit and not reddit.get('error'):
            out['reddit'] = {
                'sentiment_score': reddit.get('sentiment_score', 0),
                'signal': reddit.get('signal', 'neutral'),
                'bullish_percent': reddit.get('bullish_percent'),
                'bearish_percent': reddit.get('bearish_percent'),
                'neutral_percent': reddit.get('neutral_percent'),
                'top_mentions': reddit.get('top_mentions', {}) or {},
                'total_posts': reddit.get('total_posts_analyzed', 0),
            }
    except Exception:
        pass
    try:
        social = get_social_analyzer()
        trending = social.get_trending_coins()
        if trending and trending.get('trending_coins'):
            out['trending'] = [
                {'name': c.get('name'), 'symbol': (c.get('symbol') or '').upper(), 'rank': c.get('market_cap_rank')}
                for c in trending['trending_coins'][:8]
            ]
    except Exception:
        pass
    try:
        news = news_analyzer.get_news_sentiment_score()
        if news is not None:
            out['news'] = {
                'score': news.get('score', 0),
                'bullish': news.get('bullish', 0),
                'bearish': news.get('bearish', 0),
                'neutral': news.get('neutral', 0),
            }
    except Exception:
        pass
    return out


def update_performance_stats(trader: PaperTrader):
    """Recalcule les statistiques de performance depuis l'historique."""
    history = trader.get_trades_history()
    sales = [t for t in history if 'VENTE' in t.get('type', '')]
    
    total = len(sales)
    winners = sum(1 for t in sales if t.get('pnl', 0) > 0)
    total_pnl = sum(t.get('pnl', 0) for t in sales)
    
    shared_data['performance'] = {
        'total_trades': total,
        'winning_trades': winners,
        'total_pnl': round(total_pnl, 2),
        'win_rate': round((winners / total * 100) if total > 0 else 0, 1)
    }


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SCANNER PRINCIPAL
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_adaptive_state = {'min_score_adjust': 0}

def _update_adaptive_params():
    """Auto-ajuste le score min selon le winrate recent."""
    try:
        trader = PaperTrader()
        history = trader.get_trades_history()
        sales = [t for t in history if 'VENTE' in t.get('type', '')][:50]
        if len(sales) < 10:
            return
        wins = sum(1 for t in sales if t.get('pnl', 0) > 0)
        wr = wins / len(sales)
        if wr < 0.42:
            _adaptive_state['min_score_adjust'] = 5
        elif wr > 0.58:
            _adaptive_state['min_score_adjust'] = -3
        else:
            _adaptive_state['min_score_adjust'] = 0
    except Exception:
        pass

def _check_correlation(symbol, open_positions, all_indicators):
    """Penalise si trop de positions dans la meme direction."""
    if not open_positions:
        return 1.0
    sym_ind = all_indicators.get(symbol, {})
    sym_mom = sym_ind.get('price_momentum', 'NEUTRAL')
    same_dir = sum(1 for ps in open_positions
                   if all_indicators.get(ps, {}).get('price_momentum') == sym_mom and sym_mom != 'NEUTRAL')
    if same_dir >= 3:
        return 0.5
    elif same_dir >= 2:
        return 0.7
    return 1.0

def _check_setup_similarity(best, trader):
    """Compare le setup actuel avec les setups passes similaires."""
    try:
        history = trader.get_trades_history()
        sales = [t for t in history if 'VENTE' in t.get('type', '')][:200]
        if len(sales) < 20:
            return 0
        rsi_lo, rsi_hi = best.get('rsi', 50) - 5, best.get('rsi', 50) + 5
        similar = [t for t in sales if rsi_lo <= t.get('rsi', 50) <= rsi_hi]
        if len(similar) < 5:
            return 0
        wins = sum(1 for t in similar if t.get('pnl', 0) > 0)
        wr = wins / len(similar)
        if wr > 0.65:
            return 8
        elif wr < 0.35:
            return -8
        return 0
    except Exception:
        return 0

_slippage_history = {}

def _get_avg_slippage(symbol):
    """Retourne le slippage moyen pour un symbole."""
    if symbol in _slippage_history and _slippage_history[symbol]:
        return sum(_slippage_history[symbol]) / len(_slippage_history[symbol])
    return 0.05

def _record_slippage(symbol, slip_pct):
    """Enregistre le slippage."""
    if symbol not in _slippage_history:
        _slippage_history[symbol] = []
    _slippage_history[symbol].append(slip_pct)
    if len(_slippage_history[symbol]) > 50:
        _slippage_history[symbol] = _slippage_history[symbol][-50:]


def run_scanner():
    """
    Scanner SHORT uniquement — grandes baisses.

    Étapes:
      1. Récupérer les bougies 1m sur toutes les paires USDT (Binance).
      2. Vérifier qu’on peut trader (pas 3 pertes de suite, pas de position ouverte).
      3. Pour chaque paire: calculer indicateurs, appliquer filtres (volume, spread, volatilité, tendance 15m).
      4. Si signal LONG (RSI survendu + Bollinger basse + volume): calculer taille de position pour 1€ de gain, placer l’ordre et sortir.
      5. Sinon passer à la paire suivante; si aucune opportunité, retourner [].
    """
    from short_crash_strategy import (
        position_size_usdt, position_size_long_usdt, compute_sl_tp_from_chart,
    )
    try:
        from adaptive_scorer import score_adaptive
    except ImportError:
        add_bot_log("Module adaptive_scorer non trouvé — utilisation du score de repli (pas d'ouverture). Ajoutez src/adaptive_scorer.py au déploiement.", 'WARNING')
        def score_adaptive(indicators, momentum_15m, momentum_1h, momentum_4h, spread_pct, atr_pct,
                          momentum_5m=None, order_flow=None, depth_imbalance=None, fear_greed=None):
            return 50.0, 50.0, 'UNKNOWN'
    from indicators import calculate_indicators
    from data_fetcher import fetch_multiple_pairs, get_top_pairs, fetch_multi_timeframe, fetch_order_flow, fetch_orderbook_depth

    _update_adaptive_params()
    shared_data['scan_count'] += 1
    scan_num = shared_data['scan_count']

    # Filtre heures de trading: uniquement sessions liquides (Europe + US)
    utc_now = datetime.utcnow()
    if TRADING_HOURS_ENABLED:
        h = utc_now.hour
        if h < TRADING_START_HOUR or h >= TRADING_END_HOUR:
            add_bot_log("Hors session ({:02d}h UTC, actif {}h-{}h) — scan en pause.".format(h, TRADING_START_HOUR, TRADING_END_HOUR), 'INFO')
            return []
        if AVOID_WEEKENDS and utc_now.weekday() >= 5:
            add_bot_log("Weekend — volumes faibles, pas de trading.", 'INFO')
            return []

    # Liste des paires (limité en mode test pour exécution rapide)
    symbols = list(get_top_pairs())
    if SCAN_PAIRS_LIMIT:
        symbols = symbols[:SCAN_PAIRS_LIMIT]
    # Toujours inclure les paires des positions ouvertes pour mettre à jour last_prices
    try:
        from trader import PaperTrader
        for sym in PaperTrader().get_open_positions():
            if sym not in symbols:
                symbols.append(sym)
    except Exception:
        pass
    add_bot_log("=== SCAN #{} ({} paires) LONG + SHORT — risk mgt optimal ===".format(scan_num, len(symbols)), 'INFO')

    # —— 1. Données marché (15m) ——
    data, real_prices = fetch_multiple_pairs(symbols, interval=TIMEFRAME, limit=CANDLE_LIMIT)
    if not data:
        add_bot_log("Aucune donnée reçue de Binance", 'ERROR')
        return []
    shared_data['last_prices'] = real_prices
    shared_data['last_indicators'] = {}

    # —— 1b. BTC contexte (info seulement, pas de blocage) ——
    btc_regime = 'UNKNOWN'
    btc_df = data.get('BTCUSDT')
    if btc_df is not None:
        btc_ind = calculate_indicators(btc_df)
        if btc_ind:
            btc_regime = btc_ind.get('market_regime', 'UNKNOWN')
            btc_adx = btc_ind.get('adx') or 0
            add_bot_log("BTC {} (ADX {:.0f}) — scan adaptatif actif.".format(btc_regime, btc_adx), 'INFO')

    # —— 2. État du trader + vérif SL/TP ——
    from trader import PaperTrader
    trader = PaperTrader()
    try:
        trader.check_and_apply_breakeven(real_prices)
    except Exception as e:
        add_bot_log("Erreur breakeven: {}".format(e), 'ERROR')
    try:
        trader.check_and_apply_trailing_stop(real_prices)
    except Exception as e:
        add_bot_log("Erreur trailing: {}".format(e), 'ERROR')
    try:
        trader.check_and_apply_partial_tp(real_prices)
    except Exception as e:
        add_bot_log("Erreur partial_tp: {}".format(e), 'ERROR')
    # DCA desactive: ne pas moyenner a la baisse (capital preservation)
    try:
        trader.check_time_based_exits(real_prices, max_hold_hours=24)
    except Exception as e:
        add_bot_log("Erreur time_exits: {}".format(e), 'ERROR')
    trader.check_positions(real_prices)
    open_pos = trader.get_open_positions()
    if len(open_pos) >= MAX_POSITIONS:
        add_bot_log("{}/{} positions ouvertes — max atteint.".format(len(open_pos), MAX_POSITIONS), 'INFO')
        return []

    total_capital = trader.get_total_capital(real_prices)
    trader.update_daily_start_if_new_day(total_capital)
    daily_dd = trader.get_daily_drawdown_pct(total_capital)
    if daily_dd >= MAX_DAILY_DRAWDOWN_PCT:
        add_bot_log(f"Pause: drawdown jour {daily_dd:.1f}% >= {MAX_DAILY_DRAWDOWN_PCT}% — reprise demain.", 'WARN')
        return []

    # Vérifier les 3 DERNIÈRES ventes (trades fermés): si toutes en perte → stop
    recent = trader.get_trades_history()
    sales = [t for t in recent if 'VENTE' in t.get('type', '')]
    last_3_sales = sales[:3]
    if len(last_3_sales) >= MAX_CONSECUTIVE_LOSSES and all(t.get('pnl', 0) < 0 for t in last_3_sales):
        add_bot_log(f"STOP: {MAX_CONSECUTIVE_LOSSES} pertes consécutives, trading suspendu.", 'ERROR')
        return []

    # —— 3. Fear & Greed (une fois par scan) ——
    fear_greed_val = None
    try:
        fg = get_social_fear_greed()
        if fg and not fg.get('error'):
            fear_greed_val = fg.get('value')
    except Exception:
        pass

    # —— 4. Parcourir les paires, collecter opportunités LONG et SHORT ——
    long_opportunities = []
    short_opportunities = []
    n_pairs = len(data)
    n_volume_ok = 0
    n_spread_ok = 0
    n_short_signal = 0
    n_long_signal = 0
    n_no_indicators = 0

    utc_hour = datetime.utcnow().hour
    in_session = SESSION_BONUS_ENABLED and (SESSION_BONUS_UTC_START <= utc_hour < SESSION_BONUS_UTC_END)
    session_bonus = SESSION_BONUS_PTS if in_session else 0

    for symbol, df in data.items():
      try:
        try:
            indicators = calculate_indicators(df)
        except Exception:
            indicators = {}
        shared_data['last_indicators'][symbol] = indicators

        if not indicators or indicators.get('volume_ratio') is None:
            n_no_indicators += 1
            continue
        vol_r = indicators.get('volume_ratio')
        if vol_r is None or vol_r < VOLUME_RATIO_MIN:
            continue
        n_volume_ok += 1
        close_val = df['close'].iloc[-1]
        if close_val is None or close_val == 0:
            continue
        spread_pct = (df['high'].iloc[-1] - df['low'].iloc[-1]) / close_val * 100
        if spread_pct > SPREAD_MAX_PCT:
            continue
        n_spread_ok += 1
        atr_pct = indicators.get('atr_percent') or 0
        if atr_pct is None:
            atr_pct = 0
        if atr_pct > VOLATILITY_MAX:
            continue

        # Recuperer tendances 5m, 15m, 1h et optionnellement 4h (multi-TF day trader pro)
        momentum_5m = None
        momentum_15m = None
        momentum_1h = None
        momentum_4h = None
        timeframes = ['5m', '15m', '1h']
        if TREND_4H_ENABLED:
            timeframes.append('4h')
        tf_data = fetch_multi_timeframe(symbol, timeframes)
        if tf_data.get('5m') is not None:
            tf_ind_5m = calculate_indicators(tf_data['5m'])
            momentum_5m = tf_ind_5m.get('price_momentum') if tf_ind_5m else None
        if tf_data.get('15m') is not None:
            tf_ind = calculate_indicators(tf_data['15m'])
            momentum_15m = tf_ind.get('price_momentum') if tf_ind else None
        if tf_data.get('1h') is not None:
            tf_ind_1h = calculate_indicators(tf_data['1h'])
            momentum_1h = tf_ind_1h.get('price_momentum') if tf_ind_1h else None
        if TREND_4H_ENABLED and tf_data.get('4h') is not None:
            tf_ind_4h = calculate_indicators(tf_data['4h'])
            momentum_4h = tf_ind_4h.get('price_momentum') if tf_ind_4h else None

        price = indicators.get('current_price')
        if not price or price <= 0:
            continue

        in_cooldown, _ = trader.is_in_cooldown(symbol)
        if in_cooldown:
            continue

        # Score adaptatif: combine RSI, MACD, ADX, Bollinger, Ichimoku, Stoch, VWAP, OBV, MFI, regime...
        score_long, score_short, regime = score_adaptive(
            indicators, momentum_15m or 'NEUTRAL', momentum_1h or 'NEUTRAL', momentum_4h,
            spread_pct, atr_pct,
            momentum_5m=momentum_5m,
            fear_greed=fear_greed_val,
        )
        final_long = score_long + session_bonus
        final_short = score_short + session_bonus

        # LONG si score suffisant
        if final_long >= MIN_SCORE_TO_OPEN:
            n_long_signal += 1
            stop_loss, take_profit, sl_pct_eff = compute_sl_tp_from_chart(price, indicators, 'LONG')
            if stop_loss is None:
                stop_loss = price * (1 - LONG_STOP_LOSS_PCT / 100)
                take_profit = price * (1 + LONG_TAKE_PROFIT_PCT / 100)
                sl_pct_eff = LONG_STOP_LOSS_PCT
            rr = abs(take_profit - price) / abs(price - stop_loss) if (stop_loss != price) else 1.5
            long_opportunities.append({
                'symbol': symbol, 'pair': symbol, 'price': price,
                'stop_loss': stop_loss, 'take_profit': take_profit,
                'sl_pct_effective': sl_pct_eff,
                'entry_signal': 'LONG', 'score': final_long,
                'rsi': indicators.get('rsi14'), 'volume_ratio': vol_r,
                'momentum_5m': momentum_5m, 'momentum_15m': momentum_15m or '-', 'momentum_1h': momentum_1h or '-', 'momentum_4h': momentum_4h,
                'spread_pct': spread_pct, 'atr_pct': atr_pct, 'rr_ratio': round(rr, 1),
                'adx': indicators.get('adx'), 'macd_bullish': indicators.get('macd_hist', 0) > 0,
                'is_signal': True, 'regime': regime, 'indicators': indicators,
            })

        # SHORT si score suffisant
        if final_short >= MIN_SCORE_TO_OPEN:
            n_short_signal += 1
            stop_loss, take_profit, sl_pct_eff = compute_sl_tp_from_chart(price, indicators, 'SHORT')
            if stop_loss is None:
                stop_loss = price * (1 + STOP_LOSS_PCT / 100)
                take_profit = price * (1 - TAKE_PROFIT_PCT / 100)
                sl_pct_eff = STOP_LOSS_PCT
            rr = abs(take_profit - price) / abs(stop_loss - price) if (stop_loss != price) else 1.5
            short_opportunities.append({
                'symbol': symbol, 'pair': symbol, 'price': price,
                'stop_loss': stop_loss, 'take_profit': take_profit,
                'sl_pct_effective': sl_pct_eff,
                'entry_signal': 'SHORT', 'score': final_short,
                'rsi': indicators.get('rsi14'), 'volume_ratio': vol_r,
                'momentum_5m': momentum_5m, 'momentum_15m': momentum_15m or '-', 'momentum_1h': momentum_1h or '-', 'momentum_4h': momentum_4h,
                'spread_pct': spread_pct, 'atr_pct': atr_pct, 'rr_ratio': round(rr, 1),
                'adx': indicators.get('adx'), 'macd_bearish': indicators.get('macd_hist', 0) < 0,
                'is_signal': True, 'regime': regime, 'indicators': indicators,
            })
      except Exception as pair_err:
        add_bot_log("Erreur paire {}: {}".format(symbol, pair_err), 'ERROR')
        continue

    # Fusionner et trier par score (meilleure opportunité en premier)
    opportunities_list = list(long_opportunities) + list(short_opportunities)
    opportunities_list.sort(key=lambda x: x['score'], reverse=True)

    # Confluence bonus: order flow + depth pour top 20 (day trader pro)
    TOP_FOR_CONFLUENCE = 20
    for opp in opportunities_list[:TOP_FOR_CONFLUENCE]:
        try:
            sym = opp['symbol']
            ind = opp.get('indicators') or shared_data.get('last_indicators', {}).get(sym, {})
            if not ind:
                continue
            of = fetch_order_flow(sym)
            depth = fetch_orderbook_depth(sym)
            m15 = opp.get('momentum_15m') if isinstance(opp.get('momentum_15m'), str) else 'NEUTRAL'
            m1h = opp.get('momentum_1h') if isinstance(opp.get('momentum_1h'), str) else 'NEUTRAL'
            m4h = opp.get('momentum_4h') if isinstance(opp.get('momentum_4h'), str) else None
            m5 = opp.get('momentum_5m')
            score_l, score_s, _ = score_adaptive(
                ind, m15, m1h, m4h,
                opp.get('spread_pct', 0.05), opp.get('atr_pct', 2),
                momentum_5m=m5, order_flow=of, depth_imbalance=depth.get('depth_imbalance'),
                fear_greed=fear_greed_val,
            )
            is_long = opp.get('entry_signal') == 'LONG'
            opp['score'] = (score_l + session_bonus) if is_long else (score_s + session_bonus)
        except Exception:
            pass
    opportunities_list.sort(key=lambda x: x['score'], reverse=True)
    shared_data['opportunities'] = opportunities_list[:30]

    if n_no_indicators > 0:
        add_bot_log("{} paire(s) sans indicateurs (donnees insuffisantes ou < 200 bougies).".format(n_no_indicators), 'INFO')
    add_bot_log("Scan #{}: {} paires | volume OK: {} | spread OK: {} | LONG: {} | SHORT: {} -> {} opportunite(s).".format(
        scan_num, n_pairs, n_volume_ok, n_spread_ok, n_long_signal, n_short_signal, len(opportunities_list)), 'INFO')

    # —— 4. Ouvrir la meilleure opportunité ——
    current_open = trader.get_open_positions()
    already_open_symbols = set(current_open.keys())

    MAX_PORTFOLIO_EXPOSURE = 0.85  # Max 85% deploye (4 pos x 35%)
    deployed_capital = sum(p.get('amount_usdt', 0) for p in current_open.values())
    available_pct = 1.0 - (deployed_capital / total_capital) if total_capital > 0 else 0
    if available_pct < (1.0 - MAX_PORTFOLIO_EXPOSURE):
        add_bot_log("Portfolio exposure {:.0f}% >= {:.0f}% max — pas de nouvelle position.".format(
            (deployed_capital / total_capital) * 100, MAX_PORTFOLIO_EXPOSURE * 100), 'INFO')
        return shared_data['opportunities']

    # BTC erratique: relever le score minimum
    btc_score_penalty = 5 if btc_regime == 'VOLATILE' else 0

    if opportunities_list and len(current_open) < MAX_POSITIONS:
        # Meilleure opportunite: score max, R:R OK, pas deja ouverte
        best = None
        for opp in opportunities_list:
            if opp['symbol'] in already_open_symbols:
                continue
            rr = opp.get('rr_ratio') or 0
            if rr >= MIN_RISK_REWARD:
                best = opp
                break
        if best is None:
            for opp in opportunities_list:
                if opp['symbol'] in already_open_symbols:
                    continue
                if (opp.get('rr_ratio') or 0) >= 1.0:
                    best = opp
                    break

        if best is not None:
            is_long = best.get('entry_signal') == 'LONG'
            # Setup similarity bonus/malus
            similarity_bonus = _check_setup_similarity(best, trader)
            best['score'] += similarity_bonus
            # Adaptive score adjustment
            min_score = MIN_SCORE_TO_OPEN + btc_score_penalty + _adaptive_state.get('min_score_adjust', 0)
            if DYNAMIC_SCORE_ENABLED:
                try:
                    fg = get_social_fear_greed()
                    if fg and not fg.get('error'):
                        v = fg.get('value', 50)
                        if v < 25:
                            min_score = SCORE_BEARISH_MARKET
                        elif v < 45:
                            min_score = SCORE_NEUTRAL_MARKET
                        else:
                            min_score = SCORE_BULLISH_MARKET
                except Exception:
                    pass
            if best['score'] < min_score:
                add_bot_log("Meilleure opp {} score {} < {} (min) — pas d'ouverture.".format(best['symbol'], best['score'], min_score), 'INFO')
            else:
                skip_sentiment = False
                if SENTIMENT_FILTER_ENABLED:
                    try:
                        fg = get_social_fear_greed()
                        if fg and not fg.get('error'):
                            v = fg.get('value', 50)
                            if is_long and v >= FEAR_GREED_MAX_TO_LONG:
                                add_bot_log("Extreme Greed ({}): pas de LONG.".format(v), 'INFO')
                                skip_sentiment = True
                            elif not is_long and v <= FEAR_GREED_MIN_TO_SHORT:
                                add_bot_log("Extreme Fear ({}) mais SHORT autorise (trend-following).".format(v), 'INFO')
                    except Exception:
                        pass
                if not skip_sentiment:
                    symbol = best['symbol']
                    price = best['price']
                    stop_loss = best['stop_loss']
                    take_profit = best['take_profit']

                    # Dernier filtre: order flow ne doit pas contredire fortement
                    try:
                        of = fetch_order_flow(symbol)
                        pressure = of.get('pressure', 'NEUTRAL')
                        if is_long and pressure == 'SELL':
                            best['score'] -= 8
                        elif not is_long and pressure == 'BUY':
                            best['score'] -= 8
                    except Exception:
                        pass

                    if best['score'] < min_score:
                        add_bot_log("Opp {} score {} apres order flow < {} — skip.".format(symbol, best['score'], min_score), 'INFO')
                        return shared_data['opportunities']

                    balance = trader.get_usdt_balance()
                    if KELLY_RISK_ENABLED:
                        kelly = position_sizer.calculate_kelly()
                        risk_pct = min(KELLY_RISK_MAX_PCT, max(KELLY_RISK_MIN_PCT, kelly))
                    else:
                        risk_pct = RISK_PCT_SMALL_ACCOUNT if balance < SMALL_ACCOUNT_THRESHOLD else RISK_PCT_CAPITAL
                    atr_pct = best.get('atr_pct')
                    if atr_pct is None or atr_pct == 0:
                        atr_pct = 2.0
                    n_open = len(current_open)
                    multi_pos_factor = 1.0 / math.sqrt(1 + n_open)
                    corr_factor = _check_correlation(symbol, current_open, shared_data.get('last_indicators', {})) or 1.0
                    avg_slip = _get_avg_slippage(symbol) or 0
                    slip_factor = max(0.7, 1.0 - avg_slip * 2) if avg_slip > 0.1 else 1.0
                    atr_adj = position_sizer.calculate_atr_adjustment(atr_pct) or 1.0
                    score_adj = position_sizer.calculate_score_adjustment(best['score'], 50) or 1.0
                    dd_adj = position_sizer.calculate_drawdown_adjustment(total_capital) or 1.0
                    size_mult = atr_adj * score_adj * dd_adj * multi_pos_factor * corr_factor * slip_factor
                    if is_long:
                        lev = trader.long_leverage
                        sl_pct = best.get('sl_pct_effective') or LONG_STOP_LOSS_PCT
                        pos_size = position_size_long_usdt(
                            balance, risk_pct=risk_pct, sl_pct=sl_pct,
                            leverage=lev, max_pct_balance=POSITION_PCT_BALANCE, min_usdt=MIN_POSITION_USDT,
                        )
                        pos_size = min(pos_size * size_mult, pos_size * 1.5, max(0, balance * 0.98))
                        take_profit_2 = price + (take_profit - price) * 1.5 if take_profit > price else None
                        if pos_size >= MIN_POSITION_USDT and trader.place_buy_order(symbol, pos_size, price, stop_loss, take_profit, entry_trend='DIP_LONG', take_profit_2=take_profit_2, atr_pct=best.get('atr_pct')):
                            trader.record_trade_time(symbol)
                            _record_slippage(symbol, best.get('spread_pct', 0.05))
                            ta = "RSI {}, ADX {}, MACD {}, 15m {}, 1h {}, OF {}".format(
                                best['rsi'], best.get('adx') or '-',
                                'bull' if best.get('macd_bullish') else '-',
                                best['momentum_15m'], best['momentum_1h'],
                                'OK' if best.get('score', 0) > min_score else '-')
                            add_bot_log("LONG {} @ {:.4f} | Score {} | {} | SL {:.4f} TP {:.4f}".format(symbol, price, best['score'], ta, stop_loss, take_profit), 'TRADE')
                            return shared_data['opportunities']
                    else:
                        lev = trader.short_leverage
                        sl_pct = best.get('sl_pct_effective') or STOP_LOSS_PCT
                        pos_size = position_size_usdt(
                            balance, risk_pct=risk_pct, sl_pct=sl_pct,
                            leverage=lev, max_pct_balance=POSITION_PCT_BALANCE, min_usdt=MIN_POSITION_USDT,
                        )
                        pos_size = min(pos_size * size_mult, pos_size * 1.5, max(0, balance * 0.98))
                        take_profit_2 = price - (price - take_profit) * 1.5 if take_profit < price else None
                        if pos_size >= MIN_POSITION_USDT and trader.place_short_order(symbol, pos_size, price, stop_loss, take_profit, entry_trend='CRASH_SHORT', take_profit_2=take_profit_2, atr_pct=best.get('atr_pct')):
                            trader.record_trade_time(symbol)
                            _record_slippage(symbol, best.get('spread_pct', 0.05))
                            ta = "RSI {}, ADX {}, MACD {}, 15m {}, 1h {}, OF {}".format(
                                best['rsi'], best.get('adx') or '-',
                                'bear' if best.get('macd_bearish') else '-',
                                best['momentum_15m'], best['momentum_1h'],
                                'OK' if best.get('score', 0) > min_score else '-')
                            add_bot_log("SHORT {} @ {:.4f} | Score {} | {} | SL {:.4f} TP {:.4f}".format(symbol, price, best['score'], ta, stop_loss, take_profit), 'TRADE')
                            return shared_data['opportunities']

    if not opportunities_list:
        add_bot_log("Aucune opportunité détectée sur ce scan.", 'INFO')
    elif best is None:
        n_rr_ok = sum(1 for o in opportunities_list if (o.get('rr_ratio') or 0) >= MIN_RISK_REWARD)
        n_score_ok = sum(1 for o in opportunities_list if o.get('score', 0) >= MIN_SCORE_TO_OPEN)
        add_bot_log("{} opps mais aucune avec R:R>={:.1f} ET score>={} — pas d'ouverture.".format(
            len(opportunities_list), MIN_RISK_REWARD, MIN_SCORE_TO_OPEN), 'INFO')
    else:
        add_bot_log("{} opps, best={} score={} — bloqué par score_min/sentiment.".format(
            len(opportunities_list), best['symbol'], best['score']), 'INFO')

    return shared_data['opportunities']


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# ROUTES FLASK
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _prices_for_dashboard(open_positions):
    """Prix a jour: last_prices + fetch des symboles des positions si manquants."""
    last = dict(shared_data.get('last_prices') or {})
    missing = [s for s in open_positions if s not in last]
    if missing:
        try:
            extra = fetch_current_prices(missing)
            last.update(extra)
            if extra:
                shared_data.setdefault('last_prices', {})
                shared_data['last_prices'].update(extra)
        except Exception:
            pass
    return last


@app.route('/')
def dashboard():
    """Dashboard principal â€” rendu cÃ´tÃ© serveur."""
    trader = PaperTrader()
    update_performance_stats(trader)
    balance = trader.get_usdt_balance()
    open_positions = trader.get_open_positions()
    prices = _prices_for_dashboard(open_positions)
    positions_view = []
    total_unrealized_pnl = 0
    for symbol, pos_data in open_positions.items():
        entry = pos_data['entry_price']
        current = prices.get(symbol, entry)
        direction = pos_data.get('direction', 'LONG')
        
        # Calcul PnL selon direction
        if direction == 'LONG':
            pnl_value = (current - entry) * pos_data['quantity']
            pnl_percent = ((current - entry) / entry) * 100
        else:  # SHORT
            pnl_value = (entry - current) * pos_data['quantity']
            pnl_percent = ((entry - current) / entry) * 100
        
        total_unrealized_pnl += pnl_value
        
        # Calcul du % parcouru vers TP
        sl = pos_data.get('stop_loss', entry)
        tp = pos_data.get('take_profit', entry)
        
        if direction == 'LONG':
            range_total = tp - sl if (tp - sl) != 0 else 1
            progress = max(0, min(100, ((current - sl) / range_total) * 100))
        else:  # SHORT (inversÃ©)
            range_total = sl - tp if (sl - tp) != 0 else 1
            progress = max(0, min(100, ((sl - current) / range_total) * 100))
        
        positions_view.append({
            'symbol':      symbol,
            'direction':   direction,
            'entry':       entry,
            'current':     current,
            'amount':      pos_data.get('amount_usdt', 0),
            'quantity':    pos_data.get('quantity', 0),
            'pnl_value':   pnl_value,
            'pnl_percent': pnl_percent,
            'sl':          pos_data.get('stop_loss', entry),
            'tp':          pos_data.get('take_profit', entry),
            'entry_time':  pos_data.get('entry_time', 'N/A'),
            'progress':    progress,
            'leverage':    pos_data.get('leverage', 1),
            'amount':      pos_data['amount_usdt'],
            'quantity':    pos_data['quantity'],
            'pnl_value':   pnl_value,
            'pnl_percent': pnl_percent,
            'sl':          sl,
            'tp':          tp,
            'entry_time':  pos_data.get('entry_time', 'N/A'),
            'progress':    progress,
            'leverage':    pos_data.get('leverage', 1),
        })

    total_invested = sum(p['amount'] for p in positions_view)
    total_capital = balance + total_invested + total_unrealized_pnl
    perf = shared_data.get('performance') or {'total_trades': 0, 'winning_trades': 0, 'total_pnl': 0, 'win_rate': 0}
    # Taux USD -> EUR (1 USDT = X EUR) pour affichage PnL en €
    try:
        eur_usdt = shared_data.get('last_prices', {}).get('EURUSDT') or fetch_current_prices(['EURUSDT']).get('EURUSDT', 1.08)
        usd_to_eur = 1.0 / float(eur_usdt) if eur_usdt else 0.92
    except Exception:
        usd_to_eur = 0.92

    all_trades = trader.get_trades_history()
    trades_history = [t for t in all_trades if 'VENTE' in t.get('type', '')][:50]

    return render_template_string(
        get_minimal_dashboard_html(),
        balance=balance,
        total_capital=total_capital,
        positions=positions_view,
        total_unrealized_pnl=total_unrealized_pnl,
        usd_to_eur=usd_to_eur,
        opportunities=shared_data['opportunities'],
        is_scanning=shared_data['is_scanning'],
        last_update=shared_data['last_update'],
        scan_count=shared_data['scan_count'],
        bot_log=shared_data['bot_log'],
        perf=perf,
        trades_history=trades_history,
    )


@app.route('/api/data')
def api_data():
    """API JSON pour le rechargement AJAX du dashboard."""
    try:
        trader = PaperTrader()
        balance = trader.get_usdt_balance()
        open_positions = trader.get_open_positions()
        all_trades = trader.get_trades_history()
        history = [t for t in all_trades if 'VENTE' in t.get('type', '')]

        prices = _prices_for_dashboard(open_positions)
        positions_view = []
        total_unrealized_pnl = 0
        for symbol, pos_data in open_positions.items():
            entry = pos_data['entry_price']
            current = prices.get(symbol, entry)
            direction = pos_data.get('direction', 'LONG')
            if direction == 'LONG':
                pnl_value = (current - entry) * pos_data['quantity']
                pnl_percent = ((current - entry) / entry) * 100
            else:
                pnl_value = (entry - current) * pos_data['quantity']
                pnl_percent = ((entry - current) / entry) * 100
            total_unrealized_pnl += pnl_value
            sl = pos_data.get('stop_loss', entry)
            tp = pos_data.get('take_profit', entry)
            if direction == 'LONG':
                range_total = tp - sl if (tp - sl) != 0 else 1
                progress = max(0, min(100, ((current - sl) / range_total) * 100))
            else:
                range_total = sl - tp if (sl - tp) != 0 else 1
                progress = max(0, min(100, ((sl - current) / range_total) * 100))
            positions_view.append({
                'symbol': symbol, 'direction': direction, 'entry': entry, 'current': current,
                'amount': pos_data['amount_usdt'], 'quantity': pos_data['quantity'],
                'pnl_value': round(pnl_value, 2), 'pnl_percent': round(pnl_percent, 2),
                'sl': sl, 'tp': tp, 'entry_time': pos_data.get('entry_time', 'N/A'), 'progress': progress,
                'leverage': pos_data.get('leverage', 1),
            })

        # Sanitize opportunities for JSON serialization
        safe_opps = []
        for opp in shared_data.get('opportunities', []):
            safe_opp = {}
            for k, v in opp.items():
                if isinstance(v, float) and (v != v):  # NaN check
                    safe_opp[k] = 0
                else:
                    safe_opp[k] = v
            safe_opps.append(safe_opp)

        return jsonify({
            'balance': balance,
            'positions': positions_view,
            'total_unrealized_pnl': round(total_unrealized_pnl, 2),
            'history': history[:10],
            'opportunities': safe_opps,
            'is_scanning': shared_data['is_scanning'],
            'last_update': shared_data['last_update'],
            'scan_count': shared_data['scan_count'],
            'bot_log': shared_data['bot_log'][:15],
            'performance': shared_data.get('performance', {}),
            'market_stats': shared_data.get('market_stats', {}),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/trades')
def export_trades_csv():
    """Exporte l'historique des trades en CSV (téléchargement)."""
    import csv
    import io
    trader = PaperTrader()
    history = trader.get_trades_history()
    output = io.StringIO()
    keys = ['time', 'type', 'symbol', 'direction', 'entry_price', 'price', 'amount', 'pnl', 'pnl_percent', 'reason']
    writer = csv.DictWriter(output, fieldnames=keys, extrasaction='ignore')
    writer.writeheader()
    for t in history:
        row = {k: t.get(k, '') for k in keys}
        writer.writerow(row)
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=trades_export.csv'})


@app.route('/api/close/<symbol>', methods=['POST'])
def close_position_route(symbol):
    """Ferme manuellement une position. Si prix indisponible, ferme au prix d'entree (force)."""
    trader = PaperTrader()
    open_pos = trader.get_open_positions()
    if symbol not in open_pos:
        return jsonify({'success': False, 'error': 'Position inexistante'})
    current_price = shared_data.get('last_prices', {}).get(symbol)
    if not current_price:
        try:
            fetched = fetch_current_prices([symbol])
            current_price = fetched.get(symbol)
        except Exception:
            pass
    if not current_price:
        # Force close: utilise le prix d'entree (PnL = 0) pour supprimer la position bloquee
        current_price = open_pos[symbol]['entry_price']
        add_bot_log("Prix {} indisponible (API) — fermeture forcee au prix d'entree.".format(symbol), 'WARN')
    success = trader.close_position(symbol, current_price, "MANUEL")
    if success:
        add_bot_log(f"ðŸ’° VENTE MANUELLE {symbol} @ ${current_price:.4f}", 'TRADE')
    return jsonify({'success': success})


@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Réinitialise le portefeuille à 100€ et vide l'historique des trades."""
    trader = PaperTrader()
    ok = trader.reset_to_initial(100)
    if ok:
        add_bot_log("Réinitialisation: 100€, 0 positions, historique vide.", 'INFO')
    return jsonify({'success': ok, 'error': None if ok else 'Erreur reset'})


@app.route('/health')
def health():
    """Health check pour load balancers et monitoring (production)."""
    return jsonify({
        'status': 'ok',
        'scan_count': shared_data['scan_count'],
        'is_scanning': shared_data.get('is_scanning', False),
    }), 200


@app.route('/api/crash_status')
def crash_status():
    """Retourne le statut du systÃ¨me anti-crash."""
    status = get_crash_status()
    status['stats'] = crash_protector.get_crash_stats()
    return jsonify(status)


@app.route('/api/resume_trading', methods=['POST'])
def resume_trading():
    """Force la reprise du trading aprÃ¨s un crash (bypass manuel)."""
    crash_protector.force_resume_trading()
    add_bot_log("âš ï¸ REPRISE MANUELLE du trading aprÃ¨s crash", 'WARN')
    return jsonify({'success': True, 'message': 'Trading resumed'})


@app.route('/api/sentiment')
def api_sentiment():
    """Retourne l'analyse de sentiment marchÃ©."""
    try:
        sentiment = get_market_sentiment()
        sentiment['cached'] = shared_data.get('market_sentiment', {})
        return jsonify(sentiment)
    except Exception as e:
        return jsonify({'error': str(e), 'cached': shared_data.get('market_sentiment', {})})


@app.route('/api/intelligence')
def api_intelligence():
    """Retourne l'intelligence de marchÃ© complÃ¨te."""
    try:
        intel = get_market_intelligence()
        intel['cached'] = shared_data.get('market_intelligence', {})
        return jsonify(intel)
    except Exception as e:
        return jsonify({'error': str(e), 'cached': shared_data.get('market_intelligence', {})})


@app.route('/api/quick_intel')
def api_quick_intel():
    """Version rapide de l'intelligence (moins de donnÃ©es)."""
    try:
        return jsonify({
            'funding': market_intel.get_funding_rates(),
            'ls_ratio': market_intel.get_long_short_ratio(),
            'orderbook': market_intel.get_order_book_imbalance(),
            'top_movers': market_intel.get_top_movers(),
            'cached': shared_data.get('market_intelligence', {})
        })
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/ml_prediction/<symbol>')
def api_ml_prediction(symbol):
    """Retourne la prédiction ML pour une paire."""
    try:
        direction = request.args.get('direction', 'LONG')
        all_indicators = shared_data.get('last_indicators', {})
        indicators = all_indicators.get(symbol, {})
        
        if not indicators:
            return jsonify({'error': f'No indicators for {symbol}'})
        
        sentiment = shared_data.get('market_sentiment', {})
        prediction = get_ml_prediction(indicators, direction, sentiment, 0)
        
        return jsonify({
            'symbol': symbol,
            'direction': direction,
            'prediction': prediction
        })
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/ml_stats')
def api_ml_stats():
    """Retourne les statistiques du modÃ¨le ML."""
    try:
        stats = ml_predictor.get_model_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/ml_update', methods=['POST'])
def api_ml_update():
    """Force une mise Ã  jour du modÃ¨le ML avec les donnÃ©es d'entraÃ®nement."""
    try:
        ml_predictor.update_weights_from_history()
        return jsonify({'success': True, 'message': 'ML model updated'})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/onchain')
def api_onchain():
    """Retourne l'analyse on-chain complÃ¨te."""
    try:
        btc_price = shared_data.get('last_prices', {}).get('BTCUSDT', 45000)
        analysis = get_onchain_analysis(btc_price)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/onchain/tvl')
def api_onchain_tvl():
    """Retourne les donnÃ©es TVL DeFi."""
    try:
        tvl = onchain_analyzer.get_defi_tvl()
        return jsonify(tvl)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/onchain/nupl')
def api_onchain_nupl():
    """Retourne l'estimation NUPL."""
    try:
        btc_price = shared_data.get('last_prices', {}).get('BTCUSDT', 45000)
        nupl = onchain_analyzer.estimate_nupl(btc_price)
        return jsonify(nupl)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/position_sizing')
def api_position_sizing():
    """Retourne les statistiques et recommandations de position sizing."""
    try:
        trader = PaperTrader()
        balance = trader.get_usdt_balance()
        stats = position_sizer.get_stats()
        recommendations = get_position_recommendations(balance, MAX_POSITIONS)
        return jsonify({
            'stats': stats,
            'recommendations': recommendations,
            'current_balance': balance
        })
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/position_sizing/calculate')
def api_calculate_position():
    """Calcule la taille de position optimale pour un trade."""
    try:
        trader = PaperTrader()
        symbol = request.args.get('symbol', 'BTCUSDT')
        score = int(request.args.get('score', 70))
        ml_prob = float(request.args.get('ml_prob', 50))

        balance = trader.get_usdt_balance()
        all_indicators = shared_data.get('last_indicators', {})
        indicators = all_indicators.get(symbol, {})
        
        position_size, breakdown = calculate_position_size(
            capital=balance,
            indicators=indicators,
            score=score,
            ml_probability=ml_prob
        )
        
        return jsonify({
            'symbol': symbol,
            'position_size': position_size,
            'breakdown': breakdown,
            'balance': balance
        })
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/intelligence_summary')
def api_intelligence_summary():
    """Retourne un résumé de toute l'intelligence disponible."""
    try:
        trader = PaperTrader()
        btc_price = shared_data.get('last_prices', {}).get('BTCUSDT', 45000)

        return jsonify({
            'sentiment': shared_data.get('market_sentiment', {}),
            'intelligence': shared_data.get('market_intelligence', {}),
            'onchain': get_onchain_analysis(btc_price),
            'ml_stats': ml_predictor.get_model_stats(),
            'position_sizing': position_sizer.get_stats(),
            'kelly_recommendations': get_position_recommendations(trader.get_usdt_balance(), MAX_POSITIONS),
            'macro': shared_data.get('macro_analysis', {}),
            'social_sentiment': get_social_sentiment('BTC') if SOCIAL_SENTIMENT_ENABLED else {},
            'trade_journal': get_journal_stats(30) if TRADE_JOURNAL_ENABLED else {}
        })
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/macro')
def api_macro():
    """Retourne l'analyse macroÃ©conomique complÃ¨te."""
    try:
        analysis = get_macro_analysis()
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/macro/events')
def api_macro_events():
    """Retourne les Ã©vÃ©nements Ã©conomiques Ã  venir."""
    try:
        days = request.args.get('days', 7, type=int)
        events = get_upcoming_economic_events(days)
        return jsonify({
            'events': events,
            'count': len(events),
            'days_ahead': days
        })
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/macro/today')
def api_macro_today():
    """Retourne les Ã©vÃ©nements du jour."""
    try:
        analysis = get_macro_analysis()
        return jsonify({
            'today_events': analysis.get('economic_events', {}).get('today', []),
            'should_pause': analysis.get('should_pause_trading', False),
            'pause_reason': analysis.get('pause_reason'),
            'regulation_alerts': analysis.get('regulation', {})
        })
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/macro/add_event', methods=['POST'])
def api_add_macro_event():
    """Ajoute un Ã©vÃ©nement personnalisÃ© au calendrier."""
    try:
        data = request.json
        success = macro_analyzer.add_custom_event(
            date=data.get('date'),
            name=data.get('name'),
            impact=data.get('impact', 'MEDIUM'),
            event_type=data.get('type', 'CUSTOM'),
            pause_hours=data.get('pause_hours', 1)
        )
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)})


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# API SOCIAL SENTIMENT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.route('/api/social')
def api_social_sentiment():
    """Retourne l'analyse du sentiment social complÃ¨te."""
    try:
        symbol = request.args.get('symbol', 'BTC')
        return jsonify(get_social_sentiment(symbol))
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/social/fear_greed')
def api_fear_greed():
    """Retourne le Fear & Greed Index."""
    try:
        return jsonify(get_social_fear_greed())
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/social/trending')
def api_trending():
    """Retourne les coins trending."""
    try:
        analyzer = get_social_analyzer()
        return jsonify(analyzer.get_trending_coins())
    except Exception as e:
        return jsonify({'error': str(e)})


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# API TRADE JOURNAL AI
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.route('/api/journal')
def api_trade_journal():
    """Retourne l'analyse complÃ¨te du journal de trading."""
    try:
        return jsonify(get_trade_journal().get_complete_analysis())
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/journal/stats')
def api_journal_stats():
    """Retourne les statistiques de performance."""
    try:
        days = request.args.get('days', 30, type=int)
        return jsonify(get_journal_stats(days))
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/journal/errors')
def api_journal_errors():
    """Retourne l'analyse des erreurs."""
    try:
        return jsonify(get_trade_journal().analyze_errors())
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/journal/successes')
def api_journal_successes():
    """Retourne l'analyse des succÃ¨s."""
    try:
        return jsonify(get_trade_journal().analyze_successes())
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/journal/daily')
def api_journal_daily():
    """Retourne le rapport journalier."""
    try:
        return jsonify(get_trade_journal().get_daily_report())
    except Exception as e:
        return jsonify({'error': str(e)})


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# TEMPLATE HTML SIMPLIFIÃ‰
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_html_template():

    return r"""
<!DOCTYPE html>
<html lang=\"fr\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>SHORT Grandes Baisses Bot</title>
<style>
/* ...existing code... */
</style>
</head>
<body>
<div class=\"app\">

<!-- HEADER -->
<div class=\"header\">
    <div>
        <h1>SHORT Grandes Baisses Bot</h1>
        <span style=\"font-size:0.8em;color:var(--text3)\">SHORT only &#8226; TF: {{ timeframe|upper }} &#8226; TP: -{{ TAKE_PROFIT_PCT }}% &#8226; SL: +{{ STOP_LOSS_PCT }}% &#8226; 1 position max</span>
    </div>
    <div class=\"status\">
        <div class=\"dot {% if is_scanning %}scanning{% endif %}\"></div>
        {% if is_scanning %}Scanning...{% else %}Active{% endif %}
        <span style=\"margin-left:16px;color:var(--text3)\">Scan #{{ scan_count }} &#8226; {{ last_update }}</span>
    </div>
</div>

<!-- STATS PRINCIPAUX -->
<div class="stats">
    <div class="stat">
        <div class="stat-label">&#128176; Capital</div>
        <div class="stat-value blue">${{ "%.2f"|format(total_capital) }}</div>
        <div class="stat-sub">Disponible: ${{ "%.2f"|format(balance) }}</div>
    </div>
    <div class="stat">
        <div class="stat-label">&#128200; PnL Latent</div>
        <div class="stat-value {% if total_unrealized_pnl >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(total_unrealized_pnl) }}$</div>
        <div class="stat-sub">{{ positions|length }} position(s) ouverte(s)</div>
    </div>
    <div class="stat">
        <div class="stat-label">&#10004; PnL Realise</div>
        <div class="stat-value {% if perf.total_pnl >= 0 %}green{% else %}red{% endif %}">{{ "%+.2f"|format(perf.total_pnl) }}$</div>
        <div class="stat-sub">{{ perf.winning_trades }}/{{ perf.total_trades }} trades gagnants</div>
    </div>
    <div class="stat">
        <div class="stat-label">&#127919; Win Rate</div>
        <div class="stat-value">{{ perf.win_rate }}%</div>
        <div class="stat-sub">{{ perf.total_trades }} trades au total</div>
    </div>
</div>

<!-- POSITIONS ACTIVES -->
<div class="card">
    <div class="card-header">
        <h2>&#128188; Positions Actives ({{ positions|length }})</h2>
        <span class="badge b-blue">PAPER TRADING</span>
    </div>
    {% if positions %}
    <div style="overflow-x:auto;">
        <table>
            <thead><tr>
                <th>Paire</th><th>Type</th><th>Entree</th><th>Actuel</th><th>Investi</th>
                <th>PnL</th><th>SL / TP</th><th>Progression</th><th>Action</th>
            </tr></thead>
            <tbody>
            {% for p in positions %}
            <tr>
                <td style="font-weight:700;color:var(--blue)">{{ p.symbol }}</td>
                <td><span class="badge {% if p.direction == 'LONG' %}b-green{% else %}b-red{% endif %}">{{ p.direction }}</span></td>
                <td>${{ "%.4f"|format(p.entry) }}</td>
                <td style="font-weight:600">${{ "%.4f"|format(p.current) }}</td>
                <td>${{ "%.0f"|format(p.amount) }}</td>
                <td class="{% if p.pnl_percent >= 0 %}green{% else %}red{% endif %}" style="font-weight:700">
                    {{ "%+.2f"|format(p.pnl_percent) }}% ({{ "%+.2f"|format(p.pnl_value) }}$)
                </td>
                <td style="font-size:0.85em;color:var(--text3)">
                    <span class="red">{{ "%.4f"|format(p.sl) }}</span> / 
                    <span class="green">{{ "%.4f"|format(p.tp) }}</span>
                </td>
                <td>
                    <div style="display:flex;align-items:center;gap:8px;">
                        <div class="progress"><div class="progress-fill" style="width:{{ [0,[100,p.progress]|min]|max }}%"></div></div>
                        <span style="font-size:0.8em;color:var(--text3)">{{ "%.0f"|format(p.progress) }}%</span>
                    </div>
                </td>
                <td><button class="btn btn-close" onclick="closePos('{{ p.symbol }}')">Fermer</button></td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="empty">Aucune position ouverte</div>
    {% endif %}
</div>

<div class="grid-2">
    <!-- OPPORTUNITES -->
    <div class="card">
        <div class="card-header">
            <h2>&#127919; Meilleures Opportunites ({{ opportunities|length }})</h2>
            <span style="font-size:0.8em;color:var(--text3)">Score &#8805; {{ min_score }} = Auto-achat</span>
        </div>
        {% if opportunities %}
        <div style="overflow-x:auto;">
            <table>
                <thead><tr><th>Paire</th><th>Prix</th><th>Signal</th><th>Score</th><th>R/R</th></tr></thead>
                <tbody>
                {% for opp in opportunities[:10] %}
                <tr>
                    <td style="font-weight:700">{{ opp.pair }}</td>
                    <td>${{ "%.4f"|format(opp.price) }}</td>
                    <td><span class="badge {% if opp.entry_signal == 'LONG' %}b-green{% elif opp.entry_signal == 'SHORT' %}b-red{% else %}b-yellow{% endif %}">{{ opp.entry_signal }}</span></td>
                    <td style="font-weight:700;color:{% if opp.score >= 80 %}var(--green){% elif opp.score >= 60 %}var(--yellow){% else %}var(--text3){% endif %}">{{ opp.score }}</td>
                    <td style="color:var(--blue)">{{ opp.rr_ratio }}x</td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
        <div class="empty">Aucune opportunite detectee</div>
        {% endif %}
    </div>

    <!-- HISTORIQUE -->
    <div class="card">
        <div class="card-header">
            <h2>&#128220; Derniers Trades</h2>
            <span class="{% if perf.total_pnl >= 0 %}green{% else %}red{% endif %}" style="font-weight:600">Total: {{ "%+.2f"|format(perf.total_pnl) }}$</span>
        </div>
        {% if history %}
        <div style="overflow-x:auto;">
            <table>
                <thead><tr><th>Paire</th><th>PnL</th><th>Date</th></tr></thead>
                <tbody>
                {% for t in history[:8] %}
                <tr>
                    <td style="font-weight:600">{{ t.symbol }}</td>
                    <td class="{% if t.pnl >= 0 %}green{% else %}red{% endif %}" style="font-weight:700">{{ "%+.2f"|format(t.pnl) }}$ ({{ "%+.1f"|format(t.pnl_percent) }}%)</td>
                    <td style="color:var(--text3);font-size:0.85em">{{ t.time }}</td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
        <div class="empty">Aucun trade ferme</div>
        {% endif %}
    </div>
</div>

<!-- BOT LOG -->
<div class="card">
    <div class="card-header">
        <h2>&#129302; Journal du Bot</h2>
    </div>
    <div class="log">
        {% if bot_log %}
        {% for entry in bot_log %}
        <div class="log-line">
            <span class="log-time">{{ entry.time }}</span>
            <span class="log-level l-{{ entry.level }}">{{ entry.level }}</span>
            <span class="log-msg">{{ entry.msg }}</span>
        </div>
        {% endfor %}
        {% else %}
        <div class="empty">En attente d'activite...</div>
        {% endif %}
    </div>
    <!-- Quick Indicators -->
    <div class="indicators">
        <div class="ind"><span class="ind-label">Sentiment:</span><span class="ind-value">{{ mkt.sentiment }}</span></div>
        <div class="ind"><span class="ind-label">RSI moy:</span><span class="ind-value">{{ mkt.avg_rsi }}</span></div>
        <div class="ind"><span class="ind-label">Bullish:</span><span class="ind-value green">{{ mkt.total_bullish }}</span></div>
        <div class="ind"><span class="ind-label">Bearish:</span><span class="ind-value red">{{ mkt.total_bearish }}</span></div>
        <div class="ind" id="fear-greed-display"><span class="ind-label">Fear/Greed:</span><span class="ind-value" id="fg-val">--</span></div>
    </div>
</div>

<!-- FOOTER -->
<div style="text-align:center;padding:20px;color:var(--text3);font-size:0.8em;">
    Crypto Trading Bot v2.0 &#8226; Tous modules actifs (ML, On-Chain, Kelly, Macro, Social)
</div>

</div>

<script>
function closePos(symbol) {
    if (confirm('Fermer la position ' + symbol + ' ?')) {
        fetch('/api/close/' + symbol, {method: 'POST'})
            .then(r => r.json())
            .then(d => {
                if(d.success) {
                    alert('Position ' + symbol + ' fermée avec succès!');
                    location.reload();
                } else {
                    alert('Erreur: ' + (d.error || 'Echec de la fermeture'));
                }
            })
            .catch(err => alert('Erreur réseau: ' + err));
    }
}

// Fetch Fear & Greed
fetch('/api/social/fear_greed')
    .then(r => r.json())
    .then(data => {
        if(data.value) {
            const el = document.getElementById('fg-val');
            el.textContent = data.value + ' (' + data.classification + ')';
            el.style.color = data.value <= 30 ? 'var(--red)' : (data.value >= 70 ? 'var(--green)' : 'var(--yellow)');
        }
    })
    .catch(() => {});
</script>
</body>
</html>
"""


# BOUCLE PRINCIPALE (THREAD BACKGROUND)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

AVOID_WEEKENDS = False  # Day trader pro H24: crypto trade 7j/7

def _get_scan_interval():
    """Day trader pro H24: 90s en session, 5 min la nuit (volumes plus faibles), 90s sinon."""
    utc_hour = datetime.utcnow().hour
    if SESSION_BONUS_ENABLED and SESSION_BONUS_UTC_START <= utc_hour < SESSION_BONUS_UTC_END:
        return SCAN_INTERVAL_SESSION  # 90s
    elif utc_hour < 6 or utc_hour >= 23:
        return SCAN_INTERVAL_NIGHT  # 900s
    return SCAN_INTERVAL  # 90s

def run_loop():
    """Boucle infinie qui lance le scanner periodiquement."""
    add_bot_log("âš¡ Swing Bot dÃ©marrÃ© â€” Timeframe: " + TIMEFRAME, 'INFO')
    add_bot_log("Day Trader Pro H24 | Score>={} | R:R>={} | Max {} pos | 7j/7".format(MIN_SCORE_TO_OPEN, MIN_RISK_REWARD, MAX_POSITIONS), 'INFO')
    while True:
        now_utc = datetime.utcnow()
        if AVOID_WEEKENDS and now_utc.weekday() >= 5:
            add_bot_log("Weekend: pause trading, volume trop faible.", 'INFO')
            time.sleep(3600)
            continue
        try:
            shared_data['sentiment_display'] = fetch_sentiment_for_dashboard()
        except Exception as e:
            add_bot_log("Sentiment: {}".format(str(e)[:60]), 'WARN')
        shared_data['is_scanning'] = True
        try:
            shared_data['opportunities'] = run_scanner()
            shared_data['last_update'] = datetime.now().strftime('%H:%M:%S')
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(tb)
            add_bot_log("Erreur boucle: {} | {}".format(str(e), tb.split('\n')[-3].strip() if len(tb.split('\n')) > 3 else ''), 'ERROR')
        finally:
            shared_data['is_scanning'] = False

        interval = _get_scan_interval()
        pause_str = "{} min".format(interval // 60) if interval >= 60 else "{} s".format(interval)
        add_bot_log("Pause {} — prochain scan a {}".format(pause_str, datetime.now().strftime('%H:%M')), 'INFO')
        time.sleep(interval)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# LANCEMENT
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    scanner_thread = threading.Thread(target=run_loop, daemon=True)
    scanner_thread.start()

    port = int(os.environ.get('PORT', 8080))
    add_bot_log('Dashboard: http://localhost:{}'.format(port), 'INFO')
    app.run(host='0.0.0.0', port=port, debug=False)
