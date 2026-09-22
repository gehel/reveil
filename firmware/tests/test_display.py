"""Tests de la classe Afficheurs (firmware/reveil/display.py).

Afficheurs est teste par injection de dependances : on lui passe de
faux "chips" MAX7219 (memorisant les appels .pixel()/.show()/
.brightness()) plutot que du vrai materiel. depuis_broches() (qui
construit le vrai materiel) n'est pas teste ici, faute de Pico.
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
        afficheurs, heure_alarme, date_annee = None, FauxChip(), FauxChip()
        Afficheurs(heure_alarme, date_annee, luminosite=5)
        assert heure_alarme.luminosite == 5
        assert date_annee.luminosite == 5

    def test_luminosite_par_defaut(self):
        heure_alarme, date_annee = FauxChip(), FauxChip()
        Afficheurs(heure_alarme, date_annee)
        assert heure_alarme.luminosite == 8
        assert date_annee.luminosite == 8


class TestAfficherChamp:
    def test_ecrit_les_chiffres_a_la_bonne_position_physique(self):
        # Regression du bug d'inversion : "22" affiche a partir de la
        # position 0 doit donner digit(0)=2, digit(1)=2, PAS l'inverse
        # ni un chevauchement avec le bloc annee.
        afficheurs, _, date_annee = construire()
        afficheurs.afficher_champ(0, 22, 2)
        assert date_annee.digit_bcd(0) == 2
        assert date_annee.digit_bcd(1) == 2

    def test_deux_champs_distincts_ne_se_marchent_pas_dessus(self):
        # Cas exact du bug rapporte : jour=22, mois=09, annee=2026.
        # Avant le fix, les deux blocs de 4 digits se retrouvaient
        # inverses ET echanges (2026 -> "6202", 2209 -> "9022").
        afficheurs, _, date_annee = construire()
        afficheurs.afficher_champ(0, 22, 2)  # jour
        afficheurs.afficher_champ(2, 9, 2)  # mois
        afficheurs.afficher_champ(4, 2026, 4)  # annee

        assert [date_annee.digit_bcd(i) for i in range(8)] == [2, 2, 0, 9, 2, 0, 2, 6]

    def test_visible_faux_efface_le_champ(self):
        afficheurs, _, date_annee = construire()
        afficheurs.afficher_champ(0, 22, 2, visible=False)
        assert date_annee.digit_bcd(0) == BLANC
        assert date_annee.digit_bcd(1) == BLANC

    def test_ne_touche_pas_a_lautre_puce(self):
        afficheurs, heure_alarme, _ = construire()
        afficheurs.afficher_champ(0, 22, 2)
        assert heure_alarme.pixels == [[0] * 8 for _ in range(8)]


class TestSeparateurDate:
    def test_point_visible(self):
        afficheurs, _, date_annee = construire()
        afficheurs.separateur_date(True)
        assert date_annee.dot(1) == 1

    def test_point_invisible(self):
        afficheurs, _, date_annee = construire()
        afficheurs.separateur_date(False)
        assert date_annee.dot(1) == 0

    def test_ne_touche_pas_les_chiffres(self):
        afficheurs, _, date_annee = construire()
        afficheurs.afficher_champ(0, 22, 2)
        afficheurs.separateur_date(True)
        assert date_annee.digit_bcd(1) == 2


class TestRafraichir:
    def test_rafraichit_lafficheur_date_annee(self):
        afficheurs, _, date_annee = construire()
        afficheurs.rafraichir()
        assert date_annee.affiche is True
