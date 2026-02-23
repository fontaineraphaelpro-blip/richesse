"""
Script principal: Crypto Swing Trader Bot & Dashboard ULTIME.
Version: ULTIMATE v2.0 â€” Scanner complet + Bot Swing + Paper Trading + Dashboard Pro
"""

import time
import os
import threading
import json
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request

# Import des modules internes
from trader import PaperTrader
from data_fetcher import fetch_multiple_pairs, validate_signal_multi_timeframe
from dashboard_template import get_enhanced_dashboard
from dashboard_stats import calculate_advanced_stats, calculate_chart_data, format_history_for_display, get_all_pairs_from_history
from indicators import calculate_indicators
from scorer import calculate_opportunity_score
from support import find_swing_low
from scalping_signals import find_resistance
from trade_filters import trade_filters
from crash_protection import crash_protector, check_for_crash, is_crash_mode, get_crash_status
from news_analyzer import news_analyzer, get_market_sentiment, get_fear_greed
from market_intelligence import market_intel, get_market_intelligence, should_trade_with_intel
from ml_predictor import ml_predictor, get_ml_prediction, log_trade_result
from onchain_analyzer import onchain_analyzer, get_onchain_analysis, get_onchain_signal_adjustment
from position_sizing import position_sizer, calculate_position_size, update_position_stats, get_position_recommendations
from macro_events import macro_analyzer, get_macro_analysis, check_macro_events, get_upcoming_economic_events
from social_sentiment import get_social_analyzer, get_fear_greed as get_social_fear_greed, get_social_sentiment, get_sentiment_modifier
from trade_journal_ai import get_trade_journal, record_entry, record_exit, get_journal_stats, should_trade as journal_should_trade, get_trade_modifier
from fundamental_analysis import fundamental_analyzer, get_fundamental_score, should_trade_fundamentally, get_fundamental_modifier
from advanced_technical_analysis import advanced_ta, get_advanced_technical_analysis, get_technical_score_adjustment
from adaptive_strategy import adaptive_strategy, analyze_and_adapt, get_adaptive_strategy

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CONFIGURATION DU BOT
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# STRATÉGIE SHORT UNIQUEMENT — Grandes baisses
# ─────────────────────────────────────────────────────────
TIMEFRAME        = '15m'   # Bougies 15 min (détecter les vraies baisses)
CANDLE_LIMIT     = 100     # Nombre de bougies par paire
# Pour un SHORT: SL au-dessus du prix, TP en dessous
STOP_LOSS_PCT    = 1.0     # Stop loss au-dessus de l'entrée (%)
TAKE_PROFIT_PCT  = 2.0     # Take profit en dessous de l'entrée (%) → R:R = 2
SCAN_INTERVAL    = 60      # Secondes entre chaque scan
MAX_POSITIONS    = 1       # Une seule position à la fois
MAX_CONSECUTIVE_LOSSES = 3 # Arrêt après 3 pertes d'affilée
COOLDOWN_MINUTES = 15      # Pause après chaque trade (min)
# Filtres de qualité
SPREAD_MAX_PCT   = 0.15    # Écart max bougie
VOLUME_RATIO_MIN = 1.0     # Volume au moins égal à la moyenne
VOLATILITY_MAX   = 5.0     # ATR % max
TREND_15M_MUST_BEARISH = True  # Ne short que si tendance 15m baissière
POSITION_PCT_BALANCE   = 0.20  # Taille position = 20% du solde max
MIN_POSITION_USDT      = 10    # Minimum 10 USDT par short

# Limite de paires pour le scan (20 = test rapide, None = toutes les paires)
SCAN_PAIRS_LIMIT = 20

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# NOUVELLES CONFIGURATIONS RENTABILITÃ‰
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# Take Profit Partiel (Scaling Out)
PARTIAL_TP_ENABLED = True    # Activer TP partiel
PARTIAL_TP_RATIO = 0.5       # Prendre 50% Ã  TP1
# Le reste court vers TP2

