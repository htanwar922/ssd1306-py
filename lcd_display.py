# lcd_display_udp.py
import socket
import sys
from colorama import init, Cursor
import shutil

from ssd1306 import *

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

# Global variables
printable_row = 0
printable_row_save = 0

class LCDDisplay:
    _mode = OPTION_ADDRESSING_MODE_PAGE
    _display = [[0 for _ in range(COLUMNS)] for _ in range(PAGES)]
    _current_page1 = 0
    _current_page2 = 0
    _current_col1 = 0
    _current_col2 = 0
    _current_page = 0
    _current_col = 0
    _cmd_buffer = []
    _n_times = 10  # For debugging purposes

    @staticmethod
    def set_mode(mode):
        if mode in (OPTION_ADDRESSING_MODE_PAGE, OPTION_ADDRESSING_MODE_HORIZONTAL):
            LCDDisplay._mode = mode
        elif mode == OPTION_ADDRESSING_MODE_VERTICAL:
            raise NotImplementedError('Vertical mode is not implemented yet. Use page or horizontal mode instead.')

    @staticmethod
    def set_page(page1, page2):
        if 0 <= page1 < PAGES and 0 <= page2 < PAGES:
            LCDDisplay._current_page1 = page1
            LCDDisplay._current_page2 = page2
            LCDDisplay._current_page = page1

    @staticmethod
    def set_col(col1, col2):
        if 0 <= col1 < COLUMNS and 0 <= col2 < COLUMNS:
            LCDDisplay._current_col1 = col1
            LCDDisplay._current_col2 = col2
            LCDDisplay._current_col = col1

    @staticmethod
    def _get_cursor(page, col):
        if 0 <= page < PAGES and 0 <= col < COLUMNS:
            return page * 4 + 2, col + 1
        else:
            raise ValueError('Invalid page or column number')

    @staticmethod
    def write(byte):
        LCDDisplay._cmd_buffer = []

        LCDDisplay._display[LCDDisplay._current_page][LCDDisplay._current_col] = byte
        first_double_row, col = LCDDisplay._get_cursor(LCDDisplay._current_page, LCDDisplay._current_col)

        if LCDDisplay._n_times:
            print('N times 1', first_double_row, col, f'{byte:02x}')
            LCDDisplay._n_times -= 1

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
            if LCDDisplay._n_times:
                print('N times 2', double_row, col + 1, f'{bits:02b}')
                LCDDisplay._n_times -= 1
            LCDDisplay._write_pos(double_row, col + 1, char)

        LCDDisplay._current_col = LCDDisplay._current_col + 1
        if LCDDisplay._mode == OPTION_ADDRESSING_MODE_HORIZONTAL and LCDDisplay._current_col > LCDDisplay._current_col2:
            LCDDisplay._current_col = LCDDisplay._current_col1
            LCDDisplay._current_page = LCDDisplay._current_page + 1
        if LCDDisplay._current_page > LCDDisplay._current_page2:
            LCDDisplay._current_page = LCDDisplay._current_page1

    @staticmethod
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

    @staticmethod
    def parse_command(data):
        LCDDisplay._cmd_buffer += list(data)
        for cmd in SSD1306_COMMANDS:
            try:
                cmd.parse(LCDDisplay._cmd_buffer)
                break
            except AssertionError:
                pass
        else:
            if len(LCDDisplay._cmd_buffer) > 7:
                LCDDisplay._cmd_buffer = LCDDisplay._cmd_buffer[1:]
                LCDDisplay.parse_command([])
            # print('\tWaiting for command to complete...')
            return False

        context, LCDDisplay._cmd_buffer = cmd.parse(LCDDisplay._cmd_buffer)
        if cmd is SSD1306_I2C_ADDRESS:
            print('I2C address:', context)
            return True
        if cmd is SSD1306_SETCONTRAST:
            print('Contrast:', context)
            return True
        if cmd is SSD1306_DISPLAY:
            if context == OPTION_DISPLAY_ALLON_CLEAR:
                print('Display all on clear')
            elif context == OPTION_DISPLAY_ALLON_RESUME:
                print('Display all on resume')
            elif context == OPTION_DISPLAY_NORMAL:
                print('Display normal')
            elif context == OPTION_DISPLAY_INVERT:
                print('Display inverse')
            elif context == OPTION_DISPLAY_OFF:
                print('Display off')
            elif context == OPTION_DISPLAY_ON:
                print('Display on')
            else:
                print('Display:', context)
            return True
        if cmd is SSD1306_SCROLL_HORIZONTAL:
            print('Scroll horizontal:', context)
            return True
        if cmd is SSD1306_SCROLL_HORIZONTAL_VERTICAL:
            print('Scroll horizontal vertical:', context)
            return True
        if cmd is SSD1306_SCROLL_DEACTIVATE:
            print('Scroll deactivate:', context)
            return True
        if cmd is SSD1306_SCROLL_ACTIVATE:
            print('Scroll activate:', context)
            return True
        if cmd is SSD1306_SET_VERTICAL_SCROLL_AREA:
            print('Set vertical scroll area:', context)
            return True
        if cmd is SSD1306_SET_MEMORY_ADDRESSING_MODE:
            print('Set memory addressing mode:', context)
            if context[0] == OPTION_ADDRESSING_MODE_HORIZONTAL:
                LCDDisplay.set_mode(OPTION_ADDRESSING_MODE_HORIZONTAL)
            elif context == OPTION_ADDRESSING_MODE_VERTICAL:
                LCDDisplay.set_mode(OPTION_ADDRESSING_MODE_VERTICAL)
            elif context == OPTION_ADDRESSING_MODE_PAGE:
                LCDDisplay.set_mode(OPTION_ADDRESSING_MODE_PAGE)
            else:
                print('Invalid addressing mode:', context)
            return True
        if cmd is SSD1306_PA_MODE_SET_PAGE_ADDR:
            print('Page address:', context)
            LCDDisplay.set_page(context, PAGES - 1)
            return True
        if cmd is SSD1306_PA_MODE_SET_COLUMN_ADDR_LOW:
            print('Column address low:', context)
            LCDDisplay.set_col(LCDDisplay._current_col1 & 0xF0 | context[0] & 0x0F, LCDDisplay._current_col2)
            return True
        if cmd is SSD1306_PA_MODE_SET_COLUMN_ADDR_HIGH:
            print('Column address high:', context)
            LCDDisplay.set_col(LCDDisplay._current_col1 & 0x0F | context[0] & 0xF0, LCDDisplay._current_col2)
            return True
        if cmd is SSD1306_HAVA_MODE_SET_PAGE_ADDR:
            print('Page address:', context)
            LCDDisplay.set_page(context[0], context[1])
            return True
        if cmd is SSD1306_HAVA_MODE_SET_COLUMN_ADDR:
            print('Column address:', context)
            LCDDisplay.set_col(context[0], context[1])
            return True
        if cmd is SSD1306_SET_START_LINE:
            print('Set start line:', context)
            LCDDisplay.set_col(context, LCDDisplay._current_col2)
            return True
        if cmd is SSD1306_SEGMENT_REMAP:
            print('Segment remap:', context)
            return True
        if cmd is SSD1306_SET_MULTIPLEX:
            print('Set multiplex:', context)
            return True
        if cmd is SSD1306_COM_OUTPUT_SCAN_DIR:
            print('COM output scan direction:', context)
            return True
        if cmd is SSD1306_SET_DISPLAY_OFFSET:
            print('Set display offset:', context)
            LCDDisplay.set_page(context[0], LCDDisplay._current_page2)
            return True
        if cmd is SSD1306_SET_COM_PINS:
            print('Set COM pins:', context)
            return True
        if cmd is SSD1306_SET_DISPLAY_CLOCK_DIV_RATIO:
            print('Set display clock div ratio:', context)
            return True
        if cmd is SSD1306_SET_PRECHARGE_PERIOD:
            print('Set precharge period:', context)
            return True
        if cmd is SSD1306_SET_VCOM_DESELECT_LEVEL:
            print('Set VCOM deselect level:', context)
            return True
        if cmd is SSD1306_NOP:
            print('No operation:', context)
            return True
        if cmd is SSD1306_CHARGE_PUMP:
            print('Charge pump:', context)
            return True
        if cmd is SSD1306_EXTERNAL_VCC:
            print('External VCC:', context)
            return True
        if cmd is SSD1306_SWITCH_CAP_VCC:
            print('Switch cap VCC:', context)
            return True
        if cmd is SSD1306_SET_PRECHARGE_PERIOD:
            print('Set precharge period:', context)
            return True
        if cmd is SSD1306_SET_VCOM_DESELECT_LEVEL:
            print('Set VCOM deselect level:', context)
            return True
        raise NotImplementedError(f'Command {cmd} not implemented yet.')

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
    LCDDisplay.set_mode(OPTION_ADDRESSING_MODE_PAGE)
    LCDDisplay.set_page(0x0, PAGES - 1)
    LCDDisplay.set_col(0x00, COLUMNS - 1)
    try:
        while True:
            try:
                data, _ = sock.recvfrom(1024)
                if not data:
                    continue
                data = list(data)
                if data[0] >> 1 != 0x3C:
                    continue
                if data[0] & 1 == 0:
                    if data[1] == 0x00:
                        LCDDisplay.parse_command(data[2:])
                    else:
                        print('Data: ', ''.join(f'{byte:02x}' for byte in data))
                        print(LCDDisplay._current_page, LCDDisplay._current_col)
                        for byte in data[2:]:
                            LCDDisplay.write(byte)
                else:
                    print('Read mode')
                    raise NotImplementedError('Read mode is not implemented yet.')
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

