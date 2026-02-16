"""
Script principal: Crypto Swing Trader Bot & Dashboard ULTIME.
Version: ULTIMATE v2.0 — Scanner complet + Bot Swing + Paper Trading + Dashboard Pro
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
from indicators import calculate_indicators
from scorer import calculate_opportunity_score
from support import find_swing_low
from scalping_signals import find_resistance
from trade_filters import trade_filters
from crash_protection import crash_protector, check_for_crash, is_crash_mode, get_crash_status
from news_analyzer import news_analyzer, get_market_sentiment, get_fear_greed

# ─────────────────────────────────────────────────────────────
# CONFIGURATION DU BOT
# ─────────────────────────────────────────────────────────────
TIMEFRAME        = '1h'    # Timeframe Swing Trading
CANDLE_LIMIT     = 500     # SMA200 requires 200+ candles
TRADE_AMOUNT     = 200     # USDT par trade
MIN_SCORE_BUY    = 70      # Score min pour auto-buy
SCAN_INTERVAL    = 300     # Secondes entre scans (5 min)
MAX_POSITIONS    = 5       # Positions simultanées max
RISK_PERCENT     = 2.0     # % du capital par trade (risk management)

# Configuration Multi-Timeframe
MTF_TIMEFRAMES   = ['15m', '1h', '4h']  # Timeframes pour confirmation
MTF_ENABLED      = True                  # Activer/désactiver multi-TF
MTF_MIN_ALIGN    = 66                    # Alignement minimum requis (%)

# Configuration Drawdown & Break-Even
MAX_DRAWDOWN_PCT = 10.0    # Arrêter si perte > 10% du capital initial
BREAKEVEN_TRIGGER = 1.0    # Activer break-even à +1% de gain

# Configuration Trailing Stop Loss
TRAILING_ENABLED = True     # Activer/désactiver le trailing stop
TRAILING_ACTIVATION = 1.5   # Activer trailing à +1.5% de gain
TRAILING_DISTANCE = 1.0     # Distance du SL (1% sous le plus haut)

# ─────────────────────────────────────────────────────────────
# NOUVELLES CONFIGURATIONS RENTABILITÉ
# ─────────────────────────────────────────────────────────────

# Take Profit Partiel (Scaling Out)
PARTIAL_TP_ENABLED = True    # Activer TP partiel
PARTIAL_TP_RATIO = 0.5       # Prendre 50% à TP1
# Le reste court vers TP2

# Filtrage Volume
VOLUME_FILTER_ENABLED = True
MIN_VOLUME_RATIO = 1.2       # Volume doit être 1.2x la moyenne

# Heures de Trading Optimales (UTC)
TRADING_HOURS_ENABLED = True
TRADING_START_HOUR = 7       # 7h UTC (8h Paris, 2h New York)
TRADING_END_HOUR = 22        # 22h UTC (23h Paris, 17h New York)
AVOID_WEEKENDS = True        # Éviter samedi/dimanche

# Score Dynamique selon Marché
DYNAMIC_SCORE_ENABLED = True
SCORE_BULLISH_MARKET = 65    # Score min si marché haussier
SCORE_BEARISH_MARKET = 80    # Score min si marché baissier
SCORE_NEUTRAL_MARKET = 70    # Score min si marché neutre

# Risk/Reward Minimum
MIN_RISK_REWARD = 2.0        # Rejeter si R/R < 2:1

# Configuration News & Sentiment
NEWS_ENABLED = True           # Activer l'analyse des news
SENTIMENT_SCORE_ADJUST = True # Ajuster le score selon sentiment
PAUSE_ON_EVENTS = True        # Pause trading lors d'événements majeurs (FOMC, CPI)

# Pyramiding (Renforcement de position)
PYRAMIDING_ENABLED = False   # Désactivé par défaut (risqué)
MAX_PYRAMIDING = 2           # Max 2 ajouts par position
PYRAMIDING_GAIN_THRESHOLD = 2.0  # Ajouter si position gagne +2%

# Cooldown après Trade
COOLDOWN_ENABLED = True
COOLDOWN_MINUTES = 30        # Attendre 30 min avant de re-trader la même paire

# ─────────────────────────────────────────────────────────────
# ÉTAT PARTAGÉ (Thread Scanner ↔ Serveur Web Flask)
# ─────────────────────────────────────────────────────────────
shared_data = {
    'opportunities': [],        # Top opportunités du dernier scan
    'all_scanned': [],          # Toutes les paires analysées
    'last_prices': {},          # Prix actuels
    'is_scanning': False,
    'last_update': 'Jamais',
    'scan_count': 0,
    'bot_log': [],              # Journal d'activité du bot (20 derniers events)
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
    'market_sentiment': {       # Sentiment marché (News & Fear/Greed)
        'fear_greed': 50,
        'fear_greed_class': 'Neutral',
        'news_bullish': 0,
        'news_bearish': 0,
        'action': 'NORMAL',
        'updated': None
    }
}

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────
# FONCTIONS UTILITAIRES
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# SCANNER PRINCIPAL
# ─────────────────────────────────────────────────────────────

def run_scanner():
    """
    Cœur du système :
    1. Récupère les données Binance
    2. Vérifie les positions (SL/TP)
    3. Analyse les 200 paires LONG + SHORT
    4. Execute les ordres si score >= seuil
    """
    shared_data['scan_count'] += 1
    scan_num = shared_data['scan_count']
    
    add_bot_log(f"=== SCAN #{scan_num} DÉMARRÉ ===", 'INFO')

    try:
        # ── ÉTAPE 1 : Données Marché ──────────────────────────
        add_bot_log("Récupération données Binance (200 paires)...", 'INFO')
        data, real_prices = fetch_multiple_pairs(None, interval=TIMEFRAME, limit=CANDLE_LIMIT)

        if not data:
            add_bot_log("CRITIQUE: Aucune donnée reçue de Binance", 'ERROR')
            return []

        shared_data['last_prices'] = real_prices
        add_bot_log(f"{len(data)} paires chargées avec succès", 'INFO')

        # ── ÉTAPE 2 : DÉTECTION CRASH ────────────────────────────
        btc_price = real_prices.get('BTCUSDT', 0)
        if btc_price > 0:
            # Calculer les variations de prix pour détection multi-asset
            price_changes = {}
            for symbol, df in data.items():
                if len(df) >= 2:
                    current = df['close'].iloc[-1]
                    prev = df['close'].iloc[-4] if len(df) >= 4 else df['close'].iloc[0]  # ~15min ago
                    change = ((current - prev) / prev) * 100
                    price_changes[symbol] = change
            
            # Vérifier crash
            crash_analysis = check_for_crash(btc_price, price_changes)
            
            if crash_analysis.get('crash_detected'):
                crash_type = crash_analysis.get('crash_type', 'UNKNOWN')
                add_bot_log(f"🚨 CRASH DÉTECTÉ: {crash_type}! Fermeture LONG uniquement...", 'ERROR')
                
                # Fermer seulement les LONG (les SHORT profitent du crash)
                trader = PaperTrader()
                closed_count = trader.emergency_close_all(real_prices, f"Crash {crash_type}", close_direction="LONG")
                add_bot_log(f"💥 {closed_count} LONG fermé(s) - SHORT conservés (en profit)", 'ERROR')
                
                # Ajouter au dashboard
                shared_data['crash_status'] = crash_analysis
                return []  # Arrêter le scan
            
            if not crash_analysis.get('trading_allowed'):
                reason = crash_analysis.get('reason', 'Trading pausé')
                add_bot_log(f"⏸️ {reason}", 'WARN')
                return []  # Pas de trading pendant la pause
        
        # ── ÉTAPE 2b : ANALYSE SENTIMENT & NEWS ────────────────────────────
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
                    f"📊 Sentiment: Fear&Greed={fg_value} ({fg_class}) | "
                    f"News: {news_sent.get('bullish', 0)}↑ {news_sent.get('bearish', 0)}↓",
                    'INFO'
                )
                
                # Pause si événement économique majeur
                if PAUSE_ON_EVENTS and trading_action == 'PAUSE':
                    reason = market_sentiment.get('reason', 'Événement majeur')
                    add_bot_log(f"⏸️ NEWS PAUSE: {reason}", 'WARN')
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
                add_bot_log(f"⚠️ Erreur analyse sentiment: {str(e)[:50]}", 'WARN')
        
        # ── ÉTAPE 3 : Analyse Technique (faire AVANT la vérification des positions) ────────────────────────
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
                
                # Stocker les indicateurs pour utilisation ultérieure
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
                    # Indicateurs affichés dans le dashboard
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

        # Trier par score décroissant
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Stats marché globales
        avg_rsi = round(sum(rsi_values) / len(rsi_values), 1) if rsi_values else 0
        shared_data['market_stats'] = {
            'total_bullish': bullish_count,
            'total_bearish': bearish_count,
            'total_neutral': neutral_count,
            'avg_rsi': avg_rsi,
            'sentiment': 'HAUSSIER 📈' if bullish_count > bearish_count else ('BAISSIER 📉' if bearish_count > bullish_count else 'NEUTRE ⚖️'),
        }

        add_bot_log(
            f"Scan terminé: {bullish_count}↑ {bearish_count}↓ | RSI moyen: {avg_rsi} | "
            f"{len([r for r in all_results if r['entry_signal'] != 'NEUTRAL'])} signaux actifs",
            'INFO'
        )

        # ── ÉTAPE 2b : Gestion Positions (SL / TP) avec PROTECTION ─────────────
        # Maintenant on a tous les indicateurs, on peut vérifier les positions avec protection
        trader = PaperTrader()
        open_pos = trader.get_open_positions()
        
        if open_pos:
            add_bot_log(f"Vérification de {len(open_pos)} position(s) ouverte(s) WITH PROTECTION...", 'INFO')
            trader.check_positions_with_protection(real_prices, all_indicators)
            
            # ── BREAK-EVEN AUTOMATIQUE ─────────────
            breakeven_count = trader.check_and_apply_breakeven(real_prices)
            if breakeven_count > 0:
                add_bot_log(f"🔒 BREAK-EVEN appliqué sur {breakeven_count} position(s)", 'TRADE')
            
            # ── TRAILING STOP LOSS ─────────────
            trailing_count = trader.check_and_apply_trailing_stop(real_prices)
            if trailing_count > 0:
                add_bot_log(f"📈 TRAILING SL ajusté sur {trailing_count} position(s)", 'TRADE')
            
            # ── TAKE PROFIT PARTIEL ─────────────
            if PARTIAL_TP_ENABLED:
                partial_count = trader.check_and_apply_partial_tp(real_prices)
                if partial_count > 0:
                    add_bot_log(f"💰 TP PARTIEL exécuté sur {partial_count} position(s)", 'TRADE')
        
        # Afficher le status du circuit breaker si actif
        protection_status = trader.protector.get_protection_status()
        if protection_status['circuit_breaker_active']:
            add_bot_log(
                f"⛔ CIRCUIT BREAKER ACTIF: {protection_status['recent_sl_count']} SL récents, "
                f"{protection_status['circuit_breaker_remaining']}s restants",
                'WARN'
            )
        
        # ── VÉRIFICATION DRAWDOWN MAX ─────────────
        is_drawdown_exceeded, drawdown_pct, total_capital = trader.check_drawdown(real_prices)
        if is_drawdown_exceeded:
            add_bot_log(
                f"🚨 DRAWDOWN MAX ATTEINT: -{drawdown_pct:.1f}% | Capital: ${total_capital:.2f}",
                'ERROR'
            )
            # Fermer toutes les positions en urgence
            closed_count = trader.emergency_close_all(real_prices, "DRAWDOWN MAX")
            add_bot_log(f"🚨 {closed_count} position(s) fermée(s) en urgence", 'ERROR')
            shared_data['drawdown_alert'] = True
        else:
            shared_data['drawdown_alert'] = False
            if drawdown_pct > 5:
                add_bot_log(f"⚠️ Drawdown actuel: -{drawdown_pct:.1f}% (max: {MAX_DRAWDOWN_PCT}%)", 'WARN')

        update_performance_stats(trader)

        # Sauvegarder les résultats
        shared_data['all_scanned'] = all_results
        opportunities = [r for r in all_results if r['entry_signal'] != 'NEUTRAL'][:20]
        shared_data['opportunities'] = opportunities

        # ── ÉTAPE 4 : Auto-Trading ─────────────────────────────
        balance = trader.get_usdt_balance()
        my_positions = trader.get_open_positions()
        
        # Vérifier circuit breaker
        is_cb_active, cb_remaining = trader.protector.is_circuit_breaker_active()
        
        # Vérifier les heures de trading
        hours_valid, hours_reason = trade_filters.check_trading_hours()
        
        # Obtenir le score minimum dynamique selon le marché
        dynamic_min_score, score_reason = trade_filters.get_dynamic_min_score(shared_data['market_stats'])
        
        # Vérifier si drawdown max atteint - pas de nouveau trading
        if is_drawdown_exceeded:
            add_bot_log(f"🚨 TRADING SUSPENDU - Drawdown max dépassé", 'ERROR')
        # Vérifier si circuit breaker est actif
        elif is_cb_active:
            add_bot_log(f"⛔ CIRCUIT BREAKER - Pas de nouveaux achats ({cb_remaining}s)", 'WARN')
        # Vérifier les heures de trading
        elif TRADING_HOURS_ENABLED and not hours_valid:
            add_bot_log(f"⏰ {hours_reason}", 'INFO')
        else:
            add_bot_log(f"Auto-trade | Solde: ${balance:.2f} | {len(my_positions)} pos | {score_reason}", 'INFO')

            for opp in opportunities:
                # Utiliser le score dynamique au lieu du fixe
                effective_min_score = dynamic_min_score if DYNAMIC_SCORE_ENABLED else MIN_SCORE_BUY
                
                # Direction du signal
                signal_direction = opp['entry_signal']  # 'LONG', 'SHORT', ou 'NEUTRAL'
                
                # Ajuster le score selon le sentiment marché
                adjusted_score = opp['score'] + sentiment_modifier
                
                # Vérifier compatibilité direction/sentiment
                if NEWS_ENABLED and 'market_sentiment' in shared_data:
                    ms = shared_data['market_sentiment']
                    fg_value = ms.get('fear_greed', 50)
                    
                    # Éviter LONG en Extreme Greed (risque de correction)
                    if signal_direction == 'LONG' and fg_value >= 80:
                        add_bot_log(f"⚠️ {opp['pair']} LONG évité (Extreme Greed {fg_value})", 'WARN')
                        continue
                    
                    # Éviter SHORT en Extreme Fear (rebond probable)
                    if signal_direction == 'SHORT' and fg_value <= 20:
                        add_bot_log(f"⚠️ {opp['pair']} SHORT évité (Extreme Fear {fg_value})", 'WARN')
                        continue
                
                # Règles strictes d'ouverture (LONG ou SHORT)
                if (adjusted_score >= effective_min_score
                        and signal_direction in ['LONG', 'SHORT']  # Accepter LONG ET SHORT
                        and opp['pair'] not in my_positions
                        and len(my_positions) < MAX_POSITIONS
                        and opp['stop_loss'] is not None
                        and opp['take_profit_1'] is not None):

                    # ── COOLDOWN CHECK ─────────────
                    if COOLDOWN_ENABLED:
                        in_cooldown, cooldown_remaining = trader.is_in_cooldown(opp['pair'])
                        if in_cooldown:
                            add_bot_log(f"⏳ {opp['pair']} en cooldown ({cooldown_remaining:.0f}min restantes)", 'INFO')
                            continue

                    # ── FILTRE VOLUME ─────────────
                    opp_indicators = all_indicators.get(opp['pair'], {})
                    if VOLUME_FILTER_ENABLED:
                        vol_valid, vol_reason = trade_filters.check_volume_filter(opp_indicators)
                        if not vol_valid:
                            add_bot_log(f"❌ {opp['pair']} {vol_reason}", 'WARN')
                            continue

                    # ── FILTRE RISK/REWARD ─────────────
                    rr_valid, rr_ratio, rr_reason = trade_filters.check_risk_reward(
                        opp['price'], opp['stop_loss'], opp['take_profit_1'], signal_direction
                    )
                    if not rr_valid:
                        add_bot_log(f"❌ {opp['pair']} {rr_reason}", 'WARN')
                        continue

                    # Vérifier les conditions de volatilité
                    can_open, open_reason = trader.protector.can_open_position(opp_indicators)
                    if not can_open:
                        add_bot_log(f"❌ {opp['pair']} rejeté: {open_reason}", 'WARN')
                        continue
                    
                    # ── VALIDATION MULTI-TIMEFRAME ─────────────
                    if MTF_ENABLED:
                        mtf_result = validate_signal_multi_timeframe(
                            opp['pair'], 
                            signal_direction, 
                            MTF_TIMEFRAMES
                        )
                        if not mtf_result['is_valid']:
                            add_bot_log(
                                f"❌ {opp['pair']} MTF rejeté: {mtf_result['reason']}", 
                                'WARN'
                            )
                            continue
                        else:
                            add_bot_log(
                                f"✅ {opp['pair']} MTF confirmé: {mtf_result['alignment_score']}% aligné",
                                'INFO'
                            )

                    if balance >= TRADE_AMOUNT:
                        # ── EXÉCUTION LONG OU SHORT ─────────────
                        if signal_direction == 'LONG':
                            success = trader.place_buy_order(
                                symbol=opp['pair'],
                                amount_usdt=TRADE_AMOUNT,
                                current_price=opp['price'],
                                stop_loss_price=opp['stop_loss'],
                                take_profit_price=opp['take_profit_1'],
                                entry_trend=opp['trend'],
                                take_profit_2=opp.get('take_profit_2')
                            )
                            trade_emoji = "🟢 LONG"
                        else:  # SHORT
                            success = trader.place_short_order(
                                symbol=opp['pair'],
                                amount_usdt=TRADE_AMOUNT,
                                current_price=opp['price'],
                                stop_loss_price=opp['stop_loss'],
                                take_profit_price=opp['take_profit_1'],
                                entry_trend=opp['trend']
                            )
                            trade_emoji = "🔴 SHORT"
                        
                        if success:
                            # Enregistrer le trade pour le cooldown
                            trader.record_trade_time(opp['pair'])
                            balance -= TRADE_AMOUNT
                            my_positions = trader.get_open_positions()
                            add_bot_log(
                                f"{trade_emoji} {opp['pair']} | ${opp['price']:.4f} | "
                                f"SL:${opp['stop_loss']:.4f} | TP:${opp['take_profit_1']:.4f} | "
                                f"Score:{opp['score']} | R/R:{opp['rr_ratio']}",
                                'TRADE'
                            )
                    else:
                        add_bot_log(f"Solde insuffisant pour {opp['pair']} (nécessite ${TRADE_AMOUNT})", 'WARN')
                        break

        update_performance_stats(trader)
        add_bot_log(f"=== SCAN #{scan_num} TERMINÉ ===", 'INFO')
        return opportunities

    except Exception as e:
        add_bot_log(f"ERREUR CRITIQUE SCAN: {str(e)}", 'ERROR')
        import traceback
        traceback.print_exc()
        return []


# ─────────────────────────────────────────────────────────────
# ROUTES FLASK
# ─────────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    """Dashboard principal — rendu côté serveur."""
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
        else:  # SHORT (inversé)
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
    
    return render_template_string(
        get_html_template(),
        balance=balance,
        total_capital=total_capital,
        positions=positions_view,
        total_unrealized_pnl=total_unrealized_pnl,
        history=history,
        opportunities=shared_data['opportunities'],
        all_scanned=shared_data['all_scanned'][:50],
        is_scanning=shared_data['is_scanning'],
        last_update=shared_data['last_update'],
        scan_count=shared_data['scan_count'],
        bot_log=shared_data['bot_log'],
        perf=perf,
        mkt=mkt,
        min_score=MIN_SCORE_BUY,
        timeframe=TIMEFRAME,
        trade_amount=TRADE_AMOUNT,
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
    success = trader.close_position(symbol, current_price, "MANUEL 👤")
    if success:
        add_bot_log(f"💰 VENTE MANUELLE {symbol} @ ${current_price:.4f}", 'TRADE')
    return jsonify({'success': success})


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'scan_count': shared_data['scan_count']}), 200


@app.route('/api/crash_status')
def crash_status():
    """Retourne le statut du système anti-crash."""
    status = get_crash_status()
    status['stats'] = crash_protector.get_crash_stats()
    return jsonify(status)


@app.route('/api/resume_trading', methods=['POST'])
def resume_trading():
    """Force la reprise du trading après un crash (bypass manuel)."""
    crash_protector.force_resume_trading()
    add_bot_log("⚠️ REPRISE MANUELLE du trading après crash", 'WARN')
    return jsonify({'success': True, 'message': 'Trading resumed'})


@app.route('/api/sentiment')
def api_sentiment():
    """Retourne l'analyse de sentiment marché."""
    try:
        sentiment = get_market_sentiment()
        sentiment['cached'] = shared_data.get('market_sentiment', {})
        return jsonify(sentiment)
    except Exception as e:
        return jsonify({'error': str(e), 'cached': shared_data.get('market_sentiment', {})})


