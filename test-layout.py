import time

from layout import Layout, Printer
from fonts import FontBase, font8x9, font6x4, font16x8, print_columns
from lcd_display import PAGES, COLUMNS, MODE_PAGE, MODE_HORIZONTAL, MODE_VERTICAL
from lcd_update import set_mode, set_page, set_column, write, send_update

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
