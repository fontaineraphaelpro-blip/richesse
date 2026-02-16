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

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CONFIGURATION DU BOT
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
TIMEFRAME        = '1h'    # Timeframe Swing Trading
CANDLE_LIMIT     = 500     # SMA200 requires 200+ candles
TRADE_AMOUNT     = 200     # USDT par trade
MIN_SCORE_BUY    = 75      # Score min pour auto-buy (AUGMENTE de 70 a 75)
SCAN_INTERVAL    = 300     # Secondes entre scans (5 min)
MAX_POSITIONS    = 5       # Positions simultanees max
RISK_PERCENT     = 2.0     # % du capital par trade (risk management)

# Configuration Multi-Timeframe
MTF_TIMEFRAMES   = ['15m', '1h', '4h']  # Timeframes pour confirmation
MTF_ENABLED      = True                  # Activer/desactiver multi-TF
MTF_MIN_ALIGN    = 70                    # Alignement minimum requis (AUGMENTE de 66 a 70%)

# Configuration Drawdown & Break-Even
MAX_DRAWDOWN_PCT = 10.0    # ArrÃªter si perte > 10% du capital initial
BREAKEVEN_TRIGGER = 1.0    # Activer break-even Ã  +1% de gain

# Configuration Trailing Stop Loss
TRAILING_ENABLED = True     # Activer/dÃ©sactiver le trailing stop
TRAILING_ACTIVATION = 1.5   # Activer trailing Ã  +1.5% de gain
TRAILING_DISTANCE = 1.0     # Distance du SL (1% sous le plus haut)

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
TRADING_HOURS_ENABLED = True
TRADING_START_HOUR = 7       # 7h UTC (8h Paris, 2h New York)
TRADING_END_HOUR = 22        # 22h UTC (23h Paris, 17h New York)
AVOID_WEEKENDS = True        # Ã‰viter samedi/dimanche

# Score Dynamique selon Marche (PARAMETRES STRICTS)
DYNAMIC_SCORE_ENABLED = True
SCORE_BULLISH_MARKET = 70    # Score min si marche haussier (AUGMENTE de 65)
SCORE_BEARISH_MARKET = 85    # Score min si marche baissier (AUGMENTE de 80)
SCORE_NEUTRAL_MARKET = 75    # Score min si marche neutre (AUGMENTE de 70)

# Risk/Reward Minimum
MIN_RISK_REWARD = 2.0        # Rejeter si R/R < 2:1 (AUGMENTE de 1.5 - qualite obligatoire)

# Configuration News & Sentiment
NEWS_ENABLED = True           # Activer l'analyse des news
SENTIMENT_SCORE_ADJUST = True # Ajuster le score selon sentiment
PAUSE_ON_EVENTS = True        # Pause trading lors d'Ã©vÃ©nements majeurs (FOMC, CPI)

# Configuration Machine Learning
ML_ENABLED = True             # Activer les prÃ©dictions ML
ML_MIN_PROBABILITY = 60       # ProbabilitÃ© minimum pour trader
ML_SCORE_ADJUST = True        # Ajuster le score selon ML

# Configuration On-Chain
ONCHAIN_ENABLED = True        # Activer l'analyse on-chain
ONCHAIN_SCORE_ADJUST = True   # Ajuster le score selon on-chain

# Configuration Position Sizing (Kelly)
KELLY_SIZING_ENABLED = True   # Utiliser Kelly pour le sizing
FIXED_TRADE_AMOUNT = 200      # Montant fixe si Kelly dÃ©sactivÃ©

# Configuration Macro Events (Calendrier Ã©conomique)
MACRO_EVENTS_ENABLED = True   # Activer le calendrier Ã©conomique
PAUSE_ON_FOMC = True          # Pause trading autour du FOMC
PAUSE_ON_CPI = True           # Pause trading autour du CPI
REGULATION_ALERTS = True      # Alertes rÃ©gulations crypto

# Social Sentiment
SOCIAL_SENTIMENT_ENABLED = True  # Utiliser Fear & Greed Index
SOCIAL_SCORE_MODIFIER = True     # Modifier score selon sentiment

# Trade Journal AI
TRADE_JOURNAL_ENABLED = True     # Enregistrer tous les trades
JOURNAL_LEARN_PATTERNS = True    # Apprendre des erreurs passees

# ANALYSE FONDAMENTALE (NOUVEAU)
FUNDAMENTAL_ENABLED = True       # Activer l'analyse fondamentale
FUNDAMENTAL_SCORE_ADJUST = True  # Ajuster score selon fondamentaux
FUNDAMENTAL_MIN_SCORE = 40       # Score fondamental minimum pour trader
FUNDAMENTAL_BLOCK_AVOID = True   # Bloquer les trades sur tokens "AVOID"

# ANALYSE TECHNIQUE AVANCEE (NOUVEAU)
ADVANCED_TA_ENABLED = True       # Activer l'analyse technique avancee
ADVANCED_TA_SCORE_ADJUST = True  # Ajuster score selon analyse avancee
ADVANCED_TA_MIN_SCORE = 55       # Score technique minimum (0-100)
ADVANCED_TA_WEIGHT = 0.3         # Poids de l'analyse avancee dans le score final

# Pyramiding (Renforcement de position)
PYRAMIDING_ENABLED = False   # DÃ©sactivÃ© par dÃ©faut (risquÃ©)
MAX_PYRAMIDING = 2           # Max 2 ajouts par position
PYRAMIDING_GAIN_THRESHOLD = 2.0  # Ajouter si position gagne +2%

