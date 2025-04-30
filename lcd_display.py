# lcd_display_udp.py
import socket
import sys
from colorama import init, Cursor
import shutil

# Initialize colorama for Windows
init()
TERM_WIDTH, TERM_HEIGHT = shutil.get_terminal_size()

PAGES = 4
COLUMNS = 128
ROWS = PAGES * 8

# UPPER_0 = '˙'
# LOWER_0 = '.'
# BOTH_0 = ':'

BOTH_0 = '░'
UPPER_1 = '▀'
LOWER_1 = '▄'
BOTH_1 = '█'

'''
Character | Unicode | Name | Description
█ | U+2588 | Full Block | Solid full-height block
▀ | U+2580 | Upper Half Block | Top half of the cell is filled
▄ | U+2584 | Lower Half Block | Bottom half filled
▌ | U+258C | Left Half Block | Left side filled
▐ | U+2590 | Right Half Block | Right side filled
▖,▗,▘,▝,▚,▞,▙,▛,▜,▟ | U+2596-U+259F | Quadrant Blocks | Precise pixel-like 2x2 control

Character | Unicode | Description
─ | U+2500 | Horizontal line
│ | U+2502 | Vertical line
┌ | U+250C | Top-left corner
┐ | U+2510 | Top-right corner
└ | U+2514 | Bottom-left corner
┘ | U+2518 | Bottom-right corner
├ ┤ ┬ ┴ ┼ |  | T-junctions, cross
'''

HORIZONTAL_LINE = '─'
VERTICAL_LINE = '│'
LOWER_LINE = '_'
TOP_LEFT_CORNER = '┌'
TOP_RIGHT_CORNER = '┐'
BOTTOM_LEFT_CORNER = '└'
BOTTOM_RIGHT_CORNER = '┘'

MODE_PAGE = 'page'
MODE_HORIZONTAL = 'horizontal'
MODE_VERTICAL = 'vertical'

# Global variables
printable_row = 0
printable_row_save = 0

class LCDDisplay:
    # Create display buffer
    _display = [[0 for _ in range(COLUMNS)] for _ in range(PAGES)]
    _current_page = 0
    _current_col = 0
    _mode = MODE_PAGE

    @staticmethod
    def set_mode(mode):
        if mode in (MODE_PAGE, MODE_HORIZONTAL):
            LCDDisplay._mode = mode
        elif mode == MODE_VERTICAL:
            raise NotImplementedError('Vertical mode is not implemented yet. Use page or horizontal mode instead.')

    @staticmethod
    def set_page(page):
        if 0 <= page < PAGES:
            LCDDisplay._current_page = page

    @staticmethod
    def set_col(col):
        if 0 <= col < COLUMNS:
            LCDDisplay._current_col = col

    @staticmethod
    def _get_cursor(page, col):
        if 0 <= page < PAGES and 0 <= col < COLUMNS:
            return page * 4 + 2, col + 1
        else:
            raise ValueError('Invalid page or column number')

    @staticmethod
    def write(byte):
        LCDDisplay._display[LCDDisplay._current_page][LCDDisplay._current_col] = byte
        first_double_row, col = LCDDisplay._get_cursor(LCDDisplay._current_page, LCDDisplay._current_col)
        print(first_double_row, col, byte)

        for double_row in range(first_double_row, first_double_row + 4):
            bits = byte & 0b1
            byte >>= 1
            bits = bits << 1 | (byte & 0b1)
            byte >>= 1
            if bits == 0:
                char = BOTH_0
            elif bits == 1:
                char = LOWER_1
            elif bits == 2:
                char = UPPER_1
            elif bits == 3:
                char = BOTH_1
            LCDDisplay._write_pos(double_row, col + 1, char)

        LCDDisplay._current_col = (LCDDisplay._current_col + 1) % COLUMNS
        if LCDDisplay._mode == MODE_HORIZONTAL and LCDDisplay._current_col == 0:
            LCDDisplay._current_page = (LCDDisplay._current_page + 1) % PAGES

    def clear_screen():
        sys.stdout.write('\033[2J')
        sys.stdout.flush()

    @staticmethod
    def _write_pos(row, col, byte):
        sys.stdout.write(Cursor.POS(col, row))
        sys.stdout.write(byte)
        sys.stdout.flush()

    @staticmethod
    def draw_initial_display():
        # Top border
        top_border_row = 1
        number_of_double_rows = ROWS // 2
        bottom_border_row = top_border_row + 1 + number_of_double_rows

        left_border_col = 1
        number_of_columns = COLUMNS
        right_border_col = left_border_col + 1 + number_of_columns

        LCDDisplay._write_pos(top_border_row, 1, TOP_LEFT_CORNER)
        for col in range(left_border_col + 1, right_border_col):
            LCDDisplay._write_pos(top_border_row, col, HORIZONTAL_LINE)
        LCDDisplay._write_pos(top_border_row, right_border_col, TOP_RIGHT_CORNER)

        for double_row in range(top_border_row + 1, bottom_border_row):
            # Left border
            LCDDisplay._write_pos(double_row, left_border_col, VERTICAL_LINE)

            for col in range(left_border_col + 1, right_border_col):
                LCDDisplay._write_pos(double_row, col, BOTH_0)

            # Right border
            LCDDisplay._write_pos(double_row, right_border_col, VERTICAL_LINE)

        # Bottom border
        LCDDisplay._write_pos(bottom_border_row, 1, BOTTOM_LEFT_CORNER)
        for col in range(left_border_col + 1, right_border_col):
            LCDDisplay._write_pos(bottom_border_row, col, HORIZONTAL_LINE)
        LCDDisplay._write_pos(bottom_border_row, right_border_col, BOTTOM_RIGHT_CORNER)

        return bottom_border_row + 1

