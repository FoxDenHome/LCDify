from driver import LCDDriver
from page_updating import UpdatingLCDPage
from prometheus import query_prometheus

class PingPacketLossLCDPage(UpdatingLCDPage):
    def __init__(self, config, driver: LCDDriver):
        super().__init__(config, driver, "PACKET LOSS")
        self.packet_loss_res = None

    def _set_loss_led(self, idx: int, loss: float):
        if loss < 5:
            self.driver.set_led(idx, 0, 10)
        elif loss < 90:
            self.driver.set_led(idx, 5, 10)
        else:
            self.driver.set_led(idx, 10, 0)

    def update(self):
        self.packet_loss_res = query_prometheus("ping_percent_packet_loss")

    def render(self):
        super().render()

        if self.packet_loss_res is None:
            self.driver.set_line(1, "Loading...")
            return

        lte_loss = None
        eth_loss = None
        wan_loss = None
        for loss in self.packet_loss_res["result"]:
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
        
        self.driver.set_line(1, f"WAN {wan_loss:3.0f} %")
        self.driver.set_line(2, f"ETH {eth_loss:3.0f} %")
        self.driver.set_line(3, f"LTE {lte_loss:3.0f} %")

PAGE = PingPacketLossLCDPage
