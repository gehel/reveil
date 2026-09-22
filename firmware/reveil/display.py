"""Pilotage des 4 affichages 7-segments (2x MAX7219) du reveil."""

BLANC = 15  # code MAX7219 (Code B) pour un digit vide


class Afficheurs:
    """Regroupe les deux puces MAX7219 : Heure/Alarme (digits 0-3 = Heure,
    4-7 = Alarme) et Date/Annee (digits 0-3 = Date, 4-7 = Annee)."""

    def __init__(self, chip_heure_alarme, chip_date_annee, luminosite=8):
        """chip_heure_alarme, chip_date_annee : objets exposant .pixel(x, y, bit),
        .show() et .brightness(niveau) (ex. adafruit_max7219.bcddigits.BCDDigits)."""
        self.heure_alarme = chip_heure_alarme
        self.date_annee = chip_date_annee
        for chip in (self.heure_alarme, self.date_annee):
            chip.brightness(luminosite)

    @classmethod
    def depuis_broches(cls, luminosite=8):
        """Construit les Afficheurs a partir des broches GPIO reelles du reveil."""
        import board
        import busio
        import digitalio
        from adafruit_max7219.bcddigits import BCDDigits

        spi_heure_alarme = busio.SPI(clock=board.GP6, MOSI=board.GP7)
        cs_heure_alarme = digitalio.DigitalInOut(board.GP5)
        chip_heure_alarme = BCDDigits(spi_heure_alarme, cs_heure_alarme, nDigits=8)

        spi_date_annee = busio.SPI(clock=board.GP10, MOSI=board.GP11)
        cs_date_annee = digitalio.DigitalInOut(board.GP9)
        chip_date_annee = BCDDigits(spi_date_annee, cs_date_annee, nDigits=8)

        return cls(chip_heure_alarme, chip_date_annee, luminosite=luminosite)

    def _ecrire_digit(self, chip, pos, valeur_bcd):
        """Ecrit un digit BCD (0-15) a la position physique 'pos' (0 = premier
        digit a gauche de la puce, 7 = dernier a droite).

        BCDDigits.set_digit()/show_str() appliquent une inversion de
        position (dpos = ndigits - dpos - 1) calculee sur les 8 digits de
        la puce entiere. Tant qu'on adresse toute la puce comme un seul
        afficheur de 8 digits ca tombe juste, mais des qu'on la decoupe en
        deux afficheurs logiques de 4 digits (DATE/ANNEE) cette inversion
        echange les deux moities ET inverse l'ordre des chiffres dans
        chacune (constate a l'ecran : "2026"/"2209" affiches en
        "6202"/"9022", cf. historique git). On ecrit donc directement dans
        le framebuffer, sans passer par cette inversion.
        """
        for i in range(4):
            chip.pixel(pos, i, valeur_bcd & 0x01)
            valeur_bcd >>= 1

    def afficher_champ(self, depart, valeur, largeur, visible=True):
        """Affiche 'valeur' sur 'largeur' digits de l'affichage Date/Annee
        a partir de la position physique 'depart' (0 = premier digit a
        gauche ; 0-3 = DATE, 4-7 = ANNEE).
        Si visible est faux, le champ est vide (utilise pour le clignotement)."""
        if visible:
            for i, car in enumerate(f"{valeur:0{largeur}}"):
                self._ecrire_digit(self.date_annee, depart + i, int(car))
        else:
            for pos in range(depart, depart + largeur):
                self._ecrire_digit(self.date_annee, pos, BLANC)

    def separateur_date(self, visible=True):
        """Point decimal entre jour et mois sur l'affichage DATE (format JJ.MM)."""
        self.date_annee.pixel(1, 7, 1 if visible else 0)

    def rafraichir(self):
        self.date_annee.show()
