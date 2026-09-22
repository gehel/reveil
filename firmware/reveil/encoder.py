"""Encodeur rotatif + bouton poussoir associe.

Les annotations de type materiel (rotaryio.IncrementalEncoder,
digitalio.DigitalInOut, microcontroller.Pin) sont en chaines (forward
references) : ces modules ne sont jamais importes au niveau module
(seulement dans depuis_broches(), pour l'usage reel), et les
annotations ne sont de toute facon pas evaluees a l'execution sur
CircuitPython."""


class Encodeur:
    def __init__(self, encodeur_rotatif: "rotaryio.IncrementalEncoder", interrupteur: "digitalio.DigitalInOut") -> None:
        """encodeur_rotatif : objet expose un attribut 'position' (ex. rotaryio.IncrementalEncoder).
        interrupteur : objet expose un attribut 'value', actif a l'etat bas (ex. digitalio.DigitalInOut)."""
        self._encodeur = encodeur_rotatif
        self._sw = interrupteur
        self._position = self._encodeur.position
        self._sw_precedent = True

    @classmethod
    def depuis_broches(
        cls,
        pin_a: "microcontroller.Pin",
        pin_b: "microcontroller.Pin",
        pin_sw: "microcontroller.Pin",
    ) -> "Encodeur":
        """Construit un Encodeur a partir de broches GPIO reelles."""
        import digitalio
        import rotaryio

        encodeur_rotatif = rotaryio.IncrementalEncoder(pin_a, pin_b)
        interrupteur = digitalio.DigitalInOut(pin_sw)
        interrupteur.direction = digitalio.Direction.INPUT
        interrupteur.pull = digitalio.Pull.UP
        return cls(encodeur_rotatif, interrupteur)

    def lire_delta(self) -> int:
        """Retourne le deplacement depuis le dernier appel (0 si pas de rotation)."""
        position = self._encodeur.position
        delta = position - self._position
        self._position = position
        return delta

    def clic(self) -> bool:
        """Retourne True une seule fois par appui sur le bouton (front descendant)."""
        sw_actuel = self._sw.value
        clique = self._sw_precedent and not sw_actuel
        self._sw_precedent = sw_actuel
        return clique
