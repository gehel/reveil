"""Tests de la logique de reglage date/annee (firmware/reglage_date.py).

Module pur, sans dependance materielle : pas de stub CircuitPython necessaire.
"""
import pytest

from reglage_date import (
    MODES,
    appliquer_rotation,
    champs_visibles,
    jours_dans_mois,
    mode_suivant,
)


class TestJoursDansMois:
    def test_mois_a_31_jours(self):
        for mois in (1, 3, 5, 7, 8, 10, 12):
            assert jours_dans_mois(mois, 2026) == 31

    def test_mois_a_30_jours(self):
        for mois in (4, 6, 9, 11):
            assert jours_dans_mois(mois, 2026) == 30

    def test_fevrier_annee_non_bissextile(self):
        assert jours_dans_mois(2, 2026) == 28

    def test_fevrier_annee_bissextile_div_4(self):
        assert jours_dans_mois(2, 2024) == 29

    def test_fevrier_annee_seculaire_non_bissextile(self):
        # divisible par 100 mais pas par 400 -> pas bissextile
        assert jours_dans_mois(2, 1900) == 28

    def test_fevrier_annee_seculaire_bissextile(self):
        # divisible par 400 -> bissextile
        assert jours_dans_mois(2, 2000) == 29


class TestModeSuivant:
    def test_cycle_complet(self):
        mode = "NORMAL"
        vus = [mode]
        for _ in range(len(MODES)):
            mode = mode_suivant(mode)
            vus.append(mode)
        assert vus == ["NORMAL", "JOUR", "MOIS", "ANNEE", "NORMAL"]

    def test_chaque_mode_a_un_suivant_valide(self):
        for mode in MODES:
            assert mode_suivant(mode) in MODES


class TestAppliquerRotation:
    def test_mode_normal_ignore_la_rotation(self):
        assert appliquer_rotation("NORMAL", 15, 6, 2026, 5) == (15, 6, 2026)

    def test_delta_nul_ne_change_rien(self):
        assert appliquer_rotation("JOUR", 15, 6, 2026, 0) == (15, 6, 2026)

    def test_jour_incremente(self):
        assert appliquer_rotation("JOUR", 15, 6, 2026, 1) == (16, 6, 2026)

    def test_jour_decremente(self):
        assert appliquer_rotation("JOUR", 15, 6, 2026, -1) == (14, 6, 2026)

    def test_jour_boucle_apres_dernier_jour_du_mois(self):
        # juin a 30 jours
        assert appliquer_rotation("JOUR", 30, 6, 2026, 1) == (1, 6, 2026)

    def test_jour_boucle_avant_le_premier(self):
        assert appliquer_rotation("JOUR", 1, 6, 2026, -1) == (30, 6, 2026)

    def test_jour_boucle_tient_compte_de_fevrier_bissextile(self):
        assert appliquer_rotation("JOUR", 29, 2, 2024, 1) == (1, 2, 2024)

    def test_mois_incremente(self):
        assert appliquer_rotation("MOIS", 15, 6, 2026, 1) == (15, 7, 2026)

    def test_mois_boucle_apres_decembre(self):
        assert appliquer_rotation("MOIS", 15, 12, 2026, 1) == (15, 1, 2026)

    def test_mois_boucle_avant_janvier(self):
        assert appliquer_rotation("MOIS", 15, 1, 2026, -1) == (15, 12, 2026)

    def test_mois_ajuste_le_jour_si_invalide_dans_le_nouveau_mois(self):
        # 31 janvier -> fevrier (28 jours en 2026, non bissextile)
        assert appliquer_rotation("MOIS", 31, 1, 2026, 1) == (28, 2, 2026)

    def test_mois_ne_touche_pas_un_jour_deja_valide(self):
        assert appliquer_rotation("MOIS", 15, 1, 2026, 1) == (15, 2, 2026)

    def test_annee_incremente(self):
        assert appliquer_rotation("ANNEE", 15, 6, 2026, 1) == (15, 6, 2027)

    def test_annee_boucle_apres_2099(self):
        assert appliquer_rotation("ANNEE", 15, 6, 2099, 1) == (15, 6, 2000)

    def test_annee_boucle_avant_2000(self):
        assert appliquer_rotation("ANNEE", 15, 6, 2000, -1) == (15, 6, 2099)

    def test_annee_ajuste_le_jour_si_29_fevrier_devient_invalide(self):
        # 29 fevrier 2024 (bissextile) -> 2025 (non bissextile)
        assert appliquer_rotation("ANNEE", 29, 2, 2024, 1) == (28, 2, 2025)

    @pytest.mark.parametrize("mode", ["JOUR", "MOIS", "ANNEE"])
    def test_grand_delta_reste_dans_les_bornes(self, mode):
        jour, mois, annee = appliquer_rotation(mode, 15, 6, 2026, 1000)
        assert 1 <= jour <= 31
        assert 1 <= mois <= 12
        assert 2000 <= annee <= 2099


class TestChampsVisibles:
    def test_mode_normal_tout_visible(self):
        assert champs_visibles("NORMAL", clignote=False) == (True, True, True)
        assert champs_visibles("NORMAL", clignote=True) == (True, True, True)

    def test_mode_jour_seul_le_jour_suit_le_clignotement(self):
        assert champs_visibles("JOUR", clignote=True) == (True, True, True)
        assert champs_visibles("JOUR", clignote=False) == (False, True, True)

    def test_mode_mois_seul_le_mois_suit_le_clignotement(self):
        assert champs_visibles("MOIS", clignote=True) == (True, True, True)
        assert champs_visibles("MOIS", clignote=False) == (True, False, True)

    def test_mode_annee_seule_lannee_suit_le_clignotement(self):
        assert champs_visibles("ANNEE", clignote=True) == (True, True, True)
        assert champs_visibles("ANNEE", clignote=False) == (True, True, False)
