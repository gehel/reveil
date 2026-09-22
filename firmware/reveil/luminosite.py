"""Reglage de la luminosite des affichages via le potentiometre LUMINOSITE."""


def niveau_depuis_adc(valeur_adc):
    """Convertit une valeur ADC brute (0-65535, cf. analogio.AnalogIn.value)
    en niveau de luminosite MAX7219 (0-15)."""
    return valeur_adc * 15 // 65535


class Potentiometre:
    def __init__(self, capteur):
        """capteur : objet exposant un attribut 'value' (0-65535), ex. analogio.AnalogIn."""
        self._capteur = capteur

    @classmethod
    def depuis_broche(cls, pin):
        """Construit un Potentiometre a partir d'une broche ADC reelle."""
        import analogio

        return cls(analogio.AnalogIn(pin))

    def lire_niveau(self):
        """Niveau de luminosite courant (0-15)."""
        return niveau_depuis_adc(self._capteur.value)
