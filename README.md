# Bot trading — SHORT grandes baisses uniquement

Un seul bot principal: **SHORT grandes baisses** (lancé par `run.py`). Il n’ouvre que des positions **SHORT** quand une forte baisse est détectée sur les paires Binance. Optionnel: bot **Arbitrage** CEX/CEX dans `src/arbitrage_strategy.py`.

## Bot SHORT grandes baisses

- **Stratégie:** uniquement des SHORT sur les grandes baisses.
- **Conditions d’entrée:**  
  - Tendance baissière (momentum BEARISH, prix sous EMA21).  
  - RSI &lt; 55 ou en baisse.  
  - Dernière bougie baissière + volume suffisant.  
  - Tendance 15m aussi baissière (optionnel, configurable).
- **Paramètres** (dans `src/main.py`) :
  - `TIMEFRAME` = 15m
  - `STOP_LOSS_PCT` = 1 % (au-dessus de l’entrée)
  - `TAKE_PROFIT_PCT` = 2 % (en dessous) → R:R = 2
  - `COOLDOWN_MINUTES` = 15
  - `POSITION_PCT_BALANCE` = 20 % du solde max
  - `RISK_PCT_CAPITAL` = 1 % (risque max par trade → taille de position)
  - `TREND_1H_MUST_BEARISH` = true (confirmation tendance 1h baissière)
  - `MAX_DAILY_DRAWDOWN_PCT` = 5 % (pause si perte du jour ≥ 5 %)
  - Arrêt après 3 pertes consécutives (sur les 3 dernières ventes).
- **Rentabilité / risque :**
  - Frais simulés 0,05 % par côté (open/close) pour un paper réaliste.
  - Taille de position calculée pour risquer au max 1 % du capital par trade (levier 10x).
  - Confirmation 15m + 1h baissières pour filtrer les faux signaux.
  - Drawdown journalier : plus de nouveaux trades si perte du jour ≥ 5 % (reprise le lendemain).

La logique est dans `src/short_crash_strategy.py` et la boucle de scan dans `run_scanner()` dans `src/main.py`.

## Les 2 bots

| Bot | Fichier | Stratégie | Lancement |
|-----|---------|-----------|-----------|
| **SHORT grandes baisses** | `main.py` + `short_crash_strategy.py` | Uniquement SHORT sur fortes baisses (15m, R:R 2) | `python run.py` |
| **Arbitrage** | `arbitrage_strategy.py` | CEX/CEX si spread ≥ seuil | `python -m src.arbitrage_strategy` (après config) |

## Données

- Données **réelles** Binance (OHLCV) via API publique.
- Paires: liste dans `data_fetcher.py`.

## Installation

```bash
pip install -r requirements.txt
```

Pour le bot Arbitrage (optionnel): `pip install ccxt web3`.

## Utilisation

### Tester le scanner (mode développement)

Pour un test rapide avec **20 paires** par cycle :

```bash
set SCAN_PAIRS_LIMIT=20
python run.py
```

Sans `SCAN_PAIRS_LIMIT` (ou vide), le scanner utilise **toutes** les paires (production).

- **Dashboard:** http://localhost:8080  
- **Onglet Bot de trading:** capital, PnL, positions, journal du scanner.  
- **Onglet Bot d’arbitrage:** logs arbitrage CEX (si `ccxt` installé).

### Production

Déploiement avec **Gunicorn** (Railway, Heroku, VPS). Par défaut : scan complet, paper trading activé.

```bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:$PORT --workers 1 wsgi:application
```

**Variables d'environnement (optionnel):**

| Variable | Défaut | Description |
|----------|--------|-------------|
| `PORT` | 8080 | Port du serveur |
| `ENV` | development | `production` pour afficher le mode dans les logs |
| `PAPER_TRADING` | true | `true` = simulation, pas d'ordres réels |
| `SCAN_PAIRS_LIMIT` | (vide = toutes) | Limiter à N paires (ex: 20 pour test) |
| `SCAN_INTERVAL` | 900 | Secondes entre chaque scan (défaut 15 min, aligné TF 15m) |
| `ARBITRAGE_SYMBOL` | BTC/USDT | Paire pour le bot arbitrage |
| `ARBITRAGE_THRESHOLD_PCT` | 0.3 | Seuil de spread (%) |
| `ARBITRAGE_POLL_SEC` | 45 | Secondes entre chaque scan arbitrage |

**Health check** (load balancers, monitoring) : `GET /health` → `200` et `{"status":"ok", ...}`.

## Structure (fichiers principaux)

```
src/
├── main.py                   # App Flask + run_scanner() SHORT only
├── short_crash_strategy.py   # Signal SHORT grandes baisses + taille position
├── data_fetcher.py           # OHLCV Binance
├── indicators.py             # RSI, EMA, momentum, etc.
├── trader.py                 # Paper trading (LONG/SHORT, SL/TP)
├── dashboard_template.py     # Template HTML dashboard
├── arbitrage_strategy.py     # Bot arbitrage (optionnel)
└── ...
run.py                        # python run.py
wsgi.py                       # Gunicorn
```

## Avertissement

Indications statistiques, pas des conseils financiers. Ne pas utiliser pour des ordres automatiques. DYOR.
