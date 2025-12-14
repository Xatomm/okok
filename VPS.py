import socket
import threading

HOST = '0.0.0.0'
PORT = 12345

def handle_client(client_socket, server_host, server_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((server_host, server_port))

    def forward(src, dst):
        while True:
            try:
                data = src.recv(4096)
                if not data:
                    break
                dst.sendall(data)
            except:
                break

    threading.Thread(target=forward, args=(client_socket, server_socket), daemon=True).start()
    threading.Thread(target=forward, args=(server_socket, client_socket), daemon=True).start()

    # quand le client ou le serveur ferme la connexion
    client_socket.close()
    server_socket.close()

def main():
    SERVER_HOST = '127.0.0.1'  # ton PC
    SERVER_PORT = 5000          # port où tourne ton GUI

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind((HOST, PORT))
    listener.listen(10)
    print(f"[Relay] Écoute sur {HOST}:{PORT}")

    while True:
        client_sock, addr = listener.accept()
        threading.Thread(target=handle_client, args=(client_sock, SERVER_HOST, SERVER_PORT), daemon=True).start()

if __name__ == "__main__":
    main()
