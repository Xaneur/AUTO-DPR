import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv, set_key
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QLabel, QLineEdit, QPushButton, QTabWidget,
                            QTextEdit, QComboBox, QMessageBox, QFileDialog, QStatusBar,
                            QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sounddevice as sd
import soundfile as sf
import numpy as np
import whisper
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import DPR functionality
sys.path.append(str(Path(__file__).parent.parent))
from src.main import updated_quantity_in_sheet
from src.sheet_data_fetch import get_available_sheets

class AudioRecorder(QThread):
    """Thread for handling audio recording"""
    update_signal = pyqtSignal(str)
    
    def __init__(self, sample_rate=16000, channels=1):
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.frames = []
        self.stream = None
        self.recording = []
        self.model = whisper.load_model("base")
    
    def run(self):
        self.is_recording = True
        self.recording = []
        
        def callback(indata, frames, time, status):
            if status:
                print(status, file=sys.stderr)
            self.recording.append(indata.copy())
        
        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, 
                          callback=callback, dtype='float32'):
            while self.is_recording:
                sd.sleep(100)
    
    def stop(self):
        self.is_recording = False
        if len(self.recording) > 0:
            audio_data = np.concatenate(self.recording, axis=0)
            self.transcribe_audio(audio_data)
    
    def transcribe_audio(self, audio_data):
        try:
            # Save to temporary file
            temp_file = "temp_recording.wav"
            sf.write(temp_file, audio_data, self.sample_rate)
            
            # Transcribe using Whisper
            result = self.model.transcribe(temp_file)
            self.update_signal.emit(result["text"])
            
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
        except Exception as e:
            self.update_signal.emit(f"Error in transcription: {str(e)}")

