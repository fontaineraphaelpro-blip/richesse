"""
Module pour le serveur web Flask.
"""

from flask import Flask, render_template_string
from typing import List, Dict
from datetime import datetime


def create_app(opportunities: List[Dict]) -> Flask:
    """
    Crée et configure l'application Flask.
    
    Args:
        opportunities: Liste des opportunités à afficher
    
    Returns:
        Application Flask configurée
    """
    app = Flask(__name__)
    
    # Template HTML
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Crypto Signal Scanner</title>
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
                max-width: 1200px;
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
                font-size: 2.5em;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 10px;
            }
            .last-update {
                color: #666;
                font-size: 0.9em;
                margin-top: 10px;
            }
            .main-content {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
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
                font-size: 1.2em;
                color: #667eea;
            }
            .score {
                font-weight: bold;
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
            .footer {
                text-align: center;
                margin-top: 30px;
                padding: 20px;
                color: white;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Crypto Signal Scanner</h1>
                <p>Top 10 Opportunités Crypto</p>
                <div class="last-update">
                    Dernière mise à jour: {{ last_update }}
                </div>
            </div>

            <div class="main-content">
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Pair</th>
                            <th>Score</th>
                            <th>Trend</th>
                            <th>RSI</th>
                            <th>Signal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for opp in opportunities %}
                        <tr>
                            <td class="rank">#{{ opp.rank }}</td>
                            <td><strong>{{ opp.pair }}</strong></td>
                            <td>
                                <span class="score {% if opp.score >= 80 %}score-high{% elif opp.score >= 60 %}score-medium{% else %}score-low{% endif %}">
                                    {{ opp.score }}
                                </span>
                            </td>
                            <td class="{% if opp.trend == 'Bullish' %}trend-bullish{% else %}trend-bearish{% endif %}">
                                {{ opp.trend }}
                            </td>
                            <td>{{ "%.1f"|format(opp.rsi) if opp.rsi else "N/A" }}</td>
                            <td>{{ opp.signal }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <div class="footer">
                <p><strong>⚠️ Avertissement:</strong> Ce scanner fournit des indications statistiques, pas des conseils financiers.</p>
                <p>Ne pas utiliser pour des ordres automatiques. Toujours faire vos propres recherches (DYOR).</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    @app.route('/')
    def home():
        """Page d'accueil avec le tableau des opportunités."""
        last_update = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        return render_template_string(HTML_TEMPLATE, opportunities=opportunities, last_update=last_update)
    
    @app.route('/health')
    def health():
        """Route de santé."""
        return {'status': 'ok', 'opportunities_count': len(opportunities)}, 200
    
    return app



