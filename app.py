import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import QProcess, Qt
from PyQt5.QtGui import QFont

# Import the main function from server module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.server import main as server_main

class ServerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.process = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Server Control App")
        self.setGeometry(100, 100, 600, 400)
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Server Control")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333333; background-color: transparent;")
        layout.addWidget(title)

        # Start Server Button
        self.start_button = QPushButton("▶ Start Server")
        self.start_button.clicked.connect(self.start_server)
        self.start_button.setProperty("class", "primary")
        layout.addWidget(self.start_button)

        # Stop Server Button
        self.stop_button = QPushButton("⏹ Stop Server")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setProperty("class", "danger")
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        # Status Label
        self.status_label = QLabel("🔴 Status: Stopped")
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)

        # Log Output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(150)
        layout.addWidget(self.log_output)

        # Clear Logs Button
        clear_logs_btn = QPushButton("🗑️ Clear Logs")
        clear_logs_btn.clicked.connect(self.log_output.clear)
        clear_logs_btn.setProperty("class", "secondary")
        layout.addWidget(clear_logs_btn)

        self.setLayout(layout)

    def start_server(self):
        """Start the server process"""
        try:
            if not self.process or self.process.state() != QProcess.Running:
                self.process = QProcess(self)
                self.process.readyReadStandardOutput.connect(self.handle_stdout)
                self.process.readyReadStandardError.connect(self.handle_stderr)
                self.process.stateChanged.connect(self.handle_state_change)
                self.process.finished.connect(self.handle_process_finished)

                # Use python to run the server module directly
                program = sys.executable
                arguments = ["-m", "src.server", "run"]
                self.process.start(program, arguments)

                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.status_label.setText("🟡 Status: Starting...")
                self.log_output.append("Starting server...\n")
            else:
                self.log_output.append("Server is already running.\n")
        except Exception as e:
            
            self.log_output.append(f"Failed to start server: {str(e)}\n")

    def stop_server(self):
        """Stop the server process"""
        if self.process and self.process.state() == QProcess.Running:
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("🔴 Status: Stopped")
            self.log_output.append("Server stopped.\n")

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.log_output.append(data)

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.log_output.append(data)

    def handle_state_change(self, state):
        if state == QProcess.NotRunning:
            self.status_label.setText("🔴 Status: Stopped")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        elif state == QProcess.Starting:
            self.status_label.setText("🟡 Status: Starting...")
        elif state == QProcess.Running:
            self.status_label.setText("🟢 Status: Running")

    def handle_process_finished(self, exit_code, exit_status):
        self.status_label.setText("🔴 Status: Stopped")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_output.append(f"Server process finished with exit code {exit_code}\n")

def main():
    app = QApplication(sys.argv)
    window = ServerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
