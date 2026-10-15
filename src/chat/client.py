import argparse
import asyncio
import ast
import curses
import random
import threading
import queue
import websockets

from cryptography.fernet import Fernet
import base64

DEFAULT_SERVER = "ws://localhost:6789"


class ChatTUI:
    def __init__(self, stdscr, username=None, server=DEFAULT_SERVER, key=None):
        self.stdscr = stdscr
        self.server = server
        self.username = username or f"username_{random.randint(0, 100)}"
        self.messages = queue.Queue()
        self.history = []
        self.input_text = ""
        if key:
            fernet = Fernet(key)
            self.encode = lambda x : str(fernet.encrypt(x.encode()))

            def decode(message):
                # Chat ciphertext is sent as the string representation of bytes
                # (for example: "b'gAAAAA...'"). Server notices stay plaintext.
                if isinstance(message, str) and message.startswith("b'"):
                    return fernet.decrypt(ast.literal_eval(message)).decode()
                return message

            self.decode = decode
        else:
            self.encode = lambda x : x
            self.decode = lambda x : x
        self.loop = None
        self.ws = None
        self.connected = threading.Event()
        self.running = True

        curses.curs_set(1)
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)

    def draw(self):
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()

        # Header
        self.stdscr.addnstr(
            0, 0, f" WebSocket Chat | {self.username} | F2 to quit ",
            width - 1, curses.A_REVERSE
        )

        # Chat messages
        visible_rows = max(1, height - 4)
        history = list(self.history)[-visible_rows:]

        for i, message in enumerate(history):
            self.stdscr.addnstr(i + 1, 0, message, width - 1)

        # Input area
        if height >= 3:
            self.stdscr.addnstr(height - 2, 0, "-" * (width - 1), width - 1)
            self.stdscr.addnstr(
                height - 1, 0, "> " + self.input_text, width - 1
            )

        self.stdscr.refresh()

    async def network(self):
        try:
            async with websockets.connect(self.server) as ws:
                self.ws = ws

                # Login with the existing server protocol
                prompt = await ws.recv()
                self.messages.put(prompt)
                await ws.send(self.username)

                response = await ws.recv()

                self.messages.put(response)

                if response == "Username cannot be empty.":
                    return

                self.connected.set()

                async for message in ws:
                    message = self.decode(message)
                    self.messages.put(message)

        except Exception as exc:
            self.messages.put(f"Connection error: {exc}")
        finally:
            self.connected.clear()
            self.running = False

    def send_message(self, message):
        if self.ws and self.loop and self.connected.is_set():
            asyncio.run_coroutine_threadsafe(
                self.ws.send(self.encode(message)), self.loop
            )
            self.history.append(message)

    def network_thread(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.network())
        self.loop.close()

    def run(self):
        thread = threading.Thread(target=self.network_thread, daemon=True)
        thread.start()

        while self.running:
            # Collect incoming messages
            while not self.messages.empty():
                self.history.append(self.messages.get())

            self.draw()

            try:
                key = self.stdscr.getch()
            except curses.error:
                key = -1

            if key == curses.KEY_F2:
                break
            elif key in (10, 13, curses.KEY_ENTER):
                message = f"<{self.username}> {self.input_text.strip()}"
                if message:
                    self.send_message(message)
                    self.input_text = ""
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_text = self.input_text[:-1]
            elif 32 <= key <= 126:
                self.input_text += chr(key)

            curses.napms(30)


def parse_args():
    parser = argparse.ArgumentParser(description="WebSocket chat TUI client")
    parser.add_argument(
        "-u", "--username",
        help="username to log in with (default: random username_N)",
    )
    parser.add_argument(
        "-s", "--server", default=DEFAULT_SERVER,
        help=f"server URL (default: {DEFAULT_SERVER})",
    )
    parser.add_argument(
        "-k", "--key", default=None,
        help=f"key (default: None)",
    )
    
    return parser.parse_args()


def main(stdscr, args):
    ChatTUI(stdscr, username=args.username, server=args.server, key= base64.b64encode(args.key.encode("ascii")) if args.key else None).run()


if __name__ == "__main__":
    args = parse_args()
    curses.wrapper(main, args)
