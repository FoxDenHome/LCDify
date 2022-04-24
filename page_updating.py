from threading import Condition, Thread
from traceback import print_exc
from driver import LCDDriver
from page import LCDPage
from utils import LEDColorPreset, critical_call

class UpdatingLCDPage(LCDPage):
    update_period: float
    use_led0_for_updates: bool
    _update_wait: Condition
    _update_thread: Thread

    def __init__(self, config, driver: LCDDriver, default_title: str = None):
        super().__init__(config, driver, default_title)

        self.use_led0_for_updates = True

        self.update_period = 30
        if "update_period" in config:
            self.update_period = config["update_period"]

        self._update_wait = Condition()
        self._update_thread = None

    def start(self):
        super().start()
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
                self._set_updating_led(LEDColorPreset.OFF)
            except Exception:
                self._set_updating_led(LEDColorPreset.CRITICAL)
                print_exc()

            self._update_wait.acquire()
            self._update_wait.wait(self.update_period)
            self._update_wait.release()

    def _set_updating_led(self, updating_color: LEDColorPreset):
        if not self.use_led0_for_updates:
            return
        self.driver.set_led(0, updating_color.value)
        self.driver.do_render()

    def update(self):
        pass
