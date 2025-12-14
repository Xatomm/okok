import asyncio
import websockets
import json
import os

clients = {}
host = None
PORT = 8080

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
                print(f"[CLIENT] {k} déconnecté")
                if host:
                    await host.send(json.dumps({
                        "event": "disconnect",
                        "id": k
                    }))

async def main():
    print("=" * 50)
    print("Relay WebSocket démarré")
    print()
    print("⚠️ OBLIGATOIRE :")
    print("1) Clique sur : Web Preview → Preview on port 8080")
    print("2) Copie l'URL HTTPS affichée dans le navigateur")
    print("3) Remplace https:// par wss:// dans tes scripts")
    print()
    print("📌 Exemple :")
    print("   https://8080-xxxx.cloudshell.dev")
    print("→ wss://8080-xxxx.cloudshell.dev")
    print("=" * 50)
    print()

    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()  # run forever

asyncio.run(main())
