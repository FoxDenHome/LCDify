from abc import ABC, abstractmethod
from importlib import import_module
from threading import Thread
from time import sleep
from lcd import LCD, LCDKey, LCDKeyEvent
from utils import critical_call
from renderable import DEFAULT_CHAR

MIN_SPACING_BETWEEN_DIFFS = 5

_MIN_SPACING_VAR = MIN_SPACING_BETWEEN_DIFFS - 1

class LCDDriver(ABC):
    id: int

    _lcd: LCD
    _should_run: bool
    _render_period: float
    _render_thread: Thread
    _lines: list[str]
    _lcd_mem_is: bytearray
    _lcd_led_is: list[tuple[int, int]]

    lcd_width: int
    lcd_height: int
    lcd_led_count: int
    lcd_change_max_len: int

    def __init__(self, config):
        self.lcd = None
        self._should_run = False
        self._render_period = 1.0 / 30.0
        if "render_period" in config:
            self._render_period = config["render_period"]
        self._render_thread = None
        self._lines = []
        self._lcd = None

    def set_port(self, port):
        self.stop()
        self._lcd = LCD(port)
        self._lcd.register_key_event_handler(self._key_event_handler)

    def start(self):
        self._lcd.open()
        self.lcd_width = self._lcd.width()
        self.lcd_height = self._lcd.height()
        self.lcd_led_count = self._lcd.led_count()
        self.lcd_change_max_len = self._lcd.max_write_len()
        self._should_run = True
        self._render_thread = Thread(name=f"LCD render {self._lcd.port}", target=critical_call, args=(self._loop,), daemon=True)
        self._render_thread.start()

    def stop(self):
        self._should_run = False

        if self._render_thread is not None:
            self._render_thread.join()
            self._render_thread = None

        if self._lcd is not None:
            self._lcd.close()

    def _key_event_handler(self, key: LCDKey, event: LCDKeyEvent):
        if event == LCDKeyEvent.PRESSED:
            self.on_key_down(key=key)
            self.on_key_press(key=key)
        elif event == LCDKeyEvent.RELEASED:
            self.on_key_up(key=key)

    def on_key_down(self, key: LCDKey):
        pass

    def on_key_up(self, key: LCDKey):
        pass

    def on_key_press(self, key: LCDKey):
        pass

    def _loop(self):
        self._lcd.clear()
        for i in range(self.lcd_led_count):
            self._lcd.write_led(i, 0, 0)

        self.lcd_pixel_count = self.lcd_width * self.lcd_height
        self._lcd_mem_is = bytearray(self.lcd_pixel_count)
        for i in range(self.lcd_pixel_count):
            self._lcd_mem_is[i] = DEFAULT_CHAR

        self._lcd_led_is = [(0, 0)] * self.lcd_led_count

        self.render_init()
        while self._should_run:
            data, leds = self.render()

            if data is not None:
                self._render_send_display(data)
            if leds is not None:
                self._render_send_leds(leds)

            sleep(self._render_period)

        self._lcd.close()

    def _render_send_leds(self, leds: list[tuple[int, int]]):
        for idx, (red, green) in enumerate(leds):
            old_red, old_green = self._lcd_led_is[idx]
            if old_red == red and old_green == green:
                continue
            self._lcd.write_led(idx, red, green)
            self._lcd_led_is[idx] = (red, green)

    def _render_send_display(self, data: bytearray):
        data = data.copy()

        changes: list[tuple[int, int]] = []

        change_start = -1
        change_end = -1
        for i in range(self.lcd_pixel_count):
            diff = self._lcd_mem_is[i] != data[i]
            if diff:
                if change_start < 0:
                    change_start = i
                elif i - change_start >= self.lcd_change_max_len:
                    if change_end < 0:
                        change_end = i
                    changes.append((change_start, change_end))
                    change_start = i
                    change_end = -1
                elif change_end >= 0:
                    change_end = -1
            elif change_start >= 0:
                if change_end < 0:
                    change_end = i
                
                if i - change_end >= _MIN_SPACING_VAR:
                    changes.append((change_start, change_end))
                    change_start = -1
                    change_end = -1

        if change_start >= 0:
            if change_end < 0:
                change_end = self.lcd_pixel_count
            changes.append((change_start, change_end))

        for start, end in changes:
            self._lcd.write(start % self.lcd_width, start // self.lcd_width, data[start:end])

        self._lcd_mem_is = data

    def render_init(self):
        pass

    @abstractmethod
    def render(self, force=True) -> tuple[bytearray, list[tuple[int, int]]]:
        pass
