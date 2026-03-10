"""
Configuration for the Crypto Setup Sniper bot.
Low trade frequency, high-quality entries, robust risk management.
"""

# Markets
MIN_QUOTE_VOLUME_24H_USDT = 20_000_000  # Filter out low-liquidity coins
BINANCE_BASE_URL = "https://api.binance.com"
BINANCE_US_BASE_URL = "https://api.binance.us/api/v3"

# Timeframes
TIMEFRAME_PRIMARY = "15m"
TIMEFRAME_HIGHER = "1h"
CANDLE_LIMIT_PRIMARY = 200
CANDLE_LIMIT_HIGHER = 200
EVALUATE_AT_CANDLE_CLOSE = True

# BTC regime (global market filter for alt longs)
BTC_SYMBOL = "BTCUSDT"
BTC_EMA200_PERIOD = 200
BTC_RSI_PERIOD = 14
BTC_BULLISH_RSI_MIN = 50  # RSI(14) > 50
# BTC close > BTC EMA200 + RSI > 50 = allow alt longs

# Trend filter
TREND_EMA_FAST = 50
TREND_EMA_SLOW = 200
TREND_ADX_PERIOD = 14
TREND_ADX_MIN = 20  # ADX(14) > 20

# Pullback filter
PULLBACK_EMA = 20  # Candle low touches EMA20
PULLBACK_PRICE_ABOVE_EMA50 = True
PULLBACK_DIST_EMA50_MAX_PCT = 3.0  # Distance from EMA50 < 3%

# Volatility contraction
ATR_SHORT = 5
ATR_LONG = 20
# ATR(5) < ATR(20) = squeeze

# Momentum breakout
RSI_PERIOD = 14
RSI_MIN = 55
# Candle close > open, close > prev candle high, volume > VolumeMA(20)

# Accumulation / volume
VOLUME_MA_PERIOD = 20
VOLUME_SPIKE_MULT = 1.5  # Volume > 1.5 * VolumeMA20

# Relative strength
RELATIVE_STRENGTH_LOOKBACK = 50  # candles

# Anti fake breakout
BREAKOUT_BODY_PCT_MIN = 0.60  # Body > 60% of range
BREAKOUT_LOOKBACK_LOW = 5
BREAKOUT_LOOKBACK_HIGH = 20

# Scoring (trade only if score >= MIN_SETUP_SCORE)
MIN_SETUP_SCORE = 7
SCORE_TREND_ALIGNMENT = 2
SCORE_BTC_CONFIRMATION = 1
SCORE_PULLBACK_QUALITY = 1
SCORE_VOLATILITY_CONTRACTION = 1
SCORE_MOMENTUM_BREAKOUT = 2
SCORE_VOLUME_ACCUMULATION = 1
SCORE_ANTI_FAKE_PASSED = 1
SCORE_RELATIVE_STRENGTH = 1

# Ranking: trade top N setups
TOP_N_SETUPS = 3

# Entry
ENTRY_BREAKOUT_ABOVE_PREV_HIGH = True
ENTRY_BUFFER_PCT = 0.02  # Stop order slightly above breakout

# Stop loss
SL_ATR_PERIOD = 14
SL_ATR_MULT = 1.5
# stop_loss = entry - ATR(14) * 1.5 (or below recent swing low)

# Take profit
TAKE_PROFIT_RR = 2.0  # 2:1
# take_profit = entry + (entry - stop_loss) * 2
TRAILING_STOP_AFTER_R = 1.0  # Optional trailing when profit > 1R

# Position sizing & risk
RISK_PCT_PER_TRADE = 0.01  # 1% of account equity
MAX_SIMULTANEOUS_TRADES = 5
ONE_TRADE_PER_ASSET = True
COOLDOWN_MINUTES_PER_ASSET = 30

# Async / scan
SCAN_INTERVAL_SEC = 60
ASYNC_WORKERS = 5
