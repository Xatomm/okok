import socket
import threading
import time

# -----------------------------
# CONFIGURATION
# -----------------------------
LISTEN_HOST = "0.0.0.0"  # Écoute toutes les interfaces
LISTEN_PORT = 12345      # Port du relay
SERVER_HOST = "127.0.0.1"  # IP locale de ton serveur GUI (depuis le VPS, ngrok redirigera)
SERVER_PORT = 5000          # Port TCP du serveur GUI

# -----------------------------
# CLIENT HANDLER
# -----------------------------
clients = []

def handle_client(client_socket, addr):
    print(f"[Relay] Nouveau client connecté: {addr}")
    clients.append(client_socket)

    # Connexion au serveur GUI
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((SERVER_HOST, SERVER_PORT))
        print(f"[Relay] Connecté au serveur GUI {SERVER_HOST}:{SERVER_PORT}")
    except Exception as e:
        print(f"[Relay] Impossible de se connecter au serveur GUI: {e}")
        client_socket.close()
        return

    # Thread pour relayer client → serveur
    def client_to_server():
        while True:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                server_socket.sendall(data)
            except:
                break
        client_socket.close()
        server_socket.close()
        print(f"[Relay] Client {addr} déconnecté")

    # Thread pour relayer serveur → client
    def server_to_client():
        while True:
            try:
                data = server_socket.recv(4096)
                if not data:
                    break
                client_socket.sendall(data)
            except:
                break
        client_socket.close()
        server_socket.close()

    threading.Thread(target=client_to_server, daemon=True).start()
    threading.Thread(target=server_to_client, daemon=True).start()

# -----------------------------
# MAIN
# -----------------------------
def main():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((LISTEN_HOST, LISTEN_PORT))
    listener.listen(10)
    print(f"[Relay] Écoute sur {LISTEN_HOST}:{LISTEN_PORT}")

    while True:
        client_sock, addr = listener.accept()
        threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()

if __name__ == "__main__":
    main()

