#!/usr/bin/env python3
"""
DPR Voice Assistant Launcher

This script launches the DPR Voice Assistant desktop application.
"""
import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import PyQt5
        import sounddevice
        import soundfile
        import numpy
        import whisper
        import openpyxl
        import pydantic
        import groq
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False

def install_dependencies():
    """Install required Python packages"""
    print("Installing required dependencies...")
    requirements_file = Path(__file__).parent / "requirements.txt"
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])

def main():
    # Check if we're running from the correct directory
    os.chdir(Path(__file__).parent)
    
    # Check and install dependencies if needed
    if not check_dependencies():
        print("Some dependencies are missing. Installing them now...")
        try:
            install_dependencies()
            print("Dependencies installed successfully!")
        except Exception as e:
            print(f"Failed to install dependencies: {e}")
            print("Please install the required packages manually using:")
            print(f"    pip install -r {Path(__file__).parent / 'requirements.txt'}")
            input("Press Enter to exit...")
            return
    
    # Import and run the main application
    try:
        from main_window import main as run_app
        run_app()
    except Exception as e:
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
