"""
Position manager: track open positions, one trade per asset, cooldown after close.
Designed to work with the existing PaperTrader or a simple in-memory state.
"""

import time
from typing import Dict, List, Optional
from datetime import datetime
from . import config as cfg


class PositionManager:
    """
    Tracks open positions and cooldowns for the sniper.
    Can delegate actual order/balance to PaperTrader.
    """

    def __init__(self):
        self._positions: Dict[str, Dict] = {}  # symbol -> position info
        self._last_close_timestamp: Dict[str, float] = {}  # symbol -> epoch sec when position closed

    def open_positions_count(self) -> int:
        return len(self._positions)

    def has_position(self, symbol: str) -> bool:
        return symbol in self._positions

    def get_open_symbols(self) -> List[str]:
        return list(self._positions.keys())

    def add_position(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        quantity: float,
        amount_usdt: float,
        metadata: Dict = None,
    ):
        if cfg.ONE_TRADE_PER_ASSET and symbol in self._positions:
            return False
        self._positions[symbol] = {
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "quantity": quantity,
            "amount_usdt": amount_usdt,
            "opened_at": datetime.now(),
            "metadata": metadata or {},
        }
        return True

    def remove_position(self, symbol: str):
        if symbol in self._positions:
            del self._positions[symbol]
        self._last_close_timestamp[symbol] = time.time()

    def is_in_cooldown(self, symbol: str) -> bool:
        ts = self._last_close_timestamp.get(symbol)
        if ts is None:
            return False
        elapsed_min = (time.time() - ts) / 60.0
        if elapsed_min >= cfg.COOLDOWN_MINUTES_PER_ASSET:
            del self._last_close_timestamp[symbol]
            return False
        return True

    def cooldown_remaining_minutes(self, symbol: str) -> float:
        ts = self._last_close_timestamp.get(symbol)
        if ts is None:
            return 0.0
        elapsed = (time.time() - ts) / 60.0
        return max(0.0, cfg.COOLDOWN_MINUTES_PER_ASSET - elapsed)

    def get_cooldown_timestamps(self) -> Dict[str, float]:
        """Return symbol -> last close timestamp (epoch sec) for risk_manager.can_open_new_trade."""
        return dict(self._last_close_timestamp)

    def get_position(self, symbol: str) -> Optional[Dict]:
        return self._positions.get(symbol)
