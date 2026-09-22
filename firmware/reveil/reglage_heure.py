"""Logique metier du reglage heure (independante du materiel).

Module pur : pas d'import CircuitPython, testable sans stub ni Pico.
"""
try:
    from typing import Tuple
except ImportError:
    pass

MODES = ("NORMAL", "HEURES", "MINUTES")


def mode_suivant(mode: str) -> str:
    """Mode suivant dans le cycle NORMAL -> HEURES -> MINUTES -> NORMAL."""
    return MODES[(MODES.index(mode) + 1) % len(MODES)]


def appliquer_rotation(mode: str, heures: int, minutes: int, delta: int) -> Tuple[int, int]:
    """Applique un deplacement d'encodeur (delta) au champ actif selon 'mode'.

    Retourne le tuple (heures, minutes) mis a jour ; inchange si
    mode == "NORMAL" ou delta == 0.
    """
    if not delta or mode == "NORMAL":
        return heures, minutes

    if mode == "HEURES":
        heures = (heures + delta) % 24
    elif mode == "MINUTES":
        minutes = (minutes + delta) % 60

    return heures, minutes


def champs_visibles(mode: str, clignote: bool) -> Tuple[bool, bool]:
    """Retourne (visible_heures, visible_minutes).

    Le champ en cours de reglage suit 'clignote' (pour le faire clignoter
    a l'affichage) ; l'autre reste toujours visible.
    """
    return (
        mode != "HEURES" or clignote,
        mode != "MINUTES" or clignote,
    )
