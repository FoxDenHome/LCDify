from driver import LCDDriver
from page import LCDPage

class DummyLCDPage(LCDPage):
    def __init__(self, config, driver: LCDDriver):
        super().__init__(config, driver, "DUMMY PAGE")

PAGE = DummyLCDPage