# ─────────────────────────────────────────────────────────────
# TEMPLATE HTML ULTIME
# ─────────────────────────────────────────────────────────────

def get_html_template():
    return r"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚡ CRYPTO SCANNER ULTIME</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
    --bg:         #080c14;
    --bg2:        #0d1420;
    --bg3:        #111827;
    --border:     #1e2d45;
    --border2:    #243348;
    --text:       #e2e8f0;
    --text2:      #94a3b8;
    --text3:      #4b6080;
    --accent:     #00d4ff;
    --accent2:    #0099bb;
    --green:      #00e89b;
    --green2:     #00b877;
    --red:        #ff4560;
    --red2:       #cc2040;
    --yellow:     #ffd700;
    --orange:     #ff8c00;
    --purple:     #a855f7;
    --font-mono:  'JetBrains Mono', monospace;
    --font-main:  'Space Grotesk', sans-serif;
    --glow-g:     0 0 20px rgba(0,232,155,0.15);
    --glow-r:     0 0 20px rgba(255,69,96,0.15);
    --glow-a:     0 0 20px rgba(0,212,255,0.15);
}
*, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }

body {
    font-family: var(--font-main);
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    overflow-x: hidden;
}

/* ── GRID BG ── */
body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg2); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

/* ── LAYOUT ── */
.app { position: relative; z-index: 1; padding: 16px; max-width: 1800px; margin: 0 auto; }

