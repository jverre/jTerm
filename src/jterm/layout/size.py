
from dataclasses import dataclass, field
from enum import Enum, auto

class SizeMode(Enum):
    FIXED = auto() # Exact size - flex: 0 0 100px
    AUTO = auto() # Shrink to content - flex: 0 0 auto
    FILL = auto() # Expand to fill - flex: 1 1 0

@dataclass
class Size:
    value: int = 0
    mode: SizeMode = field(default=SizeMode.AUTO)

    @classmethod
    def auto(cls, value: int = 0) -> "Size":
        return cls(value, SizeMode.AUTO)

    @classmethod
    def fixed(cls, value: int) -> "Size":
        return cls(value, SizeMode.FIXED)

    @classmethod
    def fill(cls) -> "Size":
        return cls(0, SizeMode.FILL)
