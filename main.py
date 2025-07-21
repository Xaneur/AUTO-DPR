import sys
import os
import platform
import re
import json
import subprocess
import webbrowser
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QPushButton, QFileDialog,
    QLineEdit, QLabel, QFormLayout, QMessageBox, QProgressBar, QTextEdit, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QSpacerItem, QSizePolicy,
    QFrame, QGridLayout
)
from PyQt5.QtCore import QProcess, Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QTextCursor, QFont, QPalette, QColor, QFontDatabase

from validation.api_validator import is_ngrok_authtoken_valid, is_groq_key_valid

ENV_FILE = ".env"

# Enhanced styling with system fonts
STYLE_SHEET = """
QWidget {
    background-color: #f5f5f5;
    font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
    font-size: 10pt;
    color: #333333;
}

QTabWidget::pane {
    border: 1px solid #c0c0c0;
    background-color: white;
    border-radius: 5px;
    color: #333333;
}

QTabBar::tab {
    background-color: #e1e1e1;
    border: 1px solid #c0c0c0;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    color: #333333;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom: 1px solid white;
    color: #333333;
}

QTabBar::tab:hover {
    background-color: #d1d1d1;
    color: #333333;
}

QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

QPushButton.danger {
    background-color: #d13438;
}

QPushButton.danger:hover {
    background-color: #b02a2f;
}

QPushButton.success {
    background-color: #107c10;
}

QPushButton.success:hover {
    background-color: #0e6e0e;
}

QPushButton.secondary {
    background-color: #6c757d;
}

QPushButton.secondary:hover {
    background-color: #5a6268;
}

QPushButton.link {
    background-color: transparent;
    color: #0078d4;
    border: 1px solid #0078d4;
    text-decoration: underline;
    padding: 4px 8px;
    min-width: 60px;
}

QPushButton.link:hover {
    background-color: #e7f3ff;
    color: #005a9e;
}

QLineEdit {
    border: 1px solid #d1d1d1;
    border-radius: 4px;
    padding: 8px;
    background-color: white;
    font-size: 10pt;
    color: #333333;
}

QLineEdit:focus {
    border: 2px solid #0078d4;
    color: #333333;
}

QLineEdit:read-only {
    background-color: #f8f9fa;
    color: #6c757d;
}

QTextEdit {
    border: 1px solid #d1d1d1;
    border-radius: 4px;
    background-color: white;
    padding: 8px;
    font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
    color: #333333;
}

QLabel {
    color: #333333;
    font-weight: 500;
    background-color: transparent;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #d1d1d1;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    color: #333333;
    background-color: transparent;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    color: #333333;
    background-color: transparent;
}

QTableWidget {
    border: 1px solid #d1d1d1;
    border-radius: 4px;
    background-color: white;
    gridline-color: #e1e1e1;
    selection-background-color: #0078d4;
    color: #333333;
}

QTableWidget::item {
    padding: 8px;
    color: #333333;
    background-color: white;
}

QTableWidget::item:selected {
    background-color: #0078d4;
    color: white;
}

QHeaderView::section {
    background-color: #f8f9fa;
    padding: 8px;
    border: 1px solid #d1d1d1;
    font-weight: bold;
    color: #333333;
}

QProgressBar {
    border: 1px solid #d1d1d1;
    border-radius: 4px;
    background-color: #f8f9fa;
    text-align: center;
    color: #333333;
}

QProgressBar::chunk {
    background-color: #107c10;
    border-radius: 3px;
}

QFrame.separator {
    border: none;
    border-top: 1px solid #d1d1d1;
    margin: 10px 0;
}
"""


