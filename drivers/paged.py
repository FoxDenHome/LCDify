from importlib import import_module
from driver import LCDDriver
from datetime import timedelta, datetime
from page import LCDPage

class PagedLCDDriver(LCDDriver):
    current_page: int
    pages: list[LCDPage]
    auto_cycle_time: timedelta
    last_cycle_time: datetime

    def __init__(self, config):
        # pages: list[LCDPage]
        super().__init__(config)
        auto_cycle_time = 5
        if "auto_cycle_time" in config:
            auto_cycle_time = config["auto_cycle_time"]

        page_types = config["pages"]
        self.pages = []
        for page_type in page_types:
            PageClass = import_module(f"pages.{page_type}", package=".").PAGE
            self.pages.append(PageClass())

        self.current_page = 0
        if auto_cycle_time > 0:
            self.auto_cycle_time = timedelta(seconds=auto_cycle_time)
        else:
            self.auto_cycle_time = None

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
        if self.auto_cycle_time is not None and now - self.last_cycle_time > self.auto_cycle_time:
            self.next_page()
            self.last_cycle_time = now
        self.pages[self.current_page].render(self)

DRIVER = PagedLCDDriver