# Cooldown aprÃ¨s Trade
COOLDOWN_ENABLED = True
COOLDOWN_MINUTES = 30        # Attendre 30 min avant de re-trader la mÃªme paire

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Ã‰TAT PARTAGÃ‰ (Thread Scanner â†” Serveur Web Flask)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
shared_data = {
    'opportunities': [],        # Top opportunitÃ©s du dernier scan
    'all_scanned': [],          # Toutes les paires analysÃ©es
    'last_prices': {},          # Prix actuels
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
    }
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
    CÅ“ur du systÃ¨me :
    1. RÃ©cupÃ¨re les donnÃ©es Binance
    2. VÃ©rifie les positions (SL/TP)
    3. Analyse les 200 paires LONG + SHORT
    4. Execute les ordres si score >= seuil
    """
    shared_data['scan_count'] += 1
    scan_num = shared_data['scan_count']
    
    add_bot_log(f"=== SCAN #{scan_num} DÃ‰MARRÃ‰ ===", 'INFO')

    try:
        # â”€â”€ Ã‰TAPE 1 : DonnÃ©es MarchÃ© â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        add_bot_log("RÃ©cupÃ©ration donnÃ©es Binance (200 paires)...", 'INFO')
        data, real_prices = fetch_multiple_pairs(None, interval=TIMEFRAME, limit=CANDLE_LIMIT)

        if not data:
            add_bot_log("CRITIQUE: Aucune donnÃ©e reÃ§ue de Binance", 'ERROR')
            return []

        shared_data['last_prices'] = real_prices
        add_bot_log(f"{len(data)} paires chargÃ©es avec succÃ¨s", 'INFO')

        # â”€â”€ Ã‰TAPE 2 : DÃ‰TECTION CRASH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        btc_price = real_prices.get('BTCUSDT', 0)
        if btc_price > 0:
            # Calculer les variations de prix pour dÃ©tection multi-asset
            price_changes = {}
            for symbol, df in data.items():
                if len(df) >= 2:
                    current = df['close'].iloc[-1]
                    prev = df['close'].iloc[-4] if len(df) >= 4 else df['close'].iloc[0]  # ~15min ago
                    change = ((current - prev) / prev) * 100
                    price_changes[symbol] = change
            
            # VÃ©rifier crash
            crash_analysis = check_for_crash(btc_price, price_changes)
            
            if crash_analysis.get('crash_detected'):
                crash_type = crash_analysis.get('crash_type', 'UNKNOWN')
                add_bot_log(f"ðŸš¨ CRASH DÃ‰TECTÃ‰: {crash_type}! Fermeture LONG uniquement...", 'ERROR')
                
                # Fermer seulement les LONG (les SHORT profitent du crash)
                trader = PaperTrader()
                closed_count = trader.emergency_close_all(real_prices, f"Crash {crash_type}", close_direction="LONG")
                add_bot_log(f"ðŸ’¥ {closed_count} LONG fermÃ©(s) - SHORT conservÃ©s (en profit)", 'ERROR')
                
                # Ajouter au dashboard
                shared_data['crash_status'] = crash_analysis
                return []  # ArrÃªter le scan
            
            if not crash_analysis.get('trading_allowed'):
                reason = crash_analysis.get('reason', 'Trading pausÃ©')
                add_bot_log(f"â¸ï¸ {reason}", 'WARN')
                return []  # Pas de trading pendant la pause
        
        # â”€â”€ Ã‰TAPE 2b : ANALYSE SENTIMENT & NEWS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        sentiment_modifier = 0
        if NEWS_ENABLED:
            try:
                market_sentiment = get_market_sentiment()
                fg = market_sentiment.get('fear_greed', {})
                news_sent = market_sentiment.get('news_sentiment', {})
                
                fg_value = fg.get('value', 50)
                fg_class = fg.get('classification', 'Neutral')
                trading_action = market_sentiment.get('trading_action', 'NORMAL')
                
                add_bot_log(
                    f"ðŸ“Š Sentiment: Fear&Greed={fg_value} ({fg_class}) | "
                    f"News: {news_sent.get('bullish', 0)}â†‘ {news_sent.get('bearish', 0)}â†“",
                    'INFO'
                )
                
                # Pause si Ã©vÃ©nement Ã©conomique majeur
                if PAUSE_ON_EVENTS and trading_action == 'PAUSE':
                    reason = market_sentiment.get('reason', 'Ã‰vÃ©nement majeur')
                    add_bot_log(f"â¸ï¸ NEWS PAUSE: {reason}", 'WARN')
                    return []
                
                # Enregistrer le sentiment pour le dashboard
                shared_data['market_sentiment'] = {
                    'fear_greed': fg_value,
                    'fear_greed_class': fg_class,
                    'news_bullish': news_sent.get('bullish', 0),
                    'news_bearish': news_sent.get('bearish', 0),
                    'action': trading_action,
                    'updated': datetime.now().strftime('%H:%M')
                }
                
                # Modificateur de score
                if SENTIMENT_SCORE_ADJUST:
                    sentiment_modifier = market_sentiment.get('combined_score_modifier', 0)
                    
            except Exception as e:
                add_bot_log(f"âš ï¸ Erreur analyse sentiment: {str(e)[:50]}", 'WARN')
        
        # â”€â”€ Ã‰TAPE 2c : INTELLIGENCE MARCHÃ‰ COMPLÃˆTE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        intel_modifier = 0
        try:
            market_intelligence = get_market_intelligence()
            bias = market_intelligence.get('overall_bias', 'NEUTRAL')
            confidence = market_intelligence.get('confidence', 0)
            alerts = market_intelligence.get('alerts', [])
            intel_data = market_intelligence.get('data', {})
            
            # Log intelligence
            funding = intel_data.get('funding', {}).get('btc_funding', 0)
            ls_ratio = intel_data.get('long_short_ratio', {}).get('ratio', 1)
            breadth = intel_data.get('top_movers', {}).get('market_breadth', 50)
            
            add_bot_log(
                f"ðŸ§  Intelligence: {bias} ({confidence:.0f}%) | "
                f"Funding:{funding:.3f}% | L/S:{ls_ratio:.2f} | Breadth:{breadth:.0f}%",
                'INFO'
            )
            
            # Afficher les alertes
            for alert in alerts[:3]:  # Max 3 alertes
                add_bot_log(f"   {alert}", 'INFO')
            
            # Stocker pour le dashboard
            shared_data['market_intelligence'] = {
                'bias': bias,
                'confidence': confidence,
                'funding': funding,
                'ls_ratio': ls_ratio,
                'breadth': breadth,
                'alerts': alerts,
                'updated': datetime.now().strftime('%H:%M')
            }
            
            # Modificateur de score basÃ© sur l'intelligence
            intel_modifier = market_intelligence.get('score_modifier', 0)
            sentiment_modifier += intel_modifier  # Combiner avec news
            
        except Exception as e:
            add_bot_log(f"âš ï¸ Erreur intelligence marchÃ©: {str(e)[:50]}", 'WARN')
        
        # â”€â”€ Ã‰TAPE 3 : Analyse Technique (faire AVANT la vÃ©rification des positions) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        add_bot_log("Analyse technique en cours...", 'INFO')
        
        all_results = []
        all_indicators = {}  # Stocker tous les indicateurs par symbole
        bullish_count = bearish_count = neutral_count = 0
        rsi_values = []

        for symbol, df in data.items():
            try:
                inds = calculate_indicators(df)
                if not inds:
                    continue

                support = find_swing_low(df, lookback=30)
                resistance = find_resistance(df, lookback=30)
                score_data = calculate_opportunity_score(inds, None, df)
                
                # Stocker les indicateurs pour utilisation ultÃ©rieure
                all_indicators[symbol] = inds
                
                rsi = inds.get('rsi14')
                if rsi:
                    rsi_values.append(rsi)

                entry_sig = score_data.get('entry_signal', 'NEUTRAL')
                trend = score_data.get('trend', 'NEUTRAL')
                
                if trend == 'Bullish': bullish_count += 1
                elif trend == 'Bearish': bearish_count += 1
                else: neutral_count += 1

                result = {
                    'pair':          symbol,
                    'score':         score_data.get('score', 0),
                    'trend':         trend,
                    'signal':        score_data.get('signal', 'N/A'),
                    'entry_signal':  entry_sig,
                    'confidence':    score_data.get('confidence', 0),
                    'details':       score_data.get('details', ''),
                    'atr_percent':   round(score_data.get('atr_percent', 0), 2),
                    # Prix & Niveaux
                    'price':         inds.get('current_price', 0),
                    'entry_price':   score_data.get('entry_price'),
                    'stop_loss':     score_data.get('stop_loss'),
                    'take_profit_1': score_data.get('take_profit_1'),
                    'take_profit_2': score_data.get('take_profit_2'),
                    'rr_ratio':      score_data.get('risk_reward_ratio'),
                    'support':       support,
                    'resistance':    resistance,
                    # Indicateurs affichÃ©s dans le dashboard
                    'rsi':           round(rsi, 1) if rsi else None,
                    'macd':          round(inds.get('macd', 0), 4) if inds.get('macd') else None,
                    'macd_hist':     round(inds.get('macd_hist', 0), 4) if inds.get('macd_hist') else None,
                    'adx':           round(inds.get('adx', 0), 1) if inds.get('adx') else None,
                    'atr':           round(inds.get('atr', 0), 4) if inds.get('atr') else None,
                    'bb_percent':    round(inds.get('bb_percent', 0) * 100, 1) if inds.get('bb_percent') else None,
                    'bb_width':      round(inds.get('bb_width', 0) * 100, 2) if inds.get('bb_width') else None,
                    'volume_ratio':  round(inds.get('volume_ratio', 0), 2),
                    'sma50':         round(inds.get('sma50', 0), 4) if inds.get('sma50') else None,
                    'sma200':        round(inds.get('sma200', 0), 4) if inds.get('sma200') else None,
                    'ema9':          round(inds.get('ema9', 0), 4) if inds.get('ema9') else None,
                    'ema21':         round(inds.get('ema21', 0), 4) if inds.get('ema21') else None,
                    'dist_sma50':    round(inds.get('dist_sma50_percent', 0), 2),
                    'dist_sma200':   round(inds.get('dist_sma200_percent', 0), 2),
                    'stoch_k':       round(inds.get('stoch_k', 0), 1) if inds.get('stoch_k') else None,
                    'stoch_d':       round(inds.get('stoch_d', 0), 1) if inds.get('stoch_d') else None,
                    'patterns':      inds.get('candlestick_patterns', []),
                    'high_24h':      round(inds.get('high_price', 0), 4),
                    'low_24h':       round(inds.get('low_price', 0), 4),
                }
                all_results.append(result)

            except Exception as e:
                add_bot_log(f"Erreur analyse {symbol}: {str(e)[:50]}", 'WARN')
                continue

        # Trier par score dÃ©croissant
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Stats marchÃ© globales
        avg_rsi = round(sum(rsi_values) / len(rsi_values), 1) if rsi_values else 0
        shared_data['market_stats'] = {
            'total_bullish': bullish_count,
            'total_bearish': bearish_count,
            'total_neutral': neutral_count,
            'avg_rsi': avg_rsi,
            'sentiment': 'HAUSSIER ðŸ“ˆ' if bullish_count > bearish_count else ('BAISSIER ðŸ“‰' if bearish_count > bullish_count else 'NEUTRE âš–ï¸'),
        }

        add_bot_log(
            f"Scan terminÃ©: {bullish_count}â†‘ {bearish_count}â†“ | RSI moyen: {avg_rsi} | "
            f"{len([r for r in all_results if r['entry_signal'] != 'NEUTRAL'])} signaux actifs",
            'INFO'
        )

        # â”€â”€ Ã‰TAPE 2b : Gestion Positions (SL / TP) avec PROTECTION â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Maintenant on a tous les indicateurs, on peut vÃ©rifier les positions avec protection
        trader = PaperTrader()
        open_pos = trader.get_open_positions()
        
        if open_pos:
            add_bot_log(f"VÃ©rification de {len(open_pos)} position(s) ouverte(s) WITH PROTECTION...", 'INFO')
            trader.check_positions_with_protection(real_prices, all_indicators)
            
            # -- DETECTION SIGNAL CONTRAIRE & INVERSION --
            # Si une position ouverte recoit un signal contraire fort, on inverse
            for symbol, pos_data in list(open_pos.items()):
                current_direction = pos_data.get('direction', 'LONG')
                
                # Trouver l'opportunite pour cette paire
                opp_for_pos = next((opp for opp in all_results if opp['pair'] == symbol), None)
                
                if opp_for_pos and opp_for_pos['entry_signal'] != 'NEUTRAL':
                    new_signal = opp_for_pos['entry_signal']
                    signal_score = opp_for_pos['score']
                    
                    # Verifier si c'est un signal contraire avec un score eleve (>=65)
                    is_opposite = (
                        (current_direction == 'LONG' and new_signal == 'SHORT') or
                        (current_direction == 'SHORT' and new_signal == 'LONG')
                    )
                    
                    if is_opposite and signal_score >= 65:
                        current_price = real_prices.get(symbol)
                        if current_price and opp_for_pos['stop_loss'] and opp_for_pos['take_profit_1']:
                            add_bot_log(
                                f"SIGNAL CONTRAIRE detecte: {symbol} {current_direction} -> {new_signal} (Score:{signal_score})",
                                'TRADE'
                            )
                            
                            # Inverser la position
                            success = trader.reverse_position(
                                symbol=symbol,
                                current_price=current_price,
                                new_direction=new_signal,
                                amount_usdt=pos_data['amount_usdt'],  # Reutiliser le meme montant
                                stop_loss_price=opp_for_pos['stop_loss'],
                                take_profit_price=opp_for_pos['take_profit_1'],
                                entry_trend=opp_for_pos['trend'],
                                take_profit_2=opp_for_pos.get('take_profit_2')
                            )
                            
                            if success:
                                add_bot_log(f"INVERSION REUSSIE: {symbol} maintenant en {new_signal}", 'TRADE')
                                # Mettre a jour les positions pour la suite du scan
                                open_pos = trader.get_open_positions()
            
            # â”€â”€ BREAK-EVEN AUTOMATIQUE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            breakeven_count = trader.check_and_apply_breakeven(real_prices)
            if breakeven_count > 0:
                add_bot_log(f"ðŸ”’ BREAK-EVEN appliquÃ© sur {breakeven_count} position(s)", 'TRADE')
            
            # â”€â”€ TRAILING STOP LOSS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            trailing_count = trader.check_and_apply_trailing_stop(real_prices)
            if trailing_count > 0:
                add_bot_log(f"ðŸ“ˆ TRAILING SL ajustÃ© sur {trailing_count} position(s)", 'TRADE')
            
            # â”€â”€ TAKE PROFIT PARTIEL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            if PARTIAL_TP_ENABLED:
                partial_count = trader.check_and_apply_partial_tp(real_prices)
                if partial_count > 0:
                    add_bot_log(f"ðŸ’° TP PARTIEL exÃ©cutÃ© sur {partial_count} position(s)", 'TRADE')
        
        # Afficher le status du circuit breaker si actif
        protection_status = trader.protector.get_protection_status()
        if protection_status['circuit_breaker_active']:
            add_bot_log(
                f"â›” CIRCUIT BREAKER ACTIF: {protection_status['recent_sl_count']} SL rÃ©cents, "
                f"{protection_status['circuit_breaker_remaining']}s restants",
                'WARN'
            )
        
        # â”€â”€ VÃ‰RIFICATION DRAWDOWN MAX â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        is_drawdown_exceeded, drawdown_pct, total_capital = trader.check_drawdown(real_prices)
        if is_drawdown_exceeded:
            add_bot_log(
                f"ðŸš¨ DRAWDOWN MAX ATTEINT: -{drawdown_pct:.1f}% | Capital: ${total_capital:.2f}",
                'ERROR'
            )
            # Fermer toutes les positions en urgence
            closed_count = trader.emergency_close_all(real_prices, "DRAWDOWN MAX")
            add_bot_log(f"ðŸš¨ {closed_count} position(s) fermÃ©e(s) en urgence", 'ERROR')
            shared_data['drawdown_alert'] = True
        else:
            shared_data['drawdown_alert'] = False
            if drawdown_pct > 5:
                add_bot_log(f"âš ï¸ Drawdown actuel: -{drawdown_pct:.1f}% (max: {MAX_DRAWDOWN_PCT}%)", 'WARN')

        update_performance_stats(trader)

        # Sauvegarder les rÃ©sultats
        shared_data['all_scanned'] = all_results
        opportunities = [r for r in all_results if r['entry_signal'] != 'NEUTRAL'][:20]
        shared_data['opportunities'] = opportunities

        # â”€â”€ Ã‰TAPE 4 : Auto-Trading â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        balance = trader.get_usdt_balance()
        my_positions = trader.get_open_positions()
        
        # VÃ©rifier circuit breaker
        is_cb_active, cb_remaining = trader.protector.is_circuit_breaker_active()
        
        # VÃ©rifier les heures de trading
        hours_valid, hours_reason = trade_filters.check_trading_hours()
        
        # Obtenir le score minimum dynamique selon le marchÃ©
        dynamic_min_score, score_reason = trade_filters.get_dynamic_min_score(shared_data['market_stats'])
        
        # VÃ©rifier les Ã©vÃ©nements macroÃ©conomiques
        macro_can_trade = True
        macro_modifier = 0
        if MACRO_EVENTS_ENABLED:
            try:
                macro_can_trade, macro_modifier, macro_reason = check_macro_events()
                if not macro_can_trade:
                    add_bot_log(f"ðŸ“… {macro_reason}", 'WARN')
                elif macro_modifier != 0:
                    add_bot_log(f"ðŸ“… Macro: {macro_reason} (score {macro_modifier:+d})", 'INFO')
                
                # Stocker l'analyse macro
                shared_data['macro_analysis'] = get_macro_analysis()
            except Exception as e:
                add_bot_log(f"âš ï¸ Erreur macro events: {e}", 'WARN')
                macro_can_trade = True
        
        # VÃ©rifier si drawdown max atteint - pas de nouveau trading
        if is_drawdown_exceeded:
            add_bot_log(f"ðŸš¨ TRADING SUSPENDU - Drawdown max dÃ©passÃ©", 'ERROR')
        # VÃ©rifier si circuit breaker est actif
        elif is_cb_active:
            add_bot_log(f"â›” CIRCUIT BREAKER - Pas de nouveaux achats ({cb_remaining}s)", 'WARN')
        # VÃ©rifier les heures de trading
        elif TRADING_HOURS_ENABLED and not hours_valid:
            add_bot_log(f"â° {hours_reason}", 'INFO')
        # VÃ©rifier les Ã©vÃ©nements macro (FOMC, CPI, etc.)
        elif not macro_can_trade:
            add_bot_log(f"ðŸ“… TRADING SUSPENDU - Ã‰vÃ©nement macro en cours", 'WARN')
        else:
            add_bot_log(f"Auto-trade | Solde: ${balance:.2f} | {len(my_positions)} pos | {score_reason}", 'INFO')

            for opp in opportunities:
                # Utiliser le score dynamique au lieu du fixe
                effective_min_score = dynamic_min_score if DYNAMIC_SCORE_ENABLED else MIN_SCORE_BUY
                
                # Direction du signal
                signal_direction = opp['entry_signal']  # 'LONG', 'SHORT', ou 'NEUTRAL'
                
                # Ajuster le score selon le sentiment marchÃ© ET les Ã©vÃ©nements macro
                adjusted_score = opp['score'] + sentiment_modifier + macro_modifier
                
                # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
                # STRATÃ‰GIE HYBRIDE PROUVÃ‰E (Trend Following + Sentiment)
                # Ã‰tudes montrent: Suivre la tendance + confirmation > Contrarian pur
                # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
                
                opp_indicators = all_indicators.get(opp['pair'], {})
                rsi = opp_indicators.get('rsi14', 50)
                macd = opp_indicators.get('macd', 0)
                macd_signal = opp_indicators.get('macd_signal', 0)
                
                if NEWS_ENABLED and 'market_sentiment' in shared_data:
                    ms = shared_data['market_sentiment']
                    fg_value = ms.get('fear_greed', 50)
                    
                    # â”€â”€ EXTREME GREED (â‰¥80): Risque de correction â”€â”€
                    if fg_value >= 80:
                        if signal_direction == 'LONG':
                            # LONG en Extreme Greed = TrÃ¨s risquÃ©
                            # Mais si RSI < 70 et MACD bullish, peut-Ãªtre ok avec pÃ©nalitÃ©
                            if rsi > 70:
                                add_bot_log(f"âš ï¸ {opp['pair']} LONG bloquÃ© (Greed {fg_value} + RSI {rsi:.0f})", 'WARN')
                                continue
                            else:
                                adjusted_score -= 15  # PÃ©nalitÃ© forte
                                add_bot_log(f"âš ï¸ {opp['pair']} LONG pÃ©nalisÃ© -15 (Extreme Greed)", 'INFO')
                        elif signal_direction == 'SHORT':
                            # SHORT en Extreme Greed = BONUS (correction probable)
                            adjusted_score += 10
                            add_bot_log(f"ðŸ’¡ {opp['pair']} SHORT bonus +10 (Extreme Greed = correction)", 'INFO')
                    
                    # â”€â”€ EXTREME FEAR (â‰¤20): MarchÃ© en panique â”€â”€
                    elif fg_value <= 20:
                        if signal_direction == 'SHORT':
                            # SHORT en Extreme Fear:
                            # - Si technique BEARISH (RSI > 30, MACD nÃ©gatif) = OK, suivre tendance
                            # - Si technique BULLISH (RSI < 30 survendu, MACD divergence) = Ã‰viter
                            if rsi < 30:
                                # RSI survendu = rebond probable
                                add_bot_log(f"âš ï¸ {opp['pair']} SHORT bloquÃ© (Fear {fg_value} + RSI survendu {rsi:.0f})", 'WARN')
                                continue
                            elif macd > macd_signal:
                                # MACD croise Ã  la hausse = retournement
                                adjusted_score -= 10
                                add_bot_log(f"âš ï¸ {opp['pair']} SHORT pÃ©nalisÃ© -10 (MACD haussier en Fear)", 'INFO')
                            else:
                                # Technique encore baissiÃ¨re = SHORT OK
                                add_bot_log(f"âœ… {opp['pair']} SHORT confirmÃ© (Fear + technique bearish)", 'INFO')
                        elif signal_direction == 'LONG':
                            # LONG en Extreme Fear = BONUS (contrarian prouvÃ©)
                            if rsi < 35:  # Oversold
                                adjusted_score += 15  # Gros bonus
                                add_bot_log(f"ðŸ’° {opp['pair']} LONG bonus +15 (Extreme Fear + RSI {rsi:.0f})", 'INFO')
                            else:
                                adjusted_score += 5
                    
                    # â”€â”€ FEAR (21-40): Prudent mais opportunitÃ©s â”€â”€
                    elif fg_value <= 40:
                        if signal_direction == 'SHORT' and rsi < 35:
                            adjusted_score -= 5  # LÃ©gÃ¨re pÃ©nalitÃ© si RSI dÃ©jÃ  bas
                        elif signal_direction == 'LONG' and rsi < 40:
                            adjusted_score += 5  # LÃ©ger bonus pour achat en fear
                    
                    # â”€â”€ GREED (60-79): Prudent sur les LONG â”€â”€
                    elif fg_value >= 60:
                        if signal_direction == 'LONG' and rsi > 65:
                            adjusted_score -= 5  # LÃ©gÃ¨re pÃ©nalitÃ©
                        elif signal_direction == 'SHORT':
                            adjusted_score += 3  # LÃ©ger bonus
                
                # RÃ¨gles strictes d'ouverture (LONG ou SHORT)
                if (adjusted_score >= effective_min_score
                        and signal_direction in ['LONG', 'SHORT']  # Accepter LONG ET SHORT
                        and opp['pair'] not in my_positions
                        and len(my_positions) < MAX_POSITIONS
                        and opp['stop_loss'] is not None
                        and opp['take_profit_1'] is not None):

                    # â”€â”€ COOLDOWN CHECK â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                    if COOLDOWN_ENABLED:
                        in_cooldown, cooldown_remaining = trader.is_in_cooldown(opp['pair'])
                        if in_cooldown:
                            add_bot_log(f"â³ {opp['pair']} en cooldown ({cooldown_remaining:.0f}min restantes)", 'INFO')
                            continue

                    # â”€â”€ FILTRE VOLUME â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                    opp_indicators = all_indicators.get(opp['pair'], {})
                    if VOLUME_FILTER_ENABLED:
                        vol_valid, vol_reason = trade_filters.check_volume_filter(opp_indicators)
                        if not vol_valid:
                            add_bot_log(f"âŒ {opp['pair']} {vol_reason}", 'WARN')
                            continue

                    # â”€â”€ FILTRE RISK/REWARD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                    rr_valid, rr_ratio, rr_reason = trade_filters.check_risk_reward(
                        opp['price'], opp['stop_loss'], opp['take_profit_1'], signal_direction
                    )
                    if not rr_valid:
                        add_bot_log(f"âŒ {opp['pair']} {rr_reason}", 'WARN')
                        continue

                    # VÃ©rifier les conditions de volatilitÃ©
                    can_open, open_reason = trader.protector.can_open_position(opp_indicators)
                    if not can_open:
                        add_bot_log(f"âŒ {opp['pair']} rejetÃ©: {open_reason}", 'WARN')
                        continue
                    
                    # -- ANALYSE FONDAMENTALE (Tokenomics, TVL, Dev, Adoption) --
                    fundamental_modifier = 0
                    if FUNDAMENTAL_ENABLED:
                        try:
                            fund_can_trade, fund_modifier, fund_reason = should_trade_fundamentally(
                                opp['pair'], 
                                signal_direction
                            )
                            
                            if FUNDAMENTAL_BLOCK_AVOID and not fund_can_trade:
                                add_bot_log(f"X {opp['pair']} FONDAMENTAUX: {fund_reason}", 'WARN')
                                continue
                            
                            fund_analysis = get_fundamental_score(opp['pair'])
                            fund_score = fund_analysis.get('score', 50)
                            fund_rec = fund_analysis.get('recommendation', 'NEUTRAL')
                            
                            if fund_score < FUNDAMENTAL_MIN_SCORE:
                                add_bot_log(f"X {opp['pair']} Fondamentaux faibles: {fund_score}/100", 'WARN')
                                continue
                            
                            if FUNDAMENTAL_SCORE_ADJUST:
                                fundamental_modifier = fund_modifier
                                adjusted_score += fundamental_modifier
                            
                            add_bot_log(f"FUND {opp['pair']}: {fund_score}/100 ({fund_rec})", 'INFO')
                            
                        except Exception as e:
                            pass  # Continuer si erreur API
                    

                    # -- ANALYSE TECHNIQUE AVANCEE --
                    advanced_ta_modifier = 0
                    if ADVANCED_TA_ENABLED:
                        try:
                            pair_df = data.get(opp['pair'])
                            if pair_df is not None and len(pair_df) >= 100:
                                ta_analysis = get_advanced_technical_analysis(pair_df, opp_indicators)
                                ta_score = ta_analysis.get('score', 50)
                                ta_direction = ta_analysis.get('direction', 'NEUTRAL')
                                ta_confidence = ta_analysis.get('confidence', 0)
                                
                                if ta_score < ADVANCED_TA_MIN_SCORE and signal_direction == 'LONG':
                                    add_bot_log(f"X {opp['pair']} TA Score faible: {ta_score:.1f}", 'WARN')
                                    continue
                                elif ta_score > (100 - ADVANCED_TA_MIN_SCORE) and signal_direction == 'SHORT':
                                    add_bot_log(f"X {opp['pair']} TA Score haut pour SHORT: {ta_score:.1f}", 'WARN')
                                    continue
                                
                                direction_aligned = (
                                    (signal_direction == 'LONG' and ta_direction == 'BULLISH') or
                                    (signal_direction == 'SHORT' and ta_direction == 'BEARISH')
                                )
                                
                                if not direction_aligned and ta_confidence > 40:
                                    add_bot_log(f"X {opp['pair']} TA contraire: {ta_direction}", 'WARN')
                                    continue
                                
                                if ADVANCED_TA_SCORE_ADJUST:
                                    advanced_ta_modifier = get_technical_score_adjustment(ta_analysis, signal_direction)
                                    adjusted_score += advanced_ta_modifier
                                
                                add_bot_log(f"TA {opp['pair']}: {ta_score:.1f}/100 {ta_direction}", 'INFO')
                        except Exception as e:
                            pass

                    # â”€â”€ VALIDATION MULTI-TIMEFRAME â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                    mtf_alignment = 0
                    if MTF_ENABLED:
                        mtf_result = validate_signal_multi_timeframe(
                            opp['pair'], 
                            signal_direction, 
                            MTF_TIMEFRAMES
                        )
                        mtf_alignment = mtf_result.get('alignment_score', 0)
                        if not mtf_result['is_valid']:
                            add_bot_log(
                                f"âŒ {opp['pair']} MTF rejetÃ©: {mtf_result['reason']}", 
                                'WARN'
                            )
                            continue
                        else:
                            add_bot_log(
                                f"âœ… {opp['pair']} MTF confirmÃ©: {mtf_alignment}% alignÃ©",
                                'INFO'
                            )
                    
                    # â”€â”€ PRÃ‰DICTION ML â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                    if ML_ENABLED:
                        sentiment_data = shared_data.get('market_sentiment', {})
                        ml_prediction = get_ml_prediction(
                            opp_indicators, 
                            signal_direction,
                            sentiment_data,
                            mtf_alignment
                        )
                        ml_prob = ml_prediction.get('probability', 50)
                        ml_confidence = ml_prediction.get('confidence', 'low')
                        
                        if ml_prob < ML_MIN_PROBABILITY:
                            add_bot_log(
                                f"ðŸ¤– {opp['pair']} ML rejetÃ©: {ml_prob:.0f}% ({ml_confidence})", 
                                'WARN'
                            )
                            continue
                        else:
                            add_bot_log(
                                f"ðŸ¤– {opp['pair']} ML: {ml_prob:.0f}% ({ml_confidence})",
                                'INFO'
                            )
                            if ML_SCORE_ADJUST:
                                ml_bonus = int((ml_prob - 60) / 4)  # +0 Ã  +10
                                adjusted_score += ml_bonus
                    
                    # â”€â”€ ANALYSE ON-CHAIN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                    if ONCHAIN_ENABLED:
                        btc_price = shared_data.get('last_prices', {}).get('BTCUSDT', 45000)
                        onchain_adj, onchain_reason = get_onchain_signal_adjustment(signal_direction, btc_price)
                        if ONCHAIN_SCORE_ADJUST and onchain_adj != 0:
                            adjusted_score += onchain_adj
                            add_bot_log(f"ðŸ”— {opp['pair']} On-chain: {onchain_reason}", 'INFO')

                    if balance >= TRADE_AMOUNT:
                        # â”€â”€ CALCUL POSITION SIZING (KELLY) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                        if KELLY_SIZING_ENABLED:
                            trade_amount, sizing_breakdown = calculate_position_size(
                                capital=balance,
                                indicators=opp_indicators,
                                score=adjusted_score,
                                ml_probability=ml_prob if ML_ENABLED else 50,
                                stop_loss_pct=abs((opp['price'] - opp['stop_loss']) / opp['price'] * 100)
                            )
                            add_bot_log(f"ðŸ“Š Kelly: ${trade_amount:.0f} ({sizing_breakdown.get('final_position', 'N/A')})", 'INFO')
                        else:
                            trade_amount = FIXED_TRADE_AMOUNT
                        
                        # VÃ©rifier qu'on a assez de balance
                        if balance < trade_amount:
                            trade_amount = balance * 0.9  # Utiliser 90% du reste
                        
                        # â”€â”€ EXÃ‰CUTION LONG OU SHORT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                        if signal_direction == 'LONG':
                            success = trader.place_buy_order(
                                symbol=opp['pair'],
                                amount_usdt=trade_amount,
                                current_price=opp['price'],
                                stop_loss_price=opp['stop_loss'],
                                take_profit_price=opp['take_profit_1'],
                                entry_trend=opp['trend'],
                                take_profit_2=opp.get('take_profit_2')
                            )
                            trade_emoji = "ðŸŸ¢ LONG"
                        else:  # SHORT
                            success = trader.place_short_order(
                                symbol=opp['pair'],
                                amount_usdt=trade_amount,
                                current_price=opp['price'],
                                stop_loss_price=opp['stop_loss'],
                                take_profit_price=opp['take_profit_1'],
                                entry_trend=opp['trend']
                            )
                            trade_emoji = "ðŸ”´ SHORT"
                        
                        if success:
                            # Enregistrer le trade pour le cooldown
                            trader.record_trade_time(opp['pair'])
                            balance -= trade_amount
                            my_positions = trader.get_open_positions()
                            add_bot_log(
                                f"{trade_emoji} {opp['pair']} | ${opp['price']:.4f} | "
                                f"Size:${trade_amount:.0f} | SL:${opp['stop_loss']:.4f} | TP:${opp['take_profit_1']:.4f} | "
                                f"Score:{adjusted_score}",
                                'TRADE'
                            )
                    else:
                        add_bot_log(f"Solde insuffisant pour {opp['pair']} (nÃ©cessite ${TRADE_AMOUNT})", 'WARN')
                        break

        update_performance_stats(trader)
        add_bot_log(f"=== SCAN #{scan_num} TERMINÃ‰ ===", 'INFO')
        return opportunities

    except Exception as e:
        add_bot_log(f"ERREUR CRITIQUE SCAN: {str(e)}", 'ERROR')
        import traceback
        traceback.print_exc()
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
            'amount':      pos_data['amount_usdt'],
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
        min_score=MIN_SCORE_BUY,
        timeframe=TIMEFRAME,
        trade_amount=TRADE_AMOUNT,
        stats=stats,
        chart_data=json.dumps(chart_data),
        all_pairs=all_pairs,
        crash=crash,
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
        pnl_value = (current - entry) * pos_data['quantity']
        pnl_percent = ((current - entry) / entry) * 100
        total_unrealized_pnl += pnl_value
        sl = pos_data.get('stop_loss', entry)
        tp = pos_data.get('take_profit', entry)
        range_total = tp - sl if (tp - sl) != 0 else 1
        progress = max(0, min(100, ((current - sl) / range_total) * 100))
        positions_view.append({
            'symbol': symbol, 'entry': entry, 'current': current,
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
    """Retourne la prÃ©diction ML pour une paire."""
    try:
        direction = request.args.get('direction', 'LONG')
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
        symbol = request.args.get('symbol', 'BTCUSDT')
        score = int(request.args.get('score', 70))
        ml_prob = float(request.args.get('ml_prob', 50))
        
        balance = trader.get_usdt_balance()
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
    """Retourne un rÃ©sumÃ© de toute l'intelligence disponible."""
    try:
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
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>&#9889; Crypto Trading Bot</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
:root {
    --bg: #0a0e17; --bg2: #111827; --border: #1f2937;
    --text: #f3f4f6; --text2: #9ca3af; --text3: #6b7280;
    --green: #10b981; --red: #ef4444; --blue: #3b82f6; --yellow: #f59e0b;
}
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
.app { max-width: 1400px; margin: 0 auto; padding: 20px; }

