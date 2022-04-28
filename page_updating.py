from enum import Enum
from threading import Condition, Thread
from time import sleep
from traceback import print_exc
from drivers.paged import PagedLCDDriver
from page import LCDPage
from utils import LEDColorPreset, critical_call

class UpdateStatus(Enum):
    NONE = (LEDColorPreset.OFF, "?")
    RUNNING = (LEDColorPreset.WARNING, "\xBB")
    SUCCESS = (LEDColorPreset.OFF, "=")
    ERROR = (LEDColorPreset.CRITICAL, "!")

class UpdatingLCDPage(LCDPage):
    update_period: float
    use_led0_for_updates: bool
    use_char0_for_updates: bool
    _update_wait: Condition
    _update_thread: Thread
    _update_status: UpdateStatus

    def __init__(self, config, driver: PagedLCDDriver, default_title: str = None):
        super().__init__(config, driver, default_title)

        self.use_led0_for_updates = True
        self.use_char0_for_updates = True
        self._update_status = UpdateStatus.NONE

        self.update_period = 30
        if "update_period" in config:
            self.update_period = config["update_period"]

        self._update_wait = Condition()
        self._update_thread = None

    def start(self):
        super().start()
        self.write_at(0, 1, "Loading...")
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
            self._set_update_status(UpdateStatus.RUNNING)
            try:
                self.update()
                self._set_update_status(UpdateStatus.SUCCESS)
            except Exception:
                self._set_update_status(UpdateStatus.ERROR)
                print_exc()

            self._update_wait.acquire()
            self._update_wait.wait(self.update_period)
            self._update_wait.release()

    def _set_update_status(self, status: UpdateStatus):
        self._update_status = status
        if self.use_led0_for_updates:
            self.set_led(0, self._update_status.value[0].value)
        if self.use_char0_for_updates:
            self.write_at(0, 0, self._update_status.value[1])

    def update(self):
        pass
