# Richesse Crypto — Setup Sniper

Un seul bot : **Setup Sniper** (stratégie multi-filtre sur Binance). Lancé par `run.py`, il scanne les paires USDT, détecte des setups haute probabilité et n’ouvre que les meilleurs (score ≥ 7, top 3).

## Setup Sniper

- **Stratégie :** tendance + pullback + contraction de volatilité + breakout momentum + confirmation BTC + force relative vs BTC + volume + anti faux breakout. Score sur 10, trade uniquement si **score ≥ 7**.
- **Timeframe :** 15m (filtre 1h). Signaux évalués **à la clôture** de la bougie.
- **Marchés :** Binance USDT, volume 24h > 20 M USD (paires récupérées via API).
- **BTC :** longs alts uniquement si BTC haussier (close > EMA200, RSI(14) > 50).
- **Entrée :** breakout du plus haut de la bougie précédente (LONG).
- **SL :** ATR(14) × 1,5 sous l’entrée.
- **TP :** ratio 2:1 (TP = entrée + (entrée − SL) × 2).
- **Risque :** 1 % du capital par trade, max 5 positions, 1 par actif, cooldown après fermeture.

Configuration détaillée dans `src/sniper/config.py`. Logique dans `src/sniper/` (market_scanner, setup_detector, scoring_engine, ranking_engine, trade_executor, risk_manager, etc.).

## Données

- Données **réelles** Binance (OHLCV) via API publique.
- Paires : liste dynamique (volume 24h > 20 M USD).

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
python run.py
```

- **Dashboard :** http://localhost:8080 (capital, positions, opportunités Sniper, journal, historique).

### Backtest (signaux uniquement)

```bash
python -m src.backtest_sniper --symbols 30 --limit 500
```

### Production

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 1 wsgi:application
```

**Variables d’environnement (optionnel) :**

| Variable | Défaut | Description |
|----------|--------|-------------|
| `PORT` | 8080 | Port du serveur |
| `ENV` | development | `production` pour les logs |
| `PAPER_TRADING` | true | Simulation, pas d’ordres réels |
| `SCAN_INTERVAL` | 60 | Secondes entre chaque scan |
| `RESET_ON_START` | 1 | 0 = garder le portefeuille paper |

**Health check :** `GET /health` → 200 et `{"status":"ok", ...}`.

## Structure (fichiers principaux)

```
src/
├── main.py              # App Flask + run_loop (Setup Sniper)
├── sniper/              # Setup Sniper
│   ├── config.py        # Seuils, scores, risk
│   ├── market_scanner.py
│   ├── setup_detector.py
│   ├── scoring_engine.py
│   ├── ranking_engine.py
│   ├── trade_executor.py
│   ├── risk_manager.py
│   ├── position_manager.py
│   └── run_sniper.py    # Cycle scan → detect → score → rank → execute
├── backtest_sniper.py   # Backtest signaux (même logique que le bot)
├── data_fetcher.py      # OHLCV Binance
├── indicators.py        # RSI, EMA, ATR, ADX, etc.
├── trader.py            # Paper trading (SL/TP, trailing, partial TP)
└── minimal_dashboard.py # Dashboard
run.py                   # python run.py
wsgi.py                  # Gunicorn
```

## Avertissement

Indications statistiques, pas des conseils financiers. Ne pas utiliser pour des ordres automatiques. DYOR.