/* ── HEADER ── */
.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 24px;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
}
.header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--green), var(--purple), var(--accent));
    background-size: 200%;
    animation: shimmer 3s linear infinite;
}
@keyframes shimmer { 0%{background-position:0%} 100%{background-position:200%} }

.header-title {
    display: flex;
    align-items: center;
    gap: 12px;
}
.header-logo {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, var(--accent), var(--purple));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
}
.header-text h1 {
    font-size: 1.3em;
    font-weight: 700;
    letter-spacing: 2px;
    color: var(--accent);
    font-family: var(--font-mono);
}
.header-text span {
    font-size: 0.75em;
    color: var(--text2);
    font-family: var(--font-mono);
    letter-spacing: 1px;
}
.header-right {
    display: flex; align-items: center; gap: 20px;
}
.status-dot {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.8em; font-family: var(--font-mono);
    color: var(--text2);
}
.dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 8px var(--green);
}
.dot.scanning {
    background: var(--yellow);
    box-shadow: 0 0 8px var(--yellow);
    animation: pulse 0.8s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

.header-meta {
    font-size: 0.75em; font-family: var(--font-mono);
    color: var(--text3); text-align: right;
}
.header-meta span { display: block; }

/* ── CARDS ── */
.card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
}
.card-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
    background: rgba(0,0,0,0.2);
}
.card-header h2 {
    font-size: 0.85em; font-weight: 600;
    letter-spacing: 2px; text-transform: uppercase;
    color: var(--text2); font-family: var(--font-mono);
    display: flex; align-items: center; gap: 8px;
}
.card-body { padding: 0; }

