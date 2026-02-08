"""
Module pour générer le rapport HTML des opportunités.
"""

from typing import List, Dict
from datetime import datetime


def generate_html_report(opportunities: List[Dict], output_file: str = 'report.html') -> None:
    """
    Génère un fichier HTML avec le classement des opportunités.
    
    Args:
        opportunities: Liste de dictionnaires avec les données des opportunités
        output_file: Nom du fichier HTML à générer
    """
    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Signal Scanner - Top Opportunités</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .timestamp {{
            background: #f8f9fa;
            padding: 15px;
            text-align: center;
            color: #666;
            border-bottom: 2px solid #e9ecef;
        }}
        .table-container {{
            padding: 30px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 1em;
        }}
        thead {{
            background: #667eea;
            color: white;
        }}
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.5px;
        }}
        td {{
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        tbody tr:hover {{
            background: #f8f9fa;
        }}
        tbody tr:nth-child(even) {{
            background: #fafafa;
        }}
        .rank {{
            font-weight: bold;
            font-size: 1.2em;
            color: #667eea;
        }}
        .score {{
            font-weight: bold;
            font-size: 1.1em;
        }}
        .score-high {{
            color: #28a745;
        }}
        .score-medium {{
            color: #ffc107;
        }}
        .score-low {{
            color: #dc3545;
        }}
        .trend-bullish {{
            color: #28a745;
            font-weight: bold;
        }}
        .trend-bearish {{
            color: #dc3545;
            font-weight: bold;
        }}
        .signal {{
            font-size: 0.9em;
            color: #666;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        .footer strong {{
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Crypto Signal Scanner</h1>
            <p>Top Opportunités d'Investissement</p>
        </div>
        <div class="timestamp">
            <strong>Dernière mise à jour:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Pair</th>
                        <th>Score</th>
                        <th>Trend</th>
                        <th>RSI</th>
                        <th>Volume Ratio</th>
                        <th>Trend Confirmation</th>
                        <th>Signal</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Trier par score décroissant (au cas où)
    opportunities_sorted = sorted(opportunities, key=lambda x: x.get('score', 0), reverse=True)
    
    # Ajouter les lignes du tableau
    for opp in opportunities_sorted:
        rank = opp.get('rank', 0)
        pair = opp.get('pair', 'N/A')
        score = opp.get('score', 0)
        trend = opp.get('trend', 'N/A')
        rsi = opp.get('rsi', None)
        signal = opp.get('signal', 'N/A')
        volume_ratio = opp.get('volume_ratio', None)
        trend_confirmation = opp.get('trend_confirmation', 'N/A')
        
        # Classes CSS pour le score (vert > 80, jaune 60-80, rouge < 60)
        if score >= 80:
            score_class = 'score-high'
        elif score >= 60:
            score_class = 'score-medium'
        else:
            score_class = 'score-low'
        
        # Classe pour le trend
        trend_class = 'trend-bullish' if trend == 'Bullish' else 'trend-bearish'
        
        # Format RSI
        rsi_display = f"{rsi:.1f}" if rsi is not None else "N/A"
        
        # Format volume ratio
        volume_ratio_display = f"{volume_ratio:.2f}x" if volume_ratio is not None else "N/A"
        
        html_content += f"""
                    <tr>
                        <td class="rank">#{rank}</td>
                        <td><strong>{pair}</strong></td>
                        <td class="score {score_class}">{score}</td>
                        <td class="{trend_class}">{trend}</td>
                        <td>{rsi_display}</td>
                        <td>{volume_ratio_display}</td>
                        <td>{trend_confirmation}</td>
                        <td class="signal">{signal}</td>
                    </tr>
"""
    
    html_content += """
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
    
    # Écrire le fichier
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Rapport HTML généré: {output_file}")

