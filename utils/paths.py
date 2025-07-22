import sys
import os

def resource_path(relative_path):
    """Get absolute path to a resource, works in development and packaged app."""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller runtime: files are in sys._MEIPASS
        base_path = sys._MEIPASS
    else:
        # Development: use project root
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_path, relative_path)