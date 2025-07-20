import sys
import os
import platform
import re
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QPushButton, QFileDialog,
    QLineEdit, QLabel, QFormLayout, QMessageBox, QProgressBar, QTextEdit, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import QProcess
from PyQt5.QtGui import QTextCursor

ENV_FILE = ".env"


def read_env():
    """Return dict of env vars from .env (simple KEY=VALUE)."""
    data = {}
    if not os.path.exists(ENV_FILE):
        return data
    with open(ENV_FILE) as f:
        for line in f.read().splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                data[k] = v
    return data


def write_env(data: dict):
    """Write dict to .env as KEY=VALUE."""
    with open(ENV_FILE, 'w') as f:
        for k, v in data.items():
            f.write(f"{k}={v}\n")


class SetupTab(QWidget):
    # unchanged...
    pass


class ConfigTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        form = QFormLayout()

        # Static config fields
        env = read_env()
        self.ngrok_key = QLineEdit(env.get("NGROK_AUTH_TOKEN", ""))
        self.groq_key = QLineEdit(env.get("GROQ_API_KEY", ""))
        self.excel_path = QLineEdit(env.get("EXCEL_FILE_PATH", ""))
        self.excel_path.setReadOnly(True)
        self.excel_btn = QPushButton("Select Excel")
        self.excel_btn.clicked.connect(self.select_excel)

        form.addRow(QLabel("Ngrok Auth Token:"), self.ngrok_key)
        form.addRow(QLabel("GROQ API Key:"), self.groq_key)
        form.addRow(QLabel("Excel File Path:"), self.excel_path)
        form.addRow(self.excel_btn)

        # Connected user entry
        self.conn_user_name = QLineEdit()
        self.conn_user_location = QLineEdit()
        form.addRow(QLabel("Connected User Name:"), self.conn_user_name)
        form.addRow(QLabel("Connected User Location:"), self.conn_user_location)

        # Save button
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.clicked.connect(self.save_config)

        # Allowed users table
        self.user_table = QTableWidget(0, 2)
        self.user_table.setHorizontalHeaderLabels(["User Name", "Location"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(form)
        layout.addWidget(self.save_btn)
        layout.addWidget(QLabel("Allowed Users:"))
        layout.addWidget(self.user_table)
        self.setLayout(layout)

        # Load users from JSON in .env
        self.users = []
        users_json = env.get("ALLOWED_USERS", "[]")
        try:
            self.users = json.loads(users_json)
        except Exception:
            self.users = []
        for u in self.users:
            self.add_user_row(u['name'], u.get('location', ''))

    def select_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.excel_path.setText(file_path)

    def add_user_row(self, name, location):
        row = self.user_table.rowCount()
        self.user_table.insertRow(row)
        self.user_table.setItem(row, 0, QTableWidgetItem(name))
        self.user_table.setItem(row, 1, QTableWidgetItem(location))

    def save_config(self):
        # validate
        uname = self.conn_user_name.text().strip()
        uloc = self.conn_user_location.text().strip()
        if not uname:
            QMessageBox.warning(self, "Validation Error", "Connected user name cannot be empty.")
            return
        if any(u['name'] == uname for u in self.users):
            QMessageBox.warning(self, "Validation Error", "This user name already exists.")
            return
        # append
        self.users.append({'name': uname, 'location': uloc})
        self.add_user_row(uname, uloc)

        # build env dict
        env_data = {
            "NGROK_AUTH_TOKEN": self.ngrok_key.text().strip(),
            "GROQ_API_KEY": self.groq_key.text().strip(),    
            "EXCEL_FILE_PATH": self.excel_path.text().strip(),
            "ALLOWED_USERS": json.dumps(self.users)
        }
        write_env(env_data)
        QMessageBox.information(self, "Saved", "Configuration and users saved successfully.")


class ConnectTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        ctrl_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Server")
        self.start_button.clicked.connect(self.start_server)
        self.stop_button = QPushButton("Stop Server")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setEnabled(False)
        self.status_label = QLabel("Status: Stopped")
        ctrl_layout.addWidget(self.start_button)
        ctrl_layout.addWidget(self.stop_button)
        ctrl_layout.addWidget(self.status_label)

        pwd_layout = QHBoxLayout()
        self.pwd_field = QLineEdit()
        self.pwd_field.setReadOnly(True)
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.pwd_field.text()))
        pwd_layout.addWidget(QLabel("App Password:"))
        pwd_layout.addWidget(self.pwd_field)
        pwd_layout.addWidget(self.copy_btn)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        layout.addLayout(ctrl_layout)
        layout.addLayout(pwd_layout)
        layout.addWidget(QLabel("Logs:"))
        layout.addWidget(self.log_output)
        self.setLayout(layout)

    def start_server(self):
        self.log_output.clear()
        self.pwd_field.clear()

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_server_output)
        self.process.readyReadStandardError.connect(self.handle_server_output)
        self.process.finished.connect(self.handle_finished)

        program = sys.executable
        args = ["server.py"]
        self.process.start(program, args)

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Status: Running")

    def stop_server(self):
        if hasattr(self, 'process') and self.process.state() == QProcess.Running:
            self.process.terminate()
            self.process.waitForFinished(3000)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Status: Stopped")

    def handle_server_output(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.log_output.append(data)
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_output.setTextCursor(cursor)
        # Search entire log for password
        full_text = self.log_output.toPlainText()
        match = re.search(r"app password(?: is)?\s*:\s*(\w+)", full_text, re.IGNORECASE)
        if match:
            self.pwd_field.setText(match.group(1))

    def handle_finished(self, exitCode, exitStatus):
        self.status_label.setText("Status: Stopped")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_output.append(f"Server exited with code {exitCode}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Device Connector")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.setup_tab = SetupTab()
        self.config_tab = ConfigTab()
        self.connect_tab = ConnectTab()

        self.tabs.addTab(self.setup_tab, "Setup")
        self.tabs.addTab(self.config_tab, "Configuration")
        self.tabs.addTab(self.connect_tab, "Connect Devices")

        layout.addWidget(self.tabs)
        self.setLayout(layout)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
