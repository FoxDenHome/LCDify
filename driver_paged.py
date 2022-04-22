from driver import LCDDriver
from datetime import timedelta, datetime
from page import LCDPage

class PagedLCDDriver(LCDDriver):
    current_page: int
    pages: list[LCDPage]
    auto_cycle_time: timedelta
    last_cycle_time: datetime

    def __init__(self, id, pages: list[LCDPage], auto_cycle_time: int = 5):
        super().__init__(id)
        self.pages = pages.copy()
        self.current_page = 0
        self.auto_cycle_time = timedelta(seconds=auto_cycle_time)
        self.last_cycle_time = datetime.now()

    def next_page(self):
        self.current_page += 1
        if self.current_page >= len(self.pages):
            self.current_page = 0

    def previous_page(self):
        if self.current_page <= 0:
            self.current_page = len(self.pages) - 1
        else:
            self.current_page -= 1

    def render(self):
        now = datetime.now()
        if now - self.last_cycle_time > self.auto_cycle_time:
            self.next_page()
            self.last_cycle_time = now
        self.pages[self.current_page].render(self)

