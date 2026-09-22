"""Reveil pour sourd - firmware principal.

Pour le moment : affichages DATE et ANNEE + reglage via l'encodeur
REGLAGE_DATE. Voir le README (section "Mode de fonctionnement") pour
le comportement detaille. HEURE, ALARME et les deux autres encodeurs
ne sont pas encore geres.
"""
import board
import rtc
import time

from display import Afficheurs
from encoder import Encodeur

MODES = ("NORMAL", "JOUR", "MOIS", "ANNEE")
ANNEE_DEFAUT = 2026

afficheurs = Afficheurs()
encodeur_date = Encodeur(board.GP3, board.GP4, board.GP8)

# Horloge logicielle du RP2040 : pas de pile de sauvegarde sur cette carte,
# donc reinitialisee a une date par defaut a chaque reset/coupure d'alim.
horloge = rtc.RTC()
horloge.datetime = time.struct_time((ANNEE_DEFAUT, 1, 1, 0, 0, 0, 0, 1, -1))


def jours_dans_mois(mois, annee):
    if mois in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if mois in (4, 6, 9, 11):
        return 30
    bissextile = annee % 4 == 0 and (annee % 100 != 0 or annee % 400 == 0)
    return 29 if bissextile else 28


mode_index = 0
print("Reglage date/annee : clic sur REGLAGE_DATE pour entrer en mode reglage (jour -> mois -> annee -> normal)")

while True:
    delta = encodeur_date.lire_delta()
    if encodeur_date.clic():
        mode_index = (mode_index + 1) % len(MODES)
        print(f"Mode : {MODES[mode_index]}")

    mode = MODES[mode_index]
    maintenant = horloge.datetime
    jour, mois, annee = maintenant.tm_mday, maintenant.tm_mon, maintenant.tm_year

    if delta and mode != "NORMAL":
        if mode == "JOUR":
            jour = ((jour - 1 + delta) % jours_dans_mois(mois, annee)) + 1
        elif mode == "MOIS":
            mois = ((mois - 1 + delta) % 12) + 1
            jour = min(jour, jours_dans_mois(mois, annee))
        elif mode == "ANNEE":
            annee = 2000 + ((annee - 2000 + delta) % 100)
            jour = min(jour, jours_dans_mois(mois, annee))
        horloge.datetime = time.struct_time(
            (annee, mois, jour, maintenant.tm_hour, maintenant.tm_min, maintenant.tm_sec, 0, -1, -1)
        )

    clignote = (time.monotonic() % 0.8) < 0.4
    visible_jour = mode != "JOUR" or clignote
    visible_mois = mode != "MOIS" or clignote
    visible_annee = mode != "ANNEE" or clignote

    afficheurs.afficher_champ(0, jour, 2, visible_jour)
    afficheurs.afficher_champ(2, mois, 2, visible_mois)
    afficheurs.separateur_date()
    afficheurs.afficher_champ(4, annee, 4, visible_annee)
    afficheurs.rafraichir()

    time.sleep(0.02)
