from dataclasses import dataclass
from . import widget
from .. import logging, layout
from ..layout import DirectionMode, Rect, SizeMode


@dataclass
class Container(widget.Widget):
    """Note: This will map to a "div" in web UI"""

    direction: DirectionMode = DirectionMode.VERTICAL

    def layout(self, available: Rect):
        super().layout(available)

        if not self.children:
            return

        fixed_space = 0
        fill_count = 0

        for child in self.children:
            size = (
                child.height
                if self.direction == DirectionMode.VERTICAL
                else child.width
            )

            if size.mode == SizeMode.FIXED:
                fixed_space += size.value
            elif size.mode == SizeMode.AUTO:
                if self.direction == DirectionMode.VERTICAL:
                    fixed_space += child.get_intrinsic_height(available.width)
                else:
                    fixed_space += child.get_intrinsic_width()
            elif size.mode == SizeMode.FILL:
                fill_count += 1
            else:
                raise ValueError(f"Unknown size mode: {size.mode}")

        total_space = (
            self.rect.height
            if self.direction == DirectionMode.VERTICAL
            else self.rect.width
        )
        remaining = max(0, total_space - fixed_space)
        fill_size = remaining // max(1, fill_count)

        offset = 0
        for child in self.children:
            child_size = self._get_child_size(child, fill_size)

            if self.direction == DirectionMode.VERTICAL:
                child_rect = Rect(
                    x=self.rect.x,
                    y=self.rect.y + offset,
                    width=self.rect.width,
                    height=child_size,
                )
            else:
                child_rect = Rect(
                    x=self.rect.x + offset,
                    y=self.rect.y,
                    width=child_size,
                    height=self.rect.height,
                )

            child.layout(child_rect)
            offset += child_size

    def _get_child_size(self, child: widget.Widget, fill_size: int) -> int:
        size = child.height if self.direction == DirectionMode.VERTICAL else child.width

        # TODO: Check this
        if size.mode == SizeMode.FIXED:
            return size.value
        elif size.mode == SizeMode.AUTO:
            if self.direction == DirectionMode.VERTICAL:
                return child.get_intrinsic_height(100)
            else:
                return child.get_intrinsic_width()
        elif size.mode == SizeMode.FILL:
            return fill_size
        else:
            raise ValueError(f"Unknown size mode: {size.mode}")

    def render(self):
        logging.log("Container: ", self.content_rect)

        for child in self.children:
            child.render()
