import sys
import json
import socket
import threading
import time
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog,
    QLineEdit, QLabel, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt

# -----------------------------
# Server / Client Management
# -----------------------------

class ClientInfo:
    def __init__(self, client_id, addr, sock, name="", os="", last_seen=None):
        self.client_id = client_id
        self.addr = addr
        self.sock = sock
        self.name = name
        self.os = os
        self.last_seen = last_seen or datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ServerThread(threading.Thread):
    def __init__(self, gui, host="0.0.0.0", port=5000):
        super().__init__(daemon=True)
        self.gui = gui
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = True
        self.client_counter = 0
        self.clients = {}

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        RELAY_HOST = "8080-cs-xxxxx.cloudshell.dev"
        RELAY_PORT = 443
        SESSION_ID = "123456"

        
        self.server_socket.connect((RELAY_HOST, RELAY_PORT))
        self.server_socket.send(SESSION_ID.encode())

        client_info = ClientInfo(1, ("RELAY", 0), sock)
        self.clients[1] = client_info
        self.gui.add_client_to_table(client_info)

        self.handle_client(client_info)


        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                self.client_counter += 1
                cid = self.client_counter

                client_info = ClientInfo(cid, addr, client_sock)
                self.clients[cid] = client_info

                self.gui.add_client_to_table(client_info)

                threading.Thread(target=self.handle_client, args=(client_info,), daemon=True).start()

            except Exception:
                break

    def handle_client(self, client_info):
        sock = client_info.sock
        cid = client_info.client_id

        sock.settimeout(0.5)  # Timeout pour éviter blocage infini

        while True:
            try:
                try:
                    data = sock.recv(1024)
                except socket.timeout:
                    continue  # pas de données mais le client est toujours là

                if not data:
                    # Vérifier si la socket est réellement fermée
                    if self.is_socket_closed(sock):
                        break
                    else:
                        continue

                text = data.decode()
                client_info.last_seen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.gui.update_client_row(client_info)
                self.gui.append_terminal(f"[Client {cid}] → {text}")

            except Exception as e:
                print(f"[Erreur client {cid}] {e}")
                break

        del self.clients[cid]
        self.gui.remove_client(cid)


    def is_socket_closed(self, sock):
        try:
            sock.setblocking(0)
            data = sock.recv(16)
            if data == b'':
                return True
        except BlockingIOError:
            return False
        except Exception:
            return True
        finally:
            sock.setblocking(1)
        return False


    def send_to_client(self, cid, message):
        if cid in self.clients:
            try:
                self.clients[cid].sock.send(message.encode())
                return True
            except:
                return False
        return False

    def stop(self):
        self.running = False
        try:
            self.server_socket.close()
        except:
            pass


# -----------------------------
# GUI
# -----------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xa1om")
        self.resize(900, 600)

        self.json_folder = None
        self.json_data = {}

        self.server = ServerThread(self)
        self.server.start()

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Terminal output
        term_label = QLabel("Terminal / Résultats des commandes :")
        layout.addWidget(term_label)

        from PyQt6.QtWidgets import QTextEdit
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFixedHeight(180)
        layout.addWidget(self.terminal)

        # Table clients
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Nom", "OS", "IP", "Dernière connexion"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Command sender
        cmd_layout = QHBoxLayout()

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Entrez une commande symbolique… (ex : PING, ECHO:Hello)")
        cmd_layout.addWidget(self.cmd_input)

        send_btn = QPushButton("Envoyer au client sélectionné")
        send_btn.clicked.connect(self.send_command)
        cmd_layout.addWidget(send_btn)

        layout.addLayout(cmd_layout)

        # JSON controls
        json_layout = QHBoxLayout()

        btn_load = QPushButton("Charger fichier JSON")
        btn_load.clicked.connect(self.load_json)
        json_layout.addWidget(btn_load)

        btn_save = QPushButton("Sauvegarder JSON")
        btn_save.clicked.connect(self.save_json)
        json_layout.addWidget(btn_save)

        btn_set_folder = QPushButton("Choisir dossier clients")
        btn_set_folder.clicked.connect(self.choose_folder)
        json_layout.addWidget(btn_set_folder)

        layout.addLayout(json_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # -----------------------------
    # Client Table Handling
    # -----------------------------

    def add_client_to_table(self, client_info):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(str(client_info.client_id)))
        self.table.setItem(row, 1, QTableWidgetItem(client_info.name))
        self.table.setItem(row, 2, QTableWidgetItem(client_info.os))
        self.table.setItem(row, 3, QTableWidgetItem(client_info.addr[0]))
        self.table.setItem(row, 4, QTableWidgetItem(client_info.last_seen))

    def append_terminal(self, text):
        self.terminal.append(text)

    def update_client_row(self, client_info):
        for row in range(self.table.rowCount()):
            if int(self.table.item(row, 0).text()) == client_info.client_id:
                self.table.setItem(row, 4, QTableWidgetItem(client_info.last_seen))
                break

    def remove_client(self, cid):
        for row in range(self.table.rowCount()):
            if int(self.table.item(row, 0).text()) == cid:
                self.table.removeRow(row)
                break

    # -----------------------------
    # Command Sending
    # -----------------------------

    def send_command(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Erreur", "Sélectionne un client dans la liste.")
            return

        cid = int(self.table.item(selected, 0).text())
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return

        success = self.server.send_to_client(cid, cmd)

        if not success:
            QMessageBox.warning(self, "Erreur", "Impossible d'envoyer la commande.")

    # -----------------------------
    # JSON Handling
    # -----------------------------

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        if folder:
            self.json_folder = Path(folder)

    def load_json(self):
        file, _ = QFileDialog.getOpenFileName(self, "Ouvrir JSON", "", "JSON Files (*.json)")
        if not file:
            return

        with open(file, "r") as f:
            self.json_data = json.load(f)

        QMessageBox.information(self, "OK", "JSON chargé.")

    def save_json(self):
        if not self.json_folder:
            QMessageBox.warning(self, "Erreur", "Choisis un dossier client d'abord.")
            return

        file = self.json_folder / "clients.json"
        data = {}

        for cid, client in self.server.clients.items():
            data[str(cid)] = {
                "name": client.name,
                "os": client.os,
                "ip": client.addr[0],
                "last_seen": client.last_seen
            }

        with open(file, "w") as f:
            json.dump(data, f, indent=4)

        QMessageBox.information(self, "OK", f"Données sauvegardées dans {file}")


# -----------------------------
# App Start
# -----------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