# Filtrage Volume
VOLUME_FILTER_ENABLED = True
MIN_VOLUME_RATIO = 1.2       # Volume doit Ãªtre 1.2x la moyenne

# Heures de Trading Optimales (UTC)
TRADING_HOURS_ENABLED = False  # DÉSACTIVÉ - trade 24/7
TRADING_START_HOUR = 0         # (non utilisé)
TRADING_END_HOUR = 24          # (non utilisé)
AVOID_WEEKENDS = True        # Ã‰viter samedi/dimanche

# Score Dynamique selon Marche (EQUILIBRE)
DYNAMIC_SCORE_ENABLED = True
SCORE_BULLISH_MARKET = 68    # Score min si marche haussier (plus permissif)
SCORE_BEARISH_MARKET = 78    # Score min si marche baissier (plus strict)
SCORE_NEUTRAL_MARKET = 72    # Score min si marche neutre

# Risk/Reward Minimum REALISTE
MIN_RISK_REWARD = 2.0        # Rejeter si R/R < 2:1 (realiste et rentable)

# Configuration News & Sentiment
NEWS_ENABLED = False          # DÉSACTIVÉ - trop de bruit
SENTIMENT_SCORE_ADJUST = False # DÉSACTIVÉ
PAUSE_ON_EVENTS = False       # DÉSACTIVÉ

