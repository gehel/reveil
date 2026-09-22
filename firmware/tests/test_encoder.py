"""Tests de la classe Encodeur (firmware/reveil/encoder.py).

Encodeur est teste par injection de dependances : on lui passe de faux
objets "encodeur rotatif" (attribut .position) et "interrupteur"
(attribut .value, actif a l'etat bas) plutot que du vrai materiel
CircuitPython. depuis_broches() (qui construit le vrai materiel) n'est
pas teste ici, faute de Pico.
"""
from encoder import Encodeur


class FausseRotation:
    def __init__(self, position=0):
        self.position = position


class FauxInterrupteur:
    def __init__(self, value=True):
        self.value = value  # True = relache (pull-up), False = presse


class TestLireDelta:
    def test_pas_de_rotation_retourne_zero(self):
        enc = Encodeur(FausseRotation(0), FauxInterrupteur())
        assert enc.lire_delta() == 0

    def test_rotation_positive(self):
        rotation = FausseRotation(0)
        enc = Encodeur(rotation, FauxInterrupteur())
        rotation.position = 3
        assert enc.lire_delta() == 3

    def test_rotation_negative(self):
        rotation = FausseRotation(10)
        enc = Encodeur(rotation, FauxInterrupteur())
        rotation.position = 7
        assert enc.lire_delta() == -3

    def test_delta_consomme_apres_lecture(self):
        rotation = FausseRotation(0)
        enc = Encodeur(rotation, FauxInterrupteur())
        rotation.position = 5
        assert enc.lire_delta() == 5
        assert enc.lire_delta() == 0

    def test_lectures_successives_cumulent_correctement(self):
        rotation = FausseRotation(0)
        enc = Encodeur(rotation, FauxInterrupteur())
        rotation.position = 2
        assert enc.lire_delta() == 2
        rotation.position = 5
        assert enc.lire_delta() == 3


class TestClic:
    def test_pas_de_clic_si_relache(self):
        enc = Encodeur(FausseRotation(), FauxInterrupteur(value=True))
        assert enc.clic() is False

    def test_clic_detecte_sur_le_front_descendant(self):
        interrupteur = FauxInterrupteur(value=True)
        enc = Encodeur(FausseRotation(), interrupteur)
        interrupteur.value = False
        assert enc.clic() is True

    def test_clic_ne_se_repete_pas_tant_que_maintenu(self):
        interrupteur = FauxInterrupteur(value=True)
        enc = Encodeur(FausseRotation(), interrupteur)
        interrupteur.value = False
        assert enc.clic() is True
        assert enc.clic() is False
        assert enc.clic() is False

    def test_nouveau_clic_apres_relachement(self):
        interrupteur = FauxInterrupteur(value=True)
        enc = Encodeur(FausseRotation(), interrupteur)
        interrupteur.value = False
        assert enc.clic() is True
        interrupteur.value = True
        assert enc.clic() is False
        interrupteur.value = False
        assert enc.clic() is True
