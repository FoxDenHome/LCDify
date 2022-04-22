from abc import ABC, abstractmethod
from datetime import datetime

class Transition(ABC):
    from_data: bytearray
    to_data: bytearray
    data: bytearray
    period: int
    start_time: datetime
    running: bool
    progress: float

    def __init__(self, config):
        self.period = 1
        self.progress = 0
        self.running = False

    def start(self, from_data: bytearray, to_data: bytearray):
        self.from_data = from_data
        self.to_data = to_data
        self.data = from_data.copy()
        self.start_time = datetime.now()
        self.progress = 0
        self.running = True

    def progress(self) -> float:
        return

    @abstractmethod
    def render(self) -> bool:
        self.progess = (datetime.now() - self.start_time).total_seconds() / self.period
        if self.progress >= 1:
            self.running = False
            return False
        return True
