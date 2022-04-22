from random import random
from driver import LCDDriver
from ids import ID_LEFT
from prometheus import query_prometheus

class LCDDriverLeft(LCDDriver):
    def __init__(self):
        super().__init__(ID_LEFT)

    def _set_loss_led(self, idx: int, loss: float):
        if loss < 5:
            self.set_led(idx, 0, 10)
        elif loss < 90:
            self.set_led(idx, 5, 10)
        else:
            self.set_led(idx, 10, 0)

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
        
        self.set_line(0, "=== PACKET  LOSS ===")
        self.set_line(1, f"WAN {wan_loss:3.0f} %")
        self.set_line(2, f"ETH {eth_loss:3.0f} %")
        self.set_line(3, f"LTE {lte_loss:3.0f} %")

    def _set_rtt_led(self, idx: int, rtt: float, warn: float, crit: float):
        if rtt < warn:
            self.set_led(idx, 0, 10)
        elif rtt < crit:
            self.set_led(idx, 5, 10)
        else:
            self.set_led(idx, 10, 0)

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

        wan_rtt = random() * 666

        self._set_rtt_led(1, wan_rtt, 10, 50)
        self._set_rtt_led(2, eth_rtt, 10, 50)
        self._set_rtt_led(3, lte_rtt, 100, 300)

        self.set_line(0, "===== PING RTT =====")
        self.set_line(1, f"WAN {wan_rtt:3.0f} ms  {wan_rtt:3.0f}")
        self.set_line(2, f"ETH {eth_rtt:3.0f} ms")
        self.set_line(3, f"LTE {lte_rtt:3.0f} ms")

    def render_init(self):
        pass

    def render(self):
        self._render_rtt()
