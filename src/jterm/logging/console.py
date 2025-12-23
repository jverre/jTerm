import socket
import io
from typing import Any

class ConsoleServer:
    """Run this in a separate terminal: jterm console"""
    def __init__(self, port: int = 8765):
        self.port = port
        
    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('localhost', self.port))
            s.listen(1)
            print(f"jTerm console listening on port {self.port}...")
            print("Waiting for connection...\n")
            
            while True:
                conn, addr = s.accept()
                print("--- App connected ---\n")
                with conn:
                    while True:
                        data = conn.recv(4096)
                        if not data:
                            print("\n--- App disconnected ---")
                            break
                        print(data.decode('utf-8'), end='', flush=True)


class ConsoleClient:
    """Connects to the console server for logging"""
    _instance: "ConsoleClient | None" = None
    
    def __init__(self, port: int = 8765):
        self.port = port
        self._socket: socket.socket | None = None
        self._connected = False
        
    @classmethod
    def get(cls) -> "ConsoleClient":
        if cls._instance is None:
            cls._instance = ConsoleClient()
        return cls._instance
    
    def connect(self) -> bool:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._socket.connect(('localhost', self.port))
            self._connected = True
            return True
        except ConnectionRefusedError:
            self._socket = None
            self._connected = False
            return False
    
    def disconnect(self):
        if self._socket:
            self._socket.close()
            self._socket = None
        self._connected = False
    
    def send(self, message: str):
        if self._socket and self._connected:
            try:
                self._socket.send(message.encode('utf-8'))
            except (BrokenPipeError, ConnectionResetError):
                self._connected = False


def log(*args: Any, **kwargs: Any):
    """Log to the dev console. Safe to call even if console isn't running."""
    client = ConsoleClient.get()
    if not client._connected:
        return
    
    buffer = io.StringIO()
    print(*args, **kwargs, file=buffer)
    client.send(buffer.getvalue())


def run_console():
    """Entry point for running the console server."""
    ConsoleServer().run()
