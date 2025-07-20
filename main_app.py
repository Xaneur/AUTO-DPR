import sys
import subprocess
import threading
import queue
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                            QVBoxLayout, QWidget, QMessageBox, QTextEdit,
                            QHBoxLayout, QLabel)
from PyQt5.QtCore import QTextCodec, Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QTextCursor

class OutputReader(QObject):
    output_ready = pyqtSignal(str, bool)  
    
    def __init__(self, process):
        super().__init__()
        self.process = process
        self._stop = False
    
    def read_output(self):
        # Read from stdout
        for line in iter(self.process.stdout.readline, ''):
            if self._stop:
                break
            if line:
                self.output_ready.emit(line, False)
        
        # Read from stderr
        for line in iter(self.process.stderr.readline, ''):
            if self._stop:
                break
            if line:
                self.output_ready.emit(line, True)
    
    def stop(self):
        self._stop = True


class ServerControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Server Control")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize process
        self.process = None
        self.output_reader = None
        self.output_thread = None
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create control panel
        control_panel = QHBoxLayout()
        
        # Create button
        self.start_button = QPushButton("Start Server")
        self.start_button.clicked.connect(self.toggle_server)
        control_panel.addWidget(self.start_button)
        
        # Status label
        self.status_label = QLabel("Status: Stopped")
        control_panel.addWidget(self.status_label)
        control_panel.addStretch()
        
        # Add control panel to main layout
        main_layout.addLayout(control_panel)
        
        # Create log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("Server logs will appear here...")
        main_layout.addWidget(self.log_area)
        
        # Set text codec for process output
        self.codec = QTextCodec.codecForLocale()
        
        # Set initial state
        self.server_running = False
    
    def toggle_server(self):
        if not self.server_running:
            self.start_server()
        else:
            self.stop_server()
    
    def start_server(self):
        try:
            # Clear previous logs
            self.log_area.clear()
            self.append_log("Starting server...\n")
            
            # Start the process using subprocess
            self.process = subprocess.Popen(
                ["/bin/bash", "./setup.sh"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True
            )
            
            # Create and start output reader
            self.output_reader = OutputReader(self.process)
            self.output_reader.output_ready.connect(self.append_log)
            
            # Start output reader in a separate thread
            self.output_thread = threading.Thread(
                target=self.output_reader.read_output,
                daemon=True
            )
            self.output_thread.start()
            
            # Set up a timer to check if process is still running
            self.timer = QTimer()
            self.timer.timeout.connect(self.check_process_status)
            self.timer.start(100)  # Check every 100ms
            
            # Update UI
            self.server_running = True
            self.start_button.setText("Stop Server")
            self.status_label.setText("Status: Running")
            self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            error_msg = f"Error: Failed to start server: {str(e)}\n"
            self.append_log(error_msg, error=True)
            QMessageBox.critical(self, "Error", error_msg)
            self.cleanup()
    
    def check_process_status(self):
        if self.process and self.process.poll() is not None:
            # Process has finished
            self.server_stopped(self.process.returncode, 0)
            self.timer.stop()
    
    def append_log(self, text, error=False):
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Set text color based on error status
        if error:
            cursor.insertHtml(f'<span style="color: red;">{text}</span>')
        else:
            cursor.insertText(text)
            
        # Auto-scroll to bottom
        self.log_area.setTextCursor(cursor)
        self.log_area.ensureCursorVisible()
    
    def stop_server(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)  # Wait up to 5 seconds
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.cleanup()
    
    def cleanup(self):
        try:
            if hasattr(self, 'timer') and self.timer.isActive():
                self.timer.stop()
                
            if self.output_reader:
                self.output_reader.stop()
                self.output_reader = None
                
            if self.output_thread and self.output_thread.is_alive():
                self.output_thread.join(timeout=1.0)
                
            self.process = None
            self.server_running = False
            
            # Update UI
            self.start_button.setText("Start Server")
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet("")
            
        except Exception as e:
            self.append_log(f"Error during cleanup: {str(e)}\n", error=True)
    
    def server_stopped(self, exit_code, exit_status):
        try:
            # Update UI
            self.server_running = False
            self.start_button.setText("Start Server")
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet("")
            
            # Log exit status
            if exit_code == 0:
                self.append_log("\nServer stopped successfully.\n")
            else:
                self.append_log(f"\nServer process exited with code {exit_code}.\n", error=True)
            
        except Exception as e:
            self.append_log(f"Error during server stop: {str(e)}\n", error=True)
        finally:
            self.cleanup()

def main():
    app = QApplication(sys.argv)
    window = ServerControlApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
