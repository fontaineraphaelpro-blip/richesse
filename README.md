# Crypto Signal Scanner — Micro Scalp Bot

Scanner automatique de cryptomonnaies (Binance) qui détecte des opportunités **micro scalp** (objectif gain fixe par trade, ex: 1€) et affiche le dashboard sur le web.

## 🎯 Scanner Micro Scalp (compréhensible et rentable)

- **Objectif:** viser un gain fixe par trade (ex: 1€) avec un Risk/Reward ≥ 2.
- **Signal LONG:** RSI &lt; 30 (survendu) + prix proche de la bande basse de Bollinger + volume ≥ 1.1× la moyenne.
- **Filtres:** spread, volatilité (ATR), tendance 15m (pas d’achat si 15m baissier).
- **Paramètres principaux** (dans `src/main.py`) :
  - `PROFIT_TARGET` = 1.0 (€)
  - `SCALP_TARGET_PCT` = 0.35 % (take profit) → R:R ≈ 2.3 avec SL 0.15 %
  - `STOP_LOSS_PCT` = 0.15 %
  - `COOLDOWN_MINUTES` = 10 après chaque trade
  - Arrêt après 3 pertes consécutives.

La logique complète est dans `src/micro_scalp_strategy.py` (entrées LONG/SHORT) et la boucle de scan dans `run_scanner()` dans `src/main.py`.

## 📊 Données

- Données **réelles** Binance (OHLCV) via API publique.
- Paires: liste des principales USDT définie dans `data_fetcher.py`.

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Utilisation

### Développement local

```bash
python run.py
```

Dashboard: `http://localhost:8080` — le scanner tourne en arrière-plan (toutes les 10 s).

### Production (Gunicorn / Railway)

```bash
gunicorn --bind 0.0.0.0:$PORT wsgi:application
```

Le `Procfile` est déjà configuré ; le scanner démarre avec l’app.

## 📁 Structure (principaux fichiers)

```
src/
├── main.py                 # App Flask + run_scanner() (boucle micro scalp)
├── micro_scalp_strategy.py  # Signaux LONG/SHORT + calcul taille position
├── data_fetcher.py         # Récupération OHLCV Binance
├── indicators.py           # RSI, Bollinger, etc.
├── trader.py               # Paper trading (positions, SL/TP)
├── dashboard_template.py   # Template HTML du dashboard
└── ...
run.py                      # Point d'entrée: python run.py
wsgi.py                     # Point d'entrée Gunicorn
```

## ⚠️ Avertissement

Ce scanner fournit des indications statistiques, pas des conseils financiers. Ne pas utiliser pour des ordres automatiques. Toujours faire vos propres recherches (DYOR).
