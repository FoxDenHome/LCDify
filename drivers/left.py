from driver import PagedLCDDriver
from ids import ID_LEFT
from pages.ping_packet_loss import PingPacketLossLCDPage
from pages.ping_rtt import PingRTTLCDPage

class LCDDriverLeft(PagedLCDDriver):
    def __init__(self):
        super().__init__(ID_LEFT, [PingPacketLossLCDPage(), PingRTTLCDPage()])
