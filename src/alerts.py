"""
Module pour envoyer des alertes Telegram en temps réel.
"""

import os
import requests
from typing import Dict, List
from datetime import datetime


def send_telegram_message(token: str, chat_id: str, message: str) -> bool:
    """
    Envoie un message Telegram.
    
    Args:
        token: Token du bot Telegram (TELEGRAM_TOKEN)
        chat_id: ID du chat Telegram (TELEGRAM_CHAT_ID)
        message: Message à envoyer
    
    Returns:
        True si succès, False sinon
    """
    if not token or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi Telegram: {e}")
        return False


def format_opportunity_message(opportunity: Dict) -> str:
    """
    Formate un message Telegram pour une opportunité.
    
    Args:
        opportunity: Dictionnaire avec les données de l'opportunité
    
    Returns:
        Message formaté en HTML
    """
    pair = opportunity.get('pair', 'N/A')
    score = opportunity.get('score', 0)
    trend = opportunity.get('trend', 'N/A')
    rsi = opportunity.get('rsi', None)
    price = opportunity.get('price', None)
    signal = opportunity.get('signal', 'N/A')
    volume_ratio = opportunity.get('volume_ratio', None)
    trend_confirmation = opportunity.get('trend_confirmation', 'N/A')
    
    # Emoji selon le score
    if score >= 85:
        emoji = "🔥"
    elif score >= 70:
        emoji = "⭐"
    else:
        emoji = "📊"
    
    rsi_str = f"{rsi:.1f}" if rsi else 'N/A'
    price_str = f"${price:.8f}" if price else 'N/A'
    vol_ratio_str = f"{volume_ratio:.2f}x" if volume_ratio else 'N/A'
    
    message = f"""
{emoji} <b>Nouvelle Opportunité Crypto</b>

<b>Pair:</b> {pair}
<b>Score:</b> {score}/100
<b>Trend:</b> {trend}
<b>RSI:</b> {rsi_str}
<b>Prix:</b> {price_str}
<b>Signal:</b> {signal}
<b>Volume Ratio:</b> {vol_ratio_str}
<b>Confirmation:</b> {trend_confirmation}

⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

⚠️ <i>Ceci est une indication statistique, pas un conseil financier. DYOR.</i>
"""
    return message.strip()


def check_and_send_alerts(opportunities: List[Dict], min_score: int = 85) -> int:
    """
    Vérifie les opportunités et envoie des alertes Telegram pour celles avec score > min_score.
    
    Args:
        opportunities: Liste des opportunités
        min_score: Score minimum pour envoyer une alerte (défaut: 85)
    
    Returns:
        Nombre d'alertes envoyées
    """
    # Récupérer les variables d'environnement
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("ℹ️ Alertes Telegram désactivées (TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID non configurés)")
        return 0
    
    alerts_sent = 0
    
    for opp in opportunities:
        score = opp.get('score', 0)
        
        if score >= min_score:
            message = format_opportunity_message(opp)
            success = send_telegram_message(token, chat_id, message)
            
            if success:
                alerts_sent += 1
                print(f"✅ Alerte Telegram envoyée pour {opp.get('pair')} (Score: {score})")
            else:
                print(f"❌ Échec envoi alerte pour {opp.get('pair')}")
    
    return alerts_sent


def send_summary_alert(opportunities: List[Dict], total_analyzed: int) -> bool:
    """
    Envoie un résumé des meilleures opportunités.
    
    Args:
        opportunities: Liste des opportunités (Top 10)
        total_analyzed: Nombre total de paires analysées
    
    Returns:
        True si succès, False sinon
    """
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        return False
    
    # Formater le résumé
    top_3 = opportunities[:3]
    
    message = f"""
📊 <b>Résumé Scan Crypto</b>

<b>Paires analysées:</b> {total_analyzed}
<b>Top 3 opportunités:</b>

"""
    
    for i, opp in enumerate(top_3, 1):
        pair = opp.get('pair', 'N/A')
        score = opp.get('score', 0)
        message += f"{i}. {pair} - Score: {score}/100\n"
    
    message += f"\n⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    
    return send_telegram_message(token, chat_id, message)

