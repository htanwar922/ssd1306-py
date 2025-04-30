#!/usr/bin/env python3

from abc import ABC, abstractmethod

class FontBase(ABC):
    """
    Abstract base class for fonts.
    """
    @property
    @abstractmethod
    def height(self):
        """
        Returns the pixel height of the font.
        """
        pass

    @property
    @abstractmethod
    def width(self):
        """
        Returns the pixel width of the font.
        """
        pass

    @abstractmethod
    def get_columns(self):
        """
        Returns the columns of the font.
        """
        pass

    @abstractmethod
    def __repr__(self):
        """
        Returns a string representation of the font.
        """
        pass

class Font6x4(FontBase):
    """
    # [Tiny Monospaced Font](https://robey.lag.net/2010/01/23/tiny-monospace-font.html)
    ## Tom Thumb: A very tiny, monospace, bitmap font
    ## Font data: 96 printable ASCII characters (0x20–0x7E)
    ## Each character is 4 bytes (4 columns × 6 rows), LSB = top row
    """
    def __init__(self, swidth, dwidth, bbx, bitmap):
        self.swidth = swidth
        self.dwidth = dwidth
        self.bbx = bbx
        self.bitmap = bitmap
    @property
    def height(self):
        return self.bbx[1] - self.bbx[3] + 1
    @property
    def width(self):
        return self.dwidth[0]
    def get_columns(self):
        columns = list([0] * 4)
        for row in range(len(self.bitmap)):
            byte = self.bitmap[row] >> 4
            for col in range(4):
                columns[col] |= ((byte & (1 << (3 - col))) >> (3 - col)) << (row + (6 - len(self.bitmap)))
        if any(columns):
            while len(columns) >= 2 and columns[-1] == 0 and columns[-2] == 0:
                columns.pop()
        return columns
    def __repr__(self):
        bitmap = '[' + ', '.join(f'0x{b:02x}' for b in self.bitmap) + ']'
        return f'{__class__.__name__}({self.swidth}, {self.dwidth}, {self.bbx}, {bitmap})'


class Font8x9(FontBase):
    """
    # [Pixelated Elegance Font](https://www.fontspace.com/pixelated-elegance-font-f126145)
    ## The font Pixelated Elegance - CC0 contains 206 glyphs.
    Font data: 206 printable ASCII, Latin-1, and more characters.
    """
    def __init__(self, advance, auto_update_advance, auto_advance_amount, pixels):
        self.advance = advance
        self.auto_update_advance = auto_update_advance
        self.auto_advance_amount = auto_advance_amount
        self.pixels = pixels
    @property
    def height(self):
        return 8
    @property
    def width(self):
        return self.advance
    def get_columns(self):
        pixels = self.pixels
        pixels = sorted(pixels)
        if pixels and self.width <= pixels[-1][0]:
            print(f'Character has width {self.width} <= max {pixels[-1][0]}. Will throw...')
        columns = list([0] * self.width)
        for pixel in pixels:
            columns[pixel[0]] |= (1 << (6 - pixel[1]))
        return columns
    def __repr__(self):
        return f'{__class__.__name__}({self.advance}, {self.auto_update_advance}, {self.auto_advance_amount}, {self.pixels})'


class Font16x8(FontBase):
    """
    # [Bizcat 16 × 8 font](https://github.com/tomwaitsfornoman/lawrie-nes_ecp5/blob/master/osd/font_bizcat8x16.mem)
    """
    def __init__(self, bitmap):
        self.bitmap = bitmap
    def get_columns(self):
        columns = list([0] * 8)
        for row in range(len(self.bitmap)):
            byte = self.bitmap[row]
            for col in range(8):
                columns[col] |= ((byte & (1 << (7 - col))) >> (7 - col)) << (len(self.bitmap) - row - 1)
        return columns


if __name__ == '__main__':

    font6x4 = {}
    with open('tom-thumb.bdf', 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break
            if line.startswith('STARTCHAR'):
                line = f.readline()
                encoding = int(line.split()[1])
                line = f.readline()
                swidth = tuple(map(int, line.split()[1:]))
                line = f.readline()
                dwidth = tuple(map(int, line.split()[1:]))
                line = f.readline()
                bbx = tuple(map(int, line.split()[1:]))
                f.readline()  # Skip BITMAP line
                bitmap = []
                while True:
                    line = f.readline()
                    if line.startswith('ENDCHAR'):
                        break
                    bitmap.append(int(line.strip(), 16))
                font6x4[chr(encoding)] = Font6x4(swidth, dwidth, bbx, bitmap)

    with open('font_6x4.txt', 'w', encoding='utf-8') as f:
        for k, v in font6x4.items():
            f.write("'" + (k if k not in ("'", "\\") else f'\\{k}') + f"': {v},\n")
        print(f'Generated font_6x4.txt for {len(font6x4)} characters')


    font8x9 = {}
    with open('Pixelated Elegance v0.3-7344.pxf', 'r') as f:
        num_glyphs = 0
        while True:
            line = f.readline()
            if not line:
                break
            if line.startswith('num_glyphs'):
                num_glyphs = int(line.split()[1])
            if line.startswith('glyphs'):
                break
        assert num_glyphs, f'Expected num_glyphs to be > 0, but got {num_glyphs}'

        for _ in range(num_glyphs):
            line = f.readline()
            if line.startswith('\t'):
                encoding = int(line.strip('\t\r\n:'))
                line = f.readline()
                advance = int(line.split()[1])
                line = f.readline()
                auto_update_advance = bool(line.split()[1])
                line = f.readline()
                auto_advance_amount = int(line.split()[1])
                line = f.readline()
                line = line.strip().split(':')[1].strip()
                pixels = []
                for pair in line.split(','):
                    if not pair:
                        continue
                    x, y = map(int, pair.split())
                    pixels.append((x, y))
                font8x9[chr(encoding)] = Font8x9(advance, auto_update_advance, auto_advance_amount, pixels)

    with open('font_8x9.txt', 'w', encoding='utf-8') as f:
        for k, v in font8x9.items():
            f.write("'" + (k if k not in ("'", "\\") else f'\\{k}') + f"': {v},\n")
        print(f'Generated font_8x9.txt for {len(font8x9)} characters')
