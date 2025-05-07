#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Himanshu

# [PDF](https://cdn-shop.adafruit.com/datasheets/SSD1306.pdf)

import time
import string
from typing import Dict

from ch347bus import I2CDevice
from fonts import FontBase, font6x4, font8x9, print_columns

from ssd1306 import *

N_PAGES = 4
N_COLUMNS = 128

# ADDRESSING_MODE = OPTION_ADDRESSING_MODE_VERTICAL
ADDRESSING_MODE = OPTION_ADDRESSING_MODE_HORIZONTAL
# ADDRESSING_MODE = OPTION_ADDRESSING_MODE_PAGE

setup = [
    *SSD1306_DISPLAY.get_command(OPTION_DISPLAY_OFF),
    *SSD1306_SET_DISPLAY_CLOCK_DIV_RATIO.get_command(0x80),
    *SSD1306_SET_MULTIPLEX.get_command(0x1F),                               # 0x3F for 128x64
    *SSD1306_SET_DISPLAY_OFFSET.get_command(0x00),                          # no offset
    *SSD1306_SET_START_LINE.get_command(0x00),                              # line #0
    *SSD1306_CHARGE_PUMP.get_command(0x1),                                  # Enable
    *SSD1306_SEGMENT_REMAP.get_command(OPTION_SEGMENT_REMAP_SEG0_TO_0),     # 0 - LTR, 1 - RTL
    *SSD1306_COM_OUTPUT_SCAN_DIR.get_command(OPTION_COM_SCAN_DIR_NORMAL),   # 0xC8 - top to bottom, 0xC0 - bottom to top
    *SSD1306_SET_COM_PINS.get_command(0),
    *SSD1306_SETCONTRAST.get_command(0x8F),
    *SSD1306_SET_PRECHARGE_PERIOD.get_command(0xF1),
    *SSD1306_SET_VCOM_DESELECT_LEVEL.get_command(0x4),
    *SSD1306_DISPLAY.get_command(OPTION_DISPLAY_ALLON_RESUME),
    *SSD1306_DISPLAY.get_command(OPTION_DISPLAY_NORMAL),
    *SSD1306_DISPLAY.get_command(OPTION_DISPLAY_ON),
]

setup_ha_va = [
    *SSD1306_SET_MEMORY_ADDRESSING_MODE.get_command(ADDRESSING_MODE),
    *SSD1306_HAVA_MODE_SET_PAGE_ADDR.get_command(0x00, 0x03),
    *SSD1306_HAVA_MODE_SET_COLUMN_ADDR.get_command(0x00, 0x7F),
]

setup_pa = [
    *SSD1306_SET_MEMORY_ADDRESSING_MODE.get_command(ADDRESSING_MODE),
    *SSD1306_PA_MODE_SET_PAGE_ADDR.get_command(0x0),
    *SSD1306_PA_MODE_SET_COLUMN_ADDR_LOW.get_command(0x0),
    *SSD1306_PA_MODE_SET_COLUMN_ADDR_HIGH.get_command(0x0),
]

