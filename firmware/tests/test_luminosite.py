"""Tests du reglage de luminosite (firmware/reveil/luminosite.py).

niveau_depuis_adc() est une fonction pure (pas de stub necessaire).
Potentiometre est teste par injection de dependance : un faux capteur
avec un attribut .value (0-65535, comme analogio.AnalogIn) plutot que
du vrai materiel. depuis_broche() (qui construit le vrai materiel)
n'est pas teste ici, faute de Pico.
"""
import pytest

from luminosite import Potentiometre, niveau_depuis_adc


class TestNiveauDepuisAdc:
    def test_valeur_minimale(self):
        assert niveau_depuis_adc(0) == 0

    def test_valeur_maximale(self):
        assert niveau_depuis_adc(65535) == 15

    def test_valeur_mediane(self):
        assert niveau_depuis_adc(32768) == 7

    def test_reste_dans_les_bornes_max7219(self):
        for valeur_adc in range(0, 65536, 1000):
            niveau = niveau_depuis_adc(valeur_adc)
            assert 0 <= niveau <= 15

    def test_croissant_avec_la_valeur_adc(self):
        precedent = niveau_depuis_adc(0)
        for valeur_adc in range(0, 65536, 4096):
            niveau = niveau_depuis_adc(valeur_adc)
            assert niveau >= precedent
            precedent = niveau


class FauxCapteur:
    def __init__(self, value=0):
        self.value = value


class TestPotentiometre:
    def test_lire_niveau_delegue_a_niveau_depuis_adc(self):
        capteur = FauxCapteur(value=65535)
        potentiometre = Potentiometre(capteur)
        assert potentiometre.lire_niveau() == 15

    def test_lire_niveau_reflete_la_valeur_courante_du_capteur(self):
        capteur = FauxCapteur(value=0)
        potentiometre = Potentiometre(capteur)
        assert potentiometre.lire_niveau() == 0
        capteur.value = 65535
        assert potentiometre.lire_niveau() == 15
