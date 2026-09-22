"""Reveil pour sourd - firmware principal.

Pour le moment : affichages DATE, ANNEE, HEURE et ALARME + reglage via
les encodeurs REGLAGE_DATE, REGLAGE_HEURE et REGLAGE_ALARME. Voir le
README (section "Mode de fonctionnement") pour le comportement
detaille. L'alarme ne se declenche pas encore (pas de comparaison avec
l'heure courante, pas de LED/moteur) : seule l'heure d'alarme peut
etre affichee et reglee pour le moment.

La logique metier (reglage_date.py, reglage_heure.py) est testee
separement sur l'hote (firmware/tests/, `make test-unit`) ; ce fichier
ne fait qu'orchestrer le materiel autour d'elle. reglage_heure.py sert
a la fois pour l'heure courante et pour l'heure d'alarme : les deux
sont des paires (heures, minutes) avec les memes bornes (0-23/0-59) et
le meme cycle de reglage.
"""
import board
import rtc
import time

import reglage_date
import reglage_heure
from display import Afficheurs
from encoder import Encodeur

ANNEE_DEFAUT = 2026
ALARME_HEURES_DEFAUT = 7
ALARME_MINUTES_DEFAUT = 0

afficheurs = Afficheurs.depuis_broches()
encodeur_date = Encodeur.depuis_broches(board.GP3, board.GP4, board.GP8)
encodeur_heure = Encodeur.depuis_broches(board.GP0, board.GP1, board.GP2)
encodeur_alarme = Encodeur.depuis_broches(board.GP12, board.GP13, board.GP14)

# Horloge logicielle du RP2040 : pas de pile de sauvegarde sur cette carte,
# donc reinitialisee a une date/heure par defaut a chaque reset/coupure d'alim.
horloge = rtc.RTC()
horloge.datetime = time.struct_time((ANNEE_DEFAUT, 1, 1, 0, 0, 0, 0, 1, -1))

# L'heure d'alarme n'est pas geree par la RTC (ce n'est pas l'heure
# courante) : simple valeur locale, reinitialisee elle aussi a chaque
# demarrage.
alarme_heures = ALARME_HEURES_DEFAUT
alarme_minutes = ALARME_MINUTES_DEFAUT

mode_date = "NORMAL"
mode_heure = "NORMAL"
mode_alarme = "NORMAL"
print("Reglage date/annee : clic sur REGLAGE_DATE (jour -> mois -> annee -> normal)")
print("Reglage heure : clic sur REGLAGE_HEURE (heures -> minutes -> normal)")
print("Reglage alarme : clic sur REGLAGE_ALARME (heures -> minutes -> normal)")

while True:
    delta_date = encodeur_date.lire_delta()
    if encodeur_date.clic():
        mode_date = reglage_date.mode_suivant(mode_date)
        print(f"Mode date : {mode_date}")

    delta_heure = encodeur_heure.lire_delta()
    if encodeur_heure.clic():
        mode_heure = reglage_heure.mode_suivant(mode_heure)
        print(f"Mode heure : {mode_heure}")

    delta_alarme = encodeur_alarme.lire_delta()
    if encodeur_alarme.clic():
        mode_alarme = reglage_heure.mode_suivant(mode_alarme)
        print(f"Mode alarme : {mode_alarme}")

    maintenant = horloge.datetime
    jour, mois, annee = reglage_date.appliquer_rotation(
        mode_date, maintenant.tm_mday, maintenant.tm_mon, maintenant.tm_year, delta_date
    )
    heures, minutes = reglage_heure.appliquer_rotation(
        mode_heure, maintenant.tm_hour, maintenant.tm_min, delta_heure
    )
    alarme_heures, alarme_minutes = reglage_heure.appliquer_rotation(
        mode_alarme, alarme_heures, alarme_minutes, delta_alarme
    )

    if (jour, mois, annee, heures, minutes) != (
        maintenant.tm_mday,
        maintenant.tm_mon,
        maintenant.tm_year,
        maintenant.tm_hour,
        maintenant.tm_min,
    ):
        horloge.datetime = time.struct_time(
            (annee, mois, jour, heures, minutes, maintenant.tm_sec, 0, -1, -1)
        )

    clignote = (time.monotonic() % 0.8) < 0.4
    visible_jour, visible_mois, visible_annee = reglage_date.champs_visibles(mode_date, clignote)
    visible_heures, visible_minutes = reglage_heure.champs_visibles(mode_heure, clignote)
    visible_alarme_heures, visible_alarme_minutes = reglage_heure.champs_visibles(mode_alarme, clignote)

    afficheurs.afficher_champ(afficheurs.date_annee, 0, jour, 2, visible_jour)
    afficheurs.afficher_champ(afficheurs.date_annee, 2, mois, 2, visible_mois)
    afficheurs.afficher_separateur(afficheurs.date_annee, 1)
    afficheurs.afficher_champ(afficheurs.date_annee, 4, annee, 4, visible_annee)

    afficheurs.afficher_champ(afficheurs.heure_alarme, 0, heures, 2, visible_heures)
    afficheurs.afficher_champ(afficheurs.heure_alarme, 2, minutes, 2, visible_minutes)
    afficheurs.afficher_separateur(afficheurs.heure_alarme, 1)
    afficheurs.afficher_champ(afficheurs.heure_alarme, 4, alarme_heures, 2, visible_alarme_heures)
    afficheurs.afficher_champ(afficheurs.heure_alarme, 6, alarme_minutes, 2, visible_alarme_minutes)
    afficheurs.afficher_separateur(afficheurs.heure_alarme, 5)

    afficheurs.rafraichir()

    time.sleep(0.02)
