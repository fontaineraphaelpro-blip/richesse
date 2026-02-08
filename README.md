# 🚀 Crypto Signal Scanner

Scanner automatique de cryptomonnaies sur Binance qui détecte les meilleures opportunités d'investissement selon des critères techniques.

## 📋 Description

Ce projet scanne automatiquement les 50 principales paires USDT sur Binance, calcule des indicateurs techniques (SMA, RSI, Volume, Support), et génère un classement des meilleures opportunités avec un score de 0 à 100.

**⚠️ Important:** Ce système ne prédit pas le futur. Il fournit seulement des indications statistiques ("Top opportunités"), pas des ordres automatiques "BUY NOW". Toujours faire vos propres recherches (DYOR).

## ✨ Fonctionnalités

- ✅ Scanner multi-coins (50 principales paires USDT)
- ✅ Exclusion automatique des stablecoins
- ✅ Calcul d'indicateurs techniques (SMA20, SMA50, RSI14, Volume)
- ✅ Détection de niveaux de support
- ✅ Scoring d'opportunité (0-100) avec critères multiples
- ✅ Génération de rapport HTML lisible
- ✅ Boucle continue pour fonctionnement 24/7

## 🛠️ Installation

### Prérequis

- Python 3.10 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes

1. **Cloner ou télécharger le projet**

2. **Installer les dépendances:**
```bash
pip install -r requirements.txt
```

## 🚀 Utilisation

### Lancer le scanner

```bash
python src/main.py
```

Le script va:
1. Récupérer les 50 principales paires USDT
2. Télécharger les données OHLCV (1H, 200 bougies)
3. Calculer les indicateurs techniques
4. Générer un classement Top 10
5. Créer un fichier `report.html`
6. Attendre 1 heure et recommencer

### Arrêter le scanner

Appuyez sur `Ctrl+C` pour arrêter la boucle.

## 📊 Critères de Scoring

Le score d'opportunité (0-100) est calculé selon:

- **Trend bullish** (SMA20 > SMA50) → +30 points
- **RSI favorable** (entre 35 et 50) → +25 points
- **Prix proche support** (<2%) → +25 points
- **Volume élevé** (>1.5× volume moyen) → +20 points

## 📁 Structure du Projet

```
crypto_signal_scanner/
├── requirements.txt          # Dépendances Python
├── README.md                 # Documentation
├── Procfile                  # Configuration Railway
└── src/
    ├── fetch_pairs.py        # Récupération des paires USDT
    ├── data_fetcher.py       # Récupération données OHLCV
    ├── indicators.py         # Calcul indicateurs techniques
    ├── support.py            # Détection des supports
    ├── scorer.py             # Calcul des scores
    ├── html_report.py        # Génération rapport HTML
    └── main.py               # Script principal
```

## 🚂 Déploiement sur Railway

### 1. Créer un compte Railway

Allez sur [railway.app](https://railway.app) et créez un compte.

### 2. Créer un nouveau projet

- Cliquez sur "New Project"
- Connectez votre dépôt GitHub ou uploadez les fichiers

### 3. Configuration

Le fichier `Procfile` est déjà configuré:
```
worker: python src/main.py
```

Railway détectera automatiquement le Procfile et lancera le worker.

### 4. Variables d'environnement (optionnel)

Si vous avez des limites de rate avec l'API Binance publique, vous pouvez ajouter vos clés API dans Railway:

- `BINANCE_API_KEY` (optionnel)
- `BINANCE_API_SECRET` (optionnel)

Le script fonctionne sans clés API pour les données publiques.

### 5. Déployer

Railway déploiera automatiquement votre application. Le worker tournera en continu et mettra à jour les résultats toutes les heures.

## 📄 Fichiers Générés

- `report.html`: Rapport HTML avec le Top 10 des opportunités, mis à jour toutes les heures

## 🔮 Améliorations Futures

- 📱 Alertes Telegram
- 📈 Backtesting
- ⏱️ Multi-timeframe (4H, 1D)
- 📊 Graphiques dans le rapport HTML
- 💾 Historique des signaux
- 🔔 Notifications par email

## ⚠️ Avertissement

Ce projet est fourni à des fins éducatives uniquement. Il ne constitue pas un conseil financier. Le trading de cryptomonnaies comporte des risques. Toujours faire vos propres recherches (DYOR) avant d'investir.

## 📝 Licence

Ce projet est libre d'utilisation pour des fins éducatives.

## 🤝 Contribution

Les contributions sont les bienvenues! N'hésitez pas à ouvrir une issue ou une pull request.

---

**Développé avec ❤️ pour la communauté crypto**

