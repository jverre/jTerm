from dataclasses import dataclass
import subprocess
import sys
from . import widget
from .. import logging, messages, ascii
import textwrap


@dataclass
class Submitted(messages.Message):
    value: str = ""


@dataclass
class Input(widget.Widget):
    content: str = ""
    Submitted = Submitted

    def get_intrinsic_height(self, available_width: int) -> int:
        try:
            lines = self.content.split("\n")
            nb_lines = 0
            for line in lines:
                nb_lines += (len(line) // available_width) + 1
        except:
            nb_lines = 1
        return nb_lines + self.border.vertical_space

    def get_intrinsic_width(self) -> int:
        max_line_width = 0

        lines = self.content.split("\n")
        for line in lines:
            line_width = min(len(line), self.content_rect.width)
            max_line_width = max(max_line_wdith, line_width)

        return max_line_width + self.border.horizontal_space

    def handle_key(self, key: ascii.Key):
        if super().handle_key(key):
            return True

        logging.log("Key: ", key)
        if key.modifiers == {"shift"} and key.key == "enter":
            self.content += "\n"
            return True
        elif key.key == "enter":
            self.post_message(Input.Submitted(sender=self, value=self.content))
            self.content = ""
            return True
        elif key.key == "backspace":
            self.content = self.content[:-1]
            return True
        elif key.is_printable:
            self.content += key.key
            return True

        return False

    def render_content(self):
        logging.log("Input", self.content_rect)
        r = self.content_rect

        lines = self.content.split("\n")

        current_row = 0
        for line in lines:
            formatted_line = textwrap.fill(line, width=r.width)

            for line_content in formatted_line.split("\n"):
                sys.stdout.write(
                    f"\033[{r.y + 1 + current_row};{r.x + 1}H{line_content}"
                )
                current_row += 1
        sys.stdout.flush()
