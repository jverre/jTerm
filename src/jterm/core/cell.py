from dataclasses import dataclass


@dataclass
class Cell:
    char: str = ""
    fg: str = ""
    bg: str = ""

    def __eq__(self, other):
        return self.char == other.char and self.fg == other.fg and self.bg == other.bg
