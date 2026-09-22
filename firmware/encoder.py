"""Encodeur rotatif + bouton poussoir associe."""
import digitalio
import rotaryio


class Encodeur:
    def __init__(self, pin_a, pin_b, pin_sw):
        self._encodeur = rotaryio.IncrementalEncoder(pin_a, pin_b)
        self._sw = digitalio.DigitalInOut(pin_sw)
        self._sw.direction = digitalio.Direction.INPUT
        self._sw.pull = digitalio.Pull.UP
        self._position = self._encodeur.position
        self._sw_precedent = True

    def lire_delta(self):
        """Retourne le deplacement depuis le dernier appel (0 si pas de rotation)."""
        position = self._encodeur.position
        delta = position - self._position
        self._position = position
        return delta

    def clic(self):
        """Retourne True une seule fois par appui sur le bouton (front descendant)."""
        sw_actuel = self._sw.value
        clique = self._sw_precedent and not sw_actuel
        self._sw_precedent = sw_actuel
        return clique
