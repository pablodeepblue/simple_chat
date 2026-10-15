# WebSocket Chat

A small terminal-based chat application built with Python and WebSockets.

## Run locally

Install the dependencies, then start the server:

```sh
uv sync
uv run python -m chat.server
```

In a separate terminal, connect a client:

```sh
uv run python src/chat/client.py --username alice
```

The server listens on port `6789`. Use `--server ws://HOST:6789` to connect the client to another host.

## Run the server with Docker

Build the image:

```sh
docker build -t websocket-chat-server .
```

Run it, publishing the WebSocket port:

```sh
docker run --rm -p 6789:6789 websocket-chat-server
```

Then connect with a client using `ws://localhost:6789` (or the Docker host's address from another machine).

## Server configuration

The container accepts these optional environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `CHAT_HOST` | `0.0.0.0` | Network interface for the server to bind. |
| `CHAT_PORT` | `6789` | WebSocket listening port. |

For example:

```sh
docker run --rm -e CHAT_PORT=8080 -p 8080:8080 websocket-chat-server
```
