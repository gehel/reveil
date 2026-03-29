"""
Mocks des modules matériels CircuitPython pour les tests sur host.
Ces stubs permettent d'importer code.py sans Raspberry Pi Pico connecté.
"""
import sys
from unittest.mock import MagicMock


class MockSPI:
    def __init__(self, *args, **kwargs):
        pass


class MockDigitalInOut:
    def __init__(self, *args, **kwargs):
        pass


class MockBCDDigits:
    def __init__(self, *args, **kwargs):
        self._digits = [0] * 8

    def brightness(self, value):
        pass

    def set_digit(self, pos, value):
        self._digits[pos] = value

    def show(self):
        pass


# Mock du module board (pins du Pico)
board_mock = MagicMock()
board_mock.GP5 = "GP5"
board_mock.GP6 = "GP6"
board_mock.GP7 = "GP7"

# Mock du module busio (SPI, I2C, UART)
busio_mock = MagicMock()
busio_mock.SPI = MockSPI

# Mock du module digitalio (pins numériques)
digitalio_mock = MagicMock()
digitalio_mock.DigitalInOut = MockDigitalInOut

# Mock de la bibliothèque MAX7219
adafruit_max7219_mock = MagicMock()
adafruit_max7219_mock.bcddigits.BCDDigits = MockBCDDigits

sys.modules["board"] = board_mock
sys.modules["busio"] = busio_mock
sys.modules["digitalio"] = digitalio_mock
sys.modules["adafruit_max7219"] = adafruit_max7219_mock
sys.modules["adafruit_max7219.bcddigits"] = adafruit_max7219_mock.bcddigits
