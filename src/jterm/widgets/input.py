from dataclasses import dataclass
import sys
from . import widget
from .. import logging, messages
import textwrap


@dataclass
class Submitted(messages.Message):
    value: str = ""


@dataclass
class Input(widget.Widget):
    content: str = ""
    Submitted = Submitted

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

    def handle_key(self, key: str):
        if super().handle_key(key):
            return True

        logging.log("Key: ", ord(key))
        if ord(key) == 13:  # return
            self.post_message(Input.Submitted(sender=self, value=self.content))
            self.content = ""
        if key.isprintable():
            self.content += key
            return True
        elif ord(key) == 127:  # backspace
            self.content = self.content[:-1]
            return True

        return False

    def render_content(self):
        r = self.content_rect
        formatted_content = textwrap.fill(self.content, width=r.width)

        for i, line in enumerate(formatted_content.split("\n")):
            sys.stdout.write(f"\033[{r.y + 1 + i};{r.x + 1}H{line}")
        sys.stdout.flush()
