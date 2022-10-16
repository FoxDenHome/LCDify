from drivers.paged import PagedLCDDriver
from page_updating import UpdatingLCDPage
from prometheus import query_prometheus_map_by
from utils import LEDColorPreset

class PingLCDPage(UpdatingLCDPage):
    def __init__(self, config, driver: PagedLCDDriver):
        super().__init__(config, driver, "PING RTT / LOSS")

    def _calc_loss_led(self, packet_loss_res, iface: str, loss: float):
        return self.calc_led_upper_threshhold(loss, 5, 90)

    def _make_line_res(self, idx: int, name: str, ping_rtt_res, packet_loss_res, iface: str, ping_warn: int, ping_crit: int):
        packet_loss = 100
        ping_rtt = 9999
        if iface in ping_rtt_res:
            ping_rtt = ping_rtt_res[iface]
        if iface in packet_loss_res:
            packet_loss = packet_loss_res[iface]

        self.set_led(idx, LEDColorPreset.get_most_critical([
            self.calc_led_upper_threshhold(packet_loss, 5, 90),
            self.calc_led_upper_threshhold(ping_rtt, ping_warn, ping_crit)
        ]).value)

        self.set_line(idx, f"{name} {ping_rtt:4.0f} ms / {packet_loss:4.0f} %")

    def update(self):
        ping_rtt_res = query_prometheus_map_by("ping_average_response_ms > 0")
        packet_loss_res = query_prometheus_map_by("ping_percent_packet_loss")

        self._make_line_res(1, "WAN", ping_rtt_res, packet_loss_res, "internet", 10, 50)
        self._make_line_res(2, "ETH", ping_rtt_res, packet_loss_res, "wired", 10, 50)
        #self._make_line_res(3, "LTE", ping_rtt_res, packet_loss_res, "lte", 100, 300)

PAGE = PingLCDPage
