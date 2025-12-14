# relay.py
import asyncio
import websockets

async def handler(ws):
    print("Client connecté")
    async for msg in ws:
        print("Reçu:", msg)
        await ws.send("OK")

async def main():
    print("Relay en écoute sur 0.0.0.0:8080")
    async with websockets.serve(handler, "0.0.0.0", 8080):
        await asyncio.Future()  # run forever

asyncio.run(main())
