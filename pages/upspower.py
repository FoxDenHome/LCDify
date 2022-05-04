from drivers.paged import PagedLCDDriver
from page_updating import UpdatingLCDPage
from prometheus import build_prometheus_filter, query_prometheus_first_value

class UPSPowerLCDPage(UpdatingLCDPage):
    def __init__(self, config, driver: PagedLCDDriver):
        super().__init__(config, driver, "UPS Power")

    def update(self):
        filter = build_prometheus_filter({
            "hostname": "ups-rack",
        })
        ups_power_res = query_prometheus_first_value(f"snmp_upsAdvOutputActivePower{filter}")
        ups_runtime_res = query_prometheus_first_value(f"snmp_upsAdvBatteryRunTimeRemaining{filter} / 6000")
        ups_capacity_res = query_prometheus_first_value(f"snmp_upsHighPrecBatteryCapacity{filter}")
        ups_apparent_power_res = query_prometheus_first_value(f"snmp_upsAdvOutputApparentPower{filter}")
        ups_input_voltage_res = query_prometheus_first_value(f"snmp_upsHighPrecInputLineVoltage{filter}")
        ups_output_voltage_res = query_prometheus_first_value(f"snmp_upsHighPrecOutputVoltage{filter}")

        self.set_line(1, f"PWR {ups_power_res:4.0f} W / {ups_apparent_power_res:4.0f} VA")
        self.set_led(1, self.calc_led_upper_threshhold(ups_power_res, 800, 1000).value)
        self.set_line(2, f"BAT {ups_runtime_res:4.0f} m / {ups_capacity_res:4.0f} %")
        self.set_led(2, self.calc_led_lower_threshhold(ups_runtime_res, 15, 5).value)
        self.set_line(3, f"VIO {ups_input_voltage_res:4.0f} V / {ups_output_voltage_res:4.0f} V")
        self.set_led(3, self.calc_led_lower_threshhold(ups_input_voltage_res, 100, 80).value)

PAGE = UPSPowerLCDPage
