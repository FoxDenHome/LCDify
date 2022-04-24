from traceback import print_exc
from enum import Enum

def critical_call(func):
    try:
        return func()
    except Exception:
        print("Fatal exception happened!")
        print_exc()
        exit(1)

class LEDColorPreset(Enum):
    OFF = (0, 0)
    NORMAL = (0, 100)
    WARNING = (50, 100)
    CRITICAL = (100, 0)

    def get_most_critical(presets):
        if LEDColorPreset.CRITICAL in presets:
            return LEDColorPreset.CRITICAL
        if LEDColorPreset.WARNING in presets:
            return LEDColorPreset.WARNING
        if LEDColorPreset.NORMAL in presets:
            return LEDColorPreset.NORMAL
        return LEDColorPreset.OFF
