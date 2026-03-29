"""
Tests de l'infrastructure — à remplacer par les vrais tests métier.
"""


def test_imports():
    """Vérifie que les mocks hardware permettent d'importer les modules."""
    import board

    assert board.GP5 == "GP5"
    assert board.GP6 == "GP6"
    assert board.GP7 == "GP7"
