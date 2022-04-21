from dataclasses import dataclass
from threading import Condition, Thread
from time import sleep
from enum import Enum
from numpy import byte
from serial import Serial
from crc import crc16

LCD_BAUDRATE = 115200
MAX_DATA_LENGTH = 22

PACKET_CONST_ELEM_LEN = 1 + 1 + 2
PACKET_LEN = PACKET_CONST_ELEM_LEN + MAX_DATA_LENGTH

class LCDPacketType(Enum):
    RESPONSE = 0b01
    ERROR = 0b11
    REPORT = 0b10
    REQUEST = 0b00

class LCDKey(Enum):
    UP = 0x01
    ENTER = 0x02
    CANCEL = 0x04
    LEFT = 0x08
    RIGHT = 0x10
    DOWN = 0x20
    INVALID = 0xFFFF

class LCDCursorType(Enum):
    NONE = 0
    BLINKING_BLOCK = 1
    SOLID_UNDERSCORE = 2
    BLINKING_BLOCK_AND_UNDERSCORE = 3
    BLINKING_UNDERSCORE = 4

@dataclass
class LCDKeyMask():
    mask: int

    def has(self, key: LCDKey):
        return (self.mask & key.value) != 0

    def all(self):
        return [key for key in LCDKey if self.has(key)]

    def raw(self):
        return self.mask

class LCDPacket():
    type:  LCDPacketType
    command: int
    data: bytearray

    def __init__(self, command, data):
        self.command = command & 0b00111111
        self.type = LCDPacketType((command & 0b11000000) >> 6)
        self.data = bytearray(data)

    def data_as_str(self):
        return bytearray(self.data).decode('ascii')

    def __str__(self):
        return f"LCDPacket(type={self.type.name}, command=0x{self.command:02x}, data=[{', '.join(list(map(lambda x: f'0x{x:02x}', self.data)))}])"

@dataclass
class LCDKeyPollResult():
    current: LCDKeyMask
    released: LCDKeyMask
    pressed: LCDKeyMask

class LCDException(Exception):
    pass

class LCDTimeoutException(LCDException):
    pass

class LCDResponseException(LCDException):
    def __init__(self, packet):
        super().__init__(f"LCDResponseException: {packet.data_as_str()}")
        self.packet = packet

REPORT_KEY = 0x00
REPORT_FAN = 0x01
REPORT_TEMPERATURE = 0x02

GPO_LED3_GREEN = 5
GPO_LED3_RED = 6
GPO_LED2_GREEN = 7
GPO_LED2_RED = 8
GPO_LED1_GREEN = 9
GPO_LED1_RED = 10
GPO_LED0_GREEN = 11
GPO_LED0_RED = 12

GPO_LEDS = [
    (GPO_LED0_RED, GPO_LED0_GREEN),
    (GPO_LED1_RED, GPO_LED1_GREEN),
    (GPO_LED2_RED, GPO_LED2_GREEN),
    (GPO_LED3_RED, GPO_LED3_GREEN),
]

REPORT_KEY_MAP_TO_LCD_KEY = [
    (LCDKey.INVALID, False),
    (LCDKey.UP, True),
    (LCDKey.DOWN, True),
    (LCDKey.LEFT, True),
    (LCDKey.RIGHT, True),
    (LCDKey.ENTER, True),
    (LCDKey.CANCEL, True),
    (LCDKey.UP, False),
    (LCDKey.DOWN, False),
    (LCDKey.LEFT, False),
    (LCDKey.RIGHT, False),
    (LCDKey.ENTER, False),
    (LCDKey.CANCEL, False),
]

