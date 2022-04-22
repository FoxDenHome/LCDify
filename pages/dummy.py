from page import LCDPage

class DummyLCDPage(LCDPage):
    def __init__(self, config):
        super().__init__(config, "DUMMY PAGE")

PAGE = DummyLCDPage
