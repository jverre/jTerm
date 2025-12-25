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
  
        # Compute the available height for all children
        if self.height.mode == SizeMode.AUTO:
            available_child_height = None
        else:
            available_child_height = available_content_height

        # Compute available width for all children
        available_child_width = available_content_width

        # Compute dimensions of children
        if not self.children:
            max_child_width = 0
            total_child_height = 0
        else:
            max_child_width = 0
            total_child_height = 0
            
            for child in self.children:
                child_dims = child.measure(
                    available_width=available_child_width,
                    available_height=available_child_height,
                )
                max_child_width = max(max_child_width, child_dims.width)
                total_child_height += child_dims.height
        
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
        
        logging.log(f"Measure - Container ({self.id}) - width:{width}, height:{height}")
        return Dimensions(width=width, height=height)

    def layout(self, rect: Rect):
        self.rect = rect
        logging.log("Layout - Container ({self.id}): ", self.content_rect)
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
        logging.log(f"Container ({self.id}) - remaining_height: {remaining_height}")
        if fill_count > 0:
            base_height_per_fill = remaining_height // fill_count
            remainder = remaining_height % fill_count
        else:
            base_height_per_fill = 0
            remainder = 0
        logging.log(f"Container ({self.id}) - base_height_per_fill: {base_height_per_fill}, remainder:{remainder}")

        # Compute the correct height
        y_offset = 0
        fill_index = 0
        for child in self.children:
            if y_offset >= content.height:
                child.layout(
                    Rect(
                        x=content.x,
                        y=content.y + y_offset,
                        width=content.width,
                        height=0
                    )
                )
            else:
                if child.height.mode == SizeMode.FILL:
                    child_height = base_height_per_fill
                    if fill_index < remainder:
                        child_height += 1
                    fill_index += 1
                else:
                    child_height = child.dimensions.height
                
                logging.log(f"Container ({self.id}) - child ({child.id}) - child_height: {child_height}")
                remaining_height = content.height - y_offset
                actual_height = min(child_height, remaining_height)

                child.layout(
                    Rect(
                        x=content.x,
                        y=content.y + y_offset,
                        width=content.width,
                        height=actual_height
                    )
                )

                y_offset+= actual_height


    def render(self):
        logging.log(f"Render - Container - ({self.id}): ", self.content_rect)

        for child in self.children:
            child.render()
