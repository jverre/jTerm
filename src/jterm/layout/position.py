from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional


class PositionMode(Enum):
    FLOW = auto()  # In layout, container decides where I go
    FIXED = auto()  # Anchored to screen, stays at this screen position


@dataclass
class Position:
    mode: PositionMode = PositionMode.FLOW
    top: Optional[int] = None
    right: Optional[int] = None
    bottom: Optional[int] = None
    left: Optional[int] = None
