from enum import Enum, auto


class Overflow(Enum):
    VISIBLE = auto()  # Content can overflow (no clipping)
    HIDDEN = auto()  # Content is clipped, no scrollbar
    SCROLL = auto()  # Always show scrollbar
    AUTO = auto()  # Scrollbar only when content overflows
