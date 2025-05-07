#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: CH347-HIDAPI
# Filename: demo_2
# Created on: 2024/1/7

# [PDF](https://cdn-shop.adafruit.com/datasheets/SSD1306.pdf)

class CommandBase:
    _CMD_ID = 0x00
    def __init__(self, command):
        self.command = command
        self.ID = CommandBase._CMD_ID
        CommandBase._CMD_ID += 1

class Command(CommandBase):
    def __init__(self, command):
        super().__init__(command)

    def get_command(self):
        return [self.command]

    def parse(self, data):
        assert data[0] == self.command, f'Expected command {self.command}, got {data[0]}'
        return data[1:]

class CommandWithBitmask(CommandBase):
    def __init__(self, command, bitmask, options=None):
        super().__init__(command)
        self.bitmask = bitmask
        self.options = options

    def get_command(self, option):
        if self.options is not None:
            assert option in self.options, f'Value {option} not in options {self.options}'
        return [self.command | (option & self.bitmask)]

    def parse(self, data):
        assert len(data) >= 1, f'Expected at least 1 byte, got {len(data)}'
        assert data[0] & (~self.bitmask) == self.command, f'Expected command {self.command}, got {data[0]}'
        option = data[0] & self.bitmask
        if self.options is not None:
            assert option in self.options, f'Value {option} not in options {self.options}'
        return option, data[1:]

class CommandWithArgs(CommandBase):
    def __init__(self, command, argc=0, bitmasks=None):
        super().__init__(command)
        assert bitmasks is None or len(bitmasks) == argc, f'Expected {argc} bitmasks, got {len(bitmasks)}'
        self.argc = argc
        self.bitmasks = bitmasks if bitmasks else [0xFF] * argc

    def get_command(self, *args):
        assert len(args) == self.argc, f'Expected {self.argc} arguments, got {len(args)}'
        return [self.command] + [arg & self.bitmasks[i] for i, arg in enumerate(args)]

    def parse(self, data):
        assert len(data) >= 1 + self.argc, f'Expected at least {self.argc} arguments, got {len(data)}'
        assert data[0] == self.command, f'Expected command {self.command}, got {data[0]}'
        args = []
        for i in range(self.argc):
            arg = data[i + 1] & self.bitmasks[i]
            args.append(arg)
        return args, data[1 + self.argc:]

class CommandWithBitmaskAndArgs(CommandWithBitmask):
    def __init__(self, command, cmdbitmask, options=None, argc=0, bitmasks=None):
        super().__init__(command, cmdbitmask, options)
        assert bitmasks is None or len(bitmasks) == argc, f'Expected {argc} bitmasks, got {len(bitmasks)}'
        self.argc = argc
        self.bitmasks = bitmasks if bitmasks else [0xFF] * argc

    def get_command(self, option, *args):
        assert len(args) == self.argc, f'Expected {self.argc} arguments, got {len(args)}'
        return super().get_command(option) + [arg & self.bitmasks[i] for i, arg in enumerate(args)]

    def parse(self, data):
        assert len(data) >= self.argc + 1, f'Expected at least {self.argc + 1} arguments, got {len(data)}'
        assert data[0] & (~self.bitmask) == self.command, f'Expected command {self.command}, got {data[0]}'
        option = data[0] & self.bitmask
        if self.options is not None:
            assert option in self.options, f'Value {option} not in options {self.options}'
        args = []
        for i in range(self.argc):
            arg = data[i + 1] & self.bitmasks[i]
            args.append(arg)
        return option, args, data[1 + self.argc:]

class CommandWithCallable(CommandBase):
    def __init__(self, command, func, func_inverse=None):
        super().__init__(command)
        self.func = func
        self.func_inverse = func_inverse if func_inverse else lambda x: x

    def get_command(self, *args):
        return [self.command] + [self.func(arg) for arg in args]

    def parse(self, data):
        assert len(data) >= 2, f'Expected at least 2 bytes, got {len(data)}'
        assert data[0] == self.command, f'Expected command {self.command}, got {data[0]}'
        return self.func_inverse(data[1]), data[2:]