/* ── STAT GRID ── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
    margin-bottom: 16px;
}
@media (max-width: 1200px) { .stat-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 700px) { .stat-grid { grid-template-columns: repeat(2, 1fr); } }

.stat-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.stat-card:hover { border-color: var(--border2); }
.stat-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 0 0 10px 10px;
}
.stat-card.blue::after { background: var(--accent); }
.stat-card.green::after { background: var(--green); }
.stat-card.red::after { background: var(--red); }
.stat-card.yellow::after { background: var(--yellow); }
.stat-card.purple::after { background: var(--purple); }
.stat-card.orange::after { background: var(--orange); }

.stat-label {
    font-size: 0.7em; text-transform: uppercase;
    letter-spacing: 2px; color: var(--text3);
    font-family: var(--font-mono); margin-bottom: 8px;
}
.stat-value {
    font-size: 1.6em; font-weight: 700;
    font-family: var(--font-mono);
    line-height: 1;
}
.stat-value.positive { color: var(--green); }
.stat-value.negative { color: var(--red); }
.stat-value.neutral  { color: var(--accent); }
.stat-sub {
    font-size: 0.7em; color: var(--text3);
    font-family: var(--font-mono); margin-top: 4px;
}

/* ── MAIN LAYOUT ── */
.main-grid {
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 14px;
    margin-bottom: 14px;
}
@media (max-width: 1100px) { .main-grid { grid-template-columns: 1fr; } }

.bottom-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 14px;
    margin-bottom: 14px;
}
@media (max-width: 1100px) { .bottom-grid { grid-template-columns: 1fr; } }

/* ── TABLES ── */
.tbl-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 0.82em; }
thead tr { background: rgba(0,0,0,0.3); }
thead th {
    padding: 10px 14px;
    text-align: left;
    font-size: 0.72em; font-weight: 600;
    letter-spacing: 2px; text-transform: uppercase;
    color: var(--text3); font-family: var(--font-mono);
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
}
tbody td {
    padding: 10px 14px;
    border-bottom: 1px solid rgba(30,45,69,0.5);
    color: var(--text);
    font-family: var(--font-mono);
    font-size: 0.9em;
    white-space: nowrap;
    vertical-align: middle;
}
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover td { background: rgba(0,212,255,0.03); }

/* ── BADGES ── */
.badge {
    display: inline-block;
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.75em; font-weight: 700;
    font-family: var(--font-mono); letter-spacing: 1px;
}
.b-long  { background: rgba(0,232,155,0.12); color: var(--green); border: 1px solid rgba(0,232,155,0.3); }
.b-short { background: rgba(255,69,96,0.12); color: var(--red); border: 1px solid rgba(255,69,96,0.3); }
.b-wait  { background: rgba(148,163,184,0.08); color: var(--text3); border: 1px solid var(--border); }
.b-blue  { background: rgba(0,212,255,0.1); color: var(--accent); border: 1px solid rgba(0,212,255,0.2); }

/* ── SCORE BAR ── */
.score-wrap { display: flex; align-items: center; gap: 8px; }
.score-num {
    font-weight: 700; font-family: var(--font-mono);
    min-width: 26px; text-align: right;
}
.score-bar {
    width: 60px; height: 6px; background: var(--bg3);
    border-radius: 3px; overflow: hidden;
}
.score-fill {
    height: 100%; border-radius: 3px;
    transition: width 0.3s ease;
}
.score-high .score-num { color: var(--green); }
.score-high .score-fill { background: var(--green); }
.score-med  .score-num { color: var(--yellow); }
.score-med  .score-fill { background: var(--yellow); }
.score-low  .score-num { color: var(--text3); }
.score-low  .score-fill { background: var(--text3); }

/* ── RSI BAR ── */
.rsi-bar {
    display: flex; align-items: center; gap: 6px;
    font-family: var(--font-mono); font-size: 0.85em;
}
.rsi-track {
    width: 50px; height: 4px;
    background: var(--bg3); border-radius: 2px;
    overflow: hidden;
}
.rsi-fill { height: 100%; border-radius: 2px; }
.rsi-oversold  .rsi-fill { background: var(--red); }
.rsi-neutral   .rsi-fill { background: var(--text3); }
.rsi-overbought .rsi-fill { background: var(--orange); }

/* ── PROGRESS BAR (Position TP) ── */
.progress-wrap { display: flex; align-items: center; gap: 6px; min-width: 100px; }
.progress-track {
    flex: 1; height: 6px; background: var(--bg3);
    border-radius: 3px; overflow: hidden;
}
.progress-fill {
    height: 100%; border-radius: 3px;
    background: linear-gradient(90deg, var(--red), var(--yellow), var(--green));
}
.progress-pct { font-size: 0.75em; color: var(--text3); font-family: var(--font-mono); }