class ApiKeyTab(QWidget):
    """Tab for managing API keys and user information"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.env_path = Path(__file__).parent.parent / ".env"
        self.init_ui()
        self.load_existing_settings()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # API Key Section
        key_group = QWidget()
        key_layout = QVBoxLayout(key_group)
        
        # API Key Input
        key_input_layout = QHBoxLayout()
        key_input_layout.addWidget(QLabel("Groq API Key:"))
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.Password)
        key_input_layout.addWidget(self.key_input)
        
        # Toggle password visibility
        self.show_key_btn = QPushButton("👁️")
        self.show_key_btn.setFixedWidth(40)
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.clicked.connect(self.toggle_key_visibility)
        key_input_layout.addWidget(self.show_key_btn)
        
        key_layout.addLayout(key_input_layout)
        
        # User Information Section
        user_group = QWidget()
        user_layout = QFormLayout(user_group)
        
        # Name Input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Your Name")
        user_layout.addRow("Your Name:", self.name_input)
        
        # Location Input
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Your Location")
        user_layout.addRow("Your Location:", self.location_input)
        
        # Add sections to main layout
        layout.addWidget(self.create_group_box("API Settings", key_group))
        layout.addWidget(self.create_group_box("User Information", user_group))
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(self.save_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_fields)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def create_group_box(self, title, widget):
        """Helper method to create a group box with a title"""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.addWidget(widget)
        return group
    
    def toggle_key_visibility(self):
        if self.show_key_btn.isChecked():
            self.key_input.setEchoMode(QLineEdit.Normal)
            self.show_key_btn.setText("👁️")
        else:
            self.key_input.setEchoMode(QLineEdit.Password)
            self.show_key_btn.setText("👁️")
    
    def load_existing_settings(self):
        """Load existing settings from .env file"""
        if self.env_path.exists():
            load_dotenv(self.env_path)
            
            # Load API key
            api_key = os.getenv("GROQ_API_KEY", "")
            if api_key:
                self.key_input.setText(api_key)
            
            # Load user name and location
            self.name_input.setText(os.getenv("USER_NAME", ""))
            self.location_input.setText(os.getenv("USER_LOCATION", ""))
    
    def save_settings(self):
        """Save all settings to .env file"""
        api_key = self.key_input.text().strip()
        user_name = self.name_input.text().strip()
        user_location = self.location_input.text().strip()
        
        # Validate required fields
        if not api_key:
            QMessageBox.warning(self, "Error", "API key cannot be empty!")
            return
        
        # Create or update .env file
        if not self.env_path.exists():
            self.env_path.touch()
        
        # Save all settings
        set_key(self.env_path, "GROQ_API_KEY", api_key)
        set_key(self.env_path, "USER_NAME", user_name)
        set_key(self.env_path, "USER_LOCATION", user_location)
        
        QMessageBox.information(self, "Success", "Settings saved successfully!")
        
        # Update environment
        load_dotenv(self.env_path, override=True)
        
        # Enable main functionality if this is the first time
        if hasattr(self.parent, 'main_tab'):
            self.parent.main_tab.update_ui_state()
    
    def clear_fields(self):
        """Clear all input fields"""
        self.key_input.clear()
        self.name_input.clear()
        self.location_input.clear()
    
    def toggle_key_visibility(self):
        if self.show_key_btn.isChecked():
            self.key_input.setEchoMode(QLineEdit.Normal)
            self.show_key_btn.setText("👁️")
        else:
            self.key_input.setEchoMode(QLineEdit.Password)
            self.show_key_btn.setText("👁️")
    
    def load_existing_key(self):
        if self.env_path.exists():
            load_dotenv(self.env_path)
            api_key = os.getenv("GROQ_API_KEY", "")
            if api_key:
                self.key_input.setText(api_key)
    
    def save_api_key(self):
        api_key = self.key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Error", "API key cannot be empty!")
            return
        
        # Save to .env file
        if not self.env_path.exists():
            self.env_path.touch()
        
        set_key(self.env_path, "GROQ_API_KEY", api_key)
        QMessageBox.information(self, "Success", "API key saved successfully!")
        
        # Update environment
        load_dotenv(self.env_path, override=True)
        
        # Enable main functionality if this is the first time
        if hasattr(self.parent, 'main_tab'):
            self.parent.main_tab.update_ui_state()
    
    def clear_fields(self):
        self.key_input.clear()

class MainTab(QWidget):
    """Main tab for recording and transcribing"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.recorder = AudioRecorder()
        self.recorder.update_signal.connect(self.update_transcription)
        self.sheets = []
        self.init_ui()
        self.update_ui_state()
        self.load_sheets()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Sheet Selection
        sheet_layout = QHBoxLayout()
        sheet_layout.addWidget(QLabel("Select Sheet:"))
        self.sheet_combo = QComboBox()
        sheet_layout.addWidget(self.sheet_combo)
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh sheets")
        self.refresh_btn.clicked.connect(self.load_sheets)
        sheet_layout.addWidget(self.refresh_btn)
        layout.addLayout(sheet_layout)
        
        # Recording Controls
        self.record_btn = QPushButton("🎤 Start Recording")
        self.record_btn.setCheckable(True)
        self.record_btn.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_btn)
        
        # Transcription Display
        self.transcription_display = QTextEdit()
        self.transcription_display.setPlaceholderText("Your transcription will appear here...")
        layout.addWidget(QLabel("Transcription:"))
        layout.addWidget(self.transcription_display)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_transcription)
        btn_layout.addWidget(self.clear_btn)
        
        self.save_btn = QPushButton("Save to Sheet")
        self.save_btn.clicked.connect(self.save_to_sheet)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def update_ui_state(self):
        """Enable/disable UI elements based on API key availability"""
        has_api_key = bool(os.getenv("GROQ_API_KEY"))
        self.record_btn.setEnabled(has_api_key)
        self.sheet_combo.setEnabled(has_api_key)
        self.save_btn.setEnabled(has_api_key)
        
        if not has_api_key:
            self.parent.statusBar().showMessage("Please set your API key in the API Key tab first")
    
    def load_sheets(self):
        """Load available sheets from Excel file"""
        try:
            from src.sheet_data_fetch import get_available_sheets
            excel_path = os.path.join(os.path.dirname(__file__), "..", "excel_files", "DPR.xlsx")
            if os.path.exists(excel_path):
                self.sheets = [s for s in get_available_sheets(excel_path) if "log" not in s.lower()]
                self.sheet_combo.clear()
                self.sheet_combo.addItems(self.sheets)
                if self.sheets:
                    self.parent.statusBar().showMessage(f"Loaded {len(self.sheets)} sheets")
                else:
                    self.parent.statusBar().showMessage("No sheets found in the Excel file")
            else:
                self.parent.statusBar().showMessage(f"Excel file not found at {excel_path}")
        except Exception as e:
            self.parent.statusBar().showMessage(f"Error loading sheets: {str(e)}")
    
    def toggle_recording(self):
        if self.record_btn.isChecked():
            self.record_btn.setText("⏹️ Stop Recording")
            self.record_btn.setStyleSheet("background-color: #ff4444; color: white;")
            self.parent.statusBar().showMessage("Recording... Speak now")
            self.recorder.start()
        else:
            self.record_btn.setText("🎤 Start Recording")
            self.record_btn.setStyleSheet("")
            self.recorder.stop()
            self.parent.statusBar().showMessage("Recording stopped. Processing...")
    
    def update_transcription(self, text):
        self.transcription_display.setPlainText(text)
        self.parent.statusBar().showMessage("Transcription complete")
    
    def clear_transcription(self):
        self.transcription_display.clear()
    
    def save_to_sheet(self):
        text = self.transcription_display.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Error", "No transcription to save!")
            return
        
        sheet_name = self.sheet_combo.currentText()
        if not sheet_name:
            QMessageBox.warning(self, "Error", "Please select a sheet first!")
            return
        
        # Get user details from settings
        user_name = os.getenv("USER_NAME", "User")
        user_location = os.getenv("USER_LOCATION", "Desktop App")
        
        try:
            # Use the existing DPR functionality to update the sheet
            updated_quantity_in_sheet(
                description=text,
                sheet_name=sheet_name,
                name=user_name,
                location=user_location
            )
            
            QMessageBox.information(self, "Success", "Successfully updated the sheet!")
            self.clear_transcription()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update sheet: {str(e)}")
            self.parent.statusBar().showMessage(f"Error: {str(e)}")

class DPRWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DPR Voice Assistant")
        self.setMinimumSize(800, 600)
        
        # Initialize tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Add tabs
        self.main_tab = MainTab(self)
        self.api_key_tab = ApiKeyTab(self)
        
        self.tabs.addTab(self.main_tab, "Main")
        self.tabs.addTab(self.api_key_tab, "API Key Settings")
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Load environment
        load_dotenv(override=True)
        
        # Check for API key on startup
        if not os.getenv("GROQ_API_KEY"):
            self.tabs.setCurrentWidget(self.api_key_tab)
            self.statusBar().showMessage("Please set your Groq API key to continue")

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the main window
    window = DPRWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
