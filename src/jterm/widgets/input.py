from dataclasses import dataclass
import sys
from . import widget
from .. import logging

@dataclass
class Input(widget.Widget):
    content: str = ""

    def get_intrinsic_height(self) -> int:
        """Single-line input: 1 line + border space"""
        return 1 + self.border.vertical_space

    def get_intrinsic_width(self) -> int:
        return len(self.content) + self.border.horizontal_space

    def handle_key(self, key: str):
        if super().handle_key(key):
            return True
        logging.log("Key: ", ord(key))
        if key.isprintable():
            self.content += key
            return True
        elif ord(key) == 127:  # backspace
            self.content = self.content[:-1]
            return True
        
        return False
    
    def render_content(self):
        logging.log("Input widget", self.rect)
        r = self.content_rect
        sys.stdout.write(f"\033[{r.y + 1};{r.x + 1}H{self.content}")
        sys.stdout.flush()
