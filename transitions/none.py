from transition import Transition


class NoneTransision(Transition):
    def render(self) -> bool:
        self.running = False
        return False
