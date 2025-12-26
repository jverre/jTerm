from dataclasses import dataclass
from . import widget
from .. import logging, layout
from ..layout import Rect, SizeMode, Dimensions


@dataclass
class Container(widget.Widget):
    """Note: This will map to a "div" in web UI"""

    def _calculate_dimensions(self, available_width: int | None, available_height: int | None):
        # Compute available height without borders
        if available_width is None:
            available_content_width = None
        else:
            available_content_width = max(0, available_width - self.border.horizontal_space)

        if available_height is None:
            available_content_height = None
        else:
            available_content_height = max(0, available_height - self.border.vertical_space)

        # Compute available width for all children
        available_child_width = available_content_width

        # Two-pass approach: first measure AUTO/FIXED, then FILL with remaining height
        if not self.children:
            max_child_width = 0
            total_child_height = 0
        else:
            # First pass: measure AUTO and FIXED children to know their height
            auto_fixed_height = 0
            fill_count = 0
            for child in self.children:
                if child.height.mode == SizeMode.FILL:
                    fill_count += 1
                else:
                    child_dims = child.measure(
                        available_width=available_child_width,
                        available_height=None,  # AUTO/FIXED don't need height constraint
                    )
                    auto_fixed_height += child_dims.height

            # Calculate remaining height for FILL children
            if available_content_height is not None and fill_count > 0:
                remaining_for_fill = max(0, available_content_height - auto_fixed_height)
                height_per_fill = remaining_for_fill // fill_count
            else:
                height_per_fill = None

            # Second pass: measure FILL children with correct available height
            max_child_width = 0
            total_child_height = auto_fixed_height
            for child in self.children:
                if child.height.mode == SizeMode.FILL:
                    child_dims = child.measure(
                        available_width=available_child_width,
                        available_height=height_per_fill,
                    )
                    max_child_width = max(max_child_width, child_dims.width)
                    total_child_height += child_dims.height
                else:
                    # Already measured, just update max_child_width
                    max_child_width = max(max_child_width, child.dimensions.width)
        
        # Compute width of container
        if self.width.mode == SizeMode.FILL:
            if available_width is None:
                width = max_child_width + self.border.horizontal_space
            else:
                width = available_width
        elif self.width.mode == SizeMode.FIXED:
            width = self.width.value
        elif self.width.mode == SizeMode.AUTO:
            width = max_child_width + self.border.horizontal_space
            if available_width is not None:
                width = min(width, available_width)
        else:
            raise ValueError(f"Unknown width mode: {self.width.mode}")
        
        # Compute height of container
        # NOTE: For FILL mode, use available_height so parent sees constrained size
        # The _total_content_height property handles scrollbar calculations separately
        if self.height.mode == SizeMode.FILL:
            if available_height is None:
                height = total_child_height + self.border.vertical_space
            else:
                height = available_height
        elif self.height.mode == SizeMode.FIXED:
            height = self.height.value
        elif self.height.mode == SizeMode.AUTO:
            height = total_child_height + self.border.vertical_space
            if available_height is not None:
                height = min(height, available_height)
        else:
            raise ValueError(f"Unknown height mode: {self.height.mode}")
        
        return Dimensions(width=width, height=height)

    def layout(self, rect: Rect):
        self.rect = rect
        content = self.content_rect

        # First pass to calculate the space needed for AUTO and FIXED children
        auto_and_fixed_height = 0
        fill_count = 0
        for child in self.children:
            if child.height.mode == SizeMode.FILL:
                fill_count += 1
            elif child.height.mode == SizeMode.AUTO or child.height.mode == SizeMode.FIXED:
                auto_and_fixed_height += child.dimensions.height
            else:
                raise ValueError(f"SizeMode {child.height.mode} is not supported")
        
        # Calculate available height for FILL children
        remaining_height = max(0, content.height - auto_and_fixed_height)
        if fill_count > 0:
            base_height_per_fill = remaining_height // fill_count
            remainder = remaining_height % fill_count
        else:
            base_height_per_fill = 0
            remainder = 0
        
        # Compute the correct height, applying scroll_offset to position children
        y_offset = -self.scroll_offset  # Start offset by scroll position
        fill_index = 0
        for child in self.children:
            if child.height.mode == SizeMode.FILL:
                child_height = base_height_per_fill
                if fill_index < remainder:
                    child_height += 1
                fill_index += 1
            else:
                child_height = child.dimensions.height
            
            # Calculate the visible portion of this child
            child_top = y_offset
            child_bottom = y_offset + child_height
            
            # Check if child is at least partially visible
            if child_bottom <= 0:
                # Child is completely above the visible area
                child._clip_top = child_height  # Entire child is clipped
                child.layout(Rect(x=content.x, y=content.y, width=content.width, height=0))
            elif child_top >= content.height:
                # Child is completely below the visible area
                child._clip_top = 0
                child.layout(Rect(x=content.x, y=content.y + content.height, width=content.width, height=0))
            else:
                # Child is at least partially visible
                visible_top = max(0, child_top)
                visible_bottom = min(content.height, child_bottom)
                visible_height = visible_bottom - visible_top
                
                # Calculate how many lines are clipped from the top
                child._clip_top = max(0, -child_top)
                
                child.layout(
                    Rect(
                        x=content.x,
                        y=content.y + visible_top,
                        width=content.width,
                        height=visible_height
                    )
                )
            
            y_offset += child_height

    def render_content(self):
        """Render all children within the container."""
        for child in self.children:
            child.render()
