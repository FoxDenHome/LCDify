from importlib import import_module
from driver import LCDDriver
from datetime import timedelta, datetime
from lcd import LCDKey
from page import LCDPage

class PagedLCDDriver(LCDDriver):
    current_page: int
    pages: list[LCDPage]
    auto_cycle_time: timedelta
    last_cycle_time: datetime

    def __init__(self, config):
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

    def on_key_press(self, key: LCDKey):
        if key == LCDKey.DOWN:
            self.next_page()
        elif key == LCDKey.UP:
            self.previous_page()
        self.do_render()

    def set_page(self, page: int):
        self.last_cycle_time = datetime.now()
        self.current_page = page % len(self.pages)

    def next_page(self):
        self.set_page(self.current_page + 1)

    def previous_page(self):
        self.set_page(self.current_page - 1)

    def render(self):
        if self.auto_cycle_time is not None and datetime.now() - self.last_cycle_time > self.auto_cycle_time:
            self.next_page()
        self.pages[self.current_page].render(self)

DRIVER = PagedLCDDriver
