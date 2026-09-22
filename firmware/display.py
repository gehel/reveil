"""Pilotage des 4 affichages 7-segments (2x MAX7219) du reveil."""
import board
import busio
import digitalio

from adafruit_max7219.bcddigits import BCDDigits

BLANC = 15  # code MAX7219 (Code B) pour un digit vide


class Afficheurs:
    """Regroupe les deux puces MAX7219 : Heure/Alarme (digits 0-3 = Heure,
    4-7 = Alarme) et Date/Annee (digits 0-3 = Date, 4-7 = Annee)."""

    def __init__(self, luminosite=8):
        spi_heure_alarme = busio.SPI(clock=board.GP6, MOSI=board.GP7)
        cs_heure_alarme = digitalio.DigitalInOut(board.GP5)
        self.heure_alarme = BCDDigits(spi_heure_alarme, cs_heure_alarme, nDigits=8)

        spi_date_annee = busio.SPI(clock=board.GP10, MOSI=board.GP11)
        cs_date_annee = digitalio.DigitalInOut(board.GP9)
        self.date_annee = BCDDigits(spi_date_annee, cs_date_annee, nDigits=8)

        for disp in (self.heure_alarme, self.date_annee):
            disp.brightness(luminosite)

    def afficher_champ(self, depart, valeur, largeur, visible=True):
        """Affiche 'valeur' sur 'largeur' digits de l'affichage Date/Annee
        a partir de la position 'depart' (0-3 = DATE, 4-7 = ANNEE).
        Si visible est faux, le champ est vide (utilise pour le clignotement)."""
        if visible:
            self.date_annee.show_str(depart, f"{valeur:0{largeur}}")
        else:
            for pos in range(depart, depart + largeur):
                self.date_annee.set_digit(pos, BLANC)

    def separateur_date(self, visible=True):
        """Point decimal entre jour et mois sur l'affichage DATE (format JJ.MM)."""
        self.date_annee.show_dot(1, 1 if visible else 0)

    def rafraichir(self):
        self.date_annee.show()
