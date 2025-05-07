import time

from layout import Layout, Printer
from fonts import FontBase, font8x9, font6x4, font16x8, print_columns
from lcd_display import PAGES, COLUMNS
from lcd_update import set_mode, set_page, set_column, write

N_PAGES, N_COLUMNS = PAGES, COLUMNS

layout1 = None
"""                                                        LAYOUT 1
┌────────────────────────────────────────────────────────────────────────────────────────────────┬────────┬────────────────────────┐
│******************************************** TILE 0 ********************************************│   T5   │******** TILE 2 ********│
├────────────────────────────────────────────────────────────────────────────────────────────────│────────│────────────────────────┤
│******************************************** TILE 1 ********************************************│   T6   │******** TILE 3 ********│
├────────────────────────────────────────────────────────────────────────────────────────────────┴────────┴────────────────────────┤
│************************************************************************************************─********─************************│
│                                                           TILE 4                                                                 │
│************************************************************************************************─********─************************│
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
"""
layout2 = None
"""                                                        LAYOUT 2
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┬────┐
│********************************************************** TILE 0 **********************************************************│****│
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤ T3 │
│********************************************************** TILE 1 **********************************************************│****│
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┴────┤
│****************************************************************************************************************************│****│
│                                                           TILE 2                                                           │ T4 │
│****************************************************************************************************************************│****│
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┴────┘
"""

layout1 = Layout(N_PAGES, N_COLUMNS)
layout1.add_tile(0,                     0,                      0,                          32 * 3 - 1)
layout1.add_tile(1,                     0,                      1,                          32 * 3 - 1)
layout1.add_tile(0,            32 * 3 + 8,                      0,                       N_COLUMNS - 1)
layout1.add_tile(1,            32 * 3 + 8,                      1,                       N_COLUMNS - 1)
layout1.add_tile(2,                     0,                      3,                       N_COLUMNS - 1)
layout1.add_tile(0,                32 * 3,                      0,                          32 * 3 + 7)      # Empty tiles for aesthetics
layout1.add_tile(1,                32 * 3,                      1,                          32 * 3 + 7)      # Empty tiles for aesthetics

printer = Printer(layout1)

def send_update(tile, bytes_ : bytes) -> bool:
    # import time; time.sleep(0.001)
    return set_page(tile.startpage, tile.endpage) \
        and set_column(tile.startcolumn, tile.endcolumn) \
        and write(bytes(bytes_))

ret = layout1.clear(send_update)
print(f'Clear: {ret}')

time.sleep(1)

printer(0, '!', font8x9, send_update)
printer(0, 'Voltage - R-phase', font8x9, send_update)
printer(1, 'Unit:- V', font8x9, send_update)

printer(2, 'UV', font8x9, send_update)
printer(3, 'GF', font8x9, send_update)

printer.truncate = False
printer(4, '230.000000000000', font16x8, send_update)

time.sleep(1)

layout2 = Layout(N_PAGES, N_COLUMNS)
layout2.add_tile(0,                     0,                      0,                          N_COLUMNS - 5)
layout2.add_tile(1,                     0,                      1,                          N_COLUMNS - 5)
layout2.add_tile(2,                     0,                      3,                          N_COLUMNS - 5)
layout2.add_tile(0,         N_COLUMNS - 4,                      1,                          N_COLUMNS - 1)
layout2.add_tile(2,         N_COLUMNS - 4,                      3,                          N_COLUMNS - 1)

layout2.clear(send_update)
printer = Printer(layout2)
printer(0, 'Voltage - R-phase', font8x9, send_update)
printer(1, 'Unit:- V', font8x9, send_update)
printer(2, '230.000000000000', font16x8, send_update)

printer(4, [[0x00] * 2] * 4, None, send_update)

while True:
    printer(3, [[0xff] * 2] * 4, None, send_update)
    time.sleep(0.5)
    printer(3, [[0x00] * 2] * 4, None, send_update)
    time.sleep(0.5)


from ch347bus import I2CDevice
from ssd1306 import *

ADDRESSING_MODE = OPTION_ADDRESSING_MODE_HORIZONTAL

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

i2c = I2CDevice()

for cmd in setup:
    i2c.write_byte_data(0x3C, 0x00, cmd)

def write_func(tile, data):
    i2c.write_byte_data(0x3C, 0x00, bytes([0x20, 0x00]))
    i2c.write_byte_data(0x3C, 0x00, bytes([0x22, tile.startpage, tile.endpage]))
    i2c.write_byte_data(0x3C, 0x00, bytes([0x21, tile.startcolumn, tile.endcolumn]))
    while data:
        i2c.write_block_data(0x3C, 0x40, data[:32])
        data = data[32:]
    return True

for tile in range(len(layout1.tiles)):
    font = font16x8 if tile == 4 else font8x9
    printer(tile, f'{tile}', font, write_func)
