"""
Module pour récupérer les principales paires crypto USDT.
"""

from typing import List


def get_top_usdt_pairs(limit: int = 150) -> List[str]:
    """
    Retourne les principales paires crypto USDT (150+ paires).
    
    Args:
        limit: Nombre de paires à retourner (défaut: 150)
    
    Returns:
        Liste des symboles de paires (ex: ['BTCUSDT', 'ETHUSDT', ...])
    """
    # Liste des principales cryptos par capitalisation (excluant stablecoins et TRX)
    top_pairs = [
        # TOP 10 (Mega Cap)
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
        'ADAUSDT', 'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'AVAXUSDT',
        
        # TOP 20-50 (Large Cap)
        'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 'ETCUSDT',
        'XLMUSDT', 'ALGOUSDT', 'VETUSDT', 'ICPUSDT', 'FILUSDT',
        'EOSUSDT', 'AAVEUSDT', 'THETAUSDT', 'SANDUSDT', 'MANAUSDT',
        'AXSUSDT', 'NEARUSDT', 'FTMUSDT', 'GRTUSDT', 'HBARUSDT',
        'EGLDUSDT', 'ZECUSDT', 'CHZUSDT', 'ENJUSDT', 'BATUSDT',
        'ZILUSDT', 'IOTAUSDT', 'ONTUSDT', 'QTUMUSDT', 'WAVESUSDT',
        'OMGUSDT', 'SNXUSDT', 'MKRUSDT', 'COMPUSDT', 'YFIUSDT',
        'SUSHIUSDT', 'CRVUSDT', '1INCHUSDT', 'RENUSDT', 'LUNAUSDT',
        'USTCUSDT', 'LUNCUSDT', 'APTUSDT', 'ARBUSDT', 'OPUSDT',
        
        # TOP 50-100 (Mid Cap)
        'PEPEUSDT', 'FLOKIUSDT', 'DOGSUSDT', 'SHIBUSDT', 'SUIUSDT',
        'LDOUSDT', 'INJUSDT', 'GMUSDT', 'MNTUSDT', 'FETUSDT',
        'RDNTUSDT', 'MAGICUSDT', 'BEAMXUSDT', 'DFUSDT', 'JUPUSDT',
        'MOVEUSDT', 'SCRUSDT', 'GMXUSDT', 'CVXUSDT', 'BALLUSDT',
        'WOOUSDT', 'LQTYUSDT', 'PYTHUSDT', 'AIUSDT', 'BITUSDT',
        'TAUUSDT', 'WLDUSDT', 'WIFUSDT', 'BONKUSDT', 'XENUSDT',
        'GPTUSDT', 'COSUSDT', 'NOTUSDT', 'ONTOUSDT', 'BLZUSDT',
        'PROMUSDT', 'SPELLUSDT', 'HOOKUSDT', 'ZROUSDT', 'DEFIUSDT',
        'GTOCUSDT', 'SYNUSDT', 'LSKUSDT', 'CVOUSDT', 'JTOATUSDT',
        'SUMUSDT', 'PENDLEUSDT', 'TNSRUSDT', 'FLAMINGOBT', 'KMMUSDT',
        
        # TOP 100-150 (Small Cap Trending)
        'AXLUSDT', 'UMAUSDT', 'RAREUSDT', 'RAYUSDT', 'USHUSDT',
        'COREUSDT', 'MAVUSDT', 'MBLUSDT', 'ARUSDT', 'LTOUSDT',
        'XECUSDT', 'ALPHAUSDT', 'SLGUSDT', 'LPUSDT', 'LVSUSDT',
        'SOLOUSDT', 'ETHFIUSDT', 'CERUSDT', 'KELPUSDT', 'TURBOUSDT',
        'ZKUSDT', 'SSVUSDT', 'XAUSDT', 'NEXOUSDT', 'MTRXUSDT',
        'ARKMUSDT', 'DEXTUSDT', 'ORDIUSDT', 'RNSUSDT', 'RNDRUSDT',
        'EONUSDT', 'LARUSDT', 'LTOBT', 'MOVEUSDT', 'FXUSDT',
        'XMRUSDT', 'SKLUSDT', 'ECLIPSUSDT', 'SONICUSDT', 'JUPYTERUSDT',
        'DREAMUSDT', 'MODUSDT', 'POPUSDT', 'REXUSDT', 'METISUSDT',
        'POLYFIUSDT', 'SUPERUSDT', 'UNFIUSDT', 'TUSDT', 'DYDXUSDT'
    ]
    
    # Supprimer les doublons en cas
    top_pairs = list(dict.fromkeys(top_pairs))
    
    selected = top_pairs[:limit]
    print(f"✅ {len(selected)} paires sélectionnées (Expanded Scanner)")
    return selected
