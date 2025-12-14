import sys
import socket
import threading
import time
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
    QMessageBox, QHeaderView, QTextEdit
)
from PyQt6.QtCore import Qt

# -----------------------------
# CONFIGURATION (à modifier)
# -----------------------------
RELAY_HOST = "5.tcp.eu.ngrok.io"  # adresse Ngrok TCP
RELAY_PORT = 17229                # port Ngrok TCP
RELAY_PASS = ""                   # mot de passe si Ngrok en a un
# -----------------------------

class ClientInfo:
    def __init__(self, client_id, sock, addr):
        self.client_id = client_id
        self.sock = sock
        self.addr = addr
        self.name = "Unknown"
        self.os = "Unknown"
        self.last_seen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class RelayThread(threading.Thread):
    """Thread qui connecte le serveur au relay et gère les clients TCP"""
    def __init__(self, gui):
        super().__init__(daemon=True)
        self.gui = gui
        self.running = True
        self.clients = {}
        self.client_counter = 0
        self.sock = None

    def run(self):
        while self.running:
            try:
                print(f"[INFO] Connexion au relay {RELAY_HOST}:{RELAY_PORT} …")
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((RELAY_HOST, RELAY_PORT))
                print("[INFO] Connecté au relay")
                threading.Thread(target=self.listen_relay, daemon=True).start()
                break
            except Exception as e:
                print(f"[ERROR] Impossible de se connecter, nouvelle tentative dans 5s … {e}")
                time.sleep(5)

    def listen_relay(self):
        """Écoute les clients qui se connectent via le relay"""
        while self.running:
            try:
                data = self.sock.recv(1024)
                if not data:
                    continue
                text = data.decode()
                self.client_counter += 1
                cid = self.client_counter
                client_info = ClientInfo(cid, self.sock, ("RELAY", 0))
                self.clients[cid] = client_info
                self.gui.add_client_to_table(client_info)
                self.gui.append_terminal(f"[Client {cid}] → {text}")
            except Exception as e:
                print(f"[ERROR] {e}")
                break

    def send_to_client(self, cid, message):
        if cid in self.clients:
            try:
                self.clients[cid].sock.send(message.encode())
                return True
            except:
                return False
        return False


# -----------------------------
# GUI
# -----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Server via Relay Ngrok")
        self.resize(900, 600)

        self.relay_thread = RelayThread(self)
        self.relay_thread.start()

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Terminal / Logs :"))
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        layout.addWidget(self.terminal)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Nom", "OS", "IP", "Dernière connexion"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        cmd_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Commande à envoyer (ex: PING, INFO …)")
        cmd_layout.addWidget(self.cmd_input)

        send_btn = QPushButton("Envoyer au client sélectionné")
        send_btn.clicked.connect(self.send_command)
        cmd_layout.addWidget(send_btn)

        layout.addLayout(cmd_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # -----------------------------
    # Méthodes GUI
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
# Lancement de l'application
# -----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
