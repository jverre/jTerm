import sys
import textwrap
from dataclasses import dataclass
from . import widget
from .. import logging
from ..layout import Dimensions, SizeMode, Rect

@dataclass
class Text(widget.Widget):
    content: str = ""

    def _calculate_dimensions(self, available_width: int | None, available_height: int | None) -> Dimensions:
        """Measures the size of the Text component
        
        Args:
            available_width: Total width available including borders (None for no constraint)
            available_height: Total height available including borders (None for no constraint)
        
        Returns:
            Dimensions: Total dimensions including borders
        """
        lines = self.content.split('\n')

        # Determine available width:
        if available_width is None:
            available_content_width = None
        else:
            available_content_width = available_width - self.border.horizontal_space
        
        # Compute height
        if self.height.mode == SizeMode.FILL:
            if available_height is None: # Fallback to AUTO mode
                height = self.border.vertical_space
                for line in lines:
                    if available_content_width is not None:
                        height += len(line) // available_content_width + 1
                    else:
                        height += 1
            else:
                height = available_height
        elif self.height.mode == SizeMode.FIXED:
            height = self.height.value
        elif self.height.mode == SizeMode.AUTO:
                height = self.border.vertical_space
                for line in lines:
                    if available_content_width is not None:
                        height += len(line) // available_content_width + 1
                    else:
                        height += 1
        else:
            raise ValueError(f"SizeMode {self.height.mode} not supported")

        # Compute width
        if self.width.mode == SizeMode.FILL:
            if available_width is None:
                width = max((len(line) for line in lines)) + self.border.horizontal_space
            else:
                width = available_width
        elif self.width.mode == SizeMode.FIXED:
            width = self.width.value
        elif self.width.mode == SizeMode.AUTO:
            width = 0

            for line in lines:
                if available_width is not None:
                    line_width = min(len(line), available_content_width)
                else:
                    line_width = len(line)
                width = max(line_width, width)
            width += self.border.horizontal_space
        else:
            raise ValueError(f"SizeMode {self.width.mode} not supported")

        return Dimensions(width=width, height=height)

    def layout(self, rect: Rect):
        self.rect = rect

    def render_content(self):
        r = self.content_rect
        lines = self.content.split('\n')

        if r.height <= 0:
            return
        
        # Expand all lines with wrapping first to get the full list of display lines
        display_lines = []
        for line in lines:
            formatted_line = textwrap.fill(line, width=r.width)
            display_lines.extend(formatted_line.split("\n"))
        
        # Apply scroll_offset and _clip_top: skip lines that are scrolled or clipped by parent
        start_line = self.scroll_offset + self._clip_top
        visible_lines = display_lines[start_line:start_line + r.height]
        
        # Render only the visible lines
        for current_row, line_content in enumerate(visible_lines):
            if current_row >= r.height:
                break
            
            sys.stdout.write(
                f"\033[{r.y + 1 + current_row};{r.x + 1}H{line_content}"
            )
        
        sys.stdout.flush()
