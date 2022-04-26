from drivers.paged import PagedLCDDriver
from page_updating import UpdatingLCDPage
from prometheus import query_prometheus_first_value
from utils import LEDColorPreset

CONVERT_BYTES_TO_MB = 1024 * 1024

LTE_DATA_LIMIT = 2000

class LTELCDPage(UpdatingLCDPage):
    def __init__(self, config, driver: PagedLCDDriver):
        super().__init__(config, driver, "LTE (MB)")
        self.lte_rsrp = None
        self.lte_rsrq = None
        self.lte_rssi = None
        self.lte_snr = None

        self.lte_rx = None
        self.lte_tx = None

    def update(self):
        lte_rsrp = query_prometheus_first_value("modem_signal_lte_rsrp")
        lte_rsrq = query_prometheus_first_value("modem_signal_lte_rsrq")
        lte_rssi = query_prometheus_first_value("modem_signal_lte_rssi")
        lte_snr = query_prometheus_first_value("modem_signal_lte_snr")
        
        lte_rx = query_prometheus_first_value("increase(node_network_receive_bytes_total{instance=\"router.foxden.network:9100\",device=\"wwan0\"}[30d])")
        lte_tx = query_prometheus_first_value("increase(node_network_transmit_bytes_total{instance=\"router.foxden.network:9100\",device=\"wwan0\"}[30d])")

        self.lte_rsrp = lte_rsrp
        self.lte_rsrq = lte_rsrq
        self.lte_rssi = lte_rssi
        self.lte_snr = lte_snr
        self.lte_rx = lte_rx / CONVERT_BYTES_TO_MB
        self.lte_tx = lte_tx / CONVERT_BYTES_TO_MB

    def render_on_update(self):
        if self.lte_rsrp is None or self.lte_rsrq is None or self.lte_rssi is None or self.lte_snr is None or self.lte_rx is None or self.lte_tx is None:
            self.driver.set_line(1, "Loading...")
            return

        self.driver.set_led(1, LEDColorPreset.get_most_critical([
            self.calc_led_lower_threshhold(self.lte_rsrp, -90, -100),
            self.calc_led_lower_threshhold(self.lte_rsrq, -15, -20)
        ]).value)
        self.driver.set_line(1, f"RSRP {self.lte_rsrp:4.0f} / RSRQ {self.lte_rsrq:3.0f}")
        
        self.driver.set_led(2, LEDColorPreset.get_most_critical([
            self.calc_led_lower_threshhold(self.lte_rssi, -75, -85),
            self.calc_led_lower_threshhold(self.lte_snr, 13, 0)
        ]).value)
        self.driver.set_line(2, f"RSSI {self.lte_rssi:4.0f} / SNR  {self.lte_snr:3.0f}")
        
        self.driver.set_led(3, self.calc_led_upper_threshhold(self.lte_rx + self.lte_tx, LTE_DATA_LIMIT * 0.75, LTE_DATA_LIMIT).value)
        self.driver.set_line(3, f"RX  {self.lte_rx:5.0f} / TX {self.lte_tx:5.0f}")

PAGE = LTELCDPage
