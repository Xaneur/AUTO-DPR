import os
from pathlib import Path

# Get the root directory of the project (where this config file is located)
ROOT_DIR = Path(__file__).parent.parent.absolute()

# Excel file configuration
EXCEL_FILENAME = "DPR.xlsx"
SHEET_NAME = "July.25"

# Create excel_files directory if it doesn't exist
EXCEL_DIR = ROOT_DIR / "excel_files"
EXCEL_DIR.mkdir(exist_ok=True)

# Full path to the Excel file
FILE_PATH = str(EXCEL_DIR / EXCEL_FILENAME)

# Log directory
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Paths for different operating systems
if os.name == 'nt':  # Windows
    CONFIG_DIR = os.path.join(os.environ.get('APPDATA'), 'dpr')
else:  # Unix/Linux/macOS
    CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 'dpr')

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

# Example of how to use these paths:
# - To get the path to the Excel file: FILE_PATH
# - To create a new file in the config directory: os.path.join(CONFIG_DIR, 'config.json')
# - To create a log file: os.path.join(LOG_DIR, 'app.log')