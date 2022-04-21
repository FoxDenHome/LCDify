from dataclasses import dataclass
from threading import Condition, Thread
from time import sleep
from serial import Serial
from crc import crc16

LCD_BAUDRATE = 115200
MAX_DATA_LENGTH = 22

PACKET_CONST_ELEM_LEN = 1 + 1 + 2
PACKET_LEN = PACKET_CONST_ELEM_LEN + MAX_DATA_LENGTH

class LCDPacket():
    TYPE_RESPONSE = 0b01
    TYPE_ERROR = 0b11
    TYPE_REPORT = 0b10
    TYPE_REQUEST = 0b00

    def __init__(self, command, data):
        self.command = command & 0b00111111
        self.type = (command & 0b11000000) >> 6
        self.data = data

    def type_str(self):
        if self.type == self.TYPE_RESPONSE:
            return 'RESPONSE'
        elif self.type == self.TYPE_ERROR:
            return 'ERROR'
        elif self.type == self.TYPE_REPORT:
            return 'REPORT'
        elif self.type == self.TYPE_REQUEST:
            return 'REQUEST'
        return 'UNKNOWN'

    def data_as_str(self):
        return bytearray(self.data).decode('ascii')

    def __str__(self):
        return f"LCDPacket(type={self.type_str()}, command=0x{self.command:02x}, data=[{', '.join(list(map(lambda x: f'0x{x:02x}', self.data)))}])"

@dataclass
class LCDKeyPollResult():
    current: list[int]
    released: list[int]
    pressed: list[int]

class LCDException(Exception):
    pass

class LCDTimeoutException(LCDException):
    pass

class LCDResponseException(LCDException):
    def __init__(self, packet):
        super().__init__(f"LCDResponseException: {packet.data_as_str()}")
        self.packet = packet