/* ── BOT LOG ── */
.log-wrap { height: 300px; overflow-y: auto; }
.log-line {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 7px 16px;
    border-bottom: 1px solid rgba(30,45,69,0.3);
    font-size: 0.75em; font-family: var(--font-mono);
    transition: background 0.1s;
}
.log-line:hover { background: rgba(0,0,0,0.2); }
.log-time { color: var(--text3); flex-shrink: 0; width: 60px; }
.log-level {
    flex-shrink: 0; width: 45px; text-align: center;
    border-radius: 3px; padding: 1px 4px; font-size: 0.9em;
    font-weight: 700;
}
.level-INFO  { background: rgba(0,212,255,0.1); color: var(--accent); }
.level-TRADE { background: rgba(0,232,155,0.1); color: var(--green); }
.level-WARN  { background: rgba(255,215,0,0.1); color: var(--yellow); }
.level-ERROR { background: rgba(255,69,96,0.1); color: var(--red); }
.log-msg { color: var(--text2); flex: 1; word-break: break-all; }

/* ── MARKET SENTIMENT ── */
.sentiment-bar {
    display: flex; height: 8px; border-radius: 4px; overflow: hidden;
    margin: 8px 16px;
}
.sent-bull { background: var(--green); transition: width 0.5s ease; }
.sent-bear { background: var(--red); transition: width 0.5s ease; }
.sent-neut { background: var(--text3); transition: width 0.5s ease; }

/* ── INDICATORS MINI PANEL ── */
.ind-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 2px;
}
.ind-item {
    padding: 6px 10px;
    background: rgba(0,0,0,0.2);
    border-radius: 4px;
}
.ind-label { font-size: 0.65em; color: var(--text3); font-family: var(--font-mono); letter-spacing: 1px; text-transform: uppercase; }
.ind-val { font-size: 0.85em; font-family: var(--font-mono); font-weight: 600; }

/* ── SIGNAL STRENGTH ── */
.conf-ring {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7em; font-weight: 700; font-family: var(--font-mono);
    border: 2px solid;
    flex-shrink: 0;
}
.conf-high { border-color: var(--green); color: var(--green); }
.conf-med  { border-color: var(--yellow); color: var(--yellow); }
.conf-low  { border-color: var(--text3); color: var(--text3); }

/* ── PNL COLORS ── */
.pnl-pos { color: var(--green); }
.pnl-neg { color: var(--red); }

/* ── TREND ICON ── */
.trend-bull { color: var(--green); }
.trend-bear { color: var(--red); }
.trend-neut { color: var(--text3); }

/* ── TABS ── */
.tabs { display: flex; gap: 0; border-bottom: 1px solid var(--border); }
.tab {
    padding: 10px 20px;
    font-size: 0.8em; font-family: var(--font-mono);
    letter-spacing: 1px; text-transform: uppercase;
    color: var(--text3); cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s; user-select: none;
}
.tab:hover { color: var(--text2); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }

.tab-content { display: none; }
.tab-content.active { display: block; }

/* ── MANUAL CLOSE BTN ── */
.btn-close {
    background: rgba(255,69,96,0.1);
    border: 1px solid rgba(255,69,96,0.3);
    color: var(--red);
    padding: 4px 10px; border-radius: 4px;
    font-size: 0.75em; font-family: var(--font-mono);
    cursor: pointer; transition: all 0.2s;
    letter-spacing: 1px;
}
.btn-close:hover { background: rgba(255,69,96,0.25); }

/* ── EMPTY STATE ── */
.empty {
    text-align: center; padding: 40px;
    color: var(--text3); font-family: var(--font-mono); font-size: 0.85em;
}

/* ── FOOTER ── */
.footer {
    text-align: center; padding: 20px;
    color: var(--text3); font-size: 0.75em;
    font-family: var(--font-mono); letter-spacing: 1px;
    border-top: 1px solid var(--border); margin-top: 10px;
}
.footer span { color: var(--red); }

/* ── ANIMATIONS ── */
@keyframes fadeIn { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:none} }
.card { animation: fadeIn 0.3s ease; }

/* ── LEVEL INDICATORS ── */
.level-tag {
    font-size: 0.72em; font-family: var(--font-mono);
    padding: 2px 6px; border-radius: 3px;
}
.sl-tag { background: rgba(255,69,96,0.1); color: var(--red); }
.tp-tag { background: rgba(0,232,155,0.1); color: var(--green); }
.rr-tag { background: rgba(0,212,255,0.1); color: var(--accent); }

/* ── PATTERNS ── */
.pattern-tag {
    display: inline-block;
    font-size: 0.65em; font-family: var(--font-mono);
    background: rgba(168,85,247,0.1);
    color: var(--purple);
    border: 1px solid rgba(168,85,247,0.2);
    padding: 1px 5px; border-radius: 3px; margin: 1px;
}
</style>
</head>
<body>
<div class="app">

<!-- ══════════════════════════════════════════════════════════ -->
<!-- HEADER                                                     -->
<!-- ══════════════════════════════════════════════════════════ -->
<div class="header">
    <div class="header-title">
        <div class="header-logo">⚡</div>
        <div class="header-text">
            <h1>CRYPTO SCANNER ULTIME</h1>
            <span>SWING TRADING BOT v2.0 — BINANCE {{ timeframe|upper }}</span>
        </div>
    </div>
    <div class="header-right">
        <div class="status-dot">
            <div class="dot {% if is_scanning %}scanning{% endif %}"></div>
            {% if is_scanning %}SCAN EN COURS{% else %}ACTIF{% endif %}
        </div>
        <div class="header-meta">
            <span>SCAN #{{ scan_count }}</span>
            <span>MAJ: {{ last_update }}</span>
            <span>AUTO-BUY ≥ {{ min_score }}</span>
        </div>
    </div>
</div>

<!-- ══════════════════════════════════════════════════════════ -->
<!-- STAT CARDS                                                  -->
<!-- ══════════════════════════════════════════════════════════ -->
<div class="stat-grid">
    <div class="stat-card blue">
        <div class="stat-label">Capital Total</div>
        <div class="stat-value neutral">${{ "%.2f"|format(total_capital) }}</div>
        <div class="stat-sub">Solde libre: ${{ "%.2f"|format(balance) }}</div>
    </div>
    <div class="stat-card {% if total_unrealized_pnl >= 0 %}green{% else %}red{% endif %}">
        <div class="stat-label">PnL Latent</div>
        <div class="stat-value {% if total_unrealized_pnl >= 0 %}positive{% else %}negative{% endif %}">
            {{ "%+.2f"|format(total_unrealized_pnl) }}$
        </div>
        <div class="stat-sub">{{ positions|length }} position(s) active(s)</div>
    </div>
    <div class="stat-card {% if perf.total_pnl >= 0 %}green{% else %}red{% endif %}">
        <div class="stat-label">PnL Réalisé</div>
        <div class="stat-value {% if perf.total_pnl >= 0 %}positive{% else %}negative{% endif %}">
            {{ "%+.2f"|format(perf.total_pnl) }}$
        </div>
        <div class="stat-sub">{{ perf.total_trades }} trades fermés</div>
    </div>
    <div class="stat-card yellow">
        <div class="stat-label">Win Rate</div>
        <div class="stat-value neutral">{{ perf.win_rate }}%</div>
        <div class="stat-sub">{{ perf.winning_trades }}/{{ perf.total_trades }} gagnants</div>
    </div>
    <div class="stat-card purple">
        <div class="stat-label">Sentiment Marché</div>
        <div class="stat-value" style="font-size:1.1em">{{ mkt.sentiment }}</div>
        <div class="stat-sub">RSI moy: {{ mkt.avg_rsi }}</div>
    </div>
    <div class="stat-card orange">
        <div class="stat-label">Opportunités</div>
        <div class="stat-value neutral">{{ opportunities|length }}</div>
        <div class="stat-sub">↑{{ mkt.total_bullish }} ↓{{ mkt.total_bearish }} –{{ mkt.total_neutral }}</div>
    </div>
