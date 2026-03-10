"""
Trade executor: place market/stop order at breakout, using risk_manager for SL/TP and size.
Integrates with existing PaperTrader for paper trading.
"""

from typing import Dict, Any, Optional
import sys
import os

_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src not in sys.path:
    sys.path.insert(0, _src)

from . import config as cfg
from .risk_manager import (
    compute_stop_loss,
    compute_take_profit,
    position_size_usdt,
    can_open_new_trade,
)
from .position_manager import PositionManager


def execute_setup(
    symbol: str,
    setup: Dict[str, Any],
    account_equity: float,
    position_manager: PositionManager,
    paper_trader=None,
) -> Dict[str, Any]:
    """
    Execute LONG or SHORT entry for the given setup.
    - LONG: SL = entry - ATR(14)*1.5, TP = entry + (entry - SL)*2
    - SHORT: SL = entry + ATR(14)*1.5, TP = entry - (SL - entry)*2
    - Size: 1% risk

    Returns:
        { 'success', 'reason', 'symbol', 'direction', 'entry', 'stop_loss', 'take_profit', 'amount_usdt', 'quantity' }
    """
    direction = (setup.get("direction") or "LONG").upper()
    ind = setup.get("indicators") or {}
    entry_price = ind.get("close")
    atr14 = ind.get("atr14")
    if not entry_price or entry_price <= 0:
        return {"success": False, "reason": "No entry price", "direction": direction}

    stop_loss = compute_stop_loss(entry_price, atr14, direction)
    take_profit = compute_take_profit(entry_price, stop_loss, direction)

    pos_usdt, quantity = position_size_usdt(account_equity, entry_price, stop_loss)
    if pos_usdt <= 0 or quantity <= 0:
        return {"success": False, "reason": "Position size zero", "direction": direction}

    cooldown_ts = position_manager.get_cooldown_timestamps()
    ok, msg = can_open_new_trade(
        position_manager.open_positions_count(),
        symbol,
        cooldown_ts,
    )
    if not ok:
        return {"success": False, "reason": msg, "direction": direction}

    if position_manager.has_position(symbol):
        return {"success": False, "reason": "Already in position on {}".format(symbol), "direction": direction}

    result = {
        "success": True,
        "reason": "OK",
        "symbol": symbol,
        "direction": direction,
        "entry": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "amount_usdt": pos_usdt,
        "quantity": quantity,
    }

    if paper_trader is not None:
        try:
            if direction == "LONG":
                placed = paper_trader.place_buy_order(
                    symbol=symbol,
                    amount_usdt=pos_usdt,
                    current_price=entry_price,
                    stop_loss_price=stop_loss,
                    take_profit_price=take_profit,
                    entry_trend="SNIPER_SETUP",
                    atr_pct=(atr14 / entry_price * 100) if atr14 else None,
                )
            else:
                placed = paper_trader.place_short_order(
                    symbol=symbol,
                    amount_usdt=pos_usdt,
                    current_price=entry_price,
                    stop_loss_price=stop_loss,
                    take_profit_price=take_profit,
                    entry_trend="SNIPER_SETUP",
                    atr_pct=(atr14 / entry_price * 100) if atr14 else None,
                )
            if not placed:
                result["success"] = False
                result["reason"] = "PaperTrader refused (insufficient balance or already position)"
            else:
                position_manager.add_position(
                    symbol=symbol,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    quantity=quantity,
                    amount_usdt=pos_usdt,
                    metadata={"score": setup.get("score"), "setup": "sniper", "direction": direction},
                )
        except Exception as e:
            result["success"] = False
            result["reason"] = str(e)
    else:
        position_manager.add_position(
            symbol=symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=quantity,
            amount_usdt=pos_usdt,
            metadata={"score": setup.get("score"), "direction": direction},
        )

    return result
