"""
Module pour récupérer les principales paires crypto USDT.
"""

from typing import List


def get_top_usdt_pairs(limit: int = 50) -> List[str]:
    """
    Retourne les principales paires crypto USDT.
    
    Args:
        limit: Nombre de paires à retourner (défaut: 50)
    
    Returns:
        Liste des symboles de paires (ex: ['BTCUSDT', 'ETHUSDT', ...])
    """
    # Liste des principales cryptos par capitalisation (excluant stablecoins)
    top_pairs = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
        'ADAUSDT', 'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'AVAXUSDT',
        'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 'ETCUSDT',
        'XLMUSDT', 'ALGOUSDT', 'VETUSDT', 'ICPUSDT', 'FILUSDT',
        '', 'EOSUSDT', 'AAVEUSDT', 'THETAUSDT', 'SANDUSDT',
        'MANAUSDT', 'AXSUSDT', 'NEARUSDT', 'FTMUSDT', 'GRTUSDT',
        'HBARUSDT', 'EGLDUSDT', 'ZECUSDT', 'CHZUSDT', 'ENJUSDT',
        'BATUSDT', 'ZILUSDT', 'IOTAUSDT', 'ONTUSDT', 'QTUMUSDT',
        'WAVESUSDT', 'OMGUSDT', 'SNXUSDT', 'MKRUSDT', 'COMPUSDT',
        'YFIUSDT', 'SUSHIUSDT', 'CRVUSDT', '1INCHUSDT', 'RENUSDT',
        'LUNAUSDT', 'USTCUSDT', 'LUNCUSDT', 'APTUSDT', 'ARBUSDT'
    ]
    
    selected = top_pairs[:limit]
    print(f"✅ {len(selected)} paires sélectionnées")
    return selected
