from dataclasses import dataclass


@dataclass
class Size:
    width: int = 0
    height: int = 0


@dataclass
class Rect:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    @property
    def size(self) -> Size:
        return Size(self.width, self.height)

    def inset(
        self, top: int = 0, right: int = 0, bottom: int = 0, left: int = 0
    ) -> "Rect":
        return Rect(
            x=self.x + left,
            y=self.y + top,
            width=max(0, self.width - left - right),
            height=max(0, self.height - top - bottom),
        )