# Configuration Machine Learning
ML_ENABLED = False            # DÉSACTIVÉ - trop de bruit
ML_MIN_PROBABILITY = 60       # (non utilisé)
ML_SCORE_ADJUST = False       # DÉSACTIVÉ

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
    'arbitrage_logs': [],       # Logs arbitrage (partagé avec arbitrage_strategy si utilisé)
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
    print(f"[{entry['time']}][{level}] {msg}")


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
    from short_crash_strategy import signal_short_big_drop, position_size_usdt
    from indicators import calculate_indicators
    from data_fetcher import fetch_multiple_pairs, get_top_pairs

    shared_data['scan_count'] += 1
    scan_num = shared_data['scan_count']

    # Liste des paires (limité en mode test pour exécution rapide)
    symbols = get_top_pairs()
    if SCAN_PAIRS_LIMIT:
        symbols = symbols[:SCAN_PAIRS_LIMIT]
    add_bot_log(f"=== SHORT GRANDES BAISSES SCAN #{scan_num} ({len(symbols)} paires) ===", 'INFO')

    # —— 1. Données marché (15m) ——
    data, real_prices = fetch_multiple_pairs(symbols, interval=TIMEFRAME, limit=CANDLE_LIMIT)
    if not data:
        add_bot_log("Aucune donnée reçue de Binance", 'ERROR')
        return []
    shared_data['last_prices'] = real_prices
    shared_data['last_indicators'] = {}

    # —— 2. État du trader ——
    from trader import PaperTrader
    trader = PaperTrader()
    open_pos = trader.get_open_positions()
    if open_pos:
        add_bot_log("Déjà une position ouverte, attente fermeture/cooldown.", 'INFO')
        return []

    # Vérifier les 3 DERNIÈRES ventes (trades fermés): si toutes en perte → stop
    recent = trader.get_trades_history()
    sales = [t for t in recent if 'VENTE' in t.get('type', '')]
    last_3_sales = sales[:3]
    if len(last_3_sales) >= MAX_CONSECUTIVE_LOSSES and all(t.get('pnl', 0) < 0 for t in last_3_sales):
        add_bot_log(f"STOP: {MAX_CONSECUTIVE_LOSSES} pertes consécutives, trading suspendu.", 'ERROR')
        return []

    # —— 3. Parcourir les paires et chercher un signal SHORT (grande baisse) ——
    for symbol, df in data.items():
        indicators = calculate_indicators(df)
        shared_data['last_indicators'][symbol] = indicators

        if indicators.get('volume_ratio') is None or indicators.get('volume_ratio', 0) < VOLUME_RATIO_MIN:
            continue
        spread_pct = (df['high'].iloc[-1] - df['low'].iloc[-1]) / df['close'].iloc[-1] * 100
        if spread_pct > SPREAD_MAX_PCT:
            continue
        if (indicators.get('atr_percent') or 0) > VOLATILITY_MAX:
            continue

        # Tendance 15m baissière requise pour short les grandes baisses
        if TREND_15M_MUST_BEARISH:
            from data_fetcher import fetch_multi_timeframe
            tf_data = fetch_multi_timeframe(symbol, ['15m'])
            if tf_data.get('15m') is not None:
                tf_ind = calculate_indicators(tf_data['15m'])
                if tf_ind.get('price_momentum') != 'BEARISH':
                    continue

        if not signal_short_big_drop(df, indicators, VOLUME_RATIO_MIN):
            continue

        in_cooldown, cooldown_rem = trader.is_in_cooldown(symbol)
        if in_cooldown:
            add_bot_log(f"{symbol} en cooldown ({cooldown_rem:.1f} min)", 'INFO')
            continue

        price = indicators.get('current_price')
        if not price or price <= 0:
            continue
        balance = trader.get_usdt_balance()
        pos_size = position_size_usdt(balance, max_pct_balance=POSITION_PCT_BALANCE)
        pos_size = min(pos_size, max(0, balance * 0.98))
        if pos_size < MIN_POSITION_USDT:
            add_bot_log(f"Solde insuffisant pour {symbol} (min {MIN_POSITION_USDT} USDT)", 'INFO')
            continue

        # SHORT: SL au-dessus, TP en dessous
        stop_loss = price * (1 + STOP_LOSS_PCT / 100)
        take_profit = price * (1 - TAKE_PROFIT_PCT / 100)

        if trader.place_short_order(symbol, pos_size, price, stop_loss, take_profit, entry_trend='CRASH_SHORT'):
            trader.record_trade_time(symbol)
            add_bot_log(f"SHORT {symbol} @ {price:.4f} | SL {stop_loss:.4f} | TP {take_profit:.4f}", 'TRADE')
            return [{'pair': symbol, 'signal': 'SHORT', 'price': price}]

    add_bot_log("Aucun signal grande baisse (SHORT) détecté.", 'INFO')
    return []


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# ROUTES FLASK
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/')
def dashboard():
    """Dashboard principal â€” rendu cÃ´tÃ© serveur."""
    trader = PaperTrader()
    balance = trader.get_usdt_balance()
    all_trades = trader.get_trades_history()
    open_positions = trader.get_open_positions()
    
    history = [t for t in all_trades if 'VENTE' in t.get('type', '')]
    
    positions_view = []
    total_unrealized_pnl = 0

    for symbol, pos_data in open_positions.items():
        entry = pos_data['entry_price']
        current = shared_data['last_prices'].get(symbol, entry)
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
            'amount':      pos_data['amount_usdt'],  # Affiche la taille totale (levier désactivé)
            'quantity':    pos_data['quantity'],
            'pnl_value':   pnl_value,
            'pnl_percent': pnl_percent,
            'sl':          sl,
            'tp':          tp,
            'entry_time':  pos_data.get('entry_time', 'N/A'),
            'progress':    progress,
        })

    perf = shared_data['performance']
    mkt = shared_data['market_stats']
    
    # Capital total = Solde USDT + valeur des positions
    total_invested = sum(p['amount'] for p in positions_view)
    total_capital = balance + total_invested + total_unrealized_pnl
    
    # Calculer les stats avancees et donnees de graphiques
    stats = calculate_advanced_stats(all_trades)
    chart_data = calculate_chart_data(all_trades)
    formatted_history = format_history_for_display(all_trades)
    all_pairs = get_all_pairs_from_history(all_trades)
    crash = get_crash_status()

    return render_template_string(
        get_enhanced_dashboard(),
        balance=balance,
        total_capital=total_capital,
        positions=positions_view,
        total_unrealized_pnl=total_unrealized_pnl,
        history=formatted_history,
        opportunities=shared_data['opportunities'],
        all_scanned=shared_data['all_scanned'][:200],
        is_scanning=shared_data['is_scanning'],
        last_update=shared_data['last_update'],
        scan_count=shared_data['scan_count'],
        bot_log=shared_data['bot_log'],
        perf=perf,
        mkt=mkt,
        min_score=None,  # Plus de score minimum pour micro scalp
        timeframe=TIMEFRAME,
        trade_amount=FIXED_TRADE_AMOUNT,  # Micro scalp: montant fixe ou None
        stats=stats,
        chart_data=json.dumps(chart_data),
        all_pairs=all_pairs,
        crash=crash,
        arbitrage_logs=shared_data.get('arbitrage_logs', []),
    )


