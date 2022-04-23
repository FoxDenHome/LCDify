from lib2to3.pgen2.driver import Driver
from threading import Condition, Thread
from page import LCDPage

class UpdatingLCDPage(LCDPage):
    update_period: float
    _update_wait: Condition
    _update_thread: Thread

    def __init__(self, config, driver: Driver, default_title: str = None):
        super().__init__(config, driver, default_title)

        self.update_period = 30
        if "update_period" in config:
            self.update_period = config["update_period"]

        self._update_wait = Condition()
        self._update_thread = None

    def start(self):
        super().start()
        self._update_thread = Thread(name=f"LCD page update {self.title}", target=self._update_loop)
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
            self.update()

            self._update_wait.acquire()
            self._update_wait.wait(self.update_period)
            self._update_wait.release()

    def update(self):
        pass
