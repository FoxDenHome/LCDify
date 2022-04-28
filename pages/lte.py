from drivers.paged import PagedLCDDriver
from page_updating import UpdatingLCDPage
from prometheus import query_prometheus_first_value
from utils import LEDColorPreset

CONVERT_BYTES_TO_MB = 1024 * 1024

LTE_DATA_LIMIT = 2000

class LTELCDPage(UpdatingLCDPage):
    def __init__(self, config, driver: PagedLCDDriver):
        super().__init__(config, driver, "LTE (MB)")

    def update(self):
        lte_rsrp = query_prometheus_first_value("modem_signal_lte_rsrp")
        lte_rsrq = query_prometheus_first_value("modem_signal_lte_rsrq")
        lte_rssi = query_prometheus_first_value("modem_signal_lte_rssi")
        lte_snr = query_prometheus_first_value("modem_signal_lte_snr")
        
        lte_rx = query_prometheus_first_value("increase(node_network_receive_bytes_total{instance=\"router.foxden.network:9100\",device=\"wwan0\"}[30d])") / CONVERT_BYTES_TO_MB
        lte_tx = query_prometheus_first_value("increase(node_network_transmit_bytes_total{instance=\"router.foxden.network:9100\",device=\"wwan0\"}[30d])") / CONVERT_BYTES_TO_MB

        self.set_led(1, LEDColorPreset.get_most_critical([
            self.calc_led_lower_threshhold(lte_rsrp, -90, -100),
            self.calc_led_lower_threshhold(lte_rsrq, -15, -20)
        ]).value)
        self.set_line(1, f"RSRP {lte_rsrp:4.0f} / RSRQ {lte_rsrq:3.0f}")
        
        self.set_led(2, LEDColorPreset.get_most_critical([
            self.calc_led_lower_threshhold(lte_rssi, -75, -85),
            self.calc_led_lower_threshhold(lte_snr, 13, 0)
        ]).value)
        self.set_line(2, f"RSSI {lte_rssi:4.0f} / SNR  {lte_snr:3.0f}")
        
        self.set_led(3, self.calc_led_upper_threshhold(lte_rx + lte_tx, LTE_DATA_LIMIT * 0.75, LTE_DATA_LIMIT).value)
        self.set_line(3, f"RX  {lte_rx:5.0f} / TX {lte_tx:5.0f}")

PAGE = LTELCDPage