</div>

<!-- ══════════════════════════════════════════════════════════ -->
<!-- MARKET SENTIMENT BAR                                        -->
<!-- ══════════════════════════════════════════════════════════ -->
{% set total_pairs = mkt.total_bullish + mkt.total_bearish + mkt.total_neutral %}
{% if total_pairs > 0 %}
<div class="card" style="margin-bottom:14px;">
    <div class="card-header">
        <h2>📊 Sentiment Marché Global ({{ total_pairs }} paires)</h2>
        <span style="font-size:0.78em;font-family:var(--font-mono);color:var(--text3)">
            ↑ {{ mkt.total_bullish }} HAUSSIER | ↓ {{ mkt.total_bearish }} BAISSIER | — {{ mkt.total_neutral }} NEUTRE
        </span>
    </div>
    <div class="card-body" style="padding:12px 16px;">
        <div class="sentiment-bar">
            <div class="sent-bull" style="width:{{ (mkt.total_bullish / total_pairs * 100)|round }}%"></div>
            <div class="sent-neut" style="width:{{ (mkt.total_neutral / total_pairs * 100)|round }}%"></div>
            <div class="sent-bear" style="width:{{ (mkt.total_bearish / total_pairs * 100)|round }}%"></div>
        </div>
    </div>
</div>
{% endif %}

