from collections.abc import Iterable
from typing import Callable, List, Dict, Tuple, Union

from fonts import FontBase

class ByteArray(bytearray):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self):
        # return '{' + ' '.join(f'{byte:02x}' for byte in self) + '}'
        return ' '.join(f'{byte:02x}' for byte in self)

    def __str__(self):
        return repr(self)

class Tile:
    def __init__(self, startpage, startcolumn, endpage, endcolumn):
        assert startpage <= endpage, f'Start page {startpage} must be less than or equal to end page {endpage}'
        assert startcolumn <= endcolumn, f'Start column {startcolumn} must be less than or equal to end column {endcolumn}'
        self.startpage = startpage
        self.startcolumn = startcolumn
        self.endpage = endpage
        self.endcolumn = endcolumn
        self._data : List[ByteArray] = [ByteArray([0] * self.width) for _ in range(self.height)]
        self._dirty = False

    @property
    def width(self) -> int:
        return self.endcolumn - self.startcolumn + 1

    @property
    def height(self) -> int:
        return self.endpage - self.startpage + 1

    def __getitem__(self, item : Union[int, Tuple[int, int]]) -> Union[int, bytes]:
        if isinstance(item, tuple):
            i, j = item

            if i < 0 or i >= self.height:
                raise ValueError(f'Row {i} out of range (0-{self.height-1})')

            if j < 0 or j >= self.width:
                raise ValueError(f'Column {j} out of range (0-{self.width-1})')

            return self._data[i][j]

        elif isinstance(item, int):
            if item < 0 or item >= self.height:
                raise ValueError(f'Row {item} out of range (0-{self.height-1})')

            return bytes(self._data[item])

        else:
            raise TypeError(f'Invalid index type: {type(item)}. Expected int or tuple of int.')

    def __setitem__(self, item : Union[int, Tuple[int, int]], value : Union[int, bytes, bytearray]):
        if not isinstance(value, (int, bytes, bytearray)):
            raise TypeError(f'Invalid value type: {type(value)}. Expected int, bytes, or bytearray.')

        if isinstance(item, int):
            if not isinstance(value, (bytes, bytearray)):
                raise TypeError(f'Invalid value type: {type(value)}. Expected bytes or bytearray.')

            if len(value) != self.width:
                raise ValueError(f'Data length {len(value)} does not match width {self.width}')

            item = (item, 0)

        elif not isinstance(item, tuple):
            raise TypeError(f'Invalid index type: {type(item)}. Expected int or tuple of int.')

        i, j = item

        if i < 0 or i >= self.height:
            raise ValueError(f'Row {i} out of range (0-{self.height-1})')

        if j < 0 or j >= self.width:
            raise ValueError(f'Column {j} out of range (0-{self.width-1})')

        if isinstance(value, (bytes, bytearray)):
            if len(value) > self.width:
                raise ValueError(f'Data length {len(value)} greater than width {self.width}')

            if j + len(value) > self.width:
                raise ValueError(f'Data length {len(value)} + column {j} exceeds width {self.width}')
        else:
            value = bytes([value])

        self._data[i][j:j+len(value)] = value
        self._dirty = True

    @property
    def dirty(self):
        return self._dirty

    def clear(self, callback: Callable[['Tile', List[int]], bool]):
        self._data = [ByteArray([0] * self.width) for _ in range(self.height)]
        self._dirty = True

        return self.flush(callback)

    def flush(self, callback: Callable[['Tile', List[int]], bool], force: bool = False) -> bool:
        if not callable(callback):
            raise TypeError('Callback must be callable')

        if not self._dirty:
            if not force:
                print('Nothing to flush')
                return True

        if not callback(self, [self._data[i][j] for i in range(self.height) for j in range(self.width)]):
            return False

        self._dirty = False

        return True

    def overlaps(self, other: 'Tile') -> bool:
        if not isinstance(other, Tile):
            raise TypeError(f'Expected Tile, got {type(other)}')

        return not (self.endpage < other.startpage or self.startpage > other.endpage or
                    self.endcolumn < other.startcolumn or self.startcolumn > other.endcolumn)

    def __repr__(self):
        ret = f'Tile([{self.startpage}, {self.startcolumn}] --> [{self.endpage}, {self.endcolumn}])\n'
        ret += '>>> tile start'
        steps = 16
        startcolumn = self.startcolumn
        while startcolumn < self.endcolumn + 1:
            ret += '\n'
            endcolumn = min(startcolumn + steps, self.endcolumn + 1)
            prefix = ' ' * 4
            ret += prefix + ' ' * 4 + ' '.join(f'{col:02x}' for col in range(startcolumn, endcolumn)) + '\n'
            for page in range(self.startpage, self.endpage + 1):
                page = page - self.startpage
                ret += prefix + f'{page:02x}: ' + ' '.join(f'{self._data[page][col]:02x}' for col in range(startcolumn, endcolumn)) + '\n'
            startcolumn += steps
        ret += '<<< tile end\n'
        return ret

