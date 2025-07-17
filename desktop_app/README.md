# DPR Voice Assistant

A desktop application for voice-based daily progress reporting that integrates with Excel spreadsheets.

## Features

- **Voice Recording**: Record your voice directly in the application
- **Speech-to-Text**: Automatic transcription using Whisper AI
- **Excel Integration**: Seamlessly update Excel sheets with voice commands
- **API Key Management**: Securely store and manage your Groq API key
- **Multiple Sheets**: Support for multiple Excel sheets with easy switching

## Prerequisites

- Python 3.8 or higher
- Microphone access
- Groq API key (for Whisper transcription)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd AUTO-DPR/desktop_app
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **First Run**:
   - Launch the application:
     ```bash
     python launch.py
     ```
   - Go to the "API Key Settings" tab
   - Enter your Groq API key and click "Save API Key"

2. **Recording Audio**:
   - Select the target Excel sheet from the dropdown
   - Click the "🎤 Start Recording" button and speak clearly
   - Click "⏹️ Stop Recording" when finished
   - Review and edit the transcription if needed
   - Click "Save to Sheet" to update the Excel file

3. **Troubleshooting**:
   - If the application doesn't detect your microphone, check your system's audio settings
   - Ensure you have a stable internet connection for API calls
   - Check the status bar at the bottom for any error messages

## File Structure

- `main_window.py` - Main application window and UI
- `launch.py` - Application launcher and dependency checker
- `requirements.txt` - Python package dependencies
- `README.md` - This file

## Notes

- Your API key is stored locally in the `.env` file
- Audio recordings are processed locally; only transcriptions are sent to the API
- The application looks for an Excel file at `../excel_files/DPR.xlsx` by default

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
