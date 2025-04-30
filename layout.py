from collections.abc import Iterable
from typing import Callable, List, Tuple, Union

class ByteArray(bytearray):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return '{' + ' '.join(f'{byte:02x}' for byte in self) + '}'

class Tile:
    def __init__(self, startpage, startcolumn, endpage, endcolumn):
        self.startpage = startpage
        self.startcolumn = startcolumn
        self.endpage = endpage
        self.endcolumn = endcolumn
        self._data : List[ByteArray] = [ByteArray([0] * self.width) for _ in range(self.height)]
        self._dirty : List[Tuple[int, int, Union[bytes, bytearray]]] = []

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

        self._dirty.append((*item, ByteArray(value)))

    @property
    def dirty(self):
        return self._dirty

    def clear(self, callback: Callable[[int, int, List[int]], None]):
        self._dirty.clear()

        for i in range(self.height):
            self._dirty.append((i, 0, ByteArray([0] * self.width)))

        return self.flush(callback)

    def flush(self, callback: Callable[[int, int, List[int]], None], force: bool = False) -> bool:
        if not callable(callback):
            raise TypeError('Callback must be callable')

        if not self._dirty:
            if not force:
                print('Nothing to flush')
                return True

            self._dirty = [(i, 0, self._data[i]) for i in range(self.height)]

        while self._dirty:
            i, j, value = self._dirty.pop(0)

            if not callback(self.startpage + i, self.startcolumn + j, value):
                return False

            self._data[i][j:j+len(value)] = value

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

        seg = Tile(startpage, startcolumn, endpage, endcolumn)
        for tile in self.tiles:
            if seg.overlaps(tile):
                raise ValueError(f'Tile overlaps with existing tile: {tile}')
        self.tiles.append(seg)

    def clear(self, callback: Callable[[int, int, List[int]], None]):
        for tile in self.tiles:
            tile.clear(callback)

    def flush(self, callback: Callable[[int, int, List[int]], None], force: bool = False) -> bool:
        for tile in self.tiles:
            if not tile.flush(callback, force):
                return False
        return True

    def __repr__(self):
        ret = f'Layout({self.pages}x{self.columns} - {len(self.tiles)} tiles)\n'
        ret += '>>> layout start\n'
        for tile in self.tiles:
            seg = str(tile)
            prefix = ' ' * 4
            seg = seg.replace('\n', '\n' + prefix)
            ret += prefix + seg + '\n'
        ret += '<<< layout end\n'
        return ret

