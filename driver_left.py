from driver import LCDDriver
from ids import ID_LEFT
from prometheus import query_prometheus

class LCDDriverLeft(LCDDriver):
    def __init__(self):
        super().__init__(ID_LEFT)

    def _set_loss_led(self, idx: int, loss: int):
        if loss == 0:
            self.lcd.write_led(idx, 0, 10)
        elif loss <= 10:
            self.lcd.write_led(idx, 5, 10)
        else:
            self.lcd.write_led(idx, 10, 0)

    def _render_loss(self):
        ping_res = query_prometheus("ping_percent_packet_loss")
        lte_loss = None
        wired_loss = None
        internet_loss = None
        for ping in ping_res["result"]:
            val = int(ping["value"][1], 10)
            name = ping["metric"]["name"]

            if name == "lte":
                lte_loss = val
            elif name == "wired":
                wired_loss = val
            elif name == "internet":
                internet_loss = val

        self._set_loss_led(0, internet_loss)
        self._set_loss_led(1, wired_loss)
        self._set_loss_led(2, lte_loss)

    def render(self):
        self._render_loss()
