from abc import ABC, abstractmethod
from threading import Thread, Condition
from lcd import LCD, LCDKey, LCDKeyEvent

DEFAULT_CHAR = ord(" ")
MIN_SPACING_BETWEEN_DIFFS = 5
CHANGE_MAX_LEN = 20

_MIN_SPACING_VAR = MIN_SPACING_BETWEEN_DIFFS - 1

class LCDDriver(ABC):
    id: int
    lcd_width: int
    lcd_height: int
    lcd_led_count: int
    lcd_pixel_count: int

    _lcd: LCD
    _should_run: bool
    _render_period: float
    _render_thread: Thread
    _lines: list[str]
    _lcd_mem_is: bytearray
    _lcd_mem_set: bytearray
    _lcd_led_states: list[tuple]
    _render_wait: Condition

    def __init__(self, config):
        self.lcd = None
        self._should_run = False
        self._render_period = 1
        self._render_thread = None
        self._lines = []
        self._render_wait = Condition()

    def set_port(self, port):
        self.stop()
        self._lcd = LCD(port)
        self._lcd.register_key_event_handler(self._key_event_handler)

    def start(self):
        self._should_run = True
        self._render_thread = Thread(name=f"LCD render {self._lcd.port}", target=self._loop)
        self._render_thread.start()

    def stop(self):
        self._should_run = False

        if self._render_thread is not None:
            self.do_render()
            self._render_thread.join()
            self._render_thread = None

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

    def do_render(self):
        self._render_wait.acquire()
        self._render_wait.notify()
        self._render_wait.release()

    def _loop(self):
        self._lcd.open()

        self.lcd_width = self._lcd.width()
        self.lcd_height = self._lcd.height()
        self.lcd_led_count = self._lcd.led_count()

        self._lcd.clear()

        self.lcd_pixel_count = self.lcd_width * self.lcd_height
        self._lcd_mem_is = bytearray(self.lcd_pixel_count)
        self._lcd_mem_set = bytearray(self.lcd_pixel_count)
        for i in range(self.lcd_pixel_count):
            self._lcd_mem_is[i] = DEFAULT_CHAR
            self._lcd_mem_set[i] = DEFAULT_CHAR

        self._lcd_led_states = [(-1, -1)] * self.lcd_led_count
        for i in range(self.lcd_led_count):
            self.set_led(i, 0, 0)

        self.render_init()
        while self._should_run:
            self.render()
            self._render_send_display()
            self._render_wait.acquire()
            self._render_wait.wait(self._render_period)
            self._render_wait.release()

        self._lcd.close()

    def set_led(self, idx: int, red: int, green: int) -> None:
        old_red, old_green = self._lcd_led_states[idx]
        if old_red == red and old_green == green:
            return
        self._lcd.write_led(idx, red, green)
        self._lcd_led_states[idx] = (red, green)

    def clear(self) -> None:
        for i in range(self.lcd_pixel_count):
            self._lcd_mem_set[i] = DEFAULT_CHAR

    def write_at(self, col: int, row: int, content: str) -> None:
        content_bytes = content.encode("ascii")
        for i, c in enumerate(content_bytes):
            self._lcd_mem_set[(row * self.lcd_width) + col + i] = c

    def set_line(self, idx: int, content: str) -> None:
        content_len = len(content)
        if content_len > self.lcd_width:
            raise ValueError(f"Line longer than LCD line width of {self.lcd_width}")
        elif content_len < self.lcd_width:
            content += " " * (self.lcd_width - content_len)
        self.write_at(0, idx, content)

    def _render_send_display(self):
        changes: list[tuple] = []

        change_start = -1
        change_end = -1
        for i in range(self.lcd_pixel_count):
            diff = self._lcd_mem_is[i] != self._lcd_mem_set[i]
            if diff:
                if change_start < 0:
                    change_start = i
                elif i - change_start >= CHANGE_MAX_LEN:
                    changes.append((change_start, i))
                    change_start = i
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
            self._lcd.write(start % self.lcd_width, start // self.lcd_width, self._lcd_mem_set[start:end])

        self._lcd_mem_is = self._lcd_mem_set.copy()

    def render_init(self):
        pass

    @abstractmethod
    def render(self):
        pass
