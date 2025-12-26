from dataclasses import dataclass, field
from enum import Enum, auto
from .. import core, logging, ascii
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
    _scroll_events: List[int] = field(default_factory=list)
    
    # How many lines of this widget's content are clipped off the top
    # (set by parent container during layout when scrolling)
    _clip_top: int = 0


    @property
    def _total_content_height(self) -> int:
        """Total height of content (sum of children for containers, content height for others)."""
        if self.children:
            # For containers: sum of children dimensions (children don't include parent's border)
            return sum(child.dimensions.height for child in self.children)
        # For leaf widgets: dimensions includes borders, so subtract them to get content height
        return max(0, self.dimensions.height - self.border.vertical_space)
    
    @property
    def needs_scrollbar(self) -> bool:
        if not self.scrollable:
            return False
        
        # Check if content exceeds visible area
        # Use _inner_rect to avoid circular dependency with content_rect
        inner_height = max(0, self.rect.height - self.border.vertical_space)
        return self._total_content_height > inner_height and inner_height > 0
    
    @property
    def max_scroll_offset(self) -> int:
        """Maximum scroll offset."""
        if not self.needs_scrollbar:
            return 0
        inner_height = max(0, self.rect.height - self.border.vertical_space)
        return max(0, self._total_content_height - inner_height)

    @property
    def scrollbar_height(self) -> int:
        """Height of the scrollbar thumb."""
        if not self.needs_scrollbar:
            return 0
        inner_height = max(0, self.rect.height - self.border.vertical_space)
        # Calculate thumb size proportional to visible content
        thumb_height = max(1, int(inner_height * inner_height / self._total_content_height))
        return min(thumb_height, inner_height)

    @property
    def scrollbar_position(self) -> int:
        """Y position of scrollbar thumb (relative to content_rect top)."""
        if not self.needs_scrollbar or self.max_scroll_offset == 0:
            return 0
        inner_height = max(0, self.rect.height - self.border.vertical_space)
        scrollable_range = inner_height - self.scrollbar_height
        return int(self.scroll_offset / self.max_scroll_offset * scrollable_range)
    
    @property
    def scrollbar_width(self) -> int:
        """Width of the scrollbar (1 if needed, 0 otherwise)."""
        return 1 if self.needs_scrollbar else 0
    
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
        """Returns the inner rect available for content (after border and scrollbar insets)."""
        return Rect(
            x=self.rect.x + self.border.left_width,
            y=self.rect.y + self.border.top_width,
            width=max(0, self.rect.width - self.border.horizontal_space - self.scrollbar_width),
            height=max(0, self.rect.height - self.border.vertical_space),
        )

    def _calculate_dimensions(self, available_width: int | None, available_height: int | None) -> Dimensions:
        raise NotImplementedError

    def measure(self, available_width: int | None, available_height: int | None) -> Dimensions:
        """This measure the size of the content based on the content"""
        dims = self._calculate_dimensions(available_width, available_height)
        logging.log(f"{self.id} - Dimensions: {dims}")
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
        """Draw the scrollbar on the right edge of the widget (after border)."""
        if not self.needs_scrollbar:
            return
        
        # Calculate the inner area (after borders, but including scrollbar space)
        inner_x = self.rect.x + self.border.left_width
        inner_y = self.rect.y + self.border.top_width
        inner_width = max(0, self.rect.width - self.border.horizontal_space)
        inner_height = max(0, self.rect.height - self.border.vertical_space)
        
        if inner_width < 1 or inner_height < 1:
            return
        
        # Scrollbar appears in the rightmost column of inner area
        scrollbar_x = inner_x + inner_width - 1
        
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
        for i in range(inner_height):
            y = inner_y + i
            if thumb_start <= i < thumb_end:
                # Render thumb
                sys.stdout.write(f"\033[{y + 1};{scrollbar_x + 1}H{thumb_color}{thumb_char}{reset}")
            else:
                # Render track
                sys.stdout.write(f"\033[{y + 1};{scrollbar_x + 1}H{track_color}{track_char}{reset}")
        
        sys.stdout.flush()
        
    def render(self):
        """Template method: renders border, then delegates to render_content()."""
        logging.log(f"{self.id} - rect: {self.rect}")
        self._render_border()
        self.render_content()
        self._render_scrollbar()

    def on_frame(self):
        """Called every frame (60 FPS). Process buffered events here."""
        # Process scroll buffer
        if self._scroll_events:
            THRESHOLD = 1
            
            total = sum(self._scroll_events)
            self._scroll_events.clear()
            
            if total >= THRESHOLD:
                if self.scroll_up(3):
                    if self._app:
                        self._app._dirty = True
            elif total <= -THRESHOLD:
                if self.scroll_down(3):
                    if self._app:
                        self._app._dirty = True
        
        # Propagate to children
        for child in self.children:
            child.on_frame()

    @property
    def focused_child(self) -> Optional["Widget"]:
        """Get the currently focused child, if any."""
        for child in self.children:
            if child.focused:
                return child
        return None
    
    def handle_key(self, key: ascii.Key) -> bool:
        if self.focused_child:
            if self.focused_child.handle_key(key):
                return True

        return False

    def contains_point(self, x: int, y: int) -> bool:
        return (
            self.rect.x <= x < self.rect.x + self.rect.width
            and self.rect.y <= y < self.rect.y + self.rect.height
        )

    def handle_mouse(self, mouse: ascii.Mouse):
        # Propagate to children
        for child in self.children:
            if child.handle_mouse(mouse):
                return True
        
        if mouse.scroll_up or mouse.scroll_down:
            if self.contains_point(mouse.x, mouse.y) and self.needs_scrollbar:
                if mouse.scroll_up:
                    self._scroll_events.append(1)
                elif mouse.scroll_down:
                    self._scroll_events.append(-1)
                
                if self._app:
                    self._app._dirty=True
                
                return True
        
        return False

    def post_message(self, message: "messages.Message") -> None:
        if self._app:
            self._app.post_message(message)
        else:
            logging.log(f"Error: failed to post {message}")