class InstallationWorker(QThread):
    """Worker thread for running installation scripts"""
    progress_update = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path
        
    def run(self):
        try:
            self.progress_update.emit("Starting installation...")
            
            # Simulate some progress steps
            steps = [
                "Checking system requirements...",
                "Downloading dependencies...",
                "Installing packages...",
                "Configuring environment...",
                "Finalizing installation..."
            ]
            
            process = subprocess.Popen(
                self.script_path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            step_index = 0
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.progress_update.emit(output.strip())
                    
                # Simulate progress steps
                if step_index < len(steps):
                    self.progress_update.emit(steps[step_index])
                    step_index += 1
                    time.sleep(0.5)
            
            return_code = process.poll()
            
            if return_code == 0:
                self.progress_update.emit("Installation completed successfully! ✅")
                self.finished_signal.emit(True, "Installation completed successfully!")
            else:
                error_msg = f"Installation failed with exit code {return_code}"
                self.progress_update.emit(f"Installation failed! ❌")
                self.finished_signal.emit(False, error_msg)
                
        except Exception as e:
            error_msg = f"Installation error: {str(e)}"
            self.progress_update.emit(f"Error: {error_msg}")
            self.finished_signal.emit(False, error_msg)


def read_env():
    """Return dict of env vars from .env (simple KEY=VALUE)."""
    data = {}
    if not os.path.exists(ENV_FILE):
        return data
    with open(ENV_FILE, 'r') as f:
        for line in f.read().splitlines():
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                data[k.strip()] = v.strip()
    return data


def write_env(data: dict):
    """Write dict to .env as KEY=VALUE."""
    with open(ENV_FILE, 'w') as f:
        for k, v in data.items():
            f.write(f"{k}={v}\n")

class SetupTab(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("System Setup")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333333; background-color: transparent;")
        layout.addWidget(title)

        # Setup group
        setup_group = QGroupBox("Installation")
        setup_layout = QVBoxLayout()

        description = QLabel("Click the button below to run the installation script for your operating system.")
        description.setWordWrap(True)
        setup_layout.addWidget(description)

        self.install_button = QPushButton("🔧 Run Installation")
        self.install_button.clicked.connect(self.run_install_script)
        self.install_button.setMinimumHeight(40)
        setup_layout.addWidget(self.install_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        setup_layout.addWidget(self.progress_bar)

        # Installation logs
        self.log_output = QTextEdit()
        self.log_output.setVisible(False)
        self.log_output.setMaximumHeight(200)
        self.log_output.setReadOnly(True)
        setup_layout.addWidget(self.log_output)

        # Clear logs button
        self.clear_logs_btn = QPushButton("🗑️ Clear Logs")
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        self.clear_logs_btn.setProperty("class", "secondary")
        self.clear_logs_btn.setVisible(False)
        setup_layout.addWidget(self.clear_logs_btn)

        setup_group.setLayout(setup_layout)
        layout.addWidget(setup_group)

        # Add spacer
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.setLayout(layout)

    def run_install_script(self):
        try:
            os_type = platform.system()
            if os_type == "Windows":
                script_path = "setup_scripts/install_windows.bat"
            elif os_type == "Darwin":
                script_path = "setup_scripts/install_mac.sh"
            elif os_type == "Linux":
                script_path = "setup_scripts/install_linux.sh"
            else:
                QMessageBox.warning(self, "Unsupported OS", f"Operating system '{os_type}' is not supported.")
                return

            if not os.path.exists(script_path):
                QMessageBox.warning(self, "Script Missing", f"Installation script not found: {script_path}")
                return

            # Show progress elements
            self.progress_bar.setVisible(True)
            self.log_output.setVisible(True)
            self.clear_logs_btn.setVisible(True)
            self.log_output.clear()
            
            # Disable install button
            self.install_button.setEnabled(False)
            self.install_button.setText("🔄 Installing...")

            # Start worker thread
            self.worker = InstallationWorker(script_path)
            self.worker.progress_update.connect(self.update_log)
            self.worker.finished_signal.connect(self.installation_finished)
            self.worker.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during installation: {str(e)}")
            self.reset_ui()

    def update_log(self, message):
        """Update the log output with new message"""
        self.log_output.append(message)
        
        # Auto-scroll to bottom
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_output.setTextCursor(cursor)

    def installation_finished(self, success, message):
        """Handle installation completion"""
        self.progress_bar.setVisible(False)
        self.install_button.setEnabled(True)
        self.install_button.setText("🔧 Run Installation")
        
        if success:
            QMessageBox.information(self, "Installation Complete", message)
            # Auto-clear logs after 3 seconds on success
            QTimer.singleShot(3000, self.clear_logs)
        else:
            QMessageBox.critical(self, "Installation Failed", message)

    def clear_logs(self):
        """Clear the log output"""
        self.log_output.clear()
        self.log_output.setVisible(False)
        self.clear_logs_btn.setVisible(False)

    def reset_ui(self):
        """Reset UI to initial state"""
        self.progress_bar.setVisible(False)
        self.install_button.setEnabled(True)
        self.install_button.setText("🔧 Run Installation")

class ConfigTab(QWidget):
    def __init__(self):
        super().__init__()
        self.users = []
        self.init_ui()
        self.load_config()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Configuration")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333333; background-color: transparent;")
        layout.addWidget(title)

        # API Configuration Group
        api_group = QGroupBox("API Configuration")
        api_layout = QFormLayout()
        api_layout.setSpacing(10)

        # Ngrok configuration with help link and validation
        ngrok_layout = QHBoxLayout()
        self.ngrok_key = QLineEdit()
        self.ngrok_key.setPlaceholderText("Enter your Ngrok authentication token")
        
        ngrok_help_btn = QPushButton("🔗 Get Token")
        ngrok_help_btn.setProperty("class", "link")
        ngrok_help_btn.clicked.connect(lambda: webbrowser.open("https://dashboard.ngrok.com/get-started/your-authtoken"))
        
        self.ngrok_validate_btn = QPushButton("✅ Validate")
        self.ngrok_validate_btn.setProperty("class", "secondary")
        self.ngrok_validate_btn.clicked.connect(self.validate_ngrok_token)
        
        # Ngrok status label
        self.ngrok_status_label = QLabel("")
        self.ngrok_status_label.setMaximumHeight(20)
        
        ngrok_layout.addWidget(self.ngrok_key, 3)
        ngrok_layout.addWidget(ngrok_help_btn, 1)
        ngrok_layout.addWidget(self.ngrok_validate_btn, 1)
        
        # GROQ configuration with help link and validation
        groq_layout = QHBoxLayout()
        self.groq_key = QLineEdit()
        self.groq_key.setPlaceholderText("Enter your GROQ API key")
        self.groq_key.setEchoMode(QLineEdit.Password)
        
        groq_help_btn = QPushButton("🔗 Get API Key")
        groq_help_btn.setProperty("class", "link")
        groq_help_btn.clicked.connect(lambda: webbrowser.open("https://console.groq.com/keys"))
        
        self.groq_validate_btn = QPushButton("✅ Validate")
        self.groq_validate_btn.setProperty("class", "secondary")
        self.groq_validate_btn.clicked.connect(self.validate_groq_key)
        
        # GROQ status label
        self.groq_status_label = QLabel("")
        self.groq_status_label.setMaximumHeight(20)
        
        groq_layout.addWidget(self.groq_key, 3)
        groq_layout.addWidget(groq_help_btn, 1)
        groq_layout.addWidget(self.groq_validate_btn, 1)

        # Add rows to form layout with status labels
        api_layout.addRow("Ngrok Auth Token:", ngrok_layout)
        api_layout.addRow("", self.ngrok_status_label)
        api_layout.addRow("GROQ API Key:", groq_layout)
        api_layout.addRow("", self.groq_status_label)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # File Configuration Group
        file_group = QGroupBox("File Configuration")
        file_layout = QVBoxLayout()
        
        file_row = QHBoxLayout()
        self.excel_path = QLineEdit()
        self.excel_path.setReadOnly(True)
        self.excel_path.setPlaceholderText("No Excel file selected")
        self.excel_btn = QPushButton("📁 Select Excel File")
        self.excel_btn.clicked.connect(self.select_excel)
        
        file_row.addWidget(QLabel("Excel File Path:"))
        file_row.addWidget(self.excel_path)
        file_row.addWidget(self.excel_btn)
        file_layout.addLayout(file_row)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # User Management Group
        user_group = QGroupBox("Authorized Users Management")
        user_layout = QVBoxLayout()

        # Add user section
        add_user_layout = QHBoxLayout()
        self.conn_user_name = QLineEdit()
        self.conn_user_name.setPlaceholderText("Enter user name")
        self.conn_user_location = QLineEdit()
        self.conn_user_location.setPlaceholderText("Enter user location")
        
        self.add_user_btn = QPushButton("➕ Add User")
        self.add_user_btn.clicked.connect(self.add_user)
        self.add_user_btn.setProperty("class", "success")
        
        add_user_layout.addWidget(QLabel("Name:"))
        add_user_layout.addWidget(self.conn_user_name)
        add_user_layout.addWidget(QLabel("Location:"))
        add_user_layout.addWidget(self.conn_user_location)
        add_user_layout.addWidget(self.add_user_btn)

        user_layout.addLayout(add_user_layout)

        # Users table
        self.user_table = QTableWidget(0, 2)
        self.user_table.setHorizontalHeaderLabels(["User Name", "Location"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.user_table.setMinimumHeight(200)

        # Table buttons
        table_btn_layout = QHBoxLayout()
        self.delete_user_btn = QPushButton("🗑️ Delete Selected")
        self.delete_user_btn.clicked.connect(self.delete_user)
        self.delete_user_btn.setProperty("class", "danger")
        self.delete_user_btn.setEnabled(False)
        
        self.clear_users_btn = QPushButton("🔄 Clear All")
        self.clear_users_btn.clicked.connect(self.clear_all_users)
        self.clear_users_btn.setProperty("class", "secondary")
        
        table_btn_layout.addWidget(self.delete_user_btn)
        table_btn_layout.addWidget(self.clear_users_btn)
        table_btn_layout.addStretch()

        user_layout.addWidget(self.user_table)
        user_layout.addLayout(table_btn_layout)
        user_group.setLayout(user_layout)
        layout.addWidget(user_group)

        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_btn = QPushButton("💾 Save Configuration")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setMinimumHeight(40)
        save_layout.addWidget(self.save_btn)
        save_layout.addStretch()
        layout.addLayout(save_layout)

        # Connect table selection changed signal
        self.user_table.selectionModel().selectionChanged.connect(self.on_selection_changed)

        self.setLayout(layout)

    def validate_ngrok_token(self):
        """Validate Ngrok authentication token"""
        token = self.ngrok_key.text().strip()
        
        if not token:
            self.ngrok_status_label.setText("❌ Please enter a token first")
            self.ngrok_status_label.setStyleSheet("color: #d13438; font-weight: bold;")
            return
        
        # Disable button and show loading
        self.ngrok_validate_btn.setEnabled(False)
        self.ngrok_validate_btn.setText("🔄 Validating...")
        self.ngrok_status_label.setText("🔄 Validating token...")
        self.ngrok_status_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        
        # Process events to update UI
        QApplication.processEvents()
        
        try:
            # Call the validation function
            is_valid = is_ngrok_authtoken_valid(token)
            
            if is_valid:
                self.ngrok_status_label.setText("✅ Valid token")
                self.ngrok_status_label.setStyleSheet("color: #107c10; font-weight: bold;")
                QMessageBox.information(self, "Validation Success", "Ngrok authentication token is valid!")
            else:
                self.ngrok_status_label.setText("❌ Invalid token")
                self.ngrok_status_label.setStyleSheet("color: #d13438; font-weight: bold;")
                QMessageBox.warning(self, "Validation Failed", "Ngrok authentication token is invalid!")
                
        except Exception as e:
            self.ngrok_status_label.setText("❌ Validation error")
            self.ngrok_status_label.setStyleSheet("color: #d13438; font-weight: bold;")
            QMessageBox.critical(self, "Validation Error", f"Error validating Ngrok token: {str(e)}")
        
        finally:
            # Re-enable button
            self.ngrok_validate_btn.setEnabled(True)
            self.ngrok_validate_btn.setText("✅ Validate")

    def validate_groq_key(self):
        """Validate GROQ API key"""
        api_key = self.groq_key.text().strip()
        
        if not api_key:
            self.groq_status_label.setText("❌ Please enter an API key first")
            self.groq_status_label.setStyleSheet("color: #d13438; font-weight: bold;")
            return
        
        # Disable button and show loading
        self.groq_validate_btn.setEnabled(False)
        self.groq_validate_btn.setText("🔄 Validating...")
        self.groq_status_label.setText("🔄 Validating API key...")
        self.groq_status_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        
        # Process events to update UI
        QApplication.processEvents()
        
        try:
            # Call the validation function
            is_valid = is_groq_key_valid(api_key)
            
            if is_valid:
                self.groq_status_label.setText("✅ Valid API key")
                self.groq_status_label.setStyleSheet("color: #107c10; font-weight: bold;")
                QMessageBox.information(self, "Validation Success", "GROQ API key is valid!")
            else:
                self.groq_status_label.setText("❌ Invalid API key")
                self.groq_status_label.setStyleSheet("color: #d13438; font-weight: bold;")
                QMessageBox.warning(self, "Validation Failed", "GROQ API key is invalid!")
                
        except Exception as e:
            self.groq_status_label.setText("❌ Validation error")
            self.groq_status_label.setStyleSheet("color: #d13438; font-weight: bold;")
            QMessageBox.critical(self, "Validation Error", f"Error validating GROQ API key: {str(e)}")
        
        finally:
            # Re-enable button
            self.groq_validate_btn.setEnabled(True)
            self.groq_validate_btn.setText("✅ Validate")

    def load_config(self):
        """Load configuration from .env file"""
        env = read_env()
        self.ngrok_key.setText(env.get("NGROK_AUTH_TOKEN", ""))
        self.groq_key.setText(env.get("GROQ_API_KEY", ""))
        self.excel_path.setText(env.get("EXCEL_FILE_PATH", ""))
        
        # Clear status labels when loading
        self.ngrok_status_label.setText("")
        self.groq_status_label.setText("")
        
        # Load users from JSON in .env
        users_json = env.get("ALLOWED_USERS", "[]")
        try:
            self.users = json.loads(users_json)
        except (json.JSONDecodeError, TypeError):
            self.users = []
        
        # Populate table
        self.refresh_user_table()

    def select_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Excel File", 
            "", 
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if file_path:
            self.excel_path.setText(file_path)

    def add_user(self):
        """Add a new user to the authorized users list"""
        name = self.conn_user_name.text().strip()
        location = self.conn_user_location.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "User name cannot be empty.")
            return
        
        if any(u['name'].lower() == name.lower() for u in self.users):
            QMessageBox.warning(self, "Validation Error", "This user name already exists.")
            return
        
        # Add user
        self.users.append({'name': name, 'location': location})
        self.refresh_user_table()
        
        # Clear input fields
        self.conn_user_name.clear()
        self.conn_user_location.clear()
        
        QMessageBox.information(self, "User Added", f"User '{name}' has been added successfully.")

    def delete_user(self):
        """Delete selected user from the authorized users list"""
        current_row = self.user_table.currentRow()
        if current_row >= 0:
            user_name = self.user_table.item(current_row, 0).text()
            reply = QMessageBox.question(
                self, 
                "Confirm Deletion", 
                f"Are you sure you want to delete user '{user_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                del self.users[current_row]
                self.refresh_user_table()
                QMessageBox.information(self, "User Deleted", f"User '{user_name}' has been deleted.")

    def clear_all_users(self):
        """Clear all users from the authorized users list"""
        if not self.users:
            QMessageBox.information(self, "No Users", "There are no users to clear.")
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Clear All",
            "Are you sure you want to remove all authorized users?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.users.clear()
            self.refresh_user_table()
            QMessageBox.information(self, "Users Cleared", "All users have been removed.")

    def refresh_user_table(self):
        """Refresh the user table with current users list"""
        self.user_table.setRowCount(0)
        for user in self.users:
            self.add_user_row(user['name'], user.get('location', ''))

    def add_user_row(self, name, location):
        """Add a row to the user table"""
        row = self.user_table.rowCount()
        self.user_table.insertRow(row)
        self.user_table.setItem(row, 0, QTableWidgetItem(name))
        self.user_table.setItem(row, 1, QTableWidgetItem(location))

    def on_selection_changed(self):
        """Handle table selection changes"""
        has_selection = bool(self.user_table.selectionModel().selectedRows())
        self.delete_user_btn.setEnabled(has_selection)

    def save_config(self):
        """Save configuration to .env file"""
        # Validate required fields
        if not self.ngrok_key.text().strip():
            QMessageBox.warning(self, "Validation Error", "Ngrok Auth Token is required.")
            return
        
        if not self.groq_key.text().strip():
            QMessageBox.warning(self, "Validation Error", "GROQ API Key is required.")
            return

        # Build env dict
        env_data = {
            "NGROK_AUTH_TOKEN": self.ngrok_key.text().strip(),
            "GROQ_API_KEY": self.groq_key.text().strip(),
            "EXCEL_FILE_PATH": self.excel_path.text().strip(),
            "ALLOWED_USERS": json.dumps(self.users, indent=None, separators=(',', ':'))
        }
        
        try:
            write_env(env_data)
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")

class ConnectTab(QWidget):
    def __init__(self):
        super().__init__()
        self.process = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Device Connection")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333333; background-color: transparent;")
        layout.addWidget(title)

        # Server Control Group
        control_group = QGroupBox("Server Control")
        control_layout = QVBoxLayout()

        # Status and control buttons
        status_layout = QHBoxLayout()
        self.status_label = QLabel("🔴 Status: Stopped")
        self.status_label.setFont(QFont("Arial", 11, QFont.Bold))
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("▶️ Start Server")
        self.start_button.clicked.connect(self.start_server)
        self.start_button.setProperty("class", "success")
        
        self.stop_button = QPushButton("⏹️ Stop Server")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setProperty("class", "danger")
        self.stop_button.setEnabled(False)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()

        control_layout.addLayout(status_layout)
        control_layout.addLayout(button_layout)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # Password Group
        pwd_group = QGroupBox("Connection Information")
        pwd_layout = QHBoxLayout()
        
        pwd_layout.addWidget(QLabel("App Password:"))
        self.pwd_field = QLineEdit()
        self.pwd_field.setReadOnly(True)
        self.pwd_field.setPlaceholderText("Password will appear here when server starts")
        
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.clicked.connect(self.copy_password)
        self.copy_btn.setProperty("class", "secondary")
        
        pwd_layout.addWidget(self.pwd_field)
        pwd_layout.addWidget(self.copy_btn)
        pwd_group.setLayout(pwd_layout)
        layout.addWidget(pwd_group)

        # Logs Group
        logs_group = QGroupBox("Server Logs")
        logs_layout = QVBoxLayout()
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(300)
        
        log_controls = QHBoxLayout()
        self.clear_logs_btn = QPushButton("🗑️ Clear Logs")
        self.clear_logs_btn.clicked.connect(self.log_output.clear)
        self.clear_logs_btn.setProperty("class", "secondary")
        log_controls.addWidget(self.clear_logs_btn)
        log_controls.addStretch()
        
        logs_layout.addWidget(self.log_output)
        logs_layout.addLayout(log_controls)
        logs_group.setLayout(logs_layout)
        layout.addWidget(logs_group)

        self.setLayout(layout)

    def copy_password(self):
        """Copy password to clipboard"""
        password = self.pwd_field.text()
        if password:
            QApplication.clipboard().setText(password)
            QMessageBox.information(self, "Copied", "Password copied to clipboard!")
        else:
            QMessageBox.warning(self, "No Password", "No password available to copy.")

    def start_server(self):
        """Start the server process"""
        if not os.path.exists("server.py"):
            QMessageBox.warning(self, "Server Not Found", "server.py file not found in the current directory.")
            return

        self.log_output.clear()
        self.pwd_field.clear()

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_server_output)
        self.process.finished.connect(self.handle_finished)

        program = sys.executable
        args = ["server.py"]
        
        try:
            self.process.start(program, args)
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("🟡 Status: Starting...")
            self.log_output.append("Starting server...\n")
            
        except Exception as e:
            QMessageBox.critical(self, "Start Error", f"Failed to start server: {str(e)}")

    def stop_server(self):
        """Stop the server process"""
        if self.process and self.process.state() == QProcess.Running:
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()
                self.log_output.append("Server process was forcefully terminated.\n")
            else:
                self.log_output.append("Server stopped gracefully.\n")
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("🔴 Status: Stopped")

    def handle_server_output(self):
        """Handle server output"""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
            self.log_output.append(data)
            
            # Auto-scroll to bottom
            cursor = self.log_output.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_output.setTextCursor(cursor)
            
            # Update status when server is running
            if "running" in data.lower() or "started" in data.lower():
                self.status_label.setText("🟢 Status: Running")
            
            # Extract password from logs
            full_text = self.log_output.toPlainText()
            match = re.search(r"app password(?:\s+is)?\s*:?\s*(\w+)", full_text, re.IGNORECASE)
            if match:
                self.pwd_field.setText(match.group(1))

    def handle_finished(self, exit_code, exit_status):
        """Handle server process finishing"""
        self.status_label.setText("🔴 Status: Stopped")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_output.append(f"\nServer process exited with code {exit_code}\n")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Update Data Using AI")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)

        # Apply custom stylesheet
        self.setStyleSheet(STYLE_SHEET)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Main tabs
        self.tabs = QTabWidget()
        
        self.setup_tab = SetupTab()
        self.config_tab = ConfigTab()
        self.connect_tab = ConnectTab()

        self.tabs.addTab(self.setup_tab, "🔧 Setup")
        self.tabs.addTab(self.config_tab, "⚙️ Configuration")
        self.tabs.addTab(self.connect_tab, "🔗 Connect Devices")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def closeEvent(self, event):
        """Handle application closing"""
        # Stop server if running
        if hasattr(self.connect_tab, 'process') and self.connect_tab.process:
            if self.connect_tab.process.state() == QProcess.Running:
                reply = QMessageBox.question(
                    self,
                    "Server Running",
                    "The server is still running. Do you want to stop it and exit?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self.connect_tab.stop_server()
                else:
                    event.ignore()
                    return
        
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Update Data Using AI")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Device Connector")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()