import fcntl
import sys
import termios
import struct


def clear_screen():
    sys.stdout.write("\033[2J")


def terminal_size():
    result = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, b"\x00" * 8)
    rows, cols = struct.unpack("HHHH", result)[:2]
    return cols, rows
