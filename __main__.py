from time import sleep
from lcd import LCD

lcd = LCD('COM18')
lcd.open()
print(lcd.ping())
print(lcd.set_backlight(10))
print(lcd.set_contrast(100))
lcd.clear()
lcd.write(0,0,"FoxDen Industries")
print(lcd.version())

lcd.write_led(0, 100, 100)
lcd.write_led(1, 100, 100)
lcd.write_led(2, 100, 100)
lcd.write_led(3, 100, 100)