class LCD():
    port: str
    baudrate: int
    _serial: Serial
    _last_response: LCDPacket
    _command_lock: Condition
    _buffer: list[int]
    _reader_thread_var: Thread

    def __init__(self, port: str, baudrate: int = LCD_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self._serial = None
        self._last_response = None
        self._command_lock = Condition()
        self._buffer = []
        self._reader_thread_var = None

        self._key_press_handlers = []

    def open(self) -> None:
        self.close()
        self._serial = Serial(self.port, self.baudrate, timeout=1)
        self._reader_thread_var = Thread(target=self._reader_thread, daemon=True, name=f"LCD reader {self.port}")
        self._reader_thread_var.start()

    def close(self) -> None:
        if self._serial is None:
            return
        self._serial.close()
        self._serial = None
        self._buffer = []
        if self._reader_thread_var is not None:
            self._reader_thread_var.join()
            self._reader_thread_var = None

    def register_key_press_handler(self, handler) -> None:
        self._key_press_handlers.append(handler)

    def unregister_key_press_handler(self, handler) -> None:
        self._key_press_handlers.remove(handler)

    def ping(self) -> None:
        self.send(0x00)

    def version(self) -> str:
        return self.send(0x01).decode("ascii")

    def write_user_flash(self, data: bytearray) -> None:
        self.send(0x02, data)

    def read_user_flash(self) -> bytearray:
        return self.send(0x03)

    def save_as_default(self) -> None:
        self.send(0x04)

    def clear(self) -> None:
        self.send(0x06)

    def set_special_character(self, idx: int, data: bytearray) -> None:
        self.send(0x09, [idx] + data)

    def set_cursor(self, col: int, row: int) -> None:
        self.send(0x0B, [col, row])

    def set_cursor_style(self, style: LCDCursorType) -> None:
        self.send(0x0C, [style.value])

    def set_contrast(self, level: int) -> None:
        self.send(0x0D, [level])

    def set_backlight(self, level: int) -> None:
        self.send(0x0E, [level])

    def set_key_reporting(self, press_mask: LCDKeyMask, release_mask: LCDKeyMask) -> None:
        self.send(0x17, [press_mask, release_mask])

    def poll_keys(self) -> LCDKeyPollResult:
        res = self.send(0x18)
        return LCDKeyPollResult(current=LCDKeyMask(res[0]), pressed=LCDKeyMask(res[1]), released=LCDKeyMask(res[2]))

    def write(self, col: int, row: int, data: str) -> None:
        self.send(0x1F, [col, row] + list(bytearray(data, 'ascii')))

    def write_gpio(self, idx: int, value: int, drive: int = -1) -> None:
        if drive >= 0:
            self.send(0x22, [idx, value, drive])
        else:
            self.send(0x22, [idx, value])

    def write_led(self, idx: int, red: int, green: int) -> None:
        gpo_red, gpo_green = GPO_LEDS[idx]
        self.write_gpio(gpo_red, red)
        self.write_gpio(gpo_green, green)

    def read_gpio(self, idx: int) -> bytearray:
        return self.send(0x23, [idx])

    def _reader_thread(self) -> None:
        while self._serial is not None:
            self._read()
            sleep(0.01)

    def _read(self) -> None:
        self._buffer += self._serial.read(self._serial.in_waiting)
        packet = self._check_buffer()
        if packet is None:
            return
        if packet.type == LCDPacketType.REQUEST:
            print("REQUEST type packet from LCD. This should never happen!")
            return
        if packet.type == LCDPacketType.REPORT:
            if packet.command == REPORT_KEY:
                self._handle_key_report(packet.data)
            return
        self._command_lock.acquire()
        self._last_response = packet
        self._command_lock.notify()
        self._command_lock.release()

    def _skip_buffer(self, num: int = 1) -> LCDPacket:
        self._buffer = self._buffer[num:]
        return self._check_buffer()

    def _check_buffer(self) -> LCDPacket:
        if len(self._buffer) < 4:
            return None

        cmd = self._buffer[0]
        data_len = self._buffer[1]
        if data_len > MAX_DATA_LENGTH:
            return self._skip_buffer()

        if len(self._buffer) < data_len + 4:
            return None

        crcBytes = self._buffer[2+data_len:4+data_len]
        presentedCrc = crcBytes[0] | (crcBytes[1] << 8)
        calculatedCrc = crc16(self._buffer[:2+data_len])
        if presentedCrc != calculatedCrc:
            return self._skip_buffer()

        data = self._buffer[2:2+data_len]
        self._buffer = self._buffer[4+data_len:]
        return LCDPacket(cmd, data)

    def _handle_key_report(self, data: bytearray) -> None:
        key, pressed = REPORT_KEY_MAP_TO_LCD_KEY[data[0]]
        for handler in self._key_press_handlers:
            handler(key, pressed)

    def send(self, command: int, data: bytearray = []) -> bytearray:
        data_len = len(data)
        packet = bytearray(PACKET_CONST_ELEM_LEN + data_len)
        packet[0] = command
        packet[1] = data_len
        for i in range(data_len):
            packet[2 + i] = data[i]
        crc = crc16(packet[:-2])
        packet[2 + data_len] = crc & 0xFF
        packet[3 + data_len] = crc >> 8
        
        self._command_lock.acquire()
        self._serial.write(packet)
        if not self._command_lock.wait_for(lambda: self._last_response and self._last_response.command == command, timeout=0.25):
            raise LCDTimeoutException()

        resp = self._last_response
        self._last_response = None
        self._command_lock.release()

        if resp.type == LCDPacketType.ERROR:
            raise LCDResponseException(resp)
    
        return resp.data
