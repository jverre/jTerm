import argparse
import asyncio
from . import app, layout, logging
from .widgets import Container, Text, Input
from .messages import on


class JTERM(app.App):
    def __init__(self, dev: bool = False):
        root = Container(
            id="root",
            height=layout.Sizing.fill(),
            children=[
                Container(
                    id="messages",
                    height=layout.Sizing.fill(),
                    overflow_y=layout.Overflow.AUTO,
                    children=[
                        Text(
                            id="welcome_header",
                            content="Welcome to JTerm",
                        ),
                    ],
                ),
                Input(
                    id="input",
                    focused=True,
                    height=layout.Sizing.auto(),
                    border=layout.Border.all(style=layout.BorderStyle.ROUNDED),
                ),
            ],
        )
        super().__init__(root, dev)

    @on(Input.Submitted)
    def on_input_submitted(self, message: Input.Submitted):
        messages_container = self.query_one("#messages")

        if messages_container is None:
            logging.log("Failed to find messages container")
        else:
            message_count = len(messages_container.children)
            self.mount(
                parent=messages_container,
                child=Text(
                    id=f"msg-{message_count + 1}",
                    content=f"{message.value}",
                    height=layout.Sizing.auto(),
                ),
            )
            logging.log("added new child: ", messages_container.children)
            self.mark_dirty()


def main():
    parser = argparse.ArgumentParser(description="jTerm - Terminal Application")
    parser.add_argument("command", nargs="?", default="run", help="Command to run")
    parser.add_argument("--dev", action="store_true", help="Enable dev mode logging")

    args = parser.parse_args()
    if args.command == "console":
        logging.run_console()
    else:
        asyncio.run(JTERM(dev=args.dev).run())


if __name__ == "__main__":
    main()
