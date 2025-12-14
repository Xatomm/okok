# relay_tcp.py
import socket
import threading
import time

# -----------------------------
# CONFIGURATION
# -----------------------------
LISTEN_HOST = "0.0.0.0"     # Écoute sur toutes les interfaces
LISTEN_PORT = 12345         # Port public pour NGROK
SERVER_HOST = "4.tcp.eu.ngrok.io"   # Adresse du serveur GUI (modifie si exposé via NGROK)
SERVER_PORT = 10283           # Port du serveur GUI

# -----------------------------
# GESTION CLIENT
# -----------------------------
clients = {}
clients_lock = threading.Lock()


def forward(src_sock, dst_sock):
    """Forward toutes les données entre deux sockets."""
    try:
        while True:
            data = src_sock.recv(4096)
            if not data:
                break
            dst_sock.sendall(data)
    except Exception as e:
        print(f"[Forward] Erreur : {e}")
    finally:
        src_sock.close()
        dst_sock.close()


def handle_client(client_sock, client_addr):
    print(f"[Relay] Nouveau client connecté: {client_addr}")

    try:
        # Connecte le relay au serveur GUI
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.connect((SERVER_HOST, SERVER_PORT))
        print(f"[Relay] Connecté au serveur GUI {SERVER_HOST}:{SERVER_PORT}")
    except Exception as e:
        print(f"[Relay] Impossible de se connecter au serveur GUI: {e}")
        client_sock.close()
        return

    # Stockage client
    with clients_lock:
        clients[client_addr] = (client_sock, server_sock)

    # Threads pour forward bidirectionnel
    t1 = threading.Thread(target=forward, args=(client_sock, server_sock), daemon=True)
    t2 = threading.Thread(target=forward, args=(server_sock, client_sock), daemon=True)
    t1.start()
    t2.start()

    # Attend que les deux threads se terminent
    t1.join()
    t2.join()

    with clients_lock:
        del clients[client_addr]

    print(f"[Relay] Client déconnecté: {client_addr}")


def main():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((LISTEN_HOST, LISTEN_PORT))
    listener.listen(10)
    print(f"[Relay] Écoute sur {LISTEN_HOST}:{LISTEN_PORT}")

    while True:
        client_sock, client_addr = listener.accept()
        threading.Thread(target=handle_client, args=(client_sock, client_addr), daemon=True).start()


if __name__ == "__main__":
    main()
