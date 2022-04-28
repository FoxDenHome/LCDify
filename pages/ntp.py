from drivers.paged import PagedLCDDriver
from page_updating import UpdatingLCDPage
from prometheus import query_prometheus_first_value
from utils import LEDColorPreset

class NTPLCDPage(UpdatingLCDPage):
    def __init__(self, config, driver: PagedLCDDriver):
        super().__init__(config, driver, "NTP")

    def update(self):
        ntp_estimated_error_res = query_prometheus_first_value("node_timex_estimated_error_seconds{instance=\"ntp.foxden.network:9100\"}") * 1_000
        ntp_ppm_adjustment_res = query_prometheus_first_value("(node_timex_frequency_adjustment_ratio{instance=\"ntp.foxden.network:9100\"} - 1) * 1000000")
        ntp_stratum_res = query_prometheus_first_value("node_ntp_stratum{instance=\"ntp.foxden.network:9100\"}")
        ntp_sanity_res = query_prometheus_first_value("node_ntp_sanity{instance=\"ntp.foxden.network:9100\"}") * 100

        self.set_line(1, f"Err {ntp_estimated_error_res:12.6f} ms")
        self.set_led(1, self.calc_led_upper_threshhold(ntp_estimated_error_res, 0.001, 1).value)

        self.set_line(2, f"Adj {ntp_ppm_adjustment_res:12.6f} ppm")
        self.set_led(2, self.calc_led_upper_threshhold(abs(ntp_ppm_adjustment_res), 20, 100).value)

        self.set_line(3, f"Str {ntp_stratum_res:2.0f}    /  San {ntp_sanity_res:3.0f}")
        led3_color = LEDColorPreset.NORMAL
        if ntp_stratum_res != 1:
            led3_color = LEDColorPreset.WARNING
        if ntp_sanity_res < 100:
            led3_color = LEDColorPreset.CRITICAL
        self.set_led(3, led3_color.value)

PAGE = NTPLCDPage
