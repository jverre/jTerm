import argparse
import asyncio
from . import app, layout
from .widgets import Container, Text, Input
from .logging import run_console
from .messages import on


class JTERM(app.App):
    def __init__(self, dev: bool = False):
        root = Container(
            id="root",
            height=layout.Size.fill(),
            children=[
                Container(
                    id="messages",
                    height=layout.Size.fill(),
                    children=[
                        Text(id="welcome_header", content="Welcome to JTerm"),
                    ],
                ),
                Input(
                    id="input",
                    focused=True,
                    height=layout.Size.auto(0),
                    border=layout.Border.all(style=layout.BorderStyle.ROUNDED),
                ),
            ],
        )
        super().__init__(root, dev)

    @on(Input.Submitted)
    def on_input_submitted(self, message: Input.Submitted):
        messages_container = self.query_one("#messages")

        message_count = len(messages_container.children)
        self.mount(
            messages_container,
            Text(id=f"msg-{message_count + 1}", content=f"> {message.value}"),
        )


def main():
    parser = argparse.ArgumentParser(description="jTerm - Terminal Application")
    parser.add_argument("command", nargs="?", default="run", help="Command to run")
    parser.add_argument("--dev", action="store_true", help="Enable dev mode logging")

    args = parser.parse_args()
    if args.command == "console":
        run_console()
    else:
        asyncio.run(JTERM(dev=args.dev).run())


if __name__ == "__main__":
    main()
