import asyncio
import websockets
import json

clients = {}
host = None

async def handler(ws):
    global host
    try:
        raw = await ws.recv()
        info = json.loads(raw)

        if info["role"] == "host":
            host = ws
            print("[HOST] connecté")

            while True:
                msg = await ws.recv()
                data = json.loads(msg)

                target = data["target"]
                payload = data["data"]

                if target in clients:
                    await clients[target].send(json.dumps({
                        "from": "host",
                        "data": payload
                    }))

        elif info["role"] == "client":
            cid = info["id"]
            clients[cid] = ws
            print(f"[CLIENT] {cid} connecté")

            if host:
                await host.send(json.dumps({
                    "event": "new_client",
                    "id": cid
                }))

            while True:
                msg = await ws.recv()
                if host:
                    await host.send(json.dumps({
                        "from": cid,
                        "data": msg
                    }))

    except:
        pass
    finally:
        for k, v in list(clients.items()):
            if v == ws:
                del clients[k]
                if host:
                    await host.send(json.dumps({
                        "event": "disconnect",
                        "id": k
                    }))

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8080):
        print("Relay WebSocket actif")
        await asyncio.Future()

asyncio.run(main())
