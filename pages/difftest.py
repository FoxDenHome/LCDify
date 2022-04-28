from drivers.paged import PagedLCDDriver
from page_updating import UpdatingLCDPage

class DiffTestLCDPage(UpdatingLCDPage):
    def __init__(self, config, driver: PagedLCDDriver):
        super().__init__(config, driver, "DIFFTEST")
        self.update_period = 0.2
        self.i = 0
        self.x = 1

    def update(self):
        self.i += 1
        if self.i > 30:
            self.i = 0
            self.x += 1
        self.clear()
        for i in range(self.i):
            self.lcd_mem_set[self.lcd_pixel_count - (self.x + i)] = (self.i % 10) + ord('0')
        self.dirty = True

PAGE = DiffTestLCDPage
