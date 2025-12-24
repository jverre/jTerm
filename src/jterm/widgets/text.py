import sys
from dataclasses import dataclass
from . import widget
from .. import logging


@dataclass
class Text(widget.Widget):
    content: str = ""

    def get_intrinsic_height(self) -> int:
        try:
            nb_lines = (len(self.content) // self.content_rect.width) + 1
        except:
            nb_lines = 1
        return nb_lines + self.border.vertical_space

    def get_intrinsic_width(self) -> int:
        if len(self.content) >= self.content_rect.width:
            return self.content_rect.width + self.border.horizontal_space
        else:
            return len(self.content) + self.border.horizontal_space

    def render_content(self):
        sys.stdout.write(f"\033[{self.rect.y + 1};{self.rect.x + 1}H{self.content}")
        sys.stdout.flush()
