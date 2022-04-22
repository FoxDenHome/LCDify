from abc import ABC, abstractmethod
from threading import Thread
from lcd import LCD
from time import sleep

class LCDDriver(ABC):
    id: int
    lcd: LCD
    _should_run: bool
    _render_period: float
    _render_thread: Thread
    _lines: list[str]
    _lcd_width: int
    _lcd_height: int
    _lcd_mem_is: bytearray
    _lcd_mem_set: bytearray

    def __init__(self, id):
        self.id = id
        self.lcd = None
        self._should_run = False
        self._render_period = 1
        self._render_thread = None
        self._lines = []

    def set_port(self, port):
        self.stop()
        self.lcd = LCD(port)
        self._lcd_width = self.lcd.width()
        self._lcd_height = self.lcd.height()
        self._lcd_mem_is = bytearray(self._lcd_width * self._lcd_height)
        self._lcd_mem_set = bytearray(self._lcd_width * self._lcd_height)

    def start(self):
        self._should_run = True
        self._render_thread = Thread(name=f'LCD render {self.lcd.port}', target=self._loop)
        self._render_thread.start()

    def stop(self):
        self._should_run = False

        if self._render_thread is not None:
            self._render_thread.join()
            self._render_thread = None

    def _loop(self):
        self.lcd.open()
        self.lcd.clear()
        self.lcd.write_led(0, 0, 0)
        self.lcd.write_led(1, 0, 0)
        self.lcd.write_led(2, 0, 0)
        self.lcd.write_led(3, 0, 0)

        self.render_init()
        while self._should_run:
            self.render()
            sleep(self._render_period)

        self.lcd.close()

    def write_at(self, col: int, row: int, content: str):
        content_bytes = content.encode('ascii')
        for i, c in enumerate(content_bytes):
            self._lcd_mem_set[(row * self._lcd_width) + col + i] = c

    def set_line(self, idx: int, content: str):
        self.write_at(0, idx, content)

    def _render_send_display(self):
        changes = []

        change_start = -1
        change_end = -1
        for i in range(self._lcd_width * self._lcd_height):
            diff = self._lcd_mem_is[i] != self._lcd_mem_set[i]
            if change_start < 0 and change_end < 0 and diff:
                change_start = i
            elif change_start >= 0 and not diff:
                if change_end < 0:
                    change_end = i
                elif i - change_end > 5:
                    changes.append((change_start, change_end))
                    change_start = -1
                    change_end = -1

        if change_start >= 0:
            if change_end < 0:
                change_end = 1 + (self._lcd_width * self._lcd_height)
            changes.append((change_start, change_end))

        self._lcd_mem_is = self._lcd_mem_set.copy()

    @abstractmethod
    def render_init(self):
        pass

    @abstractmethod
    def render(self):
        pass
