from time import sleep
from drivers.left import LCDDriverLeft
from drivers.right import LCDDriverRight
from lcd import LCD_KEY_MASK_ALL, LCDWithID
from serial.tools.list_ports import comports

def initial_config(lcd: LCDWithID, id: int):
    lcd.open()
    lcd.write_id(id)
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
    lcd.close()

ports = comports()

ports_by_id = {}
ports_without_id = []
for port in ports:
    if 'CFA635-USB' not in port.description:
        continue
    lcd = LCDWithID(port.device)
    lcd.open()
    id = lcd.read_id()
    lcd.close()
    if id is not None:
        ports_by_id[id] = port.device
    else:
        ports_without_id.append(port.device)

def find_port_by_id(id: int):
    if id in ports_by_id:
        return ports_by_id[id]
    return None

def find_first_free_port():
    if len(ports_without_id) < 1:
        return None
    return ports_without_id.pop(0)

drivers = [LCDDriverLeft(), LCDDriverRight()]

for driver in drivers:
    port = find_port_by_id(driver.id)
    if port is None:
        print(f"No port found for driver {driver.id}. Trying to find a free port.")
        port = find_first_free_port()
        if port is None:
            print("No free ports found, either!")
            continue
        print(f"Found free port {port}. Writing ID...")
        lcd = LCDWithID(port)
        initial_config(lcd, driver.id)
        print(f"ID written to {port}!")

    driver.set_port(port)
    driver.start()

while True:
    try:
        sleep(1)
    except KeyboardInterrupt:
        break

for driver in drivers:
    try:
        driver.stop()
    except KeyboardInterrupt:
        pass
