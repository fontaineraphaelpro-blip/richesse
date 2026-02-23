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
  - Arrêt après 3 pertes consécutives (sur les 3 dernières ventes).

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

### Tester le scanner (recommandé pour un premier run)

Le scanner est prêt à être testé en **paper trading** avec une limite de **20 paires** par cycle pour un résultat rapide (~30–60 s par scan).

```bash
pip install -r requirements.txt
python run.py
```

- **Dashboard:** http://localhost:8080  
- **Onglet Bot de trading:** capital, PnL, positions, journal du scanner.  
- **Onglet Bot d’arbitrage:** logs arbitrage CEX (si `ccxt` installé).

Pour scanner **toutes** les paires (plus long), dans `src/main.py` mettez `SCAN_PAIRS_LIMIT = None`.

### Production (Gunicorn / Railway)

```bash
gunicorn --bind 0.0.0.0:$PORT wsgi:application
```

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
