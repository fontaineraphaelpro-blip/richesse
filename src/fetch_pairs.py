"""
Module pour récupérer les principales paires USDT sur Binance.
Exclut les stablecoins et retourne les 50 principales par volume.
"""

from binance.client import Client
from typing import List


# Liste des stablecoins à exclure
STABLECOINS = {'USDC', 'BUSD', 'TUSD', 'USDP', 'USDD', 'DAI', 'FDUSD', 'PYUSD'}


def get_top_usdt_pairs(client: Client, limit: int = 50) -> List[str]:
    """
    Récupère les principales paires USDT sur Binance.
    
    Args:
        client: Instance du client Binance
        limit: Nombre de paires à retourner (défaut: 50)
    
    Returns:
        Liste des symboles de paires (ex: ['BTCUSDT', 'ETHUSDT', ...])
    """
    try:
        # Récupérer toutes les paires de trading avec gestion d'erreur
        try:
            ticker_24h = client.get_ticker()
        except Exception as api_error:
            print(f"⚠️ Erreur API Binance lors de la récupération des paires: {api_error}")
            # Retourner la liste de fallback
            raise api_error
        
        # Filtrer les paires USDT et exclure les stablecoins
        usdt_pairs = []
        for ticker in ticker_24h:
            symbol = ticker['symbol']
            
            # Vérifier que c'est une paire USDT
            if not symbol.endswith('USDT'):
                continue
            
            # Extraire la base (ex: BTC de BTCUSDT)
            base = symbol.replace('USDT', '')
            
            # Exclure les stablecoins
            if base in STABLECOINS:
                continue
            
            # Ajouter avec le volume 24h pour trier
            usdt_pairs.append({
                'symbol': symbol,
                'volume': float(ticker['quoteVolume'])  # Volume en USDT
            })
        
        # Trier par volume décroissant et prendre les top N
        usdt_pairs.sort(key=lambda x: x['volume'], reverse=True)
        top_pairs = [pair['symbol'] for pair in usdt_pairs[:limit]]
        
        print(f"✅ {len(top_pairs)} paires USDT récupérées (excluant stablecoins)")
        return top_pairs
    
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des paires: {e}")
        # Fallback: liste de paires populaires si l'API échoue
        fallback_pairs = [
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
        print(f"⚠️ Utilisation de la liste de fallback ({len(fallback_pairs)} paires)")
        return fallback_pairs[:limit]

