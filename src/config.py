"""
Configuration centralisée (lecture depuis variables d'environnement).
"""
import os


class Config:
    # App
    TIMEFRAME = os.environ.get('TIMEFRAME', '15m')
    CANDLE_LIMIT = int(os.environ.get('CANDLE_LIMIT', '500'))
    TRADE_AMOUNT = float(os.environ.get('TRADE_AMOUNT', '100'))  # 100€ par position pour 10+ simultanées
    MIN_SCORE_TO_BUY = int(os.environ.get('MIN_SCORE_TO_BUY', '50'))  # Score bas pour + de trades
    SCAN_INTERVAL = int(os.environ.get('SCAN_INTERVAL', '600'))  # 10 min pour scanning fréquent
    MAX_OPEN_POSITIONS = int(os.environ.get('MAX_OPEN_POSITIONS', '10'))  # Max trades simultanés

    # Backtest / Paper trading
    PAPER_INITIAL_BALANCE = float(os.environ.get('PAPER_INITIAL_BALANCE', '1000'))

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'richesse.log')

    # Network / API
    FETCH_TIMEOUT = float(os.environ.get('FETCH_TIMEOUT', '5'))


cfg = Config()
