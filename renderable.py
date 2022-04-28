DEFAULT_CHAR = ord(" ")

class Renderable():
    lcd_led_set: list[tuple[int, int]]
    lcd_mem_set: bytearray
    dirty: bool
    
    lcd_height: int
    lcd_width: int
    lcd_led_count: int
    lcd_pixel_count: int

    def __init__(self):
        self.dirty = False
        self.init_arrays(0, 0, 0)

    def init_arrays(self, height: int, width: int, led_count: int):
        self.lcd_height = height
        self.lcd_width = width
        self.lcd_pixel_count = height * width
        self.lcd_led_count = led_count
        self.lcd_led_set = [(0, 0)] * led_count
        self.lcd_mem_set = bytearray(self.lcd_pixel_count)
        for i in range(self.lcd_pixel_count):
            self.lcd_mem_set[i] = DEFAULT_CHAR
        self.dirty = True

    def set_led(self, idx: int, color: tuple[int, int]) -> None:
        self.lcd_led_set[idx] = color
        self.dirty = True

    def write_at(self, col: int, row: int, content: str) -> None:
        content_bytes = content.encode("latin-1")
        for i, c in enumerate(content_bytes):
            self.lcd_mem_set[(row * self.lcd_width) + col + i] = c
        self.dirty = True

    def set_line(self, idx: int, content: str) -> None:
        content_len = len(content)
        if content_len > self.lcd_width:
            raise ValueError(f"Line longer than LCD line width of {self.lcd_width}")
        elif content_len < self.lcd_width:
            content += " " * (self.lcd_width - content_len)
        self.write_at(0, idx, content)

    def clear(self) -> None:
        for i in range(self.lcd_pixel_count):
            self.lcd_mem_set[i] = DEFAULT_CHAR
        self.dirty = True
