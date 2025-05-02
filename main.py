#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Himanshu

import time
import string
from ch347bus import I2CDevice
from fonts import font6x4, font8x9

from ssd1306 import *

addressing_mode = OPTION_ADDRESSING_MODE_PAGE

setup = [
    *SSD1306_DISPLAY.get_command(OPTION_DISPLAY_OFF),
    *SSD1306_SET_DISPLAY_CLOCK_DIV_RATIO.get_command(0x80),
    *SSD1306_SET_MULTIPLEX.get_command(0x1F),                               # 0x3F for 128x64
    *SSD1306_SET_DISPLAY_OFFSET.get_command(0x00),                          # no offset
    # *SSD1306_SET_START_LINE.get_command(0x00),                            # line #0
    *SSD1306_CHARGE_PUMP.get_command(0x1),                                  # Enable
    *SSD1306_SET_MEMORY_ADDRESSING_MODE.get_command(addressing_mode),
    *SSD1306_SEGMENT_REMAP.get_command(OPTION_SEGMENT_REMAP_SEG0_TO_0),     # 0 - RTL, 1 - LTR
    *SSD1306_COM_OUTPUT_SCAN_DIR.get_command(OPTION_COM_SCAN_DIR_REVERSE),  # 0xC8 - top to bottom, 0xC0 - bottom to top
    *SSD1306_SET_COM_PINS.get_command(0),
    *SSD1306_SETCONTRAST.get_command(0x8F),
    *SSD1306_SET_PRECHARGE_PERIOD.get_command(0xF1),
    *SSD1306_SET_VCOM_DESELECT_LEVEL.get_command(0x4),
    *SSD1306_DISPLAY.get_command(OPTION_DISPLAY_ALLON_RESUME),
    *SSD1306_DISPLAY.get_command(OPTION_DISPLAY_NORMAL),
    *SSD1306_DISPLAY.get_command(OPTION_DISPLAY_ON),
]

setup_ha_va = [
    *SSD1306_HAVA_MODE_SET_PAGE_ADDR.get_command(0x00, 0x03),
    *SSD1306_HAVA_MODE_SET_COLUMN_ADDR.get_command(0x00, 0x7F),
]

setup_pa = [
    *SSD1306_PA_MODE_SET_PAGE_ADDR.get_command(0x0),
    *SSD1306_PA_MODE_SET_COLUMN_ADDR_LOW.get_command(0x0),
    *SSD1306_PA_MODE_SET_COLUMN_ADDR_HIGH.get_command(0x0),
]

addressing_mode = OPTION_ADDRESSING_MODE_PAGE

# if __name__ == '__main__':
#     i2c = I2CDevice()

#     for cmd in setup:
#         i2c.write_byte_data(0x3C, 0x00, cmd)

#     if addressing_mode in (OPTION_ADDRESSING_MODE_HORIZONTAL, OPTION_ADDRESSING_MODE_VERTICAL):
#         for cmd in setup_ha_va:
#             i2c.write_byte_data(0x3C, 0x00, cmd)
#         raise NotImplementedError('Horizontal and vertical addressing modes are not implemented yet.')
#     elif addressing_mode == OPTION_ADDRESSING_MODE_PAGE:
#         for cmd in setup_pa:
#             i2c.write_byte_data(0x3C, 0x00, cmd)

#         for page in range(0x4):
#             i2c.write_block_data(0x3C, 0x00, SSD1306_PA_MODE_SET_PAGE_ADDR.get_command(page))
#             for _ in range(0x80):
#                 i2c.write_byte_data(0x3C, 0x40, 0xaa)
#             time.sleep(0.1)
#         for page in range(0x4):
#             i2c.write_block_data(0x3C, 0x00, SSD1306_PA_MODE_SET_PAGE_ADDR.get_command(page))
#             for _ in range(0x80):
#                 i2c.write_byte_data(0x3C, 0x40, 0x00)
#             time.sleep(0.1)

if __name__ == '__main__':
    import socket

    def send_update(page, column, byte_value, host='127.0.0.1', port=12345):
        message = f"{page} {column} {byte_value:02x}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message.encode(), (host, port))
        sock.close()

    from layout import Layout
    layout1 = Layout(0, 0, 0x3, 0x3f)
    print(layout1)

    send_update(0, 0, 0x0a)
    send_update(1, 10, 0xaa)
    send_update(2, 20, 0xaa)
    send_update(3, 30, 0xa0)
    send_update(3, 127, 0xa2)
    send_update(2, 127, 0x2e)
