import socket
import threading

HOST = "0.0.0.0"
PORT = 8080

sessions = {}

def pipe(a, b):
    try:
        while True:
            data = a.recv(4096)
            if not data:
                break
            b.sendall(data)
    except:
        pass
    finally:
        a.close()
        b.close()

def handle(conn):
    try:
        session = conn.recv(64).decode().strip()
        print(f"[+] Connexion session {session}")

        sessions.setdefault(session, []).append(conn)

        if len(sessions[session]) == 2:
            a, b = sessions[session]
            print(f"[✓] Session {session} reliée")
            threading.Thread(target=pipe, args=(a,b), daemon=True).start()
            threading.Thread(target=pipe, args=(b,a), daemon=True).start()

    except:
        conn.close()

server = socket.socket()
server.bind((HOST, PORT))
server.listen(10)

print(f"[+] Relais actif sur port {PORT}")

while True:
    conn, _ = server.accept()
    threading.Thread(target=handle, args=(conn,), daemon=True).start()
