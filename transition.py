from abc import ABC, abstractmethod
from datetime import datetime

class LCDTransition(ABC):
    from_data: bytearray
    to_data: bytearray
    from_leds: list[tuple[int, int]]
    to_leds: list[tuple[int, int]]
    data: bytearray
    leds: list[tuple[int, int]]
    period: int
    start_time: datetime
    running: bool
    progress: float
    width: int
    height: int
    pixel_count: int
    custom_led_transition: bool

    def __init__(self, config):
        self.period = 1
        if "period" in config:
            self.period = config["period"]
        self.progress = 1
        self.running = False
        self.custom_led_transition = False

    def start(self, from_data: bytearray, to_data: bytearray, from_leds: list[tuple[int, int]], to_leds: list[tuple[int, int]], width: int, height: int):
        self.from_data = from_data
        self.to_data = to_data
        self.from_leds = from_leds
        self.to_leds = to_leds
        self.data = from_data.copy()
        self.leds = from_leds.copy()
        self.start_time = datetime.now()
        self.width = width
        self.height = height
        self.pixel_count = width * height
        self.progress = 0
        self.running = True
        self.on_start()

    def update_target(self, to_data: bytearray):
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

    def linear_transition(self, from_num: int, to_num: int) -> None:
        return from_num + ((to_num - from_num,) * self.progress)

    def render_leds_simple(self) -> None:
        for idx, from_led in enumerate(self.from_leds):
            self.leds[idx] = (
                self.linear_transition(from_led[0], self.to_leds[idx][0]),
                self.linear_transition(from_led[1], self.to_leds[idx][1]),
            )

    @abstractmethod
    def render(self) -> bool:
        self.progress = (datetime.now() - self.start_time).total_seconds() / self.period
        if self.progress >= 1:
            self.running = False
            return False

        if not self.custom_led_transition:
            self.render_leds_simple()

        return True
