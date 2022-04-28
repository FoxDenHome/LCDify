from transition import LCDTransition

class NoneLCDTransition(LCDTransition):
    def render(self):
        self.running = False
        return None, None

TRANSITION = NoneLCDTransition
