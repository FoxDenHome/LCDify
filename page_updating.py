from enum import Enum
from threading import Condition, Thread
from traceback import print_exc
from drivers.paged import PagedLCDDriver
from page import LCDPage
from utils import LEDColorPreset, critical_call

class UpdateStatus(Enum):
    NONE = LEDColorPreset.OFF
    RUNNING = LEDColorPreset.WARNING
    SUCCESS = LEDColorPreset.NORMAL
    ERROR = LEDColorPreset.CRITICAL

class UpdatingLCDPage(LCDPage):
    update_period: float
    use_led0_for_updates: bool
    _update_wait: Condition
    _update_thread: Thread
    _first_update: bool
    _update_status: UpdateStatus
    _had_update: bool

    def __init__(self, config, driver: PagedLCDDriver, default_title: str = None):
        super().__init__(config, driver, default_title)

        self.use_led0_for_updates = True
        self._update_status = UpdateStatus.NONE

        self.update_period = 30
        if "update_period" in config:
            self.update_period = config["update_period"]

        self._update_wait = Condition()
        self._update_thread = None

    def start(self):
        super().start()
        self._first_update = True
        self._had_update = True
        self._update_thread = Thread(name=f"LCD page update {self.title}", target=critical_call, args=(self._update_loop,))
        self._update_thread.start()

    def stop(self):
        super().stop()
        self._update_wait.acquire()
        self._update_wait.notify()
        self._update_wait.release()
        if self._update_thread is not None:
            self._update_thread.join()
            self._update_thread = None

    def _update_loop(self):
        while self.should_run:
            self._set_updating_led(LEDColorPreset.WARNING)
            try:
                self.update()
                self._had_update = True
                self._set_updating_led(LEDColorPreset.OFF)
                if not self.use_led0_for_updates:
                    self.do_render_if_current()
            except Exception:
                self._set_updating_led(LEDColorPreset.CRITICAL)
                print_exc()

            self._update_wait.acquire()
            self._update_wait.wait(self.update_period)
            self._update_wait.release()

    def _set_updating_led(self, status: UpdateStatus):
        self._update_status = status
        if self.use_led0_for_updates:
            self.do_render_if_current()

    def render(self):
        super().render()
        if self.use_led0_for_updates:
            self.driver.set_led(0, self._update_status.value)

        if self._had_update:
            self._had_update = False
            self.render_on_update()

    def render_on_update(self):
        pass

    def update(self):
        pass