class Layout:
    def __init__(self, pages, columns):
        self.pages = pages
        self.columns = columns
        self.tiles = []

    def add_tile(self, startpage, startcolumn, endpage, endcolumn):
        if startpage < 0 or startpage >= self.pages:
            raise ValueError(f'Start page {startpage} out of range (0-{self.pages-1})')

        if startcolumn < 0 or startcolumn >= self.columns:
            raise ValueError(f'Start column {startcolumn} out of range (0-{self.columns-1})')

        if endpage < 0 or endpage >= self.pages:
            raise ValueError(f'End page {endpage} out of range (0-{self.pages-1})')

        if endcolumn < 0 or endcolumn >= self.columns:
            raise ValueError(f'End column {endcolumn} out of range (0-{self.columns-1})')

        # Check if the tile is valid
        if startpage > endpage or (startpage == endpage and startcolumn > endcolumn):
            raise ValueError(f'Invalid tile: [{startpage}, {startcolumn}] --> [{endpage}, {endcolumn}]')

        tile_ = Tile(startpage, startcolumn, endpage, endcolumn)
        for tile in self.tiles:
            if tile_.overlaps(tile):
                raise ValueError(f'{str(tile_).split(chr(0x0a))[0]} overlaps with existing tile: {str(tile).split(chr(0x0a))[0]}')
        self.tiles.append(tile_)

    def clear(self, callback: Callable[[Tile, List[int]], bool]):
        return all(tile.clear(callback) for tile in self.tiles)

    def flush(self, callback: Callable[[Tile, List[int]], bool], force: bool = False) -> bool:
        return all(tile.flush(callback, force) for tile in self.tiles)

    def __repr__(self):
        ret = f'Layout({self.pages}x{self.columns} - {len(self.tiles)} tiles)\n'
        ret += '>>> layout start\n'
        for tile in self.tiles:
            tile_ = str(tile)
            prefix = ' ' * 4
            tile_ = tile_.replace('\n', '\n' + prefix)
            ret += prefix + tile_ + '\n'
        ret += '<<< layout end\n'
        return ret

class Printer:
    def __init__(self, layout: Layout, truncate: bool = True):
        if not isinstance(layout, Layout):
            raise TypeError(f'Expected Layout, got {type(layout)}')

        self.layout = layout
        self.truncate = truncate

    def __call__(self
            , tile_index: int
            , text: Union[str, List[int], List[List[int]]]
            , font: Union[None, Dict[str, FontBase]]
            , callback: Callable[[Tile, List[int]], bool]
        ):
        if tile_index < 0 or tile_index >= len(self.layout.tiles):
            raise ValueError(f'Tile index {tile_index} out of range (0-{len(self.layout.tiles)-1})')
        tile = self.layout.tiles[tile_index]
        if not isinstance(tile, Tile):
            raise TypeError(f'Tile index {tile_index} is not a Tile object')
        if font is not None and not isinstance(text, str):
            raise TypeError(f'Text must be a string, got {type(text)}')
        if not text:
            raise ValueError('Text cannot be empty')
        if not callable(callback):
            raise TypeError('Callback must be callable')

        current_column = 0
        for c in text:
            if font is None:
                columns = text
            elif c not in font:
                raise ValueError(f'Character {c} not found in font')
            else:
                columns = font[c].get_columns()

            if not self.truncate and current_column + len(columns) > tile.width:
                raise ValueError(f'Column overflow: {tile.startcolumn} + {current_column} + {len(columns)} > {tile.endcolumn}')
            if not isinstance(columns[0], Iterable):
                columns = [[column] for column in columns]

            if len(columns[0]) > tile.height:
                raise ValueError(f'Page overflow: {tile.startpage} + {len(columns)} > {tile.endpage}')

            for column in columns:
                for page, byte in enumerate(column):
                    if not self.truncate and current_column > tile.width:
                        raise ValueError(f'Column overflow: {tile.startcolumn} + {current_column} + {page} > {tile.endcolumn}')
                    try:
                        tile[page, current_column] = byte
                    except ValueError:
                        if self.truncate:
                            print(f'WARNING: Column overflow truncated: {tile.startcolumn} + {current_column} + {page} > {tile.endcolumn}')
                            break
                        else:
                            raise
                current_column += 1
        if not tile.flush(callback):
            raise RuntimeError('Failed to flush tile')
        return True

