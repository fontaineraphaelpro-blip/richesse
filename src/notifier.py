# -*- coding: utf-8 -*-
"""
Notifications: Telegram + export CSV des trades.
"""

import os
import csv
from datetime import datetime
from typing import Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_CSV_PATH = os.path.join(_PROJECT_ROOT, 'trades_export.csv')


def send_telegram(message: str) -> bool:
    """Envoie un message via le bot Telegram si configuré."""
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
    if not token or not chat_id:
        return False
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, json={'chat_id': chat_id, 'text': message[:4000], 'disable_web_page_preview': True}, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def on_trade_opened(direction: str, symbol: str, price: float, amount: float, stop_loss: float, take_profit: float):
    """Appelé à l'ouverture d'un trade."""
    msg = f"🟢 {direction} {symbol}\nPrix: {price:.4f} | Marge: ${amount:.2f}\nSL: {stop_loss:.4f} | TP: {take_profit:.4f}"
    send_telegram(msg)


def on_trade_closed(trade_data: dict):
    """Appelé à la fermeture d'un trade. Envoie Telegram + append CSV."""
    direction = trade_data.get('direction', 'N/A')
    symbol = trade_data.get('symbol', 'N/A')
    pnl = trade_data.get('pnl', 0)
    pnl_pct = trade_data.get('pnl_percent', 0)
    reason = trade_data.get('reason', '')
    emoji = "✅" if pnl > 0 else "❌"
    msg = f"{emoji} VENTE {symbol} ({reason})\nPnL: ${pnl:+.2f} ({pnl_pct:+.2f}%)"
    send_telegram(msg)
    append_trade_to_csv(trade_data)


def append_trade_to_csv(trade_data: dict):
    """Ajoute un trade fermé au fichier CSV d'export."""
    file_exists = os.path.exists(EXPORT_CSV_PATH)
    row = {
        'time': trade_data.get('time', ''),
        'type': trade_data.get('type', ''),
        'symbol': trade_data.get('symbol', ''),
        'direction': trade_data.get('direction', ''),
        'entry_price': trade_data.get('entry_price', ''),
        'exit_price': trade_data.get('price', ''),
        'amount': trade_data.get('amount', ''),
        'pnl': trade_data.get('pnl', ''),
        'pnl_percent': trade_data.get('pnl_percent', ''),
        'reason': trade_data.get('reason', ''),
    }
    try:
        with open(EXPORT_CSV_PATH, 'a', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                w.writeheader()
            w.writerow(row)
    except Exception:
        pass
