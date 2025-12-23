from typing import Optional
import sys
import termios
import tty
import asyncio
from . import widgets, commands, core, logging, layout

class App:
    def __init__(self, root: widgets.Widget, dev: bool=False):
        self.root = root
        self._dev = dev

        self.width, self.height = commands.terminal_size()
        self._fd = sys.stdin.fileno()
        self._old_settings = None

        self._running = False
        self._key_queue: asyncio.Queue[str] = asyncio.Queue()

    def _start_terminal(self):
        self._old_settings = termios.tcgetattr(self._fd)
        tty.setraw(self._fd)
        sys.stdout.write("\033[?1049h\033[?25l")
        sys.stdout.flush()
        
    def _stop_terminal(self):
        termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_settings)
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()
    
    def _add_key_to_queue(self):
        key = sys.stdin.read(1)
        self._key_queue.put_nowait(key)

    async def read_key(self) -> str:
        return await self._key_queue.get()

    def write(self, data: str):
        """Write to terminal. Stdout writes are fast, no need for async."""
        sys.stdout.write(data)
        sys.stdout.flush()

    async def run(self):
        self._running = True
        
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
                screen_rect = layout.Rect(x=0, y=0, width=self.width, height=self.height)
                self.root.layout(screen_rect)

                self.root.render()
                
                key = await self.read_key()

                if key == 'q':
                    break
                
                self.root.handle_key(key)

                commands.clear_screen()
                self.root.render()
        finally:
            self._stop_terminal()
            if self._dev:
                logging.log("=== jTerm Dev Session Ended ===")
                logging.ConsoleClient.get().disconnect()

