# -*- coding: utf-8 -*-
"""
Stratégie MICRO SCALP — Objectif gain fixe par trade (ex: 1€).

Principe rentable:
  - Entrée LONG: prix proche de la bande basse de Bollinger + RSI survendu (< 30).
  - Entrée SHORT: prix proche de la bande haute + RSI suracheté (> 70).
  - Taille de position calculée pour atteindre un profit cible (€) avec un % de gain donné.
  - Stop loss et take profit en % pour un Risk/Reward >= 2 (ex: SL 0.15%, TP 0.35% → R:R ≈ 2.3).
"""


def micro_scalp_entry_long(df, indicators, volume_ratio_min=1.1):
    """
    Signal d'achat (LONG) micro scalp.

    Conditions (toutes requises):
      1. RSI < 30 (survendu).
      2. Prix proche de la bande basse de Bollinger (bb_percent <= 0.05).
      3. Volume >= volume_ratio_min × moyenne (confirmation).

    Returns:
        True si signal LONG valide, False sinon.
    """
    rsi = indicators.get('rsi14')
    if rsi is None or rsi >= 30:
        return False

    bb_percent = indicators.get('bb_percent')
    if bb_percent is None or bb_percent > 0.05:
        return False

    vol_ratio = indicators.get('volume_ratio')
    if vol_ratio is None or vol_ratio < volume_ratio_min:
        return False

    return True


def micro_scalp_entry_short(df, indicators, volume_ratio_min=1.1):
    """
    Signal de vente (SHORT) micro scalp.

    Conditions (toutes requises):
      1. RSI > 70 (suracheté).
      2. Prix proche de la bande haute de Bollinger (bb_percent >= 0.95).
      3. Volume >= volume_ratio_min × moyenne.

    Returns:
        True si signal SHORT valide, False sinon.
    """
    rsi = indicators.get('rsi14')
    if rsi is None or rsi <= 70:
        return False

    bb_percent = indicators.get('bb_percent')
    if bb_percent is None or bb_percent < 0.95:
        return False

    vol_ratio = indicators.get('volume_ratio')
    if vol_ratio is None or vol_ratio < volume_ratio_min:
        return False

    return True


def calculate_position_size(profit_target_eur, target_pct):
    """
    Calcule la taille de position (en unités de la devise) pour viser un profit fixe en €.

    Formule: taille = profit_target_eur / (target_pct / 100)
    Exemple: objectif 1€, TP 0.35% → taille = 1 / 0.0035 ≈ 285€ de position.

    Args:
        profit_target_eur: gain cible en euros (ex: 1.0).
        target_pct: take profit en % (ex: 0.35).

    Returns:
        Montant en unités (équivalent USDT pour une paire XXXUSDT).
    """
    if target_pct <= 0:
        return 0.0
    return profit_target_eur / (target_pct / 100.0)
