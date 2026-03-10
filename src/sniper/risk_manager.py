"""
Risk manager: 1% risk per trade, ATR-based SL, 2:1 TP, max positions, cooldown.
"""

from typing import Dict, Optional, Tuple
from . import config as cfg


def compute_stop_loss(
    entry_price: float,
    atr14: float,
    direction: str = "LONG",
) -> float:
    """
    ATR-based: stop_loss = entry - ATR(14) * 1.5 for LONG.
    For SHORT: stop_loss = entry + ATR(14) * 1.5.
    """
    if atr14 is None or atr14 <= 0:
        atr14 = entry_price * 0.02  # fallback 2%
    dist = atr14 * cfg.SL_ATR_MULT
    if direction.upper() == "LONG":
        return entry_price - dist
    return entry_price + dist


def compute_take_profit(
    entry_price: float,
    stop_loss: float,
    direction: str = "LONG",
    rr: float = None,
) -> float:
    """
    take_profit = entry + (entry - stop_loss) * rr for LONG (default rr=2).
    """
    if rr is None:
        rr = cfg.TAKE_PROFIT_RR
    risk = abs(entry_price - stop_loss)
    if direction.upper() == "LONG":
        return entry_price + risk * rr
    return entry_price - risk * rr


def position_size_usdt(
    account_equity: float,
    entry_price: float,
    stop_loss_price: float,
    risk_pct: float = None,
) -> Tuple[float, float]:
    """
    position_size = account_risk / (entry_price - stop_loss) in units of quote (USDT).
    account_risk = equity * risk_pct.
    Returns (position_size_usdt, quantity).
    """
    if risk_pct is None:
        risk_pct = cfg.RISK_PCT_PER_TRADE
    risk_amount = account_equity * risk_pct
    sl_distance = abs(entry_price - stop_loss_price)
    if sl_distance <= 0:
        return 0.0, 0.0
    # For spot/futures: risk_amount = position_size * (sl_distance/entry_price) approx for small %
    # So position_size = risk_amount / (sl_distance / entry_price) = risk_amount * entry_price / sl_distance
    position_usdt = risk_amount * entry_price / sl_distance
    quantity = position_usdt / entry_price
    return position_usdt, quantity


def can_open_new_trade(
    open_positions_count: int,
    symbol: str = None,
    cooldown_map: Dict[str, float] = None,
) -> Tuple[bool, str]:
    """
    Check max simultaneous trades and per-asset cooldown.
    cooldown_map: symbol -> timestamp of last close (to enforce COOLDOWN_MINUTES_PER_ASSET).
    """
    if open_positions_count >= cfg.MAX_SIMULTANEOUS_TRADES:
        return False, "Max simultaneous trades ({}) reached".format(cfg.MAX_SIMULTANEOUS_TRADES)
    if not symbol or not cfg.ONE_TRADE_PER_ASSET:
        return True, "OK"
    if cooldown_map is None:
        return True, "OK"
    import time
    last_close = cooldown_map.get(symbol)
    if last_close is None:
        return True, "OK"
    elapsed = (time.time() - last_close) / 60.0
    if elapsed < cfg.COOLDOWN_MINUTES_PER_ASSET:
        return False, "Cooldown {} min remaining for {}".format(
            int(cfg.COOLDOWN_MINUTES_PER_ASSET - elapsed), symbol
        )
    return True, "OK"
