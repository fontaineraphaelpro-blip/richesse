# Crypto Setup Sniper

High-probability multi-filter strategy on Binance: **low trade frequency, high-quality entries**.

## Strategy Summary

- **Markets**: Binance USDT pairs, 24h volume > 20M USD (fetched dynamically).
- **Timeframes**: Primary 15m, higher filter 1h. Signals evaluated **at candle close**.
- **BTC regime**: Alt longs only when BTC is bullish (close > EMA200, RSI(14) > 50).
- **Filters**: Trend (EMA50 > EMA200, price > EMA50, ADX > 20), pullback (low touches EMA20, close > EMA50, &lt; 3% from EMA50), volatility contraction (ATR5 &lt; ATR20), momentum breakout (RSI > 55, bullish close, close > prev high, volume > VolMA20), volume spike/accumulation, relative strength vs BTC, anti–fake breakout (body &gt; 60% range, close above 5–20 high, volume spike).
- **Scoring**: Trade only if **score ≥ 7** (max 10). Rank by score, trend strength, relative strength, volume; take **top N** (default 3).
- **Entry**: Breakout of previous candle high (market or stop slightly above).
- **Stop loss**: ATR(14) × 1.5 below entry.
- **Take profit**: 2:1 RR; optional trailing after 1R.
- **Risk**: 1% per trade, max 5 positions, one per asset, cooldown per asset after close.

## Modules

| Module | Role |
|--------|------|
| `config` | All parameters (thresholds, scores, risk). |
| `liquidity_filter` | Fetch Binance USDT pairs with 24h volume &gt; 20M. |
| `market_scanner` | Fetch OHLCV for primary + higher TF in parallel. |
| `btc_regime` | BTC trend: close &gt; EMA200 and RSI(14) &gt; 50. |
| `indicator_engine` | EMAs 20/50/200, ATR 5/20/14, RSI, ADX, volume. |
| `setup_detector` | Trend, pullback, volatility, momentum, volume, relative strength, anti-fake. |
| `scoring_engine` | Points per filter; `passed` if score ≥ 7. |
| `ranking_engine` | Rank by score, ADX, relative strength, volume; return top N. |
| `risk_manager` | SL/TP, position size (1% risk), max trades, cooldown. |
| `position_manager` | Track open positions and cooldowns. |
| `trade_executor` | Place long at breakout (paper or live). |
| `logging_system` | Log setups, scores, entries, exits. |
| `run_sniper` | Scan loop: scan → detect → score → rank → execute. |

## Run

- **One cycle (dry or with PaperTrader):**
  ```python
  from sniper.run_sniper import run_sniper_cycle
  from sniper.position_manager import PositionManager
  stats = run_sniper_cycle(paper_trader=my_trader, position_manager=PositionManager())
  ```

- **Infinite loop (paper):**
  ```bash
  python -m src.sniper.run_sniper
  ```

- **Backtest (signals only):**
  ```bash
  python -m src.backtest_sniper --symbols 30 --limit 500
  ```

## Backtest

Signal logic is separated from execution: `backtest_sniper.py` uses the same `detect_setup` and `score_setup` as the live/paper loop, so you can backtest the strategy without executing orders.
