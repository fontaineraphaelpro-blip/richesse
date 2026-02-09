"""
Module pour récupérer les principales paires crypto USDT.
Utilise une liste prédéfinie des principales cryptos.
"""

from typing import List


def get_top_usdt_pairs(limit: int = 20) -> List[str]:
    """
    Retourne les principales paires crypto USDT.
    
    Args:
        limit: Nombre de paires à retourner (défaut: 20)
    
    Returns:
        Liste des symboles de paires (ex: ['BTCUSDT', 'ETHUSDT', ...])
    """
    # Liste des principales cryptos par capitalisation
    top_pairs = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
        'ADAUSDT', 'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'AVAXUSDT',
        'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 'ETCUSDT',
        'XLMUSDT', 'ALGOUSDT', 'VETUSDT', 'ICPUSDT', 'FILUSDT',
        'TRXUSDT', 'EOSUSDT', 'AAVEUSDT', 'THETAUSDT', 'SANDUSDT',
        'MANAUSDT', 'AXSUSDT', 'NEARUSDT', 'FTMUSDT', 'GRTUSDT',
        'HBARUSDT', 'EGLDUSDT', 'ZECUSDT', 'CHZUSDT', 'ENJUSDT',
        'BATUSDT', 'ZILUSDT', 'IOTAUSDT', 'ONTUSDT', 'QTUMUSDT',
        'WAVESUSDT', 'OMGUSDT', 'SNXUSDT', 'MKRUSDT', 'COMPUSDT',
        'YFIUSDT', 'SUSHIUSDT', 'CRVUSDT', '1INCHUSDT', 'RENUSDT'
    ]
    
    selected = top_pairs[:limit]
    print(f"✅ {len(selected)} paires sélectionnées")
    return selected

