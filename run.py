#!/usr/bin/env python3
"""
Point d'entrée — Setup Sniper uniquement (paper trading).
Scan Binance, détection setups multi-filtre, score >= 7, top 3 positions.
"""

import sys
import os
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == '__main__':
    from main import app, run_loop

    env = os.environ.get('ENV', 'development').lower()
    port = int(os.environ.get('PORT', 8080))
    scan_interval = int(os.environ.get('SCAN_INTERVAL', '60'))

    scanner_thread = threading.Thread(target=run_loop, daemon=True)
    scanner_thread.start()

    mode = 'PRODUCTION' if env == 'production' else 'PAPER TRADING'
    print()
    print("  " + "=" * 56)
    print("  RICHESSE CRYPTO — SETUP SNIPER")
    print("  " + "=" * 56)
    print("  Mode          " + mode)
    print("  Dashboard     http://localhost:{}  (Ctrl+C pour arreter)".format(port))
    print()
    print("  Setup Sniper — multi-filtre, score>=7, top 3")
    print("    Timeframe 15m | Scan {} s | Risk 1% | SL ATR | TP 2:1".format(scan_interval))
    print("    Binance USDT | Vol 24h>20M | Max 5 positions")
    print("  " + "=" * 56)
    print()

    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
