from driver import LCDDriver
from page import LCDPage
from prometheus import query_prometheus

class PingPacketLossLCDPage(LCDPage):
    def __init__(self):
        super().__init__("PACKET LOSS")

    def _set_loss_led(self, driver: LCDDriver, idx: int, loss: float):
        if loss < 5:
            driver.set_led(idx, 0, 10)
        elif loss < 90:
            driver.set_led(idx, 5, 10)
        else:
            driver.set_led(idx, 10, 0)

    def render(self, driver: LCDDriver):
        super().render(driver)
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

        self._set_loss_led(driver, 1, wan_loss)
        self._set_loss_led(driver, 2, eth_loss)
        self._set_loss_led(driver, 3, lte_loss)
        
        driver.set_line(0, "=== PACKET  LOSS ===")
        driver.set_line(1, f"WAN {wan_loss:3.0f} %")
        driver.set_line(2, f"ETH {eth_loss:3.0f} %")
        driver.set_line(3, f"LTE {lte_loss:3.0f} %")

PAGE = PingPacketLossLCDPage
