import sys
import socket
import threading
import time
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog,
    QLineEdit, QLabel, QMessageBox, QHeaderView, QTextEdit
)

# -----------------------------
# CONFIGURATION NGROK RELAY
# -----------------------------
RELAY_HOST = "7.tcp.eu.ngrok.io"  # Remplace par ton host Ngrok
RELAY_PORT = 16420                 # Remplace par ton port Ngrok
RECONNECT_DELAY = 5                # secondes entre les tentatives

# -----------------------------
# CLIENT INFO
# -----------------------------
class ClientInfo:
    def __init__(self, client_id, sock, addr=None, name="RemoteClient", os="Unknown"):
        self.client_id = client_id
        self.sock = sock
        self.addr = addr or ("Relay", 0)
        self.name = name
        self.os = os
        self.last_seen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# -----------------------------
# THREAD RELAY
# -----------------------------
class RelayThread(threading.Thread):
    def __init__(self, gui):
        super().__init__(daemon=True)
        self.gui = gui
        self.sock = None
        self.running = True
        self.client_counter = 0
        self.clients = {}

    def run(self):
        while self.running:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print(f"[INFO] Connexion au relay {RELAY_HOST}:{RELAY_PORT} …")
                self.sock.connect((RELAY_HOST, RELAY_PORT))
                print("[INFO] Connecté au relay !")
                self.gui.append_terminal("[INFO] Connecté au relay !")

                # Commence à écouter les messages entrants
                self.listen_to_clients()
            except Exception as e:
                print(f"[ERROR] Impossible de se connecter, nouvelle tentative dans {RECONNECT_DELAY}s … {e}")
                self.gui.append_terminal(f"[ERROR] Impossible de se connecter, nouvelle tentative dans {RECONNECT_DELAY}s … {e}")
                time.sleep(RECONNECT_DELAY)

    def listen_to_clients(self):
        """Écoute et gère les messages entrants du relay (clients)"""
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break

                message = data.decode(errors='ignore')
                self.client_counter += 1
                cid = self.client_counter

                client_info = ClientInfo(cid, self.sock)
                self.clients[cid] = client_info
                self.gui.add_client_to_table(client_info)
                self.gui.append_terminal(f"[Client {cid}] → {message}")

            except Exception as e:
                print("[ERROR] Perte de connexion relay :", e)
                self.gui.append_terminal(f"[ERROR] Perte de connexion relay : {e}")
                break

        self.sock.close()
        self.clients.clear()
        self.gui.clear_clients()

    def send_to_client(self, cid, message):
        if cid in self.clients:
            try:
                self.clients[cid].sock.send(message.encode())
                return True
            except Exception as e:
                print("[ERROR] Impossible d'envoyer la commande :", e)
                return False
        return False

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()

# -----------------------------
# GUI
# -----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xa1om - Server GUI")
        self.resize(900, 600)

        self.json_folder = None
        self.json_data = {}

        self.relay_thread = RelayThread(self)
        self.relay_thread.start()

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Terminal
        layout.addWidget(QLabel("Terminal / Résultats :"))
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFixedHeight(180)
        layout.addWidget(self.terminal)

        # Table clients
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Nom", "OS", "IP", "Dernière connexion"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Command input
        cmd_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Entrez une commande (ex : PING, ECHO:Hello)")
        cmd_layout.addWidget(self.cmd_input)
        send_btn = QPushButton("Envoyer au client sélectionné")
        send_btn.clicked.connect(self.send_command)
        cmd_layout.addWidget(send_btn)
        layout.addLayout(cmd_layout)

        # JSON buttons
        json_layout = QHBoxLayout()
        btn_load = QPushButton("Charger JSON")
        btn_load.clicked.connect(self.load_json)
        btn_save = QPushButton("Sauvegarder JSON")
        btn_save.clicked.connect(self.save_json)
        btn_set_folder = QPushButton("Choisir dossier clients")
        btn_set_folder.clicked.connect(self.choose_folder)
        json_layout.addWidget(btn_load)
        json_layout.addWidget(btn_save)
        json_layout.addWidget(btn_set_folder)
        layout.addLayout(json_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # -----------------------------
    # Table clients
    # -----------------------------
    def add_client_to_table(self, client_info):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(client_info.client_id)))
        self.table.setItem(row, 1, QTableWidgetItem(client_info.name))
        self.table.setItem(row, 2, QTableWidgetItem(client_info.os))
        self.table.setItem(row, 3, QTableWidgetItem(str(client_info.addr[0])))
        self.table.setItem(row, 4, QTableWidgetItem(client_info.last_seen))

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

    def clear_clients(self):
        self.table.setRowCount(0)

    def append_terminal(self, text):
        self.terminal.append(text)

    # -----------------------------
    # Command sending
    # -----------------------------
    def send_command(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Erreur", "Sélectionnez un client dans la liste.")
            return

        cid = int(self.table.item(selected, 0).text())
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return

        success = self.relay_thread.send_to_client(cid, cmd)
        if not success:
            QMessageBox.warning(self, "Erreur", "Impossible d'envoyer la commande.")

    # -----------------------------
    # JSON
    # -----------------------------
    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        if folder:
            self.json_folder = Path(folder)

    def load_json(self):
        file, _ = QFileDialog.getOpenFileName(self, "Ouvrir JSON", "", "JSON Files (*.json)")
        if not file:
            return
        import json
        with open(file, "r") as f:
            self.json_data = json.load(f)
        QMessageBox.information(self, "OK", "JSON chargé.")

    def save_json(self):
        if not self.json_folder:
            QMessageBox.warning(self, "Erreur", "Choisir un dossier clients d'abord.")
            return
        import json
        file = self.json_folder / "clients.json"
        data = {}
        for cid, client in self.relay_thread.clients.items():
            data[str(cid)] = {
                "name": client.name,
                "os": client.os,
                "ip": str(client.addr[0]),
                "last_seen": client.last_seen
            }
        with open(file, "w") as f:
            json.dump(data, f, indent=4)
        QMessageBox.information(self, "OK", f"Données sauvegardées dans {file}")

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
