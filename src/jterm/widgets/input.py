from dataclasses import dataclass
import subprocess
import sys
from . import text
from .. import logging, messages, ascii
import textwrap


@dataclass
class Submitted(messages.Message):
    value: str = ""


@dataclass
class Input(text.Text):
    content: str = ""
    Submitted = Submitted

    def handle_key(self, key: ascii.Key):
        if super().handle_key(key):
            return True

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
