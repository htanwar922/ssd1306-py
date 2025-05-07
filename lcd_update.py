# send_lcd_update.py
import socket

from lcd_display import PAGES, COLUMNS, MODE_PAGE, MODE_HORIZONTAL, MODE_VERTICAL

def send_message(message, host='127.0.0.1', port=12345):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode(), (host, port))
    sock.close()
    return True

def set_mode(mode):
    if mode not in (MODE_PAGE, MODE_HORIZONTAL, MODE_VERTICAL):
        raise ValueError(f'Invalid mode: {mode}. Expected one of {MODE_PAGE}, {MODE_HORIZONTAL}, {MODE_VERTICAL}')
    message = f'mode {mode}'
    return send_message(message)

def set_page(page):
    if page < 0 or page >= PAGES:
        raise ValueError(f'Page {page} out of range (0-{PAGES-1})')
    message = f'page {page}'
    return send_message(message)

def set_column(column):
    if column < 0 or column >= COLUMNS:
        raise ValueError(f'Column {column} out of range (0-{COLUMNS-1})')
    message = f'col {column}'
    return send_message(message)

def write(bytes_ : bytes):
    if not isinstance(bytes_, (bytes, bytearray)):
        raise TypeError(f'Expected bytes or bytearray, got {type(bytes_)}')
    if len(bytes_) == 0:
        raise ValueError('Bytes object is empty')
    message = 'write ' + ' '.join(f'{byte:02x}' for byte in bytes_)
    return send_message(message)
