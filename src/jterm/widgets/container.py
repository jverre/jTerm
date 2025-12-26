from dataclasses import dataclass
from . import widget
from .. import logging, layout
from ..layout import Rect, SizeMode, Size, Overflow


@dataclass
class Container(widget.Widget):
    """Note: This will map to a "div" in web UI"""

    def _calculate_dimensions(
        self, available_width: int | None, available_height: int | None
    ) -> Size:
        """Returns CONTENT dimensions only (no borders).

        Note: available_width/height are already CONTENT space (borders subtracted by parent).
        """
        # For scrollable containers, measure children with UNCONSTRAINED height
        measure_height = (
            None if self.overflow_y != Overflow.VISIBLE else available_height
        )

        # Two-pass sizing for FILL children
        auto_fixed_height = 0
        fill_count = 0
        max_child_width = 0

        for child in self.children:
            if child.height.mode == SizeMode.FILL:
                fill_count += 1
            else:
                # measure() returns TOTAL size, content_size is stored
                child.measure(available_width, None)
                # Use TOTAL height for layout positioning (child occupies this space)
                auto_fixed_height += (
                    child.content_size.height + child.border.vertical_space
                )
                max_child_width = max(
                    max_child_width,
                    child.content_size.width + child.border.horizontal_space,
                )

        # Calculate height per FILL child
        if measure_height is not None and fill_count > 0:
            remaining = max(0, measure_height - auto_fixed_height)
            height_per_fill = remaining // fill_count
        else:
            height_per_fill = 0

        # Measure FILL children
        total_height = auto_fixed_height
        for child in self.children:
            if child.height.mode == SizeMode.FILL:
                child.measure(available_width, height_per_fill)
                total_height += child.content_size.height + child.border.vertical_space
                max_child_width = max(
                    max_child_width,
                    child.content_size.width + child.border.horizontal_space,
                )

        # Store CONTENT size (sum of children's outer sizes, but this IS our content)
        self.content_size = Size(width=max_child_width, height=total_height)

        # Apply sizing policy to determine final content dimensions
        if self.width.mode == SizeMode.FILL:
            width = available_width if available_width else max_child_width
        elif self.width.mode == SizeMode.FIXED:
            width = max(0, self.width.value - self.border.horizontal_space)
        else:  # AUTO
            width = max_child_width
            if available_width:
                width = min(width, available_width)

        if self.height.mode == SizeMode.FILL:
            height = available_height if available_height else total_height
        elif self.height.mode == SizeMode.FIXED:
            height = max(0, self.height.value - self.border.vertical_space)
        else:  # AUTO
            height = total_height
            if available_height:
                height = min(height, available_height)

        return Size(width=width, height=height)

    def layout(self, rect: Rect):
        """Layout children at their NATURAL positions - no scroll offset here!"""
        self.rect = rect
        content = self.content_rect

        # Calculate FILL heights
        auto_fixed_height = sum(
            c.content_size.height + c.border.vertical_space
            for c in self.children
            if c.height.mode != SizeMode.FILL
        )
        fill_count = sum(1 for c in self.children if c.height.mode == SizeMode.FILL)

        if fill_count > 0:
            remaining = max(0, content.height - auto_fixed_height)
            base_fill = remaining // fill_count
            extra = remaining % fill_count
        else:
            base_fill = 0
            extra = 0

        # Layout children at natural positions (0, 1, 2, ... from top)
        y = 0
        fill_idx = 0
        for child in self.children:
            if child.height.mode == SizeMode.FILL:
                h = base_fill + (1 if fill_idx < extra else 0)
                fill_idx += 1
            else:
                h = child.content_size.height + child.border.vertical_space

            # Child rect is relative to content area
            # NOTE: No scroll_offset here! That's handled in render.
            child.layout(
                Rect(
                    x=content.x,
                    y=content.y + y,  # Natural position
                    width=content.width,
                    height=h,
                )
            )
            y += h

    def render_content(self):
        """Render children with scroll-based clipping."""
        viewport = self.content_rect

        for child in self.children:
            # Calculate where child appears after scroll
            visual_y = child.rect.y - self.scroll_offset
            visual_bottom = visual_y + child.rect.height

            # Skip if completely outside viewport
            if visual_bottom <= viewport.y:
                continue
            if visual_y >= viewport.y + viewport.height:
                continue

            # Render with scroll translation
            child.render_scrolled(viewport=viewport, scroll_offset=self.scroll_offset)
