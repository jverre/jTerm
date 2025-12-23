import sys
from dataclasses import dataclass
from . import widget
from .. import logging

@dataclass
class Text(widget.Widget):
    content: str = ""

    def get_intrinsic_width(self) -> int:
        return len(self.content)
    
    def get_intrinsic_height(self) -> int:
        return self.content.count('\n') + 1

    def render_content(self):
        logging.log("Text widget:", self.rect)
        sys.stdout.write(f"\033[{self.rect.y + 1};{self.rect.x + 1}H{self.content}")
        sys.stdout.flush()
