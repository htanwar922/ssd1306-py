# send_lcd_update.py
import socket

from lcd_display import PAGES, COLUMNS
from ssd1306 import *

def send_message(data, host='127.0.0.1', port=12345):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (host, port))
    sock.close()
    return True

def set_mode(mode):
    if mode not in (OPTION_ADDRESSING_MODE_PAGE,
                    OPTION_ADDRESSING_MODE_HORIZONTAL,
                    OPTION_ADDRESSING_MODE_VERTICAL):
        raise ValueError(f'Invalid mode: {mode}.')
    data = SSD1306_SET_MEMORY_ADDRESSING_MODE.get_command(mode)
    return send_message(bytes([0x3C << 1 | 0] + [0x00] + data))

def set_page(startpage, endpage=None):
    if startpage < 0 or startpage >= PAGES:
        raise ValueError(f'Start page {startpage} out of range (0-{PAGES-1})')
    if endpage is not None:
        if endpage < 0 or endpage >= PAGES:
            raise ValueError(f'End page {endpage} out of range (0-{PAGES-1})')
        if startpage > endpage:
            raise ValueError(f'Start page {startpage} cannot be greater than end page {endpage}')
        if endpage - startpage > PAGES:
            raise ValueError(f'Page range {startpage}-{endpage} exceeds display height ({PAGES})')
        data = SSD1306_HAVA_MODE_SET_PAGE_ADDR.get_command(startpage, endpage)
    else:
        data = SSD1306_PA_MODE_SET_PAGE_ADDR.get_command(startpage)
    return send_message(bytes([0x3C << 1 | 0] + [0x00] + data))

def set_column(startcolumn, endcolumn=None):
    if startcolumn < 0 or startcolumn >= COLUMNS:
        raise ValueError(f'Column {startcolumn} out of range (0-{COLUMNS-1})')
    if endcolumn is not None:
        if endcolumn < 0 or endcolumn >= COLUMNS:
            raise ValueError(f'End column {endcolumn} out of range (0-{COLUMNS-1})')
        if startcolumn > endcolumn:
            raise ValueError(f'Start column {startcolumn} cannot be greater than end column {endcolumn}')
        if endcolumn - startcolumn > COLUMNS:
            raise ValueError(f'Column range {startcolumn}-{endcolumn} exceeds display width ({COLUMNS})')
        data = SSD1306_HAVA_MODE_SET_COLUMN_ADDR.get_command(startcolumn, endcolumn)
    else:
        data = SSD1306_PA_MODE_SET_COLUMN_ADDR_LOW.get_command(startcolumn & 0x0F)
        data += SSD1306_PA_MODE_SET_COLUMN_ADDR_HIGH.get_command(startcolumn >> 4)
    return send_message(bytes([0x3C << 1 | 0] + [0x00] + data))

def write(bytes_ : bytes):
    if not isinstance(bytes_, (bytes, bytearray)):
        raise TypeError(f'Expected bytes or bytearray, got {type(bytes_)}')
    if len(bytes_) == 0:
        raise ValueError('Bytes object is empty')
    data = bytes([0x3C << 1 | 0] + [0x40] + list(bytes_))
    return send_message(data)
