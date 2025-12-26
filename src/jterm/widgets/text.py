import sys
import textwrap
from dataclasses import dataclass
from . import widget
from .. import logging
from ..layout import Size, SizeMode, Rect


@dataclass
class Text(widget.Widget):
    content: str = ""

    def _calculate_dimensions(
        self, available_width: int | None, available_height: int | None
    ) -> Size:
        """Returns CONTENT dimensions only (no borders).

        Args:
            available_width: Width available for CONTENT (borders already subtracted)
            available_height: Height available for CONTENT (borders already subtracted)
        """
        lines = self.content.split("\n")

        # Compute CONTENT height (no borders!)
        if self.height.mode == SizeMode.FILL:
            if available_height is None:
                # Fallback to AUTO
                content_height = 0
                for line in lines:
                    if available_width is not None and available_width > 0:
                        content_height += (len(line) // available_width) + 1
                    else:
                        content_height += 1
            else:
                content_height = available_height
        elif self.height.mode == SizeMode.FIXED:
            # FIXED includes borders, so subtract them for content
            content_height = max(0, self.height.value - self.border.vertical_space)
        elif self.height.mode == SizeMode.AUTO:
            content_height = 0
            for line in lines:
                if available_width is not None and available_width > 0:
                    content_height += (len(line) // available_width) + 1
                else:
                    content_height += 1
        else:
            raise ValueError(f"SizeMode {self.height.mode} not supported")

        # Compute CONTENT width (no borders!)
        if self.width.mode == SizeMode.FILL:
            if available_width is None:
                content_width = max((len(line) for line in lines), default=0)
            else:
                content_width = available_width
        elif self.width.mode == SizeMode.FIXED:
            content_width = max(0, self.width.value - self.border.horizontal_space)
        elif self.width.mode == SizeMode.AUTO:
            content_width = 0
            for line in lines:
                if available_width is not None:
                    line_width = min(len(line), available_width)
                else:
                    line_width = len(line)
                content_width = max(line_width, content_width)
        else:
            raise ValueError(f"SizeMode {self.width.mode} not supported")

        return Size(width=content_width, height=content_height)

    def layout(self, rect: Rect):
        self.rect = rect

    def render_content(self):
        r = self.content_rect
        if r.height <= 0:
            return

        lines = self.content.split("\n")
        display_lines = []
        for line in lines:
            formatted = textwrap.fill(line, width=r.width) if r.width > 0 else line
            display_lines.extend(formatted.split("\n"))

        # Skip lines clipped by parent scroll
        clip_top = getattr(self, "_render_clip_top", 0)
        start = self.scroll_offset + clip_top
        visible = display_lines[start : start + r.height]

        for row, line in enumerate(visible):
            if row >= r.height:
                break
            sys.stdout.write(f"\033[{r.y + 1 + row};{r.x + 1}H{line}")

        sys.stdout.flush()