/* Header */
.header { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; background: var(--bg2); border-radius: 12px; margin-bottom: 20px; border: 1px solid var(--border); }
.header h1 { font-size: 1.5em; color: var(--blue); }
.header .status { display: flex; align-items: center; gap: 8px; font-size: 0.9em; color: var(--text2); }
.dot { width: 10px; height: 10px; border-radius: 50%; background: var(--green); }
.dot.scanning { background: var(--yellow); animation: pulse 1s infinite; }
@keyframes pulse { 50% { opacity: 0.5; } }

/* Stats Grid */
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }
.stat { background: var(--bg2); padding: 20px; border-radius: 12px; border: 1px solid var(--border); }
.stat-label { font-size: 0.75em; color: var(--text3); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.stat-value { font-size: 1.8em; font-weight: 700; }
.stat-sub { font-size: 0.8em; color: var(--text3); margin-top: 4px; }
.green { color: var(--green); }
.red { color: var(--red); }
.blue { color: var(--blue); }

/* Cards */
.card { background: var(--bg2); border-radius: 12px; border: 1px solid var(--border); margin-bottom: 20px; overflow: hidden; }
.card-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border); background: rgba(0,0,0,0.2); }
.card-header h2 { font-size: 1em; font-weight: 600; color: var(--text2); }
.badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: 600; }
.b-green { background: rgba(16,185,129,0.1); color: var(--green); }
.b-red { background: rgba(239,68,68,0.1); color: var(--red); }
.b-blue { background: rgba(59,130,246,0.1); color: var(--blue); }
.b-yellow { background: rgba(245,158,11,0.1); color: var(--yellow); }

