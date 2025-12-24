import sys
from dataclasses import dataclass
from . import widget
from .. import logging


@dataclass
class Text(widget.Widget):
    content: str = ""

    def get_intrinsic_height(self, available_width: int = 0) -> int:
        try:
            lines = self.content.split("\n")
            logging.log("nb_lines", len(lines))
            nb_lines = 0
            for line in lines:
                nb_lines += (len(line) // available_width) + 1
        except Exception as e:
            logging.log("Error: ", e)
            nb_lines = 1

        return nb_lines + self.border.vertical_space

    def get_intrinsic_width(self) -> int:
        max_line_width = 0

        lines = self.content.split("\n")
        for line in lines:
            line_width = min(len(line), self.content_rect.width)
            max_line_width = max(max_line_wdith, line_width)

        return max_line_width + self.border.horizontal_space

    def render_content(self):
        logging.log("Text: ", self.content_rect)
        for i, line in enumerate(self.content.split("\n")):
            if i == 0:
                sys.stdout.write(
                    f"\033[{self.content_rect.y + 1};{self.content_rect.x + 1}H> {line}"
                )
            else:
                sys.stdout.write(
                    f"\033[{self.content_rect.y + 1 + i};{self.content_rect.x + 1}H  {line}"
                )
        sys.stdout.flush()
