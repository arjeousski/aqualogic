from threading import Thread
from enum import Enum, unique
import re
import binascii

@unique
class Leds(Enum):
    HEATER_1 = 1 << 0
    VALVE_3 = 1 << 1
    CHECK_SYSTEM = 1 << 2
    POOL = 1 << 3
    SPA = 1 << 4
    FILTER = 1 << 5
    LIGHTS = 1 << 6
    AUX_1 = 1 << 7
    AUX_2 = 1 << 8
    SERVICE = 1 << 9
    AUX_3 = 1 << 10
    AUX_4 = 1 << 11
    AUX_5 = 1 << 12
    AUX_6 = 1 << 13
    VALVE_4 = 1 << 14
    SPILLOVER = 1 << 15
    SYSTEM_OFF = 1 << 16
    AUX_7 = 1 << 17
    AUX_8 = 1 << 18
    AUX_9 = 1 << 19
    AUX_10 = 1 << 20
    AUX_11 = 1 << 21
    AUX_12 = 1 << 22
    AUX_13 = 1 << 23
    AUX_14 = 1 << 24
    SUPER_CHLORINATE = 1 << 25

class AquaLogic(object):
    FRAME_DLE = 0x10
    FRAME_STX = 0x02
    FRAME_ETX = 0x03

    FRAME_TYPE_KEY_EVENT = b'\x00\x03'

    FRAME_TYPE_KEEP_ALIVE = b'\x01\x01'
    FRAME_TYPE_LEDS = b'\x01\x02'
    FRAME_TYPE_DISPLAY_UPDATE = b'\x01\x03'

    def __init__(self, stream):
        self._stream = stream
        self._is_celsius = True
        self._air_temp = None
        self._pool_temp = None
        self._chlorinator = None
        self._leds = 0

    def data_reader(self):
        while True:
            b = self._stream.read(1)

            while True:
                # Search for FRAME_DLE + FRAME_STX
                if not b:
                    return
                if b[0] == self.FRAME_DLE:
                    next_b = self._stream.read(1)
                    if not next_b:
                        return
                    if next_b[0] == self.FRAME_STX:
                        break
                    else:
                        continue
                b = self._stream.read(1)

            frame = bytearray()
            b = self._stream.read(1)

            while True:
                if not b:
                    return
                if b[0] == self.FRAME_DLE:
                    # Should be FRAME_ETX or 0 according to
                    # the AQ-CO-SERIAL manual
                    next_b = self._stream.read(1)
                    if not next_b:
                        return
                    if next_b[0] == self.FRAME_ETX:
                        break
                    elif next_b[0] != 0:
                        # Error?
                        pass

                frame.append(b[0])
                b = self._stream.read(1)
            
            # Verify CRC
            frame_crc = int.from_bytes(frame[-2:], byteorder='big')
            frame = frame[:-2]

            calculated_crc = self.FRAME_DLE + self.FRAME_STX
            for b in frame:
                calculated_crc += b
            
            if (frame_crc != calculated_crc):
                print('Bad CRC')
                continue

            frame_type = frame[0:2]
            frame = frame[2:]

            if frame_type == self.FRAME_TYPE_KEEP_ALIVE:
                # Keep alive
                continue
            elif frame_type == self.FRAME_TYPE_KEY_EVENT:
                print("Key: {}".format(binascii.hexlify(frame)))
            elif frame_type == self.FRAME_TYPE_LEDS:
                print("LEDs: {}".format(binascii.hexlify(frame)))
                self._leds = int.from_bytes(frame[0:4], byteorder='little')
                for led in Leds:
                    if led.value & self._leds != 0:
                        print(led)
            elif frame_type == self.FRAME_TYPE_DISPLAY_UPDATE:
                parts = frame.decode('latin-1').split()
                print("Display Update: {}".format(parts))

                try: 
                    if parts[0] == 'Pool' and parts[1] == 'Temp':
                        # Pool Temp <temp>°[C|F]
                        self._pool_temp = int(parts[2][:-2])
                    elif parts[0] == 'Air' and parts[1] == 'Temp':
                        # Air Temp <temp>°[C|F]
                        self._air_temp = int(parts[2][:-2])
                    elif parts[0] == 'Pool' and parts[1] == 'Chlorinator':
                        # Pool Chlorinator <value>%
                        self._chlorinator = int(parts[2][:-1])
                except ValueError:
                    pass

    @property
    def air_temp(self):
        return self._air_temp

    @property
    def pool_temp(self):
        return self._pool_temp
    
    @property
    def chlorinator(self):
        return self._chlorinator
    
    @property
    def is_celcius(self):
        return self._is_celcius

    def is_led_enabled(self, led):
        return (led.value & self._leds) != 0