/* Tables */
table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
th { padding: 12px 16px; text-align: left; font-size: 0.7em; text-transform: uppercase; letter-spacing: 1px; color: var(--text3); border-bottom: 1px solid var(--border); background: rgba(0,0,0,0.2); }
td { padding: 12px 16px; border-bottom: 1px solid rgba(31,41,55,0.5); }
tr:hover td { background: rgba(59,130,246,0.03); }
.empty { text-align: center; padding: 40px; color: var(--text3); }

/* Progress */
.progress { width: 80px; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--red), var(--yellow), var(--green)); border-radius: 3px; }

/* Buttons */
.btn { padding: 6px 14px; border-radius: 6px; font-size: 0.8em; font-weight: 600; cursor: pointer; border: none; transition: all 0.2s; }
.btn-close { background: rgba(239,68,68,0.1); color: var(--red); border: 1px solid rgba(239,68,68,0.3); }
.btn-close:hover { background: rgba(239,68,68,0.2); }

/* Log */
.log { max-height: 300px; overflow-y: auto; }
.log-line { display: flex; gap: 12px; padding: 8px 16px; border-bottom: 1px solid rgba(31,41,55,0.3); font-size: 0.8em; }
.log-time { color: var(--text3); width: 60px; flex-shrink: 0; }
.log-level { width: 50px; flex-shrink: 0; font-weight: 600; text-align: center; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }
.l-INFO { background: rgba(59,130,246,0.1); color: var(--blue); }
.l-TRADE { background: rgba(16,185,129,0.1); color: var(--green); }
.l-WARN { background: rgba(245,158,11,0.1); color: var(--yellow); }
.l-ERROR { background: rgba(239,68,68,0.1); color: var(--red); }
.log-msg { color: var(--text2); flex: 1; }

