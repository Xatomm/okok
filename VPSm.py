import socket
import threading

HOST = "0.0.0.0"  # Écoute sur toutes les interfaces du VPS
PORT = 5001       # Choisis un port libre sur le VPS

clients = []

def broadcast(message, sender):
    for c in clients:
        if c != sender:
            try:
                c.send(message)
            except:
                pass

def handle_client(conn, addr):
    print(f"[CONNECTED] {addr}")
    clients.append(conn)
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            broadcast(data, conn)
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        print(f"[DISCONNECTED] {addr}")
        clients.remove(conn)
        conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"[INFO] Relay TCP actif sur {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
