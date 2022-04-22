from transition import LCDTransition

class NoneLCDTransition(LCDTransition):
    def render(self) -> bool:
        self.running = False
        return False

TRANSITION = NoneLCDTransition
