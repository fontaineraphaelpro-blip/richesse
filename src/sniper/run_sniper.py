"""
Main scan loop: fetch symbols → filter liquidity → calc indicators → detect pullbacks →
evaluate breakouts → compute score → rank signals → execute top trades → manage positions.
Runs asynchronously; evaluate at candle close (on primary TF).
"""

import sys
import os
import time

_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src not in sys.path:
    sys.path.insert(0, _src)

from . import config as cfg
from .market_scanner import scan_markets
from .btc_regime import get_btc_regime
from .setup_detector import detect_setup
from .scoring_engine import score_setup
from .ranking_engine import rank_setups
from .trade_executor import execute_setup
from .position_manager import PositionManager
from .logging_system import (
    log_setup_detected,
    log_setup_rejected,
    log_scan_start,
    log_scan_done,
    log_trade_entry,
    log_trade_exit,
)


def run_sniper_cycle(
    paper_trader=None,
    position_manager: PositionManager = None,
    symbols: list = None,
    on_log=None,
) -> dict:
    """
    One full cycle: scan → detect → score → rank → execute.
    Returns stats: { 'candidates', 'passed', 'executed', 'setups', 'errors' }.
    """
    if position_manager is None:
        position_manager = PositionManager()

    # Sync: if paper_trader closed a position (SL/TP), remove from position_manager (and set cooldown)
    if paper_trader is not None:
        try:
            open_pos = paper_trader.get_open_positions()
            for sym in list(position_manager.get_open_symbols()):
                if sym not in open_pos:
                    position_manager.remove_position(sym)
        except Exception:
            pass

    stats = {"candidates": 0, "passed": 0, "executed": 0, "setups": [], "errors": [], "symbols_requested": 0, "symbols_with_data": 0, "symbols_analyzed": 0}

    def _log(msg, level="INFO"):
        if on_log:
            try:
                on_log(msg, level)
            except Exception:
                pass

    try:
        result = scan_markets(symbols=symbols)
        if len(result) == 4:
            data_primary, data_higher, last_prices, scan_info = result
            stats["symbols_requested"] = scan_info.get("symbols_requested", 0)
            stats["symbols_with_data"] = scan_info.get("symbols_with_data", 0)
        else:
            data_primary, data_higher, last_prices = result[:3]
            stats["symbols_requested"] = len(data_primary)
            stats["symbols_with_data"] = len(data_primary)
        log_scan_start(len(data_primary))
        _log("Donnees chargees: {} paires avec OHLCV 15m+1h ({} demandees)".format(
            stats["symbols_with_data"], stats["symbols_requested"]), "INFO")
    except Exception as e:
        stats["errors"].append("scan_markets: " + str(e))
        _log("Erreur chargement donnees: {}".format(str(e)), "ERROR")
        return stats

    btc_regime = get_btc_regime()
    btc_close = btc_regime.get("close")
    btc_str = "bullish" if btc_regime.get("is_bullish") else ("bearish" if btc_regime.get("is_bearish") else "neutre")
    _log("BTC: {} | Prix: {} | RSI: {}".format(
        btc_str, "{:.0f}".format(btc_close) if btc_close else "N/A",
        "{:.0f}".format(btc_regime.get("rsi14")) if btc_regime.get("rsi14") is not None else "N/A"), "INFO")
    if not btc_regime.get("is_bullish") and not btc_regime.get("close"):
        # Still continue to detect setups; scoring will penalize missing BTC confirmation
        pass

    setups_with_symbol = []
    symbols_analyzed = 0
    for symbol, df in data_primary.items():
        if df is None or len(df) < 200:
            continue
        symbols_analyzed += 1
        try:
            result = detect_setup(
                df_primary=df,
                df_higher=data_higher.get(symbol),
                btc_regime=btc_regime,
                btc_price_now=btc_regime.get("close"),
                btc_price_50_ago=btc_regime.get("close_50_ago"),
            )
            for direction, raw in [("LONG", result.get("long")), ("SHORT", result.get("short"))]:
                if raw is None:
                    continue
                setup = score_setup(raw)
                setup["_symbol"] = symbol
                setup["direction"] = direction
                setups_with_symbol.append(setup)
                stats["candidates"] += 1
                log_setup_detected(symbol, setup, setup.get("score", 0), setup.get("passed", False))
        except Exception as e:
            stats["errors"].append("{} detect: {}".format(symbol, str(e)))
            log_setup_rejected(symbol, str(e))

    stats["symbols_analyzed"] = symbols_analyzed
    passed = [s for s in setups_with_symbol if s.get("passed")]
    stats["passed"] = len(passed)
    rejected = [s for s in setups_with_symbol if not s.get("passed")]
    if rejected and len(rejected) <= 5:
        for s in rejected[:5]:
            _log("Rejete: {} {} score {}/10 (min {})".format(
                s.get("_symbol"), s.get("direction"), s.get("score", 0), cfg.MIN_SETUP_SCORE), "INFO")
    elif rejected:
        _log("{} setups rejetes (score < {})".format(len(rejected), cfg.MIN_SETUP_SCORE), "INFO")
    ranked = rank_setups(passed)
    if not passed:
        _log("Aucun setup qualifie ce cycle (tous score < {})".format(cfg.MIN_SETUP_SCORE), "INFO")
    elif ranked:
        _log("Top {} retenus: {}".format(len(ranked), ", ".join(
            ["{} {} ({})".format(s.get("_symbol"), s.get("direction"), s.get("score")) for s in ranked])), "INFO")

    # For dashboard: ranked setups (symbol, score, entry, direction)
    stats["ranked_setups"] = [
        {
            "symbol": s.get("_symbol"),
            "score": s.get("score", 0),
            "entry": (s.get("indicators") or {}).get("close"),
            "direction": s.get("direction", "LONG"),
        }
        for s in ranked
    ]
    stats["last_prices"] = last_prices

    # Account equity from paper trader or default
    account_equity = 100.0
    if paper_trader is not None:
        try:
            from trader import PaperTrader
            prices = last_prices or {}
            account_equity = paper_trader.get_total_capital(prices)
        except Exception:
            pass

    for setup in ranked:
        symbol = setup.get("_symbol")
        if not symbol:
            continue
        try:
            result = execute_setup(
                symbol=symbol,
                setup=setup,
                account_equity=account_equity,
                position_manager=position_manager,
                paper_trader=paper_trader,
            )
            if result.get("success"):
                stats["executed"] += 1
                log_trade_entry(
                    symbol=result["symbol"],
                    direction=result.get("direction", "LONG"),
                    entry=result["entry"],
                    sl=result["stop_loss"],
                    tp=result["take_profit"],
                    amount_usdt=result["amount_usdt"],
                    quantity=result["quantity"],
                    score=setup.get("score", 0),
                )
                _log("ENTREE {} {} @ {:.4f} | Marge: {:.2f} USDT | SL: {:.4f} | TP: {:.4f} | Score {}".format(
                    result.get("direction", "LONG"), symbol, result["entry"], result["amount_usdt"],
                    result["stop_loss"], result["take_profit"], setup.get("score", 0)), "TRADE")
                stats["setups"].append({"symbol": symbol, "direction": setup.get("direction", "LONG"), "score": setup.get("score"), "entry": result["entry"]})
            else:
                reason = result.get("reason", "execute failed")
                log_setup_rejected(symbol, reason)
                _log("{} non execute: {}".format(symbol, reason), "WARN")
        except Exception as e:
            stats["errors"].append("{} execute: {}".format(symbol, str(e)))

    log_scan_done(stats["candidates"], stats["passed"], stats["executed"])
    return stats


def run_sniper_loop(
    paper_trader=None,
    interval_sec: int = None,
):
    """
    Infinite loop: run_sniper_cycle every interval_sec (default from config).
    """
    if interval_sec is None:
        interval_sec = cfg.SCAN_INTERVAL_SEC
    position_manager = PositionManager()

    while True:
        try:
            run_sniper_cycle(paper_trader=paper_trader, position_manager=position_manager)
        except Exception as e:
            print("[SNIPER ERROR]", str(e))
        time.sleep(interval_sec)


if __name__ == "__main__":
    print("Crypto Setup Sniper — starting (paper trading)...")
    try:
        from trader import PaperTrader
        _trader = PaperTrader(initial_balance=100)
        run_sniper_loop(paper_trader=_trader)
    except ImportError:
        run_sniper_loop(paper_trader=None)
