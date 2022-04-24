from drivers.paged import PagedLCDDriver
from page import LCDPage

class DummyLCDPage(LCDPage):
    def __init__(self, config, driver: PagedLCDDriver):
        super().__init__(config, driver, "DUMMY PAGE")

PAGE = DummyLCDPage
