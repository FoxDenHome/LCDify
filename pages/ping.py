from drivers.paged import PagedLCDDriver
from page_updating import UpdatingLCDPage
from prometheus import query_prometheus_map_by
from utils import LEDColorPreset

class PingLCDPage(UpdatingLCDPage):
    def __init__(self, config, driver: PagedLCDDriver):
        super().__init__(config, driver, "PING RTT / LOSS")

    def _calc_loss_led(self, loss: float):
        return self.calc_led_upper_threshhold(loss, 5, 90)

    def update(self):
        ping_rtt_res = query_prometheus_map_by("ping_average_response_ms > 0")
        packet_loss_res = query_prometheus_map_by("ping_percent_packet_loss")

        self.set_led(1, LEDColorPreset.get_most_critical([
            self._calc_loss_led(packet_loss_res["internet"]),
            self.calc_led_upper_threshhold(ping_rtt_res["internet"], 10, 50)
        ]).value)
        self.set_led(2, LEDColorPreset.get_most_critical([
            self._calc_loss_led(packet_loss_res["wired"]),
            self.calc_led_upper_threshhold(ping_rtt_res["wired"], 10, 50)
        ]).value)
        self.set_led(3, LEDColorPreset.get_most_critical([
            self._calc_loss_led(packet_loss_res["lte"]),
            self.calc_led_upper_threshhold(ping_rtt_res["lte"], 100, 300)
        ]).value)

        self.set_line(1, f"WAN {ping_rtt_res['internet']:4.0f} ms / {packet_loss_res['internet']:4.0f} %")
        self.set_line(2, f"ETH {ping_rtt_res['wired']:4.0f} ms / {packet_loss_res['wired']:4.0f} %")
        self.set_line(3, f"LTE {ping_rtt_res['lte']:4.0f} ms / {packet_loss_res['lte']:4.0f} %")

PAGE = PingLCDPage
