from time import sleep
from lcd import LCD

lcd = LCD('COM18')
lcd.open()
print(lcd.ping())
print(lcd.set_backlight(10))
print(lcd.set_contrast(100))
print(lcd.version())

lcd.clear()
lcd.write(0, 0, "\x01\x02\x03\x04\x05\x06\x07\x08")
