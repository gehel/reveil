import board       # Accès aux pins du Raspberry Pi Pico
import busio        # Communication sur bus matériel (SPI, I2C, UART)
import digitalio    # Contrôle des pins numériques (entrée/sortie)
import time         # Fonctions de temporisation (sleep)
from adafruit_max7219.bcddigits import BCDDigits  # Pilote pour affichage 7-segments via MAX7219

# Initialisation du bus SPI : GP6=horloge (CLK), GP7=données (MOSI)
spi = busio.SPI(clock=board.GP6, MOSI=board.GP7)

# Pin de sélection du circuit MAX7219 (Chip Select / LOAD)
cs = digitalio.DigitalInOut(board.GP5)

# Création de l'objet d'affichage : 8 digits pour éviter un bug de la librairie
# (show() itère toujours sur 8 positions, le buffer doit donc avoir 8 octets)
display = BCDDigits(spi, cs, nDigits=8)

# Réglage de la luminosité (0 = minimum, 15 = maximum)
display.brightness(5)

# Avec nDigits=8, set_digit(pos) cible le registre DIGIT(7-pos).
# Pour écrire sur DIGIT0–DIGIT3 (les 4 chiffres physiques), on utilise les positions 7 à 4.
for i in range(11):
    display.set_digit(4, i // 1000)        # Chiffre des milliers  → DIGIT3
    display.set_digit(5, (i // 100) % 10)  # Chiffre des centaines → DIGIT2
    display.set_digit(6, (i // 10) % 10)   # Chiffre des dizaines  → DIGIT1
    display.set_digit(7, i % 10)           # Chiffre des unités    → DIGIT0
    display.show()                          # Envoie les données au MAX7219 pour affichage
    time.sleep(0.5)                         # Pause de 0.5s → vitesse de 2 chiffres par seconde
