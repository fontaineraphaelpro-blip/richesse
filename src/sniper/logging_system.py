"""
Logging system: log detected setups, rejected setups with reason, score details, trade entry/exit/PnL.
Timestamp, symbol, timeframe, indicator values, score.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Optional: log to file under project root
_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "sniper_logs")
_LOG_FILE = None  # set to path to enable file logging


def _ensure_log_dir():
    global _LOG_DIR
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
    except Exception:
        _LOG_DIR = None


def set_log_file(path: str = None):
    """Enable file logging. If path is None, use default sniper_logs/sniper.log."""
    global _LOG_FILE
    if path:
        _LOG_FILE = path
    else:
        _ensure_log_dir()
        _LOG_FILE = os.path.join(_LOG_DIR, "sniper.log") if _LOG_DIR else None


def _log(level: str, message: str, data: Dict = None):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    line = "{} [{}] {}".format(ts, level, message)
    if data:
        line += " | " + json.dumps(data, default=str)
    print(line)
    if _LOG_FILE:
        try:
            _ensure_log_dir()
            with open(_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


def log_setup_detected(symbol: str, setup: Dict[str, Any], score: int, passed: bool):
    """Log a detected setup (candidate or passed)."""
    data = {
        "symbol": symbol,
        "score": score,
        "passed": passed,
        "trend_ok": setup.get("trend_ok"),
        "btc_bullish": setup.get("btc_bullish"),
        "pullback_ok": setup.get("pullback_ok"),
        "momentum_ok": setup.get("momentum_ok"),
        "volume_ok": setup.get("volume_ok"),
        "anti_fake_ok": setup.get("anti_fake_ok"),
        "relative_strength_ok": setup.get("relative_strength_ok"),
    }
    status = "PASSED" if passed else "REJECTED"
    _log("SETUP", "{} {} score={} {}".format(symbol, status, score, setup.get("reasons", {})), data)


def log_setup_rejected(symbol: str, reason: str, details: Dict = None):
    """Log a rejected setup with reason."""
    _log("REJECT", "{} {}".format(symbol, reason), details or {})


def log_score_details(symbol: str, score_breakdown: Dict, total: int):
    """Log score breakdown."""
    _log("SCORE", "{} total={} breakdown={}".format(symbol, total, score_breakdown), {})


def log_trade_entry(symbol: str, entry: float, sl: float, tp: float, amount_usdt: float, quantity: float, score: int):
    """Log trade entry."""
    _log("ENTRY", "LONG {} @ {} SL={} TP={} amount=${:.2f} qty={} score={}".format(
        symbol, entry, sl, tp, amount_usdt, quantity, score), {})


def log_trade_exit(symbol: str, reason: str, entry: float, exit_price: float, pnl: float, pnl_pct: float):
    """Log trade exit and PnL."""
    _log("EXIT", "{} {} @ {} | entry={} pnl=${:.2f} ({:.2f}%)".format(
        symbol, reason, exit_price, entry, pnl, pnl_pct), {})


def log_scan_start(symbols_count: int):
    _log("SCAN", "Scan started, {} symbols".format(symbols_count), {})


def log_scan_done(candidates: int, passed: int, executed: int):
    _log("SCAN", "Scan done: {} candidates, {} passed, {} executed".format(candidates, passed, executed), {})
