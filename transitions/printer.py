from transition import LCDTransition

class PrinterLCDTransition(LCDTransition):
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

        target_set = round(self.pixel_count * self.progress)

        if target_set > self.set_up_to:
            for i in range(self.set_up_to, target_set):
                self.lcd_mem_set[i] = self.to_data[i]
            self.set_up_to = target_set - 1

        return self.lcd_mem_set, self.lcd_led_set

TRANSITION = PrinterLCDTransition
