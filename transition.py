from abc import ABC, abstractmethod
from datetime import datetime

from numpy import byte

class LCDTransition(ABC):
    from_data: bytearray
    to_data: bytearray
    data: bytearray
    period: int
    start_time: datetime
    running: bool
    progress: float
    width: int
    height: int
    pixels: int

    def __init__(self, config):
        self.period = 1
        if "period" in config:
            self.period = config["period"]
        self.progress = 1
        self.running = False

    def start(self, from_data: bytearray, to_data: bytearray, width: int, height: int):
        self.from_data = from_data
        self.to_data = to_data
        self.data = from_data.copy()
        self.start_time = datetime.now()
        self.width = width
        self.height = height
        self.pixels = width * height
        self.progress = 0
        self.running = True
        self.on_start()

    def update_target(self, to_data: byte):
        self.to_data = to_data
        self.on_update_target()

    def on_update_target(self) -> None:
        pass

    def stop(self):
        self.running = False
        self.progress = 1
        self.data = self.to_data.copy()

    def on_start(self) -> None:
        pass

    @abstractmethod
    def render(self) -> bool:
        self.progress = (datetime.now() - self.start_time).total_seconds() / self.period
        if self.progress >= 1:
            self.running = False
            return False
        
        return True