class LCD():
    REPORT_KEY = 0x00
    REPORT_FAN = 0x01
    REPORT_TEMPERATURE = 0x02

    KEY_UP = 0x01
    KEY_ENTER = 0x02
    KEY_CANCEL = 0x04
    KEY_LEFT = 0x08
    KEY_RIGHT = 0x10
    KEY_DOWN = 0x20

    CURSOR_NONE = 0
    CURSOR_BLINKING_BLOCK = 1
    CURSOR_SOLID_UNDERSCORE = 2
    CURSOR_BLINKING_BLOCK_AND_UNDERSCORE = 3
    CURSOR_BLINKING_UNDERSCORE = 4

    GPO_LED3_GREEN = 5
    GPO_LED3_RED = 6
    GPO_LED2_GREEN = 7
    GPO_LED2_RED = 8
    GPO_LED1_GREEN = 9
    GPO_LED1_RED = 10
    GPO_LED0_GREEN = 11
    GPO_LED0_RED = 12

    GPO_LEDS = [
        [GPO_LED0_RED, GPO_LED0_GREEN],
        [GPO_LED1_RED, GPO_LED1_GREEN],
        [GPO_LED2_RED, GPO_LED2_GREEN],
        [GPO_LED3_RED, GPO_LED3_GREEN],
    ]

    def __init__(self, port, baudrate=LCD_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.last_response = None
        self.command_lock = Condition()
        self.buffer = []
        self.reader_thread = None
        self.report_handlers = {
            self.REPORT_KEY: [],
            self.REPORT_FAN: [],
            self.REPORT_TEMPERATURE: [],
        }

    def open(self):
        self.close()
        self.serial = Serial(self.port, self.baudrate, timeout=1)
        self.reader_thread = Thread(target=self._reader_thread, daemon=True, name=f"LCD reader {self.port}")
        self.reader_thread.start()

    def close(self):
        if self.serial is None:
            return
        self.serial.close()
        self.serial = None
        self.buffer = []
        if self.reader_thread is not None:
            self.reader_thread.join()
            self.reader_thread = None

    def register_handler(self, report, handler):
        self.report_handlers[report].append(handler)

    def unregister_handler(self, report, handler):
        self.report_handlers[report].remove(handler)

    def ping(self):
        self.send(0x00)

    def version(self):
        return self.send(0x01)

    def write_user_flash(self, data):
        return self.send(0x2A, data)

    def read_user_flash(self, data):
        return self.send(0x2A, data)

    def save_as_default(self):
        self.send(0x04)

    def clear(self):
        self.send(0x06)

    def set_special_character(self, idx, data):
        self.send(0x09, [idx] + data)

    def set_cursor(self, col, row):
        self.send(0x0B, [col, row])

    def set_cursor_style(self, style):
        self.send(0x0C, [style])

    def set_contrast(self, level):
        self.send(0x0D, [level])

    def set_backlight(self, level):
        self.send(0x0E, [level])

    def set_key_reporting(self, press_mask, release_mask):
        self.send(0x17, [press_mask, release_mask])

    def poll_keys(self):
        res = self.send(0x18)
        return LCDKeyPollResult(current=res[0], pressed=res[1], released=res[2])

    def write(self, col, row, data):
        self.send(0x1F, [col, row] + list(bytearray(data, 'ascii')))

    def write_gpio(self, idx, value, drive=-1):
        if drive >= 0:
            self.send(0x22, [idx, value, drive])
        else:
            self.send(0x22, [idx, value])

    def write_led(self, idx, red, green):
        led_gpos = self.GPO_LEDS[idx]
        self.write_gpio(led_gpos[0], red)
        self.write_gpio(led_gpos[1], green)

    def read_gpio(self, idx):
        return self.send(0x23, [idx])

    def _reader_thread(self):
        while self.serial is not None:
            self._read()
            sleep(0.01)

    def _read(self):
        self.buffer += self.serial.read(self.serial.in_waiting)
        packet = self._check_buffer()
        if packet is None:
            return
        if packet.type == LCDPacket.TYPE_REQUEST:
            print("REQUEST type packet from LCD. This should never happen!")
            return
        if packet.type == LCDPacket.TYPE_REPORT:
            handlers = self.report_handlers[packet.command]
            if handlers is None:
                print(f"Unknown report command: {packet.command}")
                return
            for handler in handlers:
                handler(packet.data)
            return
        self.command_lock.acquire()
        self.last_response = packet
        self.command_lock.notify()
        self.command_lock.release()

    def _skip_buffer(self, num=1):
        self.buffer = self.buffer[num:]
        return self._check_buffer()

    def _check_buffer(self):
        if len(self.buffer) < 4:
            return None

        cmd = self.buffer[0]
        data_len = self.buffer[1]
        if data_len > MAX_DATA_LENGTH:
            return self._skip_buffer()

        if len(self.buffer) < data_len + 4:
            return None

        crcBytes = self.buffer[2+data_len:4+data_len]
        presentedCrc = crcBytes[0] | (crcBytes[1] << 8)
        calculatedCrc = crc16(self.buffer[:2+data_len])
        if presentedCrc != calculatedCrc:
            return self._skip_buffer()

        data = self.buffer[2:2+data_len]
        self.buffer = self.buffer[4+data_len:]
        return LCDPacket(cmd, data)

    def send(self, command, data=[]):
        data_len = len(data)
        packet = bytearray(PACKET_CONST_ELEM_LEN + data_len)
        packet[0] = command
        packet[1] = data_len
        for i in range(data_len):
            packet[2 + i] = data[i]
        crc = crc16(packet[:-2])
        packet[2 + data_len] = crc & 0xFF
        packet[3 + data_len] = crc >> 8
        
        self.command_lock.acquire()
        self.serial.write(packet)
        if not self.command_lock.wait_for(lambda: self.last_response and self.last_response.command == command, timeout=0.25):
            raise LCDTimeoutException()

        resp = self.last_response
        self.last_response = None
        self.command_lock.release()

        if resp.type == LCDPacket.TYPE_ERROR:
            raise LCDResponseException(resp)
    
        return resp.data
