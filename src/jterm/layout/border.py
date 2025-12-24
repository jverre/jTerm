from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class BorderStyle(Enum):
    NONE = auto()
    SOLID = auto()  # ─ │ ┌ ┐ └ ┘
    HEAVY = auto()  # ━ ┃ ┏ ┓ ┗ ┛
    DOUBLE = auto()  # ═ ║ ╔ ╗ ╚ ╝
    ROUNDED = auto()  # ─ │ ╭ ╮ ╰ ╯
    DASHED = auto()  # ┄ ┆ ┌ ┐ └ ┘


# Box-drawing character sets: (horizontal, vertical, top_left, top_right, bottom_left, bottom_right)
BORDER_CHARS = {
    BorderStyle.NONE: (" ", " ", " ", " ", " ", " "),
    BorderStyle.SOLID: ("─", "│", "┌", "┐", "└", "┘"),
    BorderStyle.HEAVY: ("━", "┃", "┏", "┓", "┗", "┛"),
    BorderStyle.DOUBLE: ("═", "║", "╔", "╗", "╚", "╝"),
    BorderStyle.ROUNDED: ("─", "│", "╭", "╮", "╰", "╯"),
    BorderStyle.DASHED: ("┄", "┆", "┌", "┐", "└", "┘"),
}


@dataclass
class BorderSide:
    """Represents one side of a border (like CSS border-top, etc.)"""

    style: BorderStyle = BorderStyle.NONE
    color: str = ""

    @property
    def width(self) -> int:
        """Border width is 1 if style is set, 0 otherwise (terminal limitation)"""
        return 0 if self.style == BorderStyle.NONE else 1


@dataclass
class Border:
    """CSS-like border with per-side control."""

    top: BorderSide = field(default_factory=BorderSide)
    right: BorderSide = field(default_factory=BorderSide)
    bottom: BorderSide = field(default_factory=BorderSide)
    left: BorderSide = field(default_factory=BorderSide)

    @classmethod
    def all(cls, style: BorderStyle = BorderStyle.SOLID, color: str = "") -> "Border":
        """Create a uniform border on all sides (like CSS `border: 1px solid`)"""
        side = BorderSide(style=style, color=color)
        return cls(top=side, right=side, bottom=side, left=side)

    @classmethod
    def none(cls) -> "Border":
        """No border"""
        return cls()

    @property
    def top_width(self) -> int:
        return self.top.width

    @property
    def right_width(self) -> int:
        return self.right.width

    @property
    def bottom_width(self) -> int:
        return self.bottom.width

    @property
    def left_width(self) -> int:
        return self.left.width

    @property
    def horizontal_space(self) -> int:
        """Total horizontal space taken by borders"""
        return self.left_width + self.right_width

    @property
    def vertical_space(self) -> int:
        """Total vertical space taken by borders"""
        return self.top_width + self.bottom_width
