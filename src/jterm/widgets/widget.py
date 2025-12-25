from dataclasses import dataclass, field
from enum import Enum, auto
from .. import core, logging
from ..layout import Size, Position, Rect, Border, BorderStyle, BORDER_CHARS, SizeMode, Dimensions
import sys
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .. import messages, app


@dataclass
class Widget:
    id: str

    _app: "app.App | None" = field(default=None, repr=False)

    width: "Size" = field(default_factory=Size.fill)
    height: "Size" = field(default_factory=Size.auto)
    position: "Position" = field(default_factory=Position)

    children: List["Widget"] = field(default_factory=list)

    dimensions: Dimensions = field(default_factory=Dimensions)
    rect: "Rect" = field(default_factory=Rect)

    border: "Border" = field(default_factory=Border.none)
    focused: bool = False

    scroll_offset: int = 0
    scrollable: bool = True

    @property
    def needs_scrollbar(self) -> bool:
        return(
            self.scrollable
            and self.dimensions.height > self.rect.height
            and self.rect.height > 0
        )
    
    @property
    def max_scroll_offset(self) -> int:
        """Maximum scroll offset."""
        if not self.needs_scrollbar:
            return 0
        return max(0, self.dimensions.height - self.content_rect.height)

    @property
    def scrollbar_height(self) -> int:
        """Height of the scrollbar thumb."""
        if not self.needs_scrollbar:
            return 0
        content_height = self.content_rect.height
        # Calculate thumb size proportional to visible content
        thumb_height = max(1, int(content_height * content_height / self.dimensions.height))
        return min(thumb_height, content_height)

    @property
    def scrollbar_position(self) -> int:
        """Y position of scrollbar thumb (relative to content_rect top)."""
        if not self.needs_scrollbar or self.max_scroll_offset == 0:
            return 0
        content_height = self.content_rect.height
        scrollable_range = content_height - self.scrollbar_height
        return int(self.scroll_offset / self.max_scroll_offset * scrollable_range)
    
    def scroll_up(self, lines: int = 1) -> bool:
        """Scroll content up (decrease offset). Returns True if scrolled."""
        if self.scroll_offset > 0:
            self.scroll_offset = max(0, self.scroll_offset - lines)
            return True
        return False

    def scroll_down(self, lines: int = 1) -> bool:
        """Scroll content down (increase offset). Returns True if scrolled."""
        if self.scroll_offset < self.max_scroll_offset:
            self.scroll_offset = min(self.max_scroll_offset, self.scroll_offset + lines)
            return True
        return False

    def scroll_to_top(self):
        """Scroll to the top."""
        self.scroll_offset = 0

    def scroll_to_bottom(self):
        """Scroll to the bottom."""
        self.scroll_offset = self.max_scroll_offset
        
    @property
    def content_rect(self) -> "Rect":
        """Returns the inner rect available for content (after border insets)."""
        return Rect(
            x=self.rect.x + self.border.left_width,
            y=self.rect.y + self.border.top_width,
            width=max(0, self.rect.width - self.border.horizontal_space),
            height=max(0, self.rect.height - self.border.vertical_space),
        )

    def _calculate_dimensions(self, available_width: int, available_height: int) -> Dimensions:
        raise NotImplementedError

    def measure(self, available_width: int, available_height: int) -> Dimensions:
        """This measure the size of the content based on the content"""
        dims = self._calculate_dimensions(available_width, available_height)
        
        self.dimensions = dims
        
        return dims

    def layout(self, rect: Rect):
        """This defines what should be displayed based on the available size"""
        raise NotImplementedError

    def _render_border(self):
        """Draw the border around the widget rect."""
        if self.rect.width < 2 or self.rect.height < 2:
            return  # Not enough space for a border

        # Determine which style to use (prefer top style for corners)
        primary_style = self.border.top.style
        if primary_style == BorderStyle.NONE:
            primary_style = self.border.left.style
        if primary_style == BorderStyle.NONE:
            return  # No visible border

        h, v, tl, tr, bl, br = BORDER_CHARS[primary_style]
        color = self.border.top.color
        reset = "\033[0m" if color else ""

        x, y = self.rect.x, self.rect.y
        w, h_size = self.rect.width, self.rect.height

        # Top border
        if self.border.top.style != BorderStyle.NONE:
            h_char, _, tl, tr, _, _ = BORDER_CHARS[self.border.top.style]
            top_line = tl + (h_char * (w - 2)) + tr
            sys.stdout.write(f"\033[{y + 1};{x + 1}H{color}{top_line}{reset}")

        # Left and right borders
        for row in range(1, h_size - 1):
            # Left
            if self.border.left.style != BorderStyle.NONE:
                _, v_char, _, _, _, _ = BORDER_CHARS[self.border.left.style]
                sys.stdout.write(
                    f"\033[{y + row + 1};{x + 1}H{self.border.left.color}{v_char}{reset}"
                )
            # Right
            if self.border.right.style != BorderStyle.NONE:
                _, v_char, _, _, _, _ = BORDER_CHARS[self.border.right.style]
                sys.stdout.write(
                    f"\033[{y + row + 1};{x + w}H{self.border.right.color}{v_char}{reset}"
                )

        # Bottom border
        if self.border.bottom.style != BorderStyle.NONE:
            h_char, _, _, _, bl, br = BORDER_CHARS[self.border.bottom.style]
            bottom_line = bl + (h_char * (w - 2)) + br
            sys.stdout.write(
                f"\033[{y + h_size};{x + 1}H{self.border.bottom.color}{bottom_line}{reset}"
            )

        sys.stdout.flush()

    def render_content(self):
        pass

    def _render_scrollbar(self):
        """Draw the scrollbar on the right edge of the content area."""
        if not self.needs_scrollbar:
            return
        
        r = self.content_rect
        if r.width < 1 or r.height < 1:
            return
        
        # Scrollbar appears in the rightmost column of content area
        scrollbar_x = r.x + r.width - 1
        
        # Characters for scrollbar
        track_char = "│"  # or "║" or "┃"
        thumb_char = "█"  # or "▓" or "■"
        
        # Color (you can make this configurable)
        track_color = "\033[90m"  # Dark gray
        thumb_color = "\033[37m"  # White
        reset = "\033[0m"
        
        thumb_start = self.scrollbar_position
        thumb_end = thumb_start + self.scrollbar_height
        
        # Render scrollbar track and thumb
        for i in range(r.height):
            y = r.y + i
            if thumb_start <= i < thumb_end:
                # Render thumb
                sys.stdout.write(f"\033[{y + 1};{scrollbar_x + 1}H{thumb_color}{thumb_char}{reset}")
            else:
                # Render track
                sys.stdout.write(f"\033[{y + 1};{scrollbar_x + 1}H{track_color}{track_char}{reset}")
        
        sys.stdout.flush()
        
    def render(self):
        """Template method: renders border, then delegates to render_content()."""
        self._render_border()
        self.render_content()
        self._render_scrollbar()

    @property
    def focused_child(self) -> Optional["Widget"]:
        """Get the currently focused child, if any."""
        for child in self.children:
            if child.focused:
                return child
        return None
    
    def handle_key(self, key: str) -> bool:
        if self.needs_scrollbar:
            if key == "\x1b[A":  # Up arrow
                return self.scroll_up()
            elif key == "\x1b[B":  # Down arrow
                return self.scroll_down()
            elif key == "\x1b[5~":  # Page Up
                return self.scroll_up(self.content_rect.height)
            elif key == "\x1b[6~":  # Page Down
                return self.scroll_down(self.content_rect.height)

        if self.focused_child:
            if self.focused_child.handle_key(key):
                return True

        return False
  
    def post_message(self, message: "messages.Message") -> None:
        if self._app:
            self._app.post_message(message)
        else:
            logging.log(f"Error: failed to post {message}")
