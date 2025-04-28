
import struct
from typing import Dict

import ch347api

class I2CDevice:
    _INSTANCE : 'I2CDevice' = None
    _DEVICES : Dict[int, ch347api.I2CDevice] = {}

    def __new__(cls):
        if cls._INSTANCE is None:
            cls._INSTANCE = super(I2CDevice, cls).__new__(cls)
        return cls._INSTANCE

    def __init__(self):
        # print('[I2C] Scan start...')
        # hiddev = ch347api.CH347HIDDev()
        # hiddev.init_I2C()
        # print('      ' + ''.join(map(lambda a : '{:02X} '.format(a), range(16))))
        # for i in range(128):
        #     if i % 16 == 0:
        #         print('0x{:02X}: '.format(i), end='')
        #     exists = hiddev.i2c_exists(i)
        #     if exists:
        #         self._DEVICES[i] = ch347api.I2CDevice(i)
        #         print('{:02X} '.format(i), end='')
        #     else:
        #         print('__ ', end='')
        #     if i % 16 == 15:
        #         print()
        # print('[I2C] Scan done.')
        pass

    def write_byte_data(self, addr, cmd, val):
        # print(f'[I2C] write_byte_data: addr=0x{addr:02X}, cmd=0x{cmd:02X}, val=0x{val:02X}')
        if addr not in self._DEVICES:
            self._DEVICES[addr] = ch347api.I2CDevice(addr)
            # raise ValueError(f'I2C address was not found: 0x{addr:02X}')
        if isinstance(cmd, int):
            cmd = struct.pack('B', cmd)
        if isinstance(val, int):
            val = struct.pack('B', val)
        return self._DEVICES[addr].write(cmd, val)

    def write_block_data(self, addr, cmd, vals):
        # print(f'[I2C] write_block_data: addr=0x{addr:02X}, cmd=0x{cmd:02X}, vals={vals}')
        if addr not in self._DEVICES:
            self._DEVICES[addr] = ch347api.I2CDevice(addr)
            # raise ValueError(f'I2C address was not found: 0x{addr:02X}')
        if isinstance(cmd, int):
            cmd = struct.pack('B', cmd)
        if isinstance(vals, int):
            vals = struct.pack('B', vals)
        if isinstance(vals, list):
            vals = struct.pack('B' * len(vals), *vals)
        return self._DEVICES[addr].write(cmd, vals)
