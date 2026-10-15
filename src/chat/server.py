import asyncio
import os
import websockets

clients = {}

async def handle(ws):
    try:
        await ws.send("Enter your username:")
        username = await ws.recv()
        username = username.strip()

        if not username:
            await ws.send("Username cannot be empty.")
            return


        # Register the client
        clients[ws] = username

        await ws.send(f"Welcome, {username}!")

        # Notify everyone else
        await asyncio.gather(*[
            c.send(f"{username} joined the chat.")
            for c in clients if c != ws
        ])

        # Receive and broadcast messages
        async for msg in ws:
            print(msg)
            await asyncio.gather(*[
                c.send(msg)
                for c in clients if c != ws
            ])
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.pop(ws, None)

async def main():
    host = os.getenv("CHAT_HOST", "0.0.0.0")
    port = int(os.getenv("CHAT_PORT", "6789"))
    async with websockets.serve(handle, host, port):
        print(f"Server running at ws://{host}:{port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
