"""Tests de la logique de reglage heure (firmware/reveil/reglage_heure.py).

Module pur, sans dependance materielle : pas de stub CircuitPython necessaire.
"""
import pytest

from reglage_heure import MODES, appliquer_rotation, champs_visibles, mode_suivant


class TestModeSuivant:
    def test_cycle_complet(self):
        mode = "NORMAL"
        vus = [mode]
        for _ in range(len(MODES)):
            mode = mode_suivant(mode)
            vus.append(mode)
        assert vus == ["NORMAL", "HEURES", "MINUTES", "NORMAL"]

    def test_chaque_mode_a_un_suivant_valide(self):
        for mode in MODES:
            assert mode_suivant(mode) in MODES


class TestAppliquerRotation:
    def test_mode_normal_ignore_la_rotation(self):
        assert appliquer_rotation("NORMAL", 10, 30, 5) == (10, 30)

    def test_delta_nul_ne_change_rien(self):
        assert appliquer_rotation("HEURES", 10, 30, 0) == (10, 30)

    def test_heures_incremente(self):
        assert appliquer_rotation("HEURES", 10, 30, 1) == (11, 30)

    def test_heures_decremente(self):
        assert appliquer_rotation("HEURES", 10, 30, -1) == (9, 30)

    def test_heures_boucle_apres_23(self):
        assert appliquer_rotation("HEURES", 23, 30, 1) == (0, 30)

    def test_heures_boucle_avant_0(self):
        assert appliquer_rotation("HEURES", 0, 30, -1) == (23, 30)

    def test_heures_ne_touche_pas_les_minutes(self):
        assert appliquer_rotation("HEURES", 10, 45, 3) == (13, 45)

    def test_minutes_incremente(self):
        assert appliquer_rotation("MINUTES", 10, 30, 1) == (10, 31)

    def test_minutes_decremente(self):
        assert appliquer_rotation("MINUTES", 10, 30, -1) == (10, 29)

    def test_minutes_boucle_apres_59(self):
        assert appliquer_rotation("MINUTES", 10, 59, 1) == (10, 0)

    def test_minutes_boucle_avant_0(self):
        assert appliquer_rotation("MINUTES", 10, 0, -1) == (10, 59)

    def test_minutes_ne_touche_pas_les_heures(self):
        assert appliquer_rotation("MINUTES", 10, 30, 5) == (10, 35)

    @pytest.mark.parametrize("mode", ["HEURES", "MINUTES"])
    def test_grand_delta_reste_dans_les_bornes(self, mode):
        heures, minutes = appliquer_rotation(mode, 10, 30, 1000)
        assert 0 <= heures <= 23
        assert 0 <= minutes <= 59


class TestChampsVisibles:
    def test_mode_normal_tout_visible(self):
        assert champs_visibles("NORMAL", clignote=False) == (True, True)
        assert champs_visibles("NORMAL", clignote=True) == (True, True)

    def test_mode_heures_seules_les_heures_suivent_le_clignotement(self):
        assert champs_visibles("HEURES", clignote=True) == (True, True)
        assert champs_visibles("HEURES", clignote=False) == (False, True)

    def test_mode_minutes_seules_les_minutes_suivent_le_clignotement(self):
        assert champs_visibles("MINUTES", clignote=True) == (True, True)
        assert champs_visibles("MINUTES", clignote=False) == (True, False)
