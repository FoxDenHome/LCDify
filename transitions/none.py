from transition import Transition


class NoneTransision(Transition):
    def render(self):
        self.running = False
        return self.to_data
