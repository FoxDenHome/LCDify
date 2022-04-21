from driver import LCDDriver
from ids import ID_RIGHT

class LCDDriverRight(LCDDriver):
    def __init__(self):
        super().__init__(ID_RIGHT)

    def render(self):
        pass