if __name__ == '__main__':
    i2c = I2CDevice()

    for cmd in setup:
        i2c.write_byte_data(0x3C, 0x00, cmd)

    if ADDRESSING_MODE == OPTION_ADDRESSING_MODE_HORIZONTAL:
        for cmd in setup_ha_va:
            i2c.write_byte_data(0x3C, 0x00, cmd)

        i2c.write_block_data(0x3C, 0x00, SSD1306_HAVA_MODE_SET_PAGE_ADDR.get_command(0x0, 0x3))
        i2c.write_block_data(0x3C, 0x00, SSD1306_HAVA_MODE_SET_COLUMN_ADDR.get_command(0x0, 0x7F))
        for page in range(N_PAGES):
            for _ in range(N_COLUMNS):
                i2c.write_byte_data(0x3C, 0x40, 0xaa)
            time.sleep(0.1)
        for page in range(N_PAGES):
            for _ in range(N_COLUMNS):
                i2c.write_byte_data(0x3C, 0x40, 0x00)
            time.sleep(0.1)

    elif ADDRESSING_MODE == OPTION_ADDRESSING_MODE_PAGE:
        for cmd in setup_pa:
            i2c.write_byte_data(0x3C, 0x00, cmd)

        for page in range(N_PAGES):
            i2c.write_block_data(0x3C, 0x00, SSD1306_PA_MODE_SET_PAGE_ADDR.get_command(page))
            for _ in range(N_COLUMNS):
                i2c.write_byte_data(0x3C, 0x40, 0xaa)
            time.sleep(0.1)
        for page in range(N_PAGES):
            i2c.write_block_data(0x3C, 0x00, SSD1306_PA_MODE_SET_PAGE_ADDR.get_command(page))
            for _ in range(N_COLUMNS):
                i2c.write_byte_data(0x3C, 0x40, 0x00)
            time.sleep(0.1)

    elif ADDRESSING_MODE == OPTION_ADDRESSING_MODE_VERTICAL:
        raise NotImplementedError('Vertical addressing mode is not implemented yet.')

    else:
        raise ValueError(f'Invalid mode: {ADDRESSING_MODE}. Expected one of '
                         f'{OPTION_ADDRESSING_MODE_VERTICAL}, {OPTION_ADDRESSING_MODE_HORIZONTAL}, '
                         f'{OPTION_ADDRESSING_MODE_PAGE}')

    page = 0
    column = 0
    if ADDRESSING_MODE == OPTION_ADDRESSING_MODE_HORIZONTAL:
        i2c.write_block_data(0x3C, 0x00, SSD1306_HAVA_MODE_SET_PAGE_ADDR.get_command(0x0, 0x3))
        i2c.write_block_data(0x3C, 0x00, SSD1306_HAVA_MODE_SET_COLUMN_ADDR.get_command(0x0, 0x7F))
    elif ADDRESSING_MODE == OPTION_ADDRESSING_MODE_PAGE:
        i2c.write_block_data(0x3C, 0x00, SSD1306_PA_MODE_SET_PAGE_ADDR.get_command(page))
        i2c.write_block_data(0x3C, 0x00, SSD1306_PA_MODE_SET_COLUMN_ADDR_LOW.get_command(column & 0x0F))
        i2c.write_block_data(0x3C, 0x00, SSD1306_PA_MODE_SET_COLUMN_ADDR_HIGH.get_command(column >> 4))
    else:
        raise NotImplementedError('Vertical addressing mode is not implemented yet.')

    for font in [font6x4, font8x9]:
        font : Dict[str, FontBase]
        for c in string.printable:
            if c in ('\n', '\r', '\x0b', '\x0c'):
                continue
            if c not in font:
                print(f"Character '{c}' not found in {font.values()[0].__class__}.")
                continue
            columns = font[c].get_columns()

            if ADDRESSING_MODE == OPTION_ADDRESSING_MODE_PAGE:
                width = font[c].width
                if column + width >= N_COLUMNS:
                    # Will overflow, move to next page
                    print(f'Column: {column}, Width: {width}')
                    for col in range(column, N_COLUMNS):
                        i2c.write_byte_data(0x3C, 0x40, 0x00)

                    page = (page + 1) % N_PAGES
                    column = 0
                    i2c.write_block_data(0x3C, 0x00, SSD1306_PA_MODE_SET_PAGE_ADDR.get_command(page))
                    i2c.write_block_data(0x3C, 0x00, SSD1306_PA_MODE_SET_COLUMN_ADDR_LOW.get_command(column & 0x0F))
                    i2c.write_block_data(0x3C, 0x00, SSD1306_PA_MODE_SET_COLUMN_ADDR_HIGH.get_command(column >> 4))

            for byte in columns:
                i2c.write_byte_data(0x3C, 0x40, byte)
                column += 1
                column %= N_COLUMNS
                if column == 0:
                    page = (page + 1) % N_PAGES

            if font == font6x4:
                rows = 5
            elif font == font8x9:
                rows = 8
            else:
                raise ValueError(f'Unknown font: {font}.')
            # print_columns(columns, rows)
            # time.sleep(0.001)

    print(f'Page: {page}, Column: {column}')
    for col in range(column, N_COLUMNS):
        i2c.write_byte_data(0x3C, 0x40, 0x00)

    time.sleep(1)
