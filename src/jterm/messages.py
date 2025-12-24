from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import widgets

@dataclass
class Message:
    sender: "widgets.Widget" = field(repr=False)
    
    @property
    def handler_name(self) -> str:
        widget_name = type(self.sender).__name__.lower()
        message_name = type(self).__name__.lower()

        return f"on_{widget_name}_{message_name}"

def on(message_type: type):
    def decorator(func):
        if not hasattr(func, '_handles_messages'):
            func._handles_messages = []
        
        func._handles_messages.append(message_type)
        return func
    return decorator
