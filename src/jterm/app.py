from typing import Optional
import os
import sys
import termios
import tty
import asyncio
import fcntl
from . import widgets, commands, core, logging, layout, ascii


class App:
    def __init__(self, root: widgets.Widget, dev: bool = False):
        self.root = root
        self._dev = dev

        self.width, self.height = commands.terminal_size()
        self._fd = sys.stdin.fileno()
        self._old_settings = None
        self._old_flags = None

        self._running = False
        self._key_queue: asyncio.Queue[ascii.Key] = asyncio.Queue()

        self._handlers = {}
        self._register_handlers()

    def _mount_widget(self, widget: widgets.Widget):
        widget._app = self
        for child in widget.children:
            self._mount_widget(child)

    def mount(self, parent: widgets.Widget, child: widgets.Widget):
        self._mount_widget(child)
        parent.children.append(child)

    def post_message(self, message) -> None:
        msg_type = type(message)
        handler = self._handlers.get(msg_type)
        if handler:
            handler(message)
        else:
            logging.log(f"Failed to find handler in post_message for: {message}")
        self.root.render()  # TODO: Fix render loop

    def _register_handlers(self):
        for name in dir(self):
            method = getattr(self, name)
            if callable(method) and hasattr(method, "_handles_messages"):
                for msg_type in method._handles_messages:
                    self._handlers[msg_type] = method

    def query_one(self, selector: str) -> Optional[widgets.Widget]:
        if selector.startswith("#"):
            return self._find_by_id(self.root, selector[1:])
        return None

    def _find_by_id(
        self, widget: widgets.Widget, target_id: str
    ) -> Optional[widgets.Widget]:
        if widget.id == target_id:
            return widget
        for child in widget.children:
            found = self._find_by_id(child, target_id)
            if found:
                return found
        return None

    def _start_terminal(self):
        self._old_settings = termios.tcgetattr(self._fd)

        self._old_flags = fcntl.fcntl(self._fd, fcntl.F_GETFL)
        # fcntl.fcntl(self._fd, fcntl.F_SETFL, self._old_flags | os.O_NONBLOCK)

        tty.setraw(self._fd)
        sys.stdout.write("\x1b[?1049h")  # Alternate screen
        sys.stdout.write("\x1b[?25l")  # Hide cursor
        sys.stdout.write(
            "\x1b[>1u"
        )  # https://sw.kovidgoyal.net/kitty/keyboard-protocol/
        sys.stdout.write("\033[?1000h")  # Enable mouse click tracking
        sys.stdout.write("\033[?1003h")  # Enable all mouse movement tracking
        sys.stdout.write("\033[?1006h")  # Enable SGR extended mouse mode

        sys.stdout.flush()

    def _stop_terminal(self):
        sys.stdout.write("\x1b[>0u")
        sys.stdout.write("\x1b[?25h")
        sys.stdout.write("\x1b[?1049l")
        sys.stdout.flush()

        # fcntl.fcntl(self._fd, fcntl.F_SETFL, self._old_flags)
        termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_settings)

    def _add_key_to_queue(self):
        key = ascii.read_key()
        self._key_queue.put_nowait(key)

    async def read_key(self) -> ascii.Key:
        return await self._key_queue.get()

    def write(self, data: str):
        """Write to terminal. Stdout writes are fast, no need for async."""
        sys.stdout.write(data)
        sys.stdout.flush()

    async def run(self):
        self._running = True
        self._mount_widget(self.root)

        if self._dev:
            if logging.ConsoleClient.get().connect():
                logging.log("=== jTerm Dev Session Started ===")
            else:
                pass

        loop = asyncio.get_running_loop()
        self._start_terminal()
        loop.add_reader(self._fd, self._add_key_to_queue)

        try:
            i = 0
            while self._running:
                commands.clear_screen()
                
                # Compute the size of the components
                dimensions = self.root.measure(
                    available_width=self.width,
                    available_height=self.height
                )
                
                # Compute the layout
                screen_rect = layout.Rect(
                    x=0,
                    y=0,
                    width=self.width,
                    height=self.height
                )
                self.root.layout(screen_rect)

                # Render the components
                self.root.render()

                key = await self.read_key()

                if key.key == "q":
                    break
                
                self.root.handle_key(key)

                commands.clear_screen()
                self.root.render()
        finally:
            self._stop_terminal()
            if self._dev:
                logging.log("=== jTerm Dev Session Ended ===")
                logging.ConsoleClient.get().disconnect()
