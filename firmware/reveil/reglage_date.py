"""Logique metier du reglage date/annee (independante du materiel).

Module pur : pas d'import CircuitPython, testable sans stub ni Pico.
"""

MODES = ("NORMAL", "JOUR", "MOIS", "ANNEE")


def jours_dans_mois(mois, annee):
    """Nombre de jours dans le mois donne (1-12), annees bissextiles incluses."""
    if mois in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if mois in (4, 6, 9, 11):
        return 30
    bissextile = annee % 4 == 0 and (annee % 100 != 0 or annee % 400 == 0)
    return 29 if bissextile else 28


def mode_suivant(mode):
    """Mode suivant dans le cycle NORMAL -> JOUR -> MOIS -> ANNEE -> NORMAL."""
    return MODES[(MODES.index(mode) + 1) % len(MODES)]


def appliquer_rotation(mode, jour, mois, annee, delta):
    """Applique un deplacement d'encodeur (delta) au champ actif selon 'mode'.

    Retourne le tuple (jour, mois, annee) mis a jour ; inchange si
    mode == "NORMAL" ou delta == 0. Le jour est ramene au dernier jour
    valide si le changement de mois/annee le rend invalide.
    """
    if not delta or mode == "NORMAL":
        return jour, mois, annee

    if mode == "JOUR":
        jour = ((jour - 1 + delta) % jours_dans_mois(mois, annee)) + 1
    elif mode == "MOIS":
        mois = ((mois - 1 + delta) % 12) + 1
        jour = min(jour, jours_dans_mois(mois, annee))
    elif mode == "ANNEE":
        annee = 2000 + ((annee - 2000 + delta) % 100)
        jour = min(jour, jours_dans_mois(mois, annee))

    return jour, mois, annee


def champs_visibles(mode, clignote):
    """Retourne (visible_jour, visible_mois, visible_annee).

    Le champ en cours de reglage suit 'clignote' (pour le faire clignoter
    a l'affichage) ; les autres restent toujours visibles.
    """
    return (
        mode != "JOUR" or clignote,
        mode != "MOIS" or clignote,
        mode != "ANNEE" or clignote,
    )
