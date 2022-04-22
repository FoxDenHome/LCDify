from driver import LCDDriver
from page import LCDPage
from prometheus import query_prometheus

class PingRTTLCDPage(LCDPage):
    def __init__(self):
        super().__init__("PING RTT")

    def _set_rtt_led(self, driver: LCDDriver, idx: int, rtt: float, warn: float, crit: float):
        if rtt < warn:
            driver.set_led(idx, 0, 10)
        elif rtt < crit:
            driver.set_led(idx, 5, 10)
        else:
            driver.set_led(idx, 10, 0)

    def render(self, driver: LCDDriver):
        super().render(driver)
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

        self._set_rtt_led(driver, 1, wan_rtt, 10, 50)
        self._set_rtt_led(driver, 2, eth_rtt, 10, 50)
        self._set_rtt_led(driver, 3, lte_rtt, 100, 300)

        driver.set_line(1, f"WAN {wan_rtt:3.0f} ms")
        driver.set_line(2, f"ETH {eth_rtt:3.0f} ms")
        driver.set_line(3, f"LTE {lte_rtt:3.0f} ms")

PAGE = PingRTTLCDPage
