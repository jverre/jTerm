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

        logging.log(f"Measure - Text ({self.id}) - width:{width}, height:{height}")
        return Dimensions(width=width, height=height)

    def layout(self, rect: Rect):
        logging.log(f"Layout - Text ({self.id}): ", self.content_rect)
        self.rect = rect

    def render_content(self):
        logging.log(f"Render - Text ({self.id}): ", self.content_rect)
        r = self.content_rect
        lines = self.content.split('\n')

        if r.height <= 0:
            return
        
        current_row = 0

        for line in lines:
            if current_row >= r.height:
                break
            
            formatted_line = textwrap.fill(line, width=r.width)
            for line_content in formatted_line.split("\n"):
                if current_row >= r.height:
                    break
            
                sys.stdout.write(
                    f"\033[{r.y + 1 + current_row};{r.x + 1}H{line_content}"
                )
                current_row += 1

        sys.stdout.flush()
