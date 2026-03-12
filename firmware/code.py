import board
import busio
import digitalio
from adafruit_max7219.bcddigits import BCDDigits

# SPI1 : GP10=CLK, GP11=DATA(MOSI), GP9=LOAD(CS)
spi = busio.SPI(clock=board.GP10, MOSI=board.GP11)
cs = digitalio.DigitalInOut(board.GP9)

display = BCDDigits(spi, cs, nDigits=4)