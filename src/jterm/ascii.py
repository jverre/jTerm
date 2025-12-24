from dataclasses import dataclass, field
from typing import Literal, Optional
import select
from . import logging
import sys
import re
import os
import fcntl

CSI_U_RE = re.compile(r"^\[(\d+);(\d+)u$")  # after ESC is consumed


@dataclass
class Key:
    key: str

    is_printable: bool = True

    shift: bool = False
    alt: bool = False
    ctrl: bool = False

    @property
    def modifiers(self) -> set[str]:
        modifiers: set[str] = set()
        if self.shift:
            modifiers.add("shift")
        if self.ctrl:
            modifiers.add("ctrl")
        if self.alt:
            modifiers.add("alt")
        return modifiers


def read_key() -> Optional[Key]:
    ch = sys.stdin.read(1)

    # /x1b is ESC, need to check for escape sequence
    if ch == "\x1b":
        return _read_escape_sequence()

    # \x7f is backspace
    if ch == "\x7f":
        return Key(key="backspace")

    # Handle other control characters
    if ord(ch) < 32:
        if ch == "\n" or ch == "\r":
            return Key(key="enter")
        elif ch == "\t":
            return Key(key="tab")
        elif ch == "\x7f":  # DEL/Backspace
            return Key(key="backspace")
        else:
            # Other control chars like Ctrl+C, Ctrl+D, etc.
            ctrl_char = chr(ord(ch) + 64).lower() if ord(ch) < 27 else ch
            return Key(key=ctrl_char, modifier="ctrl")

    # Regular printable character
    return Key(key=ch)


def _read_escape_sequence() -> Optional[Key]:
    sequence = ""

    while True:
        try:
            key = sys.stdin.read(1)
            if not key:
                break
            sequence += key

            if key in ("~", "u", "A", "B", "C", "D", "H", "F", "P", "Q", "R", "S"):
                break

            if len(sequence) > 20:
                logging.log("Safety limit reached")
                break
        except (IOError, BlockingIOError):
            break

    return _parse_sequence(sequence)


def _parse_sequence(sequence: str) -> Optional[Key]:
    if not sequence:
        return Key(key="escape")

    m = CSI_U_RE.match(sequence)
    if m:
        codepoint = int(m.group(1))
        mods = int(m.group(2))

        # kitty modifier encoding for CSI-u:
        # 1 none, 2 shift, 3 alt, 4 shift+alt, 5 ctrl, 6 shift+ctrl, 7 alt+ctrl, 8 shift+alt+ctrl
        modifiers = {}
        if mods in (5, 6, 7, 8):  # has ctrl
            modifiers["ctrl"] = True
        if mods in (3, 4, 7, 8):  # has alt
            modifiers["alt"] = True
        if mods in (2, 4, 6, 8):  # has shift
            modifiers["shift"] = True

        key_map = {13: "enter", 9: "tab", 27: "escape", 32: "space", 127: "backspace"}
        key_name = key_map.get(
            codepoint, chr(codepoint) if 32 <= codepoint < 127 else f"{codepoint}"
        )

        return Key(key=key_name, is_printable=False, **modifiers)

    # Standard CSI sequences (no modifiers)
    simple_keys = {
        "[A": "up",
        "[B": "down",
        "[C": "right",
        "[D": "left",
        "[H": "home",
        "[F": "end",
        "[3~": "backspace",
        "OP": "f1",
        "OQ": "f2",
        "OR": "f3",
        "OS": "f4",
        "[15~": "f5",
        "[17~": "f6",
        "[18~": "f7",
        "[19~": "f8",
        "[20~": "f9",
        "[21~": "f10",
        "[23~": "f11",
        "[24~": "f12",
    }

    if sequence in simple_keys:
        return Key(key=simple_keys[sequence], is_printable=False)

    if len(sequence) == 1:
        return Key(key=sequence)

    # Fallback for unknown sequences
    logging.log(f"Unknown sequence: {sequence}")
    return Key(key=f"{sequence}")