if __name__ == '__main__':
    import time
    import string

    from fonts import FontBase, font6x4, font8x9, print_columns
    from lcd_display import PAGES, COLUMNS, MODE_PAGE, MODE_HORIZONTAL, MODE_VERTICAL
    from lcd_update import set_mode, set_page, set_column, write, send_update

    N_PAGES = PAGES
    N_COLUMNS = COLUMNS

    layout = Layout(N_PAGES, N_COLUMNS)
    layout.add_tile(0, 0, N_PAGES - 1, N_COLUMNS - 1)
    tile1 = layout.tiles[0]
    print(layout)

    ret = tile1.clear(send_update)
    print(f'Clear: {ret}')

    # mode = MODE_VERTICAL
    mode = MODE_HORIZONTAL
    # mode = MODE_PAGE

    if mode == MODE_HORIZONTAL:
        set_mode(MODE_HORIZONTAL)

        set_page(0x0)
        set_column(0x00)
        for page in range(N_PAGES):
            for column in range(N_COLUMNS):
                tile1[page, column] = 0xaa
                layout.flush(lambda row, col, data: write(data))
                # time.sleep(0.001)
        for page in range(N_PAGES):
            for column in range(N_COLUMNS):
                tile1[page, column] = 0x00
                layout.flush(lambda row, col, data: write(data))
                # time.sleep(0.001)

    elif mode == MODE_PAGE:
        set_mode(MODE_PAGE)

        set_page(0x0)
        set_column(0x00)
        for page in range(N_PAGES):
            set_page(page)
            for column in range(N_COLUMNS):
                tile1[page, column] = 0xaa
                layout.flush(lambda row, col, data: write(data))
                # time.sleep(0.001)
        for page in range(N_PAGES):
            set_page(page)
            for column in range(N_COLUMNS):
                tile1[page, column] = 0x00
                layout.flush(lambda row, col, data: write(data))
                # time.sleep(0.001)

    elif mode == MODE_VERTICAL:
        raise NotImplementedError('Vertical addressing mode is not implemented yet.')

    else:
        raise ValueError(f'Invalid mode: {mode}. Expected one of {MODE_PAGE}, {MODE_HORIZONTAL}, {MODE_VERTICAL}')


    page = 0
    column = 0
    set_page(page)
    set_column(column)
    for font in [font6x4, font8x9]:
        font : Dict[str, FontBase]
        for c in string.printable:
            if c in ('\n', '\r', '\x0b', '\x0c'):
                continue
            if c not in font:
                print(f"Character '{c}' not found in {font.values()[0].__class__}.")
                continue
            columns = font[c].get_columns()

            if mode == MODE_PAGE:
                width = font[c].width
                if column + width >= N_COLUMNS:
                    # Will overflow, move to next page
                    print(f'Column: {column}, Width: {width}')
                    for col in range(column, N_COLUMNS):
                        tile1[page, col] = 0x00
                    layout.flush(lambda row, col, data: write(data))

                    page = (page + 1) % N_PAGES
                    column = 0
                    set_page(page)
                    set_column(column)


            for byte in columns:
                tile1[page, column] = byte
                column += 1
                column %= N_COLUMNS
                if column == 0:
                    page = (page + 1) % N_PAGES
            layout.flush(lambda row, col, data: write(data))

            if font == font6x4:
                rows = 5
            elif font == font8x9:
                rows = 8
            else:
                raise ValueError(f'Unknown font: {font}.')
            # print_columns(columns, rows)
            time.sleep(0.001)

    print(f'Page: {page}, Column: {column}')

    for col in range(column, N_COLUMNS):
        tile1[page, col] = 0x00
    layout.flush(lambda row, col, data: write(data))
    print(layout)

    time.sleep(1)

    # Not in coherence with the actual LCD behaviour - won't specify page and column every time
    for page in range(N_PAGES):
        set_page(page)
        set_column(0x00)
        for _ in range(N_COLUMNS):
            write(b'\x00')
    layout.flush(send_update, force=True)
