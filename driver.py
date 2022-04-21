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

    def __init__(self, id):
        self.id = id
        self.lcd = None
        self._should_run = False
        self._render_period = 1
        self._render_thread = None

    def set_port(self, port):
        self.stop()
        self.lcd = LCD(port)

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

    @abstractmethod
    def render_init(self):
        pass

    @abstractmethod
    def render(self):
        pass