with open('display.log', 'w') as f:
    f.write('LCD Display Log\n')
    f.write('================\n')

def print(*args, **_):
    global printable_row
    global printable_row_save
    max_chars = 80
    sys.stdout.write(Cursor.POS(1, printable_row) + ' ' * TERM_WIDTH)
    sys.stdout.write(Cursor.POS(1, printable_row) + f'{printable_row - printable_row_save}: ' + ' '.join(map(str, args))[:max_chars])
    sys.stdout.flush()
    printable_row = printable_row + 1 if printable_row < TERM_HEIGHT else printable_row_save + 1
    with open('display.log', 'a') as f:
        f.write(f'{printable_row - printable_row_save}: ' + ' '.join(map(str, args)) + '\n')

# LCDDisplay.parse_command([0xAE])
# LCDDisplay.parse_command([0xD5])
# LCDDisplay.parse_command([0x80])
# LCDDisplay.parse_command([0xA8])
# LCDDisplay.parse_command([0x1F])
# LCDDisplay.parse_command([0xD3])
# LCDDisplay.parse_command([0x00])
# LCDDisplay.parse_command([0x40])
# LCDDisplay.parse_command([0x8D])
# LCDDisplay.parse_command([0x14])
# LCDDisplay.parse_command([0x20])
# LCDDisplay.parse_command([0x00])
# LCDDisplay.parse_command([0xA1])
# LCDDisplay.parse_command([0xC0])
# LCDDisplay.parse_command([0xDA])
# LCDDisplay.parse_command([0x00])
# LCDDisplay.parse_command([0x81])
# LCDDisplay.parse_command([0x8F])
# LCDDisplay.parse_command([0xD9])
# LCDDisplay.parse_command([0xF1])
# LCDDisplay.parse_command([0xDB])
# LCDDisplay.parse_command([0x40])
# LCDDisplay.parse_command([0xA4])
# LCDDisplay.parse_command([0xA6])
# LCDDisplay.parse_command([0xAF])

# LCDDisplay.parse_command([0x20])
# LCDDisplay.parse_command([0x00])
# LCDDisplay.parse_command([0x21])
# LCDDisplay.parse_command([0x00])
# LCDDisplay.parse_command([0x7F])
# LCDDisplay.parse_command([0x22, 0x00, 0x03])

if __name__ == '__main__':
    main()
