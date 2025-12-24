from typing import List
from . import Cell


class Screen:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.buffer: List[List[Cell]] = self._create_buffer()

        self.cursor_row = 0
        self.cursor_col = 0
        self.cursor_visible = False

    def _create_buffer(self) -> List[List[Cell]]:
        return [[Cell() for _ in range(self.width)] for _ in range(self.height)]

    def clear(self):
        self.buffer = self._create_buffer()

    def write_char(self, char: str, fg: str = "", bg: str = ""):
        self.buffer[self.cursor_row][self.cursor_col] = Cell(char, fg, bg)
        self.cursor_col += 1
        if self.cursor_col >= self.width:
            self.cursor_col = 0
            self.cursor_row += 1

    def write_char_at(self, row: int, col: int, char: str, fg: str = "", bg: str = ""):
        self.buffer[row][col] = Cell(char, fg, bg)

    def render_full(self) -> str:
        output = ["\033[H"]
        for row in self.buffer:
            output.append("".join(cell.char for cell in row))
            output.append("\r\n")

        output.append(f"\033[{self.cursor_row + 1};{self.cursor_col + 1}H")
        output.append("\033[?25h")

        self._prev_buffer = [row[:] for row in self.buffer]

        return "".join(output)
