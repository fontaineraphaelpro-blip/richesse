# Crypto Signal Scanner Web

Scanner automatique de cryptomonnaies qui détecte les meilleures opportunités selon des critères techniques et affiche les résultats dans une page web.

## 🎯 Fonctionnalités

- Scanner automatique de 50 principales paires USDT
- Génération de données OHLCV réalistes (libres de droit, sans API)
- Calcul d'indicateurs techniques (SMA20, SMA50, RSI14)
- Détection de support
- Scoring d'opportunités (0-100)
- Affichage web interactif avec actualisation automatique

## 📊 Données

Le projet utilise des données de démonstration générées localement, basées sur des prix de référence réalistes. Aucune API externe n'est nécessaire - toutes les données sont libres de droit et générées en local.

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Utilisation

```bash
python src/main.py
```

Le serveur web sera accessible sur `http://localhost:5000`

## 📁 Structure

```
/crypto_signal_scanner_web
├── requirements.txt
├── README.md
├── Procfile
└── src/
    ├── fetch_pairs.py      # Récupération des paires USDT
    ├── data_fetcher.py    # Récupération des données OHLCV
    ├── indicators.py      # Calcul des indicateurs techniques
    ├── support.py          # Détection du support
    ├── scorer.py          # Calcul du score d'opportunité
    ├── web_server.py      # Serveur Flask pour la page web
    └── main.py            # Script principal
```

## ⚠️ Avertissement

Ce scanner fournit des indications statistiques, pas des conseils financiers. Ne pas utiliser pour des ordres automatiques. Toujours faire vos propres recherches (DYOR).