<!-- ══════════════════════════════════════════════════════════ -->
<!-- MAIN GRID: POSITIONS + BOT LOG                             -->
<!-- ══════════════════════════════════════════════════════════ -->
<div class="main-grid">

    <!-- POSITIONS ACTIVES -->
    <div class="card">
        <div class="card-header">
            <h2>💼 Positions Actives ({{ positions|length }})</h2>
            <span class="badge b-blue" style="font-size:0.7em">PAPER TRADING</span>
        </div>
        <div class="card-body tbl-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Paire</th>
                        <th>Entrée</th>
                        <th>Actuel</th>
                        <th>Investi</th>
                        <th>PnL $</th>
                        <th>PnL %</th>
                        <th>Stop Loss</th>
                        <th>Take Profit</th>
                        <th>Progression TP</th>
                        <th>Ouvert</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                {% if not positions %}
                <tr><td colspan="11" class="empty">Aucune position ouverte</td></tr>
                {% else %}
                {% for p in positions %}
                <tr>
                    <td style="font-weight:700;color:var(--accent)">{{ p.symbol }}</td>
                    <td>${{ "%.4f"|format(p.entry) }}</td>
                    <td style="font-weight:600">${{ "%.4f"|format(p.current) }}</td>
                    <td>${{ "%.0f"|format(p.amount) }}</td>
                    <td class="{% if p.pnl_value >= 0 %}pnl-pos{% else %}pnl-neg{% endif %}">
                        {{ "%+.2f"|format(p.pnl_value) }}$
                    </td>
                    <td class="{% if p.pnl_percent >= 0 %}pnl-pos{% else %}pnl-neg{% endif %}">
                        {{ "%+.2f"|format(p.pnl_percent) }}%
                    </td>
                    <td><span class="level-tag sl-tag">{{ "%.4f"|format(p.sl) }}</span></td>
                    <td><span class="level-tag tp-tag">{{ "%.4f"|format(p.tp) }}</span></td>
                    <td>
                        <div class="progress-wrap">
                            <div class="progress-track">
                                <div class="progress-fill" style="width:{{ [0,[100,p.progress]|min]|max }}%"></div>
                            </div>
                            <span class="progress-pct">{{ "%.0f"|format(p.progress) }}%</span>
                        </div>
                    </td>
                    <td style="color:var(--text3);font-size:0.8em">{{ p.entry_time }}</td>
                    <td>
                        <button class="btn-close" onclick="closePos('{{ p.symbol }}')">VENDRE</button>
                    </td>
                </tr>
                {% endfor %}
                {% endif %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- BOT LOG -->
    <div class="card">
        <div class="card-header">
            <h2>🤖 Journal du Bot</h2>
        </div>
        <div class="card-body">
            <div class="log-wrap" id="bot-log">
                {% if not bot_log %}
                <div class="empty">En attente d'activité...</div>
                {% else %}
                {% for entry in bot_log %}
                <div class="log-line">
                    <span class="log-time">{{ entry.time }}</span>
                    <span class="log-level level-{{ entry.level }}">{{ entry.level }}</span>
                    <span class="log-msg">{{ entry.msg }}</span>
                </div>
                {% endfor %}
                {% endif %}
            </div>
        </div>
    </div>

</div>

<!-- ══════════════════════════════════════════════════════════ -->
<!-- SCANNER OPPORTUNITÉS (ULTIME)                              -->
<!-- ══════════════════════════════════════════════════════════ -->
<div class="card" style="margin-bottom:14px;">
    <div class="card-header">
        <h2>📡 Scanner Opportunités — Top Signaux</h2>
        <span style="font-size:0.75em;color:var(--text3);font-family:var(--font-mono)">
            {{ opportunities|length }} signal(s) actif(s)
        </span>
    </div>
    <div class="card-body tbl-wrap">
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Paire</th>
                    <th>Score</th>
                    <th>Signal</th>
                    <th>Conf.</th>
                    <th>Prix</th>
                    <th>Entrée</th>
                    <th>Stop Loss</th>
                    <th>TP 1</th>
                    <th>TP 2</th>
                    <th>R/R</th>
                    <th>RSI</th>
                    <th>MACD Hist</th>
                    <th>ADX</th>
                    <th>Vol Ratio</th>
                    <th>ATR%</th>
                    <th>BB%</th>
                    <th>Tendance</th>
                    <th>EMA 9/21</th>
                    <th>SMA dist</th>
                    <th>Support</th>
                    <th>Résist.</th>
                    <th>Patterns</th>
                    <th>Détails</th>
                </tr>
            </thead>
            <tbody>
            {% if not opportunities %}
            <tr><td colspan="24" class="empty">En attente du prochain scan... ({{ timeframe|upper }})</td></tr>
            {% else %}
            {% for opp in opportunities %}
            {% set score_class = 'score-high' if opp.score >= 70 else ('score-med' if opp.score >= 45 else 'score-low') %}
            {% set sig_class   = 'b-long' if opp.entry_signal == 'LONG' else ('b-short' if opp.entry_signal == 'SHORT' else 'b-wait') %}
            {% set conf_class  = 'conf-high' if opp.confidence >= 70 else ('conf-med' if opp.confidence >= 45 else 'conf-low') %}
            {% set rsi_class   = 'rsi-oversold' if opp.rsi and opp.rsi < 35 else ('rsi-overbought' if opp.rsi and opp.rsi > 65 else 'rsi-neutral') %}
            <tr>
                <td style="color:var(--text3)">{{ loop.index }}</td>
                <td style="font-weight:700;color:var(--accent)">{{ opp.pair }}</td>
                <td>
                    <div class="score-wrap {{ score_class }}">
                        <span class="score-num">{{ opp.score }}</span>
                        <div class="score-bar">
                            <div class="score-fill" style="width:{{ opp.score }}%"></div>
                        </div>
                    </div>
                </td>
                <td><span class="badge {{ sig_class }}">{{ opp.entry_signal }}</span></td>
                <td>
                    <div class="conf-ring {{ conf_class }}">{{ opp.confidence }}</div>
                </td>
                <td style="font-weight:600">${{ "%.4f"|format(opp.price) }}</td>
                <td>{% if opp.entry_price %}<span style="color:var(--accent)">${{ "%.4f"|format(opp.entry_price) }}</span>{% else %}—{% endif %}</td>
                <td>{% if opp.stop_loss %}<span class="level-tag sl-tag">${{ "%.4f"|format(opp.stop_loss) }}</span>{% else %}—{% endif %}</td>
                <td>{% if opp.take_profit_1 %}<span class="level-tag tp-tag">${{ "%.4f"|format(opp.take_profit_1) }}</span>{% else %}—{% endif %}</td>
                <td>{% if opp.take_profit_2 %}<span class="level-tag tp-tag" style="opacity:0.7">${{ "%.4f"|format(opp.take_profit_2) }}</span>{% else %}—{% endif %}</td>
                <td>{% if opp.rr_ratio %}<span class="level-tag rr-tag">{{ opp.rr_ratio }}x</span>{% else %}—{% endif %}</td>
                <td>
                    {% if opp.rsi %}
                    <div class="rsi-bar {{ rsi_class }}">
                        <span>{{ opp.rsi }}</span>
                        <div class="rsi-track"><div class="rsi-fill" style="width:{{ opp.rsi }}%"></div></div>
                    </div>
                    {% else %}—{% endif %}
                </td>
                <td>
                    {% if opp.macd_hist is not none %}
                    <span class="{% if opp.macd_hist > 0 %}pnl-pos{% else %}pnl-neg{% endif %}">
                        {{ "%+.4f"|format(opp.macd_hist) }}
                    </span>
                    {% else %}—{% endif %}
                </td>
                <td>
                    {% if opp.adx %}
                    <span style="color:{% if opp.adx > 25 %}var(--green){% elif opp.adx > 15 %}var(--yellow){% else %}var(--text3){% endif %}">{{ opp.adx }}</span>
                    {% else %}—{% endif %}
                </td>
                <td>
                    {% if opp.volume_ratio %}
                    <span style="color:{% if opp.volume_ratio > 1.5 %}var(--green){% elif opp.volume_ratio > 1 %}var(--text){% else %}var(--text3){% endif %}">
                        {{ opp.volume_ratio }}x
                    </span>
                    {% else %}—{% endif %}
                </td>
                <td style="color:var(--text2)">{% if opp.atr_percent %}{{ opp.atr_percent }}%{% else %}—{% endif %}</td>
                <td>
                    {% if opp.bb_percent %}
                    <span style="color:{% if opp.bb_percent > 80 %}var(--red){% elif opp.bb_percent < 20 %}var(--green){% else %}var(--text2){% endif %}">
                        {{ opp.bb_percent }}%
                    </span>
                    {% else %}—{% endif %}
                </td>
                <td class="{% if opp.trend == 'Bullish' %}trend-bull{% elif opp.trend == 'Bearish' %}trend-bear{% else %}trend-neut{% endif %}">
                    {{ opp.trend }}
                </td>
                <td style="font-size:0.78em;color:var(--text3)">
                    {% if opp.ema9 and opp.ema21 %}
                    <span style="color:{% if opp.ema9 > opp.ema21 %}var(--green){% else %}var(--red){% endif %}">
                        {{ "%.3f"|format(opp.ema9) }}/{{ "%.3f"|format(opp.ema21) }}
                    </span>
                    {% else %}—{% endif %}
                </td>
                <td style="font-size:0.78em">
                    {% if opp.dist_sma50 is not none %}
                    <span class="{% if opp.dist_sma50 > 0 %}pnl-pos{% else %}pnl-neg{% endif %}">SMA50: {{ "%+.1f"|format(opp.dist_sma50) }}%</span>
                    {% endif %}
                </td>
                <td>{% if opp.support %}<span class="level-tag sl-tag" style="opacity:0.7">${{ "%.4f"|format(opp.support) }}</span>{% else %}—{% endif %}</td>
                <td>{% if opp.resistance %}<span class="level-tag tp-tag" style="opacity:0.7">${{ "%.4f"|format(opp.resistance) }}</span>{% else %}—{% endif %}</td>
                <td>
                    {% for pat in opp.patterns[:2] %}
                    <span class="pattern-tag">{{ pat }}</span>
                    {% endfor %}
                </td>
                <td style="color:var(--text3);font-size:0.8em;max-width:150px;white-space:normal">{{ opp.details }}</td>
            </tr>
            {% endfor %}
            {% endif %}
            </tbody>
        </table>
    </div>
</div>

<!-- ══════════════════════════════════════════════════════════ -->
<!-- BOTTOM GRID: ALL SCANNED + HISTORY                         -->
<!-- ══════════════════════════════════════════════════════════ -->
<div class="bottom-grid">

    <!-- TOUTES LES PAIRES SCANNÉES -->
    <div class="card">
        <div class="card-header">
            <h2>🔍 Toutes les Paires Scannées ({{ all_scanned|length }})</h2>
        </div>
        <div class="card-body">
            <div class="tabs">
                <div class="tab active" onclick="switchTab('all')">Toutes</div>
                <div class="tab" onclick="switchTab('bull')">Haussières</div>
                <div class="tab" onclick="switchTab('bear')">Baissières</div>
            </div>
            <div class="tab-content active" id="tab-all">
            <div class="tbl-wrap" style="max-height:400px;overflow-y:auto">
                <table>
                    <thead>
                        <tr>
                            <th>#</th><th>Paire</th><th>Prix</th><th>Score</th>
                            <th>Signal</th><th>Tendance</th><th>RSI</th><th>ADX</th>
                            <th>MACD↕</th><th>Vol×</th><th>SL</th><th>TP1</th><th>R/R</th>
                            <th>SMA50%</th><th>ATR%</th>
                        </tr>
                    </thead>
                    <tbody>
                    {% for item in all_scanned %}
                    {% set score_class = 'score-high' if item.score >= 70 else ('score-med' if item.score >= 45 else 'score-low') %}
                    <tr class="row-{{ item.trend|lower }}">
                        <td style="color:var(--text3)">{{ loop.index }}</td>
                        <td style="font-weight:700;color:{% if item.entry_signal == 'LONG' %}var(--green){% elif item.entry_signal == 'SHORT' %}var(--red){% else %}var(--text){% endif %}">
                            {{ item.pair }}
                        </td>
                        <td>${{ "%.4f"|format(item.price) }}</td>
                        <td>
                            <div class="score-wrap {{ score_class }}">
                                <span class="score-num">{{ item.score }}</span>
                                <div class="score-bar"><div class="score-fill" style="width:{{ item.score }}%"></div></div>
                            </div>
                        </td>
                        <td>
                            <span class="badge {% if item.entry_signal == 'LONG' %}b-long{% elif item.entry_signal == 'SHORT' %}b-short{% else %}b-wait{% endif %}">
                                {{ item.entry_signal }}
                            </span>
                        </td>
                        <td class="{% if item.trend == 'Bullish' %}trend-bull{% elif item.trend == 'Bearish' %}trend-bear{% else %}trend-neut{% endif %}">
                            {{ item.trend }}
                        </td>
                        <td>
                            {% if item.rsi %}
                            <span style="color:{% if item.rsi < 35 %}var(--red){% elif item.rsi > 65 %}var(--orange){% else %}var(--text2){% endif %}">
                                {{ item.rsi }}
                            </span>
                            {% else %}—{% endif %}
                        </td>
                        <td>
                            {% if item.adx %}
                            <span style="color:{% if item.adx > 25 %}var(--green){% else %}var(--text3){% endif %}">{{ item.adx }}</span>
                            {% else %}—{% endif %}
                        </td>
                        <td>
                            {% if item.macd_hist is not none %}
                            <span class="{% if item.macd_hist > 0 %}pnl-pos{% else %}pnl-neg{% endif %}">
                                {{ "%.4f"|format(item.macd_hist) }}
                            </span>
                            {% else %}—{% endif %}
                        </td>
                        <td style="color:{% if item.volume_ratio > 1.5 %}var(--green){% elif item.volume_ratio > 1 %}var(--text){% else %}var(--text3){% endif %}">
                            {{ item.volume_ratio }}x
                        </td>
                        <td>{% if item.stop_loss %}<span class="sl-tag level-tag">${{ "%.4f"|format(item.stop_loss) }}</span>{% else %}—{% endif %}</td>
                        <td>{% if item.take_profit_1 %}<span class="tp-tag level-tag">${{ "%.4f"|format(item.take_profit_1) }}</span>{% else %}—{% endif %}</td>
                        <td>{% if item.rr_ratio %}<span class="rr-tag level-tag">{{ item.rr_ratio }}x</span>{% else %}—{% endif %}</td>
                        <td>
                            {% if item.dist_sma50 is not none %}
                            <span class="{% if item.dist_sma50 > 0 %}pnl-pos{% else %}pnl-neg{% endif %}">{{ "%+.1f"|format(item.dist_sma50) }}%</span>
                            {% else %}—{% endif %}
                        </td>
                        <td style="color:var(--text3)">{{ item.atr_percent }}%</td>
                    </tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
            </div>
        </div>
    </div>

    <!-- HISTORIQUE DES TRADES -->
    <div class="card">
        <div class="card-header">
            <h2>📜 Historique des Trades</h2>
            <span style="font-size:0.78em;color:var(--text3);font-family:var(--font-mono)">
                PnL total: <span class="{% if perf.total_pnl >= 0 %}pnl-pos{% else %}pnl-neg{% endif %}">{{ "%+.2f"|format(perf.total_pnl) }}$</span>
            </span>
        </div>
        <div class="card-body tbl-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Paire</th>
                        <th>Type</th>
                        <th>Prix</th>
                        <th>PnL $</th>
                        <th>PnL %</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                {% if not history %}
                <tr><td colspan="6" class="empty">Aucune transaction fermée</td></tr>
                {% else %}
                {% for t in history[:20] %}
                <tr>
                    <td style="font-weight:700">{{ t.symbol }}</td>
                    <td style="font-size:0.8em;color:var(--text3)">{{ t.type }}</td>
                    <td>${{ "%.4f"|format(t.price) }}</td>
                    <td class="{% if t.pnl >= 0 %}pnl-pos{% else %}pnl-neg{% endif %}">
                        {{ "%+.2f"|format(t.pnl) }}$
                    </td>
                    <td class="{% if t.pnl_percent >= 0 %}pnl-pos{% else %}pnl-neg{% endif %}">
                        {{ "%+.2f"|format(t.pnl_percent) }}%
                    </td>
                    <td style="color:var(--text3);font-size:0.8em">{{ t.time }}</td>
                </tr>
                {% endfor %}
                {% endif %}
                </tbody>
            </table>
        </div>
    </div>

</div>

<!-- FOOTER -->
<div class="footer">
    ⚡ CRYPTO SCANNER ULTIME v2.0 — Paper Trading Only — <span>PAS DE CONSEILS FINANCIERS</span> — DYOR — Auto-refresh: 15s
</div>

</div><!-- .app -->

<!-- ══════════════════════════════════════════════════════════ -->
<!-- JAVASCRIPT                                                  -->
<!-- ══════════════════════════════════════════════════════════ -->
<script>
// ── Tabs ──────────────────────────────────────────────
function switchTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    const rows = document.querySelectorAll('#tab-all tbody tr');
    rows.forEach(r => {
        if (tab === 'all') { r.style.display = ''; }
        else if (tab === 'bull') { r.style.display = r.classList.contains('row-bullish') ? '' : 'none'; }
        else if (tab === 'bear') { r.style.display = r.classList.contains('row-bearish') ? '' : 'none'; }
    });
}