# SSD1306_I2C_ADDRESS = 0x3C    # 011110+SA0+RW - 0x3C or 0x3D
OPTION_I2C_ADDRESS_WRITE = 0x0
OPTION_I2C_ADDRESS_READ = 0x1
SSD1306_I2C_ADDRESS = CommandWithBitmask(0x3C, 0x1, [OPTION_I2C_ADDRESS_WRITE, OPTION_I2C_ADDRESS_READ])

# Fundamental commands
SSD1306_SETCONTRAST = CommandWithArgs(0x81, 1)

OPTION_DISPLAY_ALLON_RESUME = 0x0
OPTION_DISPLAY_ALLON_CLEAR = 0x1
OPTION_DISPLAY_NORMAL = 0x2
OPTION_DISPLAY_INVERT = 0x3
OPTION_DISPLAY_OFF = 0xA
OPTION_DISPLAY_ON = 0xB
SSD1306_DISPLAY = CommandWithBitmask(0xA4, 0xB, [
    OPTION_DISPLAY_ALLON_RESUME,
    OPTION_DISPLAY_ALLON_CLEAR,
    OPTION_DISPLAY_NORMAL,
    OPTION_DISPLAY_INVERT,
    OPTION_DISPLAY_OFF,
    OPTION_DISPLAY_ON
])

# Scrolling commands
OPTION_HORIZONTAL_SCROLL_RIGHT = 0x0
OPTION_HORIZONTAL_SCROLL_LEFT = 0x1
SSD1306_SCROLL_HORIZONTAL = CommandWithBitmaskAndArgs(0x26, 0x1, [
    OPTION_HORIZONTAL_SCROLL_RIGHT,
    OPTION_HORIZONTAL_SCROLL_LEFT
], 6, [0x00, 0x07, 0x07, 0x07, 0x00, 0xFF])

SSD1306_SCROLL_HORIZONTAL_VERTICAL = CommandWithBitmaskAndArgs(0x29, 0x1, [
    OPTION_HORIZONTAL_SCROLL_RIGHT,
    OPTION_HORIZONTAL_SCROLL_LEFT
], 5, [0x00, 0x07, 0x07, 0x07, 0x3F])

SSD1306_SCROLL_DEACTIVATE = Command(0x2E)
SSD1306_SCROLL_ACTIVATE = Command(0x2F)

SSD1306_SET_VERTICAL_SCROLL_AREA = CommandWithArgs(0xA3, 2, [0x3F, 0x7F])

# Address setting commands
OPTION_ADDRESSING_MODE_HORIZONTAL = 0x0
OPTION_ADDRESSING_MODE_VERTICAL = 0x1
OPTION_ADDRESSING_MODE_PAGE = 0x2
SSD1306_SET_MEMORY_ADDRESSING_MODE = CommandWithArgs(0x20, 1, [0x3])

SSD1306_PA_MODE_SET_PAGE_ADDR = CommandWithBitmask(0xB0, 0x07)
SSD1306_PA_MODE_SET_COLUMN_ADDR_LOW = CommandWithBitmask(0x00, 0x0F)
SSD1306_PA_MODE_SET_COLUMN_ADDR_HIGH = CommandWithBitmask(0x10, 0x0F)

SSD1306_HAVA_MODE_SET_PAGE_ADDR = CommandWithArgs(0x22, 2, [0x03, 0x03])
SSD1306_HAVA_MODE_SET_COLUMN_ADDR = CommandWithArgs(0x21, 2, [0x7F, 0x7F])

# Hardware configuration commands (panel resolution and layout related)
SSD1306_SET_START_LINE = CommandWithBitmask(0x40, 0x3F)

OPTION_SEGMENT_REMAP_SEG0_TO_0 = 0x0
OPTION_SEGMENT_REMAP_SEG0_TO_127 = 0x1
SSD1306_SEGMENT_REMAP = CommandWithBitmask(0xA0, 0x01, [
    OPTION_SEGMENT_REMAP_SEG0_TO_0,
    OPTION_SEGMENT_REMAP_SEG0_TO_127
])

SSD1306_SET_MULTIPLEX = CommandWithArgs(0xA8, 1, [0x3F]) # 0x3F for 128x64 or 64MUX, 0x1F for 128x32 or 32MUX

OPTION_COM_SCAN_DIR_NORMAL = 0x0
OPTION_COM_SCAN_DIR_REVERSE = 0x8
SSD1306_COM_OUTPUT_SCAN_DIR = CommandWithBitmask(0xC0, 0x08, [
    OPTION_COM_SCAN_DIR_NORMAL,
    OPTION_COM_SCAN_DIR_REVERSE
])

