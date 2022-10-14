from dataclasses import dataclass
from threading import Condition, Thread
from enum import Enum
from time import sleep
from traceback import print_exc
from serial import Serial
from crc import crc16
from utils import critical_call

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

class LCDKeyEvent(Enum):
    PRESSED = 0
    RELEASED = 1

class LCDCursorType(Enum):
    NONE = 0
    BLINKING_BLOCK = 1
    SOLID_UNDERSCORE = 2
    BLINKING_BLOCK_AND_UNDERSCORE = 3
    BLINKING_UNDERSCORE = 4

@dataclass
class LCDKeyMask():
    mask: int

    def has(self, key: LCDKey) -> bool:
        return (self.mask & key.value) != 0

    def add(self, key: LCDKey) :
        self.mask |= key.value
        return self

    def remove(self, key: LCDKey):
        self.mask &= ~key.value
        return self

    def add_all(self):
        for key in LCDKey:
            self.add(key)
        return self

    def list(self) -> list[LCDKey]:
        return [key for key in LCDKey if self.has(key)]

    def raw(self) -> int:
        return self.mask

LCD_KEY_MASK_NONE = LCDKeyMask(0)
LCD_KEY_MASK_ALL = LCDKeyMask(0).add_all()

class LCDPacket():
    type:  LCDPacketType
    command: int
    data: bytearray

    def __init__(self, command, data):
        self.command = command & 0b00111111
        self.type = LCDPacketType((command & 0b11000000) >> 6)
        self.data = bytearray(data)

    def data_as_str(self):
        return bytearray(self.data).decode("latin-1")

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
    (None, None),
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
    _command_response_cond: Condition
    _buffer: list[int]
    _reader_thread_var: Thread

    def __init__(self, port: str, baudrate: int = LCD_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self._serial = None
        self._last_response = None
        self._command_response_cond = Condition()
        self._buffer = []
        self._reader_thread_var = None
        self._should_run = False

        self._key_event_handlers = []

    def width(self) -> int:
        return 20

    def height(self) -> int:
        return 4

    def led_count(self) -> int:
        return 4

    def max_write_len(self) -> int:
        return MAX_DATA_LENGTH - 2 # col, row

    def open(self) -> None:
        self.close()
        self._serial = Serial(self.port, self.baudrate, timeout=1)
        self._should_run = True
        self._reader_thread_var = Thread(name=f"LCD reader {self.port}", target=critical_call, args=(self._reader_thread,), daemon=True)
        self._reader_thread_var.start()

    def close(self) -> None:
        self._should_run = False
        if self._reader_thread_var is not None:
            self._reader_thread_var.join()
            self._reader_thread_var = None

    def register_key_event_handler(self, handler) -> None:
        self._key_event_handlers.append(handler)

    def unregister_key_event_handler(self, handler) -> None:
        self._key_event_handlers.remove(handler)

    def ping(self) -> None:
        self.send(0x00)

    def version(self) -> str:
        return self.send(0x01).decode("latin-1")

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
        self.send(0x17, [press_mask.mask, release_mask.mask])

    def poll_keys(self) -> LCDKeyPollResult:
        res = self.send(0x18)
        return LCDKeyPollResult(current=LCDKeyMask(res[0]), pressed=LCDKeyMask(res[1]), released=LCDKeyMask(res[2]))

    def write_str(self, col: int, row: int, data: str) -> None:
        self.write(col, row, bytearray(data, "latin-1"))

    def write(self, col: int, row: int, data: bytearray) -> None:
        self.send(0x1F, [col, row] + list(data))

    def write_gpio(self, idx: int, value: int, drive: int = None) -> None:
        if drive is not None:
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
        self._buffer = []

        while self._should_run:
            try:
                self._read()
            except Exception:
                print(f"Error reading from LCD on port {self.port}", flush=True)
                print_exc()
            sleep(0.01)
    
        self._serial.close()
        self._serial = None
        self._buffer = []

    def _read(self) -> None:
        self._buffer += self._serial.read(self._serial.in_waiting)
        packet = self._check_buffer()
        if packet is None:
            return
        if packet.type == LCDPacketType.REQUEST:
            print("REQUEST type packet from LCD. This should never happen!", flush=True)
            return
        if packet.type == LCDPacketType.REPORT:
            if packet.command == REPORT_KEY:
                self._handle_key_report(packet.data)
            return
        self._command_response_cond.acquire()
        if self._last_response is not None:
            print("Got a response while another one was already buffered", self._last_response, packet, flush=True)
        self._last_response = packet
        self._command_response_cond.notify_all()
        self._command_response_cond.release()

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
        for handler in self._key_event_handlers:
            if pressed:
                event = LCDKeyEvent.PRESSED
            else:
                event = LCDKeyEvent.RELEASED
            try:
                handler(key=key, event=event)
            except Exception:
                print(f"Error in key event handler on port {self.port} with handler {handler}", flush=True)
                print_exc()

    def send(self, command: int, data: bytearray = []) -> bytearray:
        retries = 5
        while retries > 0:
            try:
                return self._send(command, data)
            except LCDTimeoutException:
                print(f"LCD timeout on {self.port}...", flush=True)
            retries -= 1
        raise LCDTimeoutException()

    def _send(self, command: int, data: bytearray = []) -> bytearray:
        data_len = len(data)
        if data_len > MAX_DATA_LENGTH:
            raise ValueError(f"Data length too long: {data_len} > {MAX_DATA_LENGTH}")
        packet = bytearray(PACKET_CONST_ELEM_LEN + data_len)
        packet[0] = command
        packet[1] = data_len
        for i in range(data_len):
            packet[2 + i] = data[i]
        crc = crc16(packet[:-2])
        packet[2 + data_len] = crc & 0xFF
        packet[3 + data_len] = crc >> 8
        
        self._command_response_cond.acquire()

        self._serial.write(packet)
        if not self._command_response_cond.wait_for(lambda: self._last_response and self._last_response.command == command, timeout=0.25):
            self._command_response_cond.release()
            raise LCDTimeoutException()

        resp = self._last_response
        self._last_response = None
        self._command_response_cond.release()

        if resp.type == LCDPacketType.ERROR:
            raise LCDResponseException(resp)
    
        return resp.data

class LCDWithID(LCD):
    def read_id_and_version(self) -> tuple[int, int]:
        data = self.read_user_flash()
        id = data[0]
        version = data[1]
        if id == 0xFF or id == 0x00:
            return None, None
        return id, version

    def write_id_and_version(self, id: int, version: int):
        if id <= 0x00 or id >= 0xFF:
            raise ValueError("ID must be between 0x00 and 0xFF exclusive")
        if version < 0x00 or version > 0xFF:
            raise ValueError("Version must be between 0x00 and 0xFF inclusive")
        flash = bytearray(16)
        flash[0] = id
        flash[1] = version
        self.write_user_flash(flash)
