"""Reglage de la luminosite des affichages via le potentiometre LUMINOSITE.

Les annotations de type materiel (analogio.AnalogIn, microcontroller.Pin)
sont en chaines (forward references) : ces modules ne sont jamais importes
au niveau module (seulement dans depuis_broche(), pour l'usage reel). Les
annotations ne sont de toute facon pas evaluees a l'execution sur
CircuitPython ; les chaines evitent aussi tout import parasite cote hote
(analogio leve NotImplementedError, pas ImportError, sur cette machine via
Blinka - un simple `try/except ImportError` ne suffit pas a le garder)."""


def niveau_depuis_adc(valeur_adc: int) -> int:
    """Convertit une valeur ADC brute (0-65535, cf. analogio.AnalogIn.value)
    en niveau de luminosite MAX7219 (0-15)."""
    return valeur_adc * 15 // 65535


class Potentiometre:
    def __init__(self, capteur: "analogio.AnalogIn") -> None:
        """capteur : objet exposant un attribut 'value' (0-65535), ex. analogio.AnalogIn."""
        self._capteur = capteur

    @classmethod
    def depuis_broche(cls, pin: "microcontroller.Pin") -> "Potentiometre":
        """Construit un Potentiometre a partir d'une broche ADC reelle."""
        import analogio

        return cls(analogio.AnalogIn(pin))

    def lire_niveau(self) -> int:
        """Niveau de luminosite courant (0-15)."""
        return niveau_depuis_adc(self._capteur.value)