SSD1306_SET_DISPLAY_OFFSET = CommandWithArgs(0xD3, 1, [0x3F])
SSD1306_SET_COM_PINS = CommandWithCallable(0xDA, lambda x: ((x & 0x03) << 4) | 0x02)

# Timing and driving scheme commands
SSD1306_SET_DISPLAY_CLOCK_DIV_RATIO = CommandWithArgs(0xD5, 1)
SSD1306_SET_PRECHARGE_PERIOD = CommandWithArgs(0xD9, 1)
SSD1306_SET_VCOM_DESELECT_LEVEL = CommandWithCallable(0xDB, lambda x: ((x & 0x07) << 4) | 0x00)
SSD1306_NOP = Command(0xE3) # No operation

SSD1306_CHARGE_PUMP = CommandWithCallable(0x8D, lambda x: ((x & 0x01) << 2) | 0x10)
SSD1306_EXTERNAL_VCC = Command(0x1)     # Unsure
SSD1306_SWITCH_CAP_VCC = Command(0x2)   # Unsure

# List of all commands
SSD1306_COMMANDS = [
    SSD1306_I2C_ADDRESS,
    SSD1306_SETCONTRAST,
    SSD1306_DISPLAY,
    SSD1306_SCROLL_HORIZONTAL,
    SSD1306_SCROLL_HORIZONTAL_VERTICAL,
    SSD1306_SCROLL_DEACTIVATE,
    SSD1306_SCROLL_ACTIVATE,
    SSD1306_SET_VERTICAL_SCROLL_AREA,
    SSD1306_SET_MEMORY_ADDRESSING_MODE,
    SSD1306_PA_MODE_SET_PAGE_ADDR,
    SSD1306_PA_MODE_SET_COLUMN_ADDR_LOW,
    SSD1306_PA_MODE_SET_COLUMN_ADDR_HIGH,
    SSD1306_HAVA_MODE_SET_PAGE_ADDR,
    SSD1306_HAVA_MODE_SET_COLUMN_ADDR,
    SSD1306_SET_START_LINE,
    SSD1306_SEGMENT_REMAP,
    SSD1306_SET_MULTIPLEX,
    SSD1306_COM_OUTPUT_SCAN_DIR,
    SSD1306_SET_DISPLAY_OFFSET,
    SSD1306_SET_COM_PINS,
    SSD1306_SET_DISPLAY_CLOCK_DIV_RATIO,
    SSD1306_SET_PRECHARGE_PERIOD,
    SSD1306_SET_VCOM_DESELECT_LEVEL,
    SSD1306_NOP,
    SSD1306_CHARGE_PUMP,
    SSD1306_EXTERNAL_VCC,
    SSD1306_SWITCH_CAP_VCC
]

# Command names
SSD1306_COMMAND_NAMES = [
    'I2C_ADDRESS',
    'SETCONTRAST',
    'DISPLAY',
    'SCROLL_HORIZONTAL',
    'SCROLL_HORIZONTAL_VERTICAL',
    'SCROLL_DEACTIVATE',
    'SCROLL_ACTIVATE',
    'SET_VERTICAL_SCROLL_AREA',
    'SET_MEMORY_ADDRESSING_MODE',
    'PA_MODE_SET_PAGE_ADDR',
    'PA_MODE_SET_COLUMN_ADDR_LOW',
    'PA_MODE_SET_COLUMN_ADDR_HIGH',
    'HAVA_MODE_SET_PAGE_ADDR',
    'HAVA_MODE_SET_COLUMN_ADDR',
    'SET_START_LINE',
    'SEGMENT_REMAP',
    'SET_MULTIPLEX',
    'COM_OUTPUT_SCAN_DIR',
    'SET_DISPLAY_OFFSET',
    'SET_COM_PINS',
    'SET_DISPLAY_CLOCK_DIV_RATIO',
    'SET_PRECHARGE_PERIOD',
    'SET_VCOM_DESELECT_LEVEL',
    'NOP',
    'CHARGE_PUMP',
    'EXTERNAL_VCC',
    'SWITCH_CAP_VCC'
]