@app.route('/api/data')
def api_data():
    """API JSON pour le rechargement AJAX du dashboard."""
    trader = PaperTrader()
    balance = trader.get_usdt_balance()
    open_positions = trader.get_open_positions()
    all_trades = trader.get_trades_history()
    history = [t for t in all_trades if 'VENTE' in t.get('type', '')]

    positions_view = []
    total_unrealized_pnl = 0
    for symbol, pos_data in open_positions.items():
        entry = pos_data['entry_price']
        current = shared_data['last_prices'].get(symbol, entry)
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
        })

    return jsonify({
        'balance': balance,
        'positions': positions_view,
        'total_unrealized_pnl': round(total_unrealized_pnl, 2),
        'history': history[:10],
        'opportunities': shared_data['opportunities'],
        'is_scanning': shared_data['is_scanning'],
        'last_update': shared_data['last_update'],
        'scan_count': shared_data['scan_count'],
        'bot_log': shared_data['bot_log'][:15],
        'performance': shared_data['performance'],
        'market_stats': shared_data['market_stats'],
    })


@app.route('/api/close/<symbol>', methods=['POST'])
def close_position_route(symbol):
    """Ferme manuellement une position."""
    trader = PaperTrader()
    current_price = shared_data['last_prices'].get(symbol)
    if not current_price:
        return jsonify({'success': False, 'error': 'Prix non disponible'})
    success = trader.close_position(symbol, current_price, "MANUEL ðŸ‘¤")
    if success:
        add_bot_log(f"ðŸ’° VENTE MANUELLE {symbol} @ ${current_price:.4f}", 'TRADE')
    return jsonify({'success': success})


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'scan_count': shared_data['scan_count']}), 200


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

def run_loop():
    """Boucle infinie qui lance le scanner pÃ©riodiquement."""
    add_bot_log("âš¡ Swing Bot dÃ©marrÃ© â€” Timeframe: " + TIMEFRAME, 'INFO')
    while True:
        shared_data['is_scanning'] = True
        try:
            shared_data['opportunities'] = run_scanner()
            shared_data['last_update'] = datetime.now().strftime('%H:%M:%S')
        except Exception as e:
            add_bot_log(f"Erreur boucle: {str(e)}", 'ERROR')
        finally:
            shared_data['is_scanning'] = False

        add_bot_log(f"Pause {SCAN_INTERVAL} s - prochain scan: {datetime.now().strftime('%H:%M')}", 'INFO')
        time.sleep(SCAN_INTERVAL)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# LANCEMENT
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

if __name__ == '__main__':
    # Thread Scanner (daemon â€” s'arrÃªte avec le programme principal)
    scanner_thread = threading.Thread(target=run_loop, daemon=True)
    scanner_thread.start()

    port = int(os.environ.get('PORT', 8080))
    add_bot_log(f"Dashboard: http://localhost:{port}", 'INFO')
    app.run(host='0.0.0.0', port=port, debug=False)


