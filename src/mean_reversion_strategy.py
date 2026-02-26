# -*- coding: utf-8 -*-
"""
Strategie Mean Reversion RSI/Bollinger - Contrarian.
LONG: RSI oversold (<30) + prix proche bande inferieure BB.
SHORT: RSI overbought (>70) + prix proche bande superieure BB.
Objectif: 60-70% WR, rentable en marches range.
"""


def signal_long_oversold(indicators, volume_ratio_min=1.2) -> bool:
    """LONG quand RSI oversold + confirmation BB."""
    rsi = indicators.get('rsi14')
    bb_pct = indicators.get('bb_percent')  # 0=lower, 1=upper
    vol_r = indicators.get('volume_ratio')
    if rsi is None or bb_pct is None or vol_r is None:
        return False
    if vol_r < volume_ratio_min:
        return False
    # RSI oversold (< 35) + prix dans zone basse BB (< 0.3)
    return rsi < 35 and bb_pct < 0.30


def signal_short_overbought(indicators, volume_ratio_min=1.2) -> bool:
    """SHORT quand RSI overbought + confirmation BB."""
    rsi = indicators.get('rsi14')
    bb_pct = indicators.get('bb_percent')
    vol_r = indicators.get('volume_ratio')
    if rsi is None or bb_pct is None or vol_r is None:
        return False
    if vol_r < volume_ratio_min:
        return False
    return rsi > 65 and bb_pct > 0.70


def compute_sl_tp_mean_reversion(price, indicators, direction, sl_pct=0.8, tp_pct=1.0):
    """SL/TP serres pour scalping mean reversion."""
    if price is None or price <= 0:
        return None, None
    atr_pct = indicators.get('atr_percent') or 0.6
    sl_eff = max(0.4, min(0.9, atr_pct * 0.8))   # SL serre
    tp_eff = max(0.5, min(1.2, sl_eff * 1.3))     # R:R 1.3:1
    if direction == 'LONG':
        sl = price * (1 - sl_eff / 100)
        tp = price * (1 + tp_eff / 100)
    else:
        sl = price * (1 + sl_eff / 100)
        tp = price * (1 - tp_eff / 100)
    return sl, tp
