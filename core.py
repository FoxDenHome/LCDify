from glob import glob
from time import sleep
from typing import Optional
from config import CONFIG
from driver import LCDDriver
from lcd import LCD_KEY_MASK_ALL, LCDWithID
from serial.tools.list_ports import comports
from importlib import import_module

LCD_INITIAL_CONFIG_VERSION = 0x01

def initial_config(lcd: LCDWithID, id: int):
    lcd.open()
    lcd.set_backlight(10)
    lcd.set_contrast(100)
    lcd.clear()
    lcd.write_str(0,0," FoxDen Industries")
    lcd.write_str(0,1,f"=" * lcd.width())
    lcd.write_str(0,2,f"ID {id}")
    lcd.write_str(0,3,f"Init config {LCD_INITIAL_CONFIG_VERSION}")
    lcd.set_key_reporting(LCD_KEY_MASK_ALL, LCD_KEY_MASK_ALL)
    lcd.write_led(0, 0, 0)
    lcd.write_led(1, 0, 0)
    lcd.write_led(2, 0, 0)
    lcd.write_led(3, 0, 0)
    lcd.save_as_default()
    lcd.write_id_and_version(id, LCD_INITIAL_CONFIG_VERSION)
    lcd.close()

def serve_core(override_glob: Optional[str]) -> None:
    ports = None
    if override_glob:
        from serial.tools.list_ports_linux import SysFS
        ports = [SysFS(p) for p in glob(override_glob)]
    else:
        ports = comports()

    ports_by_id = {}
    ports_without_id = []
    for port in ports:
        print(f"Found port \"{port.device}\" which is \"{port.description}\"")
        if "CFA635-USB" not in port.description:
            continue
        lcd = LCDWithID(port.device)
        lcd.open()
        id, version = lcd.read_id_and_version()
        lcd.close()
        if id is not None:
            ports_by_id[id] = (port.device, version)
        else:
            ports_without_id.append(port.device)

    def find_port_by_id(id: int):
        if id in ports_by_id:
            return ports_by_id[id]
        return None, None

    def find_first_free_port():
        if len(ports_without_id) < 1:
            return None
        return ports_without_id.pop(0)

    drivers = []

    for config in CONFIG["displays"]:
        id = config["id"]
        name = config["name"]
        port, version = find_port_by_id(id)

        if port is None:
            print(f"No port found for display {name} (ID {id}). Trying to find a free port.")
            port = find_first_free_port()
            if port is None:
                print("No free ports found, either!")
                return

            print(f"Found free port {port}. Writing ID...")
            lcd = LCDWithID(port)
            initial_config(lcd, id)
            version = LCD_INITIAL_CONFIG_VERSION
            print(f"ID written to {port}!")

        if version != LCD_INITIAL_CONFIG_VERSION:
            initial_config(LCDWithID(port), id)

        driver_config = config["driver"]
        DriverClass = import_module(f"drivers.{driver_config['type']}", package=".").DRIVER
        driver: LCDDriver = DriverClass(config=driver_config)
        drivers.append(driver)
        driver.set_port(port)
        driver.start()

    while True:
        try:
            sleep(1000)
        except KeyboardInterrupt:
            break
