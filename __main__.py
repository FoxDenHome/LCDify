from time import sleep
from lcd import LCD, LCD_KEY_MASK_ALL

lcd = LCD('COM18')

def initial_config(lcd: LCD):
    lcd.set_backlight(10)
    lcd.set_contrast(100)
    lcd.clear()
    lcd.write(0,0,"FoxDen Industries")
    lcd.set_key_reporting(LCD_KEY_MASK_ALL, LCD_KEY_MASK_ALL)
    lcd.write_led(0, 0, 0)
    lcd.write_led(1, 0, 0)
    lcd.write_led(2, 0, 0)
    lcd.write_led(3, 0, 0)
    lcd.save_as_default()

lcd.open()
print(lcd.ping())
lcd.clear()
lcd.write(0,0,"FoxDen Industries")
print(lcd.version())

initial_config(lcd)

lcd.write_led(0, 100, 100)
lcd.write_led(1, 100, 100)
lcd.write_led(2, 100, 100)
lcd.write_led(3, 100, 100)

lcd.register_key_press_handler(lambda x, y: print(x, y))

sleep(10)
