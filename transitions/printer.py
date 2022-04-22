from transition import LCDTransition

class PrinterLCDTransition(LCDTransition):
    set_up_to: int

    def __init__(self, config):
        super().__init__(config)
        self.set_up_to = 0

    def on_start(self):
        self.set_up_to = 0

    def render(self) -> bool:
        if not super().render():
            return False

        target_set = round(self.pixels * self.progress)

        if target_set > self.set_up_to:
            for i in range(self.set_up_to, target_set):
                self.data[i] = self.to_data[i]
            self.set_up_to = target_set - 1

        return True

TRANSITION = PrinterLCDTransition