/* Grid layouts */
.grid-2 { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
@media (max-width: 1000px) { .grid-2 { grid-template-columns: 1fr; } }

/* Quick indicators */
.indicators { display: flex; gap: 16px; padding: 12px 20px; background: rgba(0,0,0,0.2); border-top: 1px solid var(--border); font-size: 0.8em; }
.ind { display: flex; align-items: center; gap: 6px; }
.ind-label { color: var(--text3); }
.ind-value { font-weight: 600; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
</head>
<body>
<div class="app">

<!-- HEADER -->
<div class="header">
    <div>
        <h1>&#9889; Crypto Trading Bot</h1>
        <span style="font-size:0.8em;color:var(--text3)">Swing Trading &#8226; {{ timeframe|upper }} &#8226; Auto-buy &#8805; {{ min_score }}</span>
    </div>
    <div class="status">
        <div class="dot {% if is_scanning %}scanning{% endif %}"></div>
        {% if is_scanning %}Scanning...{% else %}Active{% endif %}
        <span style="margin-left:16px;color:var(--text3)">Scan #{{ scan_count }} &#8226; {{ last_update }}</span>
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

        add_bot_log(f"Pause {SCAN_INTERVAL//60} min â€” prochain scan: {datetime.now().strftime('%H:%M')}", 'INFO')
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