def main():
    global printable_row
    global printable_row_save

    assert PAGES <= TERM_HEIGHT, 'Terminal height is too small for the display'
    assert COLUMNS <= TERM_WIDTH, 'Terminal width is too small for the display'

    assert ROWS & 1 == 0, 'ROWS must be even'
    assert COLUMNS & 1 == 0, 'COLUMNS must be even'

    LCDDisplay.clear_screen()
    printable_row = LCDDisplay.draw_initial_display()
    printable_row_save = printable_row

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 12345))
    sock.settimeout(0.1)  # Set a timeout for the socket
    print('Listening for UDP packets on port 12345...')

    # Set initial position
    LCDDisplay.set_mode(MODE_PAGE)
    LCDDisplay.set_page(0)
    LCDDisplay.set_col(0)
    try:
        while True:
            try:
                data, _ = sock.recvfrom(1024)
                if not data:
                    continue
                print(data.decode())
                msg = data.decode().strip()
                if len(msg) <= 2:
                    raise ValueError('Invalid message format')
                cmd, value = msg.split()[0], msg.split()[1:]
                if cmd == 'page':
                    page = int(value[0])
                    LCDDisplay.set_page(page)
                    # print(f'Set page to {page}')
                elif cmd == 'col':
                    col = int(value[0])
                    LCDDisplay.set_col(col)
                    # print(f'Set column to {col}')
                elif cmd == 'write':
                    bytes_ = map(lambda x: int(x, 16), value)
                    for byte in bytes_:
                        LCDDisplay.write(byte)
                        print(f'Wrote byte {byte:02x} to page {LCDDisplay._current_page}, column {LCDDisplay._current_col}')
                elif cmd == 'mode':
                    LCDDisplay.set_mode(value[0])
                    # print(f'Set mode to {mode}')
                else:
                    raise ValueError(f'Unknown command: {cmd}')
            except socket.timeout:
                    continue
            except KeyboardInterrupt:
                print('Exiting...')
                break
            except Exception as e:
                print(f'Error: {e}')
    except KeyboardInterrupt:
        print('Exiting...')
    finally:
        sock.close()
        sys.stdout.write(Cursor.POS(1, TERM_HEIGHT))

def print(*args, **_):
    global printable_row
    global printable_row_save
    max_chars = 80
    sys.stdout.write(Cursor.POS(1, printable_row) + ' ' * TERM_WIDTH)
    sys.stdout.write(Cursor.POS(1, printable_row) + f'{printable_row - printable_row_save}: ' + ' '.join(map(str, args))[:max_chars])
    sys.stdout.flush()
    printable_row = printable_row + 1 if printable_row < TERM_HEIGHT else printable_row_save + 1

if __name__ == '__main__':
    main()
