from driver import PagedLCDDriver
from ids import ID_RIGHT
from pages.dummy import DummyLCDPage

class LCDDriverRight(PagedLCDDriver):
    def __init__(self):
        super().__init__(ID_RIGHT, [DummyLCDPage()])
