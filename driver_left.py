from driver import LCDDriver
from ids import ID_LEFT
from prometheus import query_prometheus

class LCDDriverLeft(LCDDriver):
    def __init__(self):
        super().__init__(ID_LEFT)

    def _set_loss_led(self, idx: int, loss: float):
        if loss < 5:
            self.lcd.write_led(idx, 0, 10)
        elif loss < 90:
            self.lcd.write_led(idx, 5, 10)
        else:
            self.lcd.write_led(idx, 10, 0)

    def _render_loss(self):
        packet_loss_res = query_prometheus("ping_percent_packet_loss")
    
        lte_loss = None
        eth_loss = None
        wan_loss = None
        for loss in packet_loss_res["result"]:
            val = float(loss["value"][1])
            name = loss["metric"]["name"]

            if name == "lte":
                lte_loss = val
            elif name == "wired":
                eth_loss = val
            elif name == "internet":
                wan_loss = val

        self._set_loss_led(1, wan_loss)
        self._set_loss_led(2, eth_loss)
        self._set_loss_led(3, lte_loss)
        
        self.lcd.write(0, 0, "=== PACKET  LOSS ===")
        self.lcd.write(4, 1, f"{wan_loss:3.0f} %")
        self.lcd.write(4, 2, f"{eth_loss:3.0f} %")
        self.lcd.write(4, 3, f"{lte_loss:3.0f} %")

    def _set_rtt_led(self, idx: int, rtt: float, warn: float, crit: float):
        if rtt < warn:
            self.lcd.write_led(idx, 0, 10)
        elif rtt < crit:
            self.lcd.write_led(idx, 5, 10)
        else:
            self.lcd.write_led(idx, 10, 0)

    def _render_rtt(self):
        lte_rtt = None
        eth_rtt = None
        wan_rtt = None
        ping_rtt_res = query_prometheus("ping_average_response_ms > 0")
        for rtt in ping_rtt_res["result"]:
            val = float(rtt["value"][1])
            name = rtt["metric"]["name"]
    
            if name == "lte":
                lte_rtt = val
            elif name == "wired":
                eth_rtt = val
            elif name == "internet":
                wan_rtt = val

        self._set_rtt_led(1, wan_rtt, 10, 50)
        self._set_rtt_led(2, eth_rtt, 10, 50)
        self._set_rtt_led(3, lte_rtt, 100, 300)

        self.lcd.write(0, 0, "===== PING RTT =====")
        self.lcd.write(4, 1, f"{wan_rtt:3.0f} ms")
        self.lcd.write(4, 2, f"{eth_rtt:3.0f} ms")
        self.lcd.write(4, 3, f"{lte_rtt:3.0f} ms")

    def render_init(self):
        self.lcd.write(0, 1, "WAN ")
        self.lcd.write(0, 2, "ETH ")
        self.lcd.write(0, 3, "LTE ")

    def render(self):
        self._render_loss()
