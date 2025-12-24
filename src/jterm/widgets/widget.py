from dataclasses import dataclass, field
from enum import Enum, auto
from .. import core, logging, layout
import sys
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .. import messages, app


@dataclass
class Widget:
    id: str

    _app: "app.App | None" = field(default=None, repr=False)

    width: "layout.Size" = field(default_factory=layout.Size.fill)
    height: "layout.Size" = field(default_factory=layout.Size.auto)
    position: "layout.Position" = field(default_factory=layout.Position)

    children: List["Widget"] = field(default_factory=list)
    rect: "layout.Rect" = field(default_factory=layout.Rect)

    border: "layout.Border" = field(default_factory=layout.Border.none)
    focused: bool = False

    @property
    def content_rect(self) -> "layout.Rect":
        """Returns the inner rect available for content (after border insets)."""
        return layout.Rect(
            x=self.rect.x + self.border.left_width,
            y=self.rect.y + self.border.top_width,
            width=max(0, self.rect.width - self.border.horizontal_space),
            height=max(0, self.rect.height - self.border.vertical_space),
        )

    @property
    def focused_child(self) -> Optional["Widget"]:
        """Get the currently focused child, if any."""
        for child in self.children:
            if child.focused:
                return child
        return None

    def layout(self, available: Rect):
        self.rect = layout.Rect(
            x=available.x,
            y=available.y,
            width=self._resolve_size(self.width, available.width),
            height=self._resolve_size(self.height, available.height),
        )

    def _resolve_size(self, size: Size, available: int) -> int:
        if size.mode == layout.SizeMode.FIXED:
            return min(size.value, available)
        else:
            return available

    def get_intrinsic_width(self) -> int:
        """Override in subclasses that have content-based sizing."""
        return 0

    def get_intrinsic_height(self) -> int:
        """Override in subclasses that have content-based sizing."""
        return 0

    def get_computed_width(self, available: int) -> int:
        """Returns resolved width given available space."""
        match self.width.mode:
            case layout.SizeMode.FIXED:
                return min(self.width.value, available)
            case layout.SizeMode.AUTO:
                return min(self.get_intrinsic_width(), available)
            case SizeMode.FILL:
                return available  # handled specially by container

    def get_computed_height(self, available: int) -> int:
        """Returns resolved height given available space."""
        match self.height.mode:
            case layout.SizeMode.FIXED:
                return min(self.height.value, available)
            case layout.SizeMode.PERCENT:
                return int(available * self.height.value / 100)
            case layout.SizeMode.AUTO:
                return min(self.get_intrinsic_height(), available)
            case layout.SizeMode.FILL:
                return available

    def handle_key(self, key: str) -> bool:
        if self.focused_child:
            if self.focused_child.handle_key(key):
                return True

        return False

    def _render_border(self):
        """Draw the border around the widget rect."""
        if self.rect.width < 2 or self.rect.height < 2:
            return  # Not enough space for a border

        # Determine which style to use (prefer top style for corners)
        primary_style = self.border.top.style
        if primary_style == layout.BorderStyle.NONE:
            primary_style = self.border.left.style
        if primary_style == layout.BorderStyle.NONE:
            return  # No visible border

        h, v, tl, tr, bl, br = layout.BORDER_CHARS[primary_style]
        color = self.border.top.color
        reset = "\033[0m" if color else ""

        x, y = self.rect.x, self.rect.y
        w, h_size = self.rect.width, self.rect.height

        # Top border
        if self.border.top.style != layout.BorderStyle.NONE:
            h_char, _, tl, tr, _, _ = layout.BORDER_CHARS[self.border.top.style]
            top_line = tl + (h_char * (w - 2)) + tr
            sys.stdout.write(f"\033[{y + 1};{x + 1}H{color}{top_line}{reset}")

        # Left and right borders
        for row in range(1, h_size - 1):
            # Left
            if self.border.left.style != layout.BorderStyle.NONE:
                _, v_char, _, _, _, _ = layout.BORDER_CHARS[self.border.left.style]
                sys.stdout.write(
                    f"\033[{y + row + 1};{x + 1}H{self.border.left.color}{v_char}{reset}"
                )
            # Right
            if self.border.right.style != layout.BorderStyle.NONE:
                _, v_char, _, _, _, _ = layout.BORDER_CHARS[self.border.right.style]
                sys.stdout.write(
                    f"\033[{y + row + 1};{x + w}H{self.border.right.color}{v_char}{reset}"
                )

        # Bottom border
        if self.border.bottom.style != layout.BorderStyle.NONE:
            h_char, _, _, _, bl, br = layout.BORDER_CHARS[self.border.bottom.style]
            bottom_line = bl + (h_char * (w - 2)) + br
            sys.stdout.write(
                f"\033[{y + h_size};{x + 1}H{self.border.bottom.color}{bottom_line}{reset}"
            )

        sys.stdout.flush()

    def render_content(self):
        pass

    def render(self):
        """Template method: renders border, then delegates to render_content()."""
        self._render_border()
        self.render_content()

    def post_message(self, message: "messages.Message") -> None:
        if self._app:
            self._app.post_message(message)
        else:
            logging.log(f"Error: failed to post {message}")
