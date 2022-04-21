from driver import LCDDriver
from ids import ID_LEFT
from prometheus import query_prometheus

ACTIVE_SYMBOL = "\x10" # Arrow right

class LCDDriverLeft(LCDDriver):
    def __init__(self):
        super().__init__(ID_LEFT)

    def _set_loss_led(self, idx: int, loss: int):
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
            val = int(loss["value"][1], 10)
            name = loss["metric"]["name"]

            if name == "lte":
                lte_loss = val
            elif name == "wired":
                eth_loss = val
            elif name == "internet":
                wan_loss = val

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

        self._set_loss_led(0, wan_loss)
        self._set_loss_led(1, eth_loss)
        self._set_loss_led(2, lte_loss)
        
        eth_active = " "
        lte_active = " "
        if wan_loss < 90:
            if eth_loss < 90:
                eth_active = ACTIVE_SYMBOL
            elif lte_loss < 90:
                lte_active = ACTIVE_SYMBOL

        self.lcd.write(0, 1, f"{eth_active}")
        self.lcd.write(0, 2, f"{lte_active}")

        self.lcd.write(5, 0, f"{wan_rtt:3.0f}")
        self.lcd.write(5, 1, f"{eth_rtt:3.0f}")
        self.lcd.write(5, 2, f"{lte_rtt:3.0f}")

    def render_init(self):
        self.lcd.write(0, 0, "WAN  --- ms")
        self.lcd.write(0, 1, " ETH --- ms")
        self.lcd.write(0, 2, " LTE --- ms")

    def render(self):
        self._render_loss()
