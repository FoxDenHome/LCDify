from drivers.paged import PagedLCDDriver
from page_updating import UpdatingLCDPage
from prometheus import query_prometheus_first_value
from utils import LEDColorPreset

class NTPLCDPage(UpdatingLCDPage):
    def __init__(self, config, driver: PagedLCDDriver):
        super().__init__(config, driver, "NTP")
        self.ntp_estimated_error_res = None
        self.ntp_ppm_adjustment_res = None
        self.ntp_stratum_res = None
        self.ntp_sanity_res = None

    def update(self):
        ntp_estimated_error_res = query_prometheus_first_value("node_timex_estimated_error_seconds{instance=\"ntp.foxden.network:9100\"}")
        ntp_ppm_adjustment_res = query_prometheus_first_value("(node_timex_frequency_adjustment_ratio{instance=\"ntp.foxden.network:9100\"} - 1) * 1000000")
        ntp_stratum_res = query_prometheus_first_value("node_ntp_stratum{instance=\"ntp.foxden.network:9100\"}")
        ntp_sanity_res = query_prometheus_first_value("node_ntp_sanity{instance=\"ntp.foxden.network:9100\"}")

        self.ntp_estimated_error_res = ntp_estimated_error_res
        self.ntp_ppm_adjustment_res = ntp_ppm_adjustment_res
        self.ntp_stratum_res = ntp_stratum_res
        self.ntp_sanity_res = ntp_sanity_res * 100

    def render_on_update(self):
        if self.ntp_estimated_error_res is None or self.ntp_ppm_adjustment_res is None:
            self.driver.set_line(1, "Loading...")
            return

        estimated_error_ms = self.ntp_estimated_error_res * 1_000

        self.driver.set_line(1, f"Err {estimated_error_ms:12.6f} ms")
        self.driver.set_led(1, self.calc_led_upper_threshhold(estimated_error_ms, 0.001, 1).value)

        self.driver.set_line(2, f"Adj {self.ntp_ppm_adjustment_res:12.6f} ppm")
        self.driver.set_led(2, self.calc_led_upper_threshhold(abs(self.ntp_ppm_adjustment_res), 20, 100).value)

        self.driver.set_line(3, f"Str {self.ntp_stratum_res:2.0f}    /  San {self.ntp_sanity_res:3.0f}")
        led3_color = LEDColorPreset.NORMAL
        if self.ntp_stratum_res != 1:
            led3_color = LEDColorPreset.WARNING
        if self.ntp_sanity_res < 100:
            led3_color = LEDColorPreset.CRITICAL
        self.driver.set_led(3, led3_color.value)

PAGE = NTPLCDPage
