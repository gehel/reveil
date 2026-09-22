"""Reveil pour sourd - firmware principal.

Pour le moment : affichages DATE et ANNEE + reglage via l'encodeur
REGLAGE_DATE. Voir le README (section "Mode de fonctionnement") pour
le comportement detaille. HEURE, ALARME et les deux autres encodeurs
ne sont pas encore geres.

La logique metier (reglage_date.py) est testee separement sur l'hote
(firmware/tests/, `make test-unit`) ; ce fichier ne fait qu'orchestrer
le materiel autour d'elle.
"""
import board
import rtc
import time

from display import Afficheurs
from encoder import Encodeur
from reglage_date import appliquer_rotation, champs_visibles, mode_suivant

ANNEE_DEFAUT = 2026

afficheurs = Afficheurs.depuis_broches()
encodeur_date = Encodeur.depuis_broches(board.GP3, board.GP4, board.GP8)

# Horloge logicielle du RP2040 : pas de pile de sauvegarde sur cette carte,
# donc reinitialisee a une date par defaut a chaque reset/coupure d'alim.
horloge = rtc.RTC()
horloge.datetime = time.struct_time((ANNEE_DEFAUT, 1, 1, 0, 0, 0, 0, 1, -1))

mode = "NORMAL"
print("Reglage date/annee : clic sur REGLAGE_DATE pour entrer en mode reglage (jour -> mois -> annee -> normal)")

while True:
    delta = encodeur_date.lire_delta()
    if encodeur_date.clic():
        mode = mode_suivant(mode)
        print(f"Mode : {mode}")

    maintenant = horloge.datetime
    jour, mois, annee = appliquer_rotation(
        mode, maintenant.tm_mday, maintenant.tm_mon, maintenant.tm_year, delta
    )
    if (jour, mois, annee) != (maintenant.tm_mday, maintenant.tm_mon, maintenant.tm_year):
        horloge.datetime = time.struct_time(
            (annee, mois, jour, maintenant.tm_hour, maintenant.tm_min, maintenant.tm_sec, 0, -1, -1)
        )

    clignote = (time.monotonic() % 0.8) < 0.4
    visible_jour, visible_mois, visible_annee = champs_visibles(mode, clignote)

    afficheurs.afficher_champ(0, jour, 2, visible_jour)
    afficheurs.afficher_champ(2, mois, 2, visible_mois)
    afficheurs.separateur_date()
    afficheurs.afficher_champ(4, annee, 4, visible_annee)
    afficheurs.rafraichir()

    time.sleep(0.02)
