"""Tests de la classe Afficheurs (firmware/reveil/display.py).

Afficheurs est teste par injection de dependances : on lui passe de
faux "chips" MAX7219 (memorisant les appels .pixel()/.show()/
.brightness()) plutot que du vrai materiel. depuis_broches() (qui
construit le vrai materiel) n'est pas teste ici, faute de Pico.

afficher_champ()/afficher_separateur() prennent la puce cible en
parametre (self.heure_alarme ou self.date_annee) : les deux puces
utilisent la meme logique d'ecriture (voir HEURE, qui partage la puce
heure_alarme avec ALARME comme DATE/ANNEE partagent date_annee).
"""
from display import BLANC, Afficheurs


class FauxChip:
    def __init__(self):
        self.pixels = [[0] * 8 for _ in range(8)]
        self.luminosite = None
        self.affiche = False

    def brightness(self, valeur):
        self.luminosite = valeur

    def pixel(self, x, y, bit):
        self.pixels[x][y] = 1 if bit else 0

    def show(self):
        self.affiche = True

    def digit_bcd(self, x):
        """Reconstruit la valeur BCD (bits 0-3) ecrite a la position x."""
        return sum(self.pixels[x][i] << i for i in range(4))

    def dot(self, x):
        return self.pixels[x][7]


def construire():
    heure_alarme = FauxChip()
    date_annee = FauxChip()
    return Afficheurs(heure_alarme, date_annee), heure_alarme, date_annee


class TestConstruction:
    def test_regle_la_luminosite_sur_les_deux_puces(self):
        heure_alarme, date_annee = FauxChip(), FauxChip()
        Afficheurs(heure_alarme, date_annee, luminosite=5)
        assert heure_alarme.luminosite == 5
        assert date_annee.luminosite == 5

    def test_luminosite_par_defaut(self):
        heure_alarme, date_annee = FauxChip(), FauxChip()
        Afficheurs(heure_alarme, date_annee)
        assert heure_alarme.luminosite == 8
        assert date_annee.luminosite == 8


class TestReglerLuminosite:
    def test_applique_le_niveau_aux_deux_puces(self):
        afficheurs, heure_alarme, date_annee = construire()
        afficheurs.regler_luminosite(12)
        assert heure_alarme.luminosite == 12
        assert date_annee.luminosite == 12

    def test_ecrase_la_luminosite_initiale(self):
        afficheurs, heure_alarme, date_annee = construire()
        afficheurs.regler_luminosite(3)
        assert heure_alarme.luminosite == 3
        assert date_annee.luminosite == 3


class TestAfficherChamp:
    def test_ecrit_les_chiffres_a_la_bonne_position_physique(self):
        # Regression du bug d'inversion : "22" affiche a partir de la
        # position 0 doit donner digit(0)=2, digit(1)=2, PAS l'inverse
        # ni un chevauchement avec le bloc annee.
        afficheurs, _, date_annee = construire()
        afficheurs.afficher_champ(date_annee, 0, 22, 2)
        assert date_annee.digit_bcd(0) == 2
        assert date_annee.digit_bcd(1) == 2

    def test_deux_champs_distincts_ne_se_marchent_pas_dessus(self):
        # Cas exact du bug rapporte : jour=22, mois=09, annee=2026.
        # Avant le fix, les deux blocs de 4 digits se retrouvaient
        # inverses ET echanges (2026 -> "6202", 2209 -> "9022").
        afficheurs, _, date_annee = construire()
        afficheurs.afficher_champ(date_annee, 0, 22, 2)  # jour
        afficheurs.afficher_champ(date_annee, 2, 9, 2)  # mois
        afficheurs.afficher_champ(date_annee, 4, 2026, 4)  # annee

        assert [date_annee.digit_bcd(i) for i in range(8)] == [2, 2, 0, 9, 2, 0, 2, 6]

    def test_visible_faux_efface_le_champ(self):
        afficheurs, _, date_annee = construire()
        afficheurs.afficher_champ(date_annee, 0, 22, 2, visible=False)
        assert date_annee.digit_bcd(0) == BLANC
        assert date_annee.digit_bcd(1) == BLANC

    def test_ne_touche_pas_a_lautre_puce(self):
        afficheurs, heure_alarme, date_annee = construire()
        afficheurs.afficher_champ(date_annee, 0, 22, 2)
        assert heure_alarme.pixels == [[0] * 8 for _ in range(8)]

    def test_ecrit_sur_la_puce_heure_alarme(self):
        # HEURE partage la puce heure_alarme avec ALARME (digits 0-3 / 4-7),
        # meme mecanique que DATE/ANNEE sur date_annee.
        afficheurs, heure_alarme, date_annee = construire()
        afficheurs.afficher_champ(heure_alarme, 0, 14, 2)  # heures
        afficheurs.afficher_champ(heure_alarme, 2, 5, 2)  # minutes
        assert [heure_alarme.digit_bcd(i) for i in range(4)] == [1, 4, 0, 5]
        assert date_annee.pixels == [[0] * 8 for _ in range(8)]

    def test_heure_et_alarme_ne_se_marchent_pas_dessus(self):
        # Meme verification que test_deux_champs_distincts_ne_se_marchent_pas_dessus
        # mais sur la puce heure_alarme (positions 0-3 = HEURE, 4-7 = ALARME) :
        # c'est exactement la zone (position 4-7) touchee par le bug d'inversion
        # deja rencontre sur date_annee, jamais testee explicitement ici.
        afficheurs, heure_alarme, _ = construire()
        afficheurs.afficher_champ(heure_alarme, 0, 14, 2)  # heure : 14
        afficheurs.afficher_champ(heure_alarme, 2, 5, 2)  # heure : 05
        afficheurs.afficher_champ(heure_alarme, 4, 7, 2)  # alarme : 07
        afficheurs.afficher_champ(heure_alarme, 6, 30, 2)  # alarme : 30

        assert [heure_alarme.digit_bcd(i) for i in range(8)] == [1, 4, 0, 5, 0, 7, 3, 0]


class TestAfficherSeparateur:
    def test_point_visible(self):
        afficheurs, _, date_annee = construire()
        afficheurs.afficher_separateur(date_annee, 1, True)
        assert date_annee.dot(1) == 1

    def test_point_invisible(self):
        afficheurs, _, date_annee = construire()
        afficheurs.afficher_separateur(date_annee, 1, False)
        assert date_annee.dot(1) == 0

    def test_ne_touche_pas_les_chiffres(self):
        afficheurs, _, date_annee = construire()
        afficheurs.afficher_champ(date_annee, 0, 22, 2)
        afficheurs.afficher_separateur(date_annee, 1, True)
        assert date_annee.digit_bcd(1) == 2

    def test_fonctionne_sur_la_puce_heure_alarme(self):
        afficheurs, heure_alarme, _ = construire()
        afficheurs.afficher_separateur(heure_alarme, 1, True)
        assert heure_alarme.dot(1) == 1


class TestRafraichir:
    def test_rafraichit_les_deux_afficheurs(self):
        afficheurs, heure_alarme, date_annee = construire()
        afficheurs.rafraichir()
        assert date_annee.affiche is True
        assert heure_alarme.affiche is True
