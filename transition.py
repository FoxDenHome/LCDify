from abc import ABC, abstractmethod
from datetime import datetime

class Transition(ABC):
    from_data: bytearray
    to_data: bytearray
    period: int
    start_time: datetime
    running: bool

    def __init__(self, config):
        self.period = 1
        self.running = False

    def start(self, from_data: bytearray, to_data: bytearray):
        self.from_data = from_data
        self.to_data = to_data
        self.start_time = datetime.now()
        self.running = True

    @abstractmethod
    def render(self) -> bytearray:
        pass