// ── Close Position ───────────────────────────────────
function closePos(symbol) {
    if (!confirm(`Fermer la position ${symbol} au prix actuel ?`)) return;
    fetch(`/api/close/${symbol}`, {method:'POST'})
        .then(r => r.json())
        .then(d => {
            if (d.success) {
                showToast(`✅ Position ${symbol} fermée`);
                setTimeout(() => location.reload(), 1500);
            } else {
                showToast(`❌ Erreur: ${d.error}`, true);
            }
        }).catch(() => showToast('❌ Erreur réseau', true));
}

// ── Toast Notification ───────────────────────────────
function showToast(msg, isError = false) {
    const t = document.createElement('div');
    t.textContent = msg;
    t.style.cssText = `
        position:fixed; bottom:24px; right:24px; z-index:9999;
        background:${isError ? 'rgba(255,69,96,0.9)' : 'rgba(0,232,155,0.9)'};
        color:#080c14; padding:12px 20px; border-radius:8px;
        font-family:'JetBrains Mono',monospace; font-size:0.85em;
        font-weight:600; box-shadow:0 4px 20px rgba(0,0,0,0.4);
        animation:fadeIn 0.2s ease;
    `;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3000);
}

// ── Auto-refresh désactivé ─────────────────────────────────────
// Refresh disabled - scan continues in background

</script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────
# BOUCLE PRINCIPALE (THREAD BACKGROUND)
# ─────────────────────────────────────────────────────────────

def run_loop():
    """Boucle infinie qui lance le scanner périodiquement."""
    add_bot_log("⚡ Swing Bot démarré — Timeframe: " + TIMEFRAME, 'INFO')
    while True:
        shared_data['is_scanning'] = True
        try:
            shared_data['opportunities'] = run_scanner()
            shared_data['last_update'] = datetime.now().strftime('%H:%M:%S')
        except Exception as e:
            add_bot_log(f"Erreur boucle: {str(e)}", 'ERROR')
        finally:
            shared_data['is_scanning'] = False

        add_bot_log(f"Pause {SCAN_INTERVAL//60} min — prochain scan: {datetime.now().strftime('%H:%M')}", 'INFO')
        time.sleep(SCAN_INTERVAL)


# ─────────────────────────────────────────────────────────────
# LANCEMENT
# ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Thread Scanner (daemon — s'arrête avec le programme principal)
    scanner_thread = threading.Thread(target=run_loop, daemon=True)
    scanner_thread.start()

    port = int(os.environ.get('PORT', 8080))
    add_bot_log(f"Dashboard: http://localhost:{port}", 'INFO')
    app.run(host='0.0.0.0', port=port, debug=False)
