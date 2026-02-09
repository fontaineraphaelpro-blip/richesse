"""
Application web Flask pour afficher le dashboard du Crypto Signal Scanner.
"""

import json
import os
import threading
from flask import Flask, render_template_string, jsonify
from datetime import datetime

# Créer l'application Flask
app = Flask(__name__)

# Configuration pour Railway
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Chemin vers le fichier JSON des données
DATA_FILE = 'opportunities_data.json'


def load_opportunities():
    """
    Charge les données des opportunités depuis le fichier JSON.
    """
    if not os.path.exists(DATA_FILE):
        return []
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('opportunities', [])
    except Exception as e:
        print(f"Erreur lors du chargement des données: {e}")
        return []


def get_last_update_time():
    """
    Récupère l'heure de la dernière mise à jour.
    """
    if not os.path.exists(DATA_FILE):
        return None
    
    try:
        stat = os.stat(DATA_FILE)
        return datetime.fromtimestamp(stat.st_mtime)
    except:
        return None


# Template HTML pour la page d'accueil
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Signal Scanner - Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }
        .header h1 {
            font-size: 3em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .header p {
            color: #666;
            font-size: 1.2em;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-card h3 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .stat-card p {
            color: #666;
            font-size: 1.1em;
        }
        .main-content {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .last-update {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 20px;
            color: #666;
        }
        .last-update strong {
            color: #667eea;
        }
        .refresh-btn {
            display: inline-block;
            margin-top: 10px;
            padding: 10px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            text-decoration: none;
        }
        .refresh-btn:hover {
            opacity: 0.9;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 1em;
        }
        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.5px;
        }
        td {
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
        }
        tbody tr:hover {
            background: #f8f9fa;
        }
        tbody tr:nth-child(even) {
            background: #fafafa;
        }
        .rank {
            font-weight: bold;
            font-size: 1.3em;
            color: #667eea;
        }
        .score {
            font-weight: bold;
            font-size: 1.2em;
            padding: 5px 10px;
            border-radius: 5px;
            display: inline-block;
        }
        .score-high {
            background: #d4edda;
            color: #155724;
        }
        .score-medium {
            background: #fff3cd;
            color: #856404;
        }
        .score-low {
            background: #f8d7da;
            color: #721c24;
        }
        .trend-bullish {
            color: #28a745;
            font-weight: bold;
        }
        .trend-bearish {
            color: #dc3545;
            font-weight: bold;
        }
        .signal {
            font-size: 0.9em;
            color: #666;
        }
        .price {
            font-weight: bold;
            color: #333;
        }
        .no-data {
            text-align: center;
            padding: 50px;
            color: #666;
        }
        .no-data h2 {
            margin-bottom: 20px;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: white;
            font-size: 0.9em;
        }
        .footer strong {
            color: #fff;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .loading {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Crypto Signal Scanner</h1>
            <p>Dashboard des Meilleures Opportunités Crypto</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3 id="total-pairs">-</h3>
                <p>Paires Analysées</p>
            </div>
            <div class="stat-card">
                <h3 id="top-opportunities">10</h3>
                <p>Top Opportunités</p>
            </div>
            <div class="stat-card">
                <h3 id="avg-score">-</h3>
                <p>Score Moyen</p>
            </div>
            <div class="stat-card">
                <h3 id="bullish-count">-</h3>
                <p>Trends Bullish</p>
            </div>
        </div>

        <div class="main-content">
            <div class="last-update">
                <strong>Dernière mise à jour:</strong> 
                <span id="last-update-time">Chargement...</span>
                <br>
                <button class="refresh-btn" onclick="loadData(); return false;">🔄 Actualiser</button>
                <button class="refresh-btn" onclick="triggerScan(); return false;" id="scan-btn" style="margin-left: 10px; background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">🚀 Lancer le Scan</button>
                <span id="scan-status" style="margin-left: 10px; color: #28a745; font-weight: bold;"></span>
            </div>

            <div id="content">
                <div class="no-data">
                    <h2>⏳ Chargement des données...</h2>
                    <p>Veuillez patienter pendant le chargement des opportunités.</p>
                </div>
            </div>
        </div>

        <div class="footer">
            <p><strong>⚠️ Avertissement:</strong> Ce scanner fournit des indications statistiques, pas des conseils financiers.</p>
            <p>Ne pas utiliser pour des ordres automatiques. Toujours faire vos propres recherches (DYOR).</p>
        </div>
    </div>

    <script>
        function formatNumber(num) {
            if (num === null || num === undefined) return '-';
            return num.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }

        function formatPrice(price) {
            if (price === null || price === undefined) return 'N/A';
            return parseFloat(price).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 8 });
        }

        function getScoreClass(score) {
            if (score >= 70) return 'score-high';
            if (score >= 40) return 'score-medium';
            return 'score-low';
        }

        function loadData() {
            // Désactiver le bouton pendant le chargement
            const refreshBtn = document.querySelector('.refresh-btn');
            if (refreshBtn) {
                refreshBtn.classList.add('loading');
                refreshBtn.disabled = true;
            }
            
            fetch('/api/opportunities')
                .then(response => response.json())
                .then(data => {
                    const opportunities = data.opportunities || [];
                    const lastUpdate = data.last_update;

                    // Mettre à jour les stats
                    document.getElementById('total-pairs').textContent = data.total_pairs || '-';
                    document.getElementById('top-opportunities').textContent = opportunities.length;
                    document.getElementById('avg-score').textContent = data.avg_score ? data.avg_score.toFixed(1) : '-';
                    document.getElementById('bullish-count').textContent = data.bullish_count || '-';
                    
                    // Mettre à jour l'heure
                    if (lastUpdate) {
                        const date = new Date(lastUpdate);
                        document.getElementById('last-update-time').textContent = 
                            date.toLocaleString('fr-FR', { 
                                day: '2-digit', 
                                month: '2-digit', 
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                                second: '2-digit'
                            });
                    }

                    // Afficher le tableau
                    if (opportunities.length === 0) {
                        let message = '📊 Aucune donnée disponible';
                        let subMessage = 'Cliquez sur "🚀 Lancer le Scan" pour commencer l\'analyse.';
                        
                        if (isScanning) {
                            message = '⏳ Scan en cours...';
                            subMessage = 'Les données seront disponibles dans quelques instants.';
                        }
                        
                        document.getElementById('content').innerHTML = `
                            <div class="no-data">
                                <h2>${message}</h2>
                                <p>${subMessage}</p>
                            </div>
                        `;
                        return;
                    }

                    let tableHTML = `
                        <table>
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Pair</th>
                                    <th>Score</th>
                                    <th>Prix</th>
                                    <th>Trend</th>
                                    <th>RSI</th>
                                    <th>Signal</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;

                    opportunities.forEach(opp => {
                        const rsi = opp.rsi !== null && opp.rsi !== undefined ? opp.rsi.toFixed(1) : 'N/A';
                        const price = formatPrice(opp.price);
                        const scoreClass = getScoreClass(opp.score);
                        const trendClass = opp.trend === 'Bullish' ? 'trend-bullish' : 'trend-bearish';

                        tableHTML += `
                            <tr>
                                <td class="rank">#${opp.rank}</td>
                                <td><strong>${opp.pair}</strong></td>
                                <td><span class="score ${scoreClass}">${opp.score}</span></td>
                                <td class="price">$${price}</td>
                                <td class="${trendClass}">${opp.trend}</td>
                                <td>${rsi}</td>
                                <td class="signal">${opp.signal}</td>
                            </tr>
                        `;
                    });

                    tableHTML += `
                            </tbody>
                        </table>
                    `;

                    document.getElementById('content').innerHTML = tableHTML;
                })
                .catch(error => {
                    console.error('Erreur:', error);
                    document.getElementById('content').innerHTML = `
                        <div class="no-data">
                            <h2>❌ Erreur de chargement</h2>
                            <p>Impossible de charger les données. Veuillez réessayer plus tard.</p>
                        </div>
                    `;
                })
                .finally(() => {
                    // Réactiver le bouton après le chargement
                    const refreshBtn = document.querySelector('.refresh-btn');
                    if (refreshBtn) {
                        refreshBtn.classList.remove('loading');
                        refreshBtn.disabled = false;
                    }
                });
        }

        // Charger les données au chargement de la page
        loadData();

        // Actualiser automatiquement toutes les 10 secondes
        setInterval(loadData, 10000);
    </script>
</body>
</html>
"""


@app.route('/')
def home():
    """Page d'accueil du dashboard."""
    return render_template_string(HOME_TEMPLATE)


@app.route('/health')
def health():
    """Route de santé pour Railway."""
    return jsonify({
        'status': 'ok',
        'service': 'Crypto Signal Scanner Web',
        'data_file_exists': os.path.exists(DATA_FILE),
        'port': os.environ.get('PORT', 'not set')
    }), 200


@app.route('/test')
def test():
    """Route de test simple."""
    return "<h1>✅ Serveur web fonctionne!</h1><p>Le serveur Flask répond correctement.</p>", 200


@app.route('/api/opportunities')
def api_opportunities():
    """API endpoint pour récupérer les opportunités en JSON."""
    opportunities = load_opportunities()
    last_update = get_last_update_time()
    
    # Calculer les statistiques
    total_pairs = len(opportunities)
    avg_score = sum(opp.get('score', 0) for opp in opportunities) / total_pairs if total_pairs > 0 else 0
    bullish_count = sum(1 for opp in opportunities if opp.get('trend') == 'Bullish')
    
    return jsonify({
        'opportunities': opportunities,
        'last_update': last_update.isoformat() if last_update else None,
        'total_pairs': total_pairs,
        'avg_score': round(avg_score, 1),
        'bullish_count': bullish_count
    })


if __name__ == '__main__':
    # Pour Railway, utiliser le PORT de l'environnement
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Démarrage du serveur web Flask sur le port {port}")
    print(f"📱 Dashboard accessible sur http://0.0.0.0:{port}")
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"❌ Erreur au démarrage: {e}")
        import traceback
        traceback.print_exc()

