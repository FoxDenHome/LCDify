from page import LCDPage

class DummyLCDPage(LCDPage):
    def __init__(self):
        super().__init__("DUMMY PAGE")

PAGE = DummyLCDPage
