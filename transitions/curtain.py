from transition import LCDTransition

class CurtainLCDTransition(LCDTransition):
    set_up_to: int

    def __init__(self, config):
        super().__init__(config)
        self.set_up_to = 0

    def on_start(self):
        self.set_up_to = 0

    def on_update_target(self):
        self.set_up_to = 0

    def render(self):
        if not super().render():
            return None, None

        if self.progress < 0.5:
            curtain_char_count = round(self.lcd_width * self.progress) # Would be progress * 2 and width // 2
            curtain_chars = "\x1F" * curtain_char_count
            for i in range(self.lcd_height):
                self.write_at(0, i, curtain_chars)
                self.write_at(self.lcd_width - curtain_char_count, i, curtain_chars)
        elif self.progress > 0.5:
            curtain_char_count = round(self.lcd_width * (1.0 - self.progress)) # Would be progress * 2 and width // 2
            curtain_chars = "\x1F" * curtain_char_count
            self.lcd_mem_set = self.to_data.copy()
            for i in range(self.lcd_height):
                self.write_at(0, i, curtain_chars)
                self.write_at(self.lcd_width - curtain_char_count, i, curtain_chars)
        else:
            self.lcd_mem_set = self.to_data.copy()

        return self.lcd_mem_set, self.lcd_led_set

TRANSITION = CurtainLCDTransition
