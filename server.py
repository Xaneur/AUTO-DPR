import logging
import os
import re
import subprocess
import time
from typing import Optional
import threading
import json
import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from platformdirs import user_config_dir
from src.main import updated_quantity_in_sheet
from src.sheet_data_fetch import get_available_sheets, get_history
from utils.logger import get_logger
from pyngrok import ngrok, conf

load_dotenv()
# PATH = resource_path(os.getenv("EXCEL_FILE_PATH"))
# GROQ_API_KEY = (os.getenv("GROQ_API_KEY"))
# AUTHRISED_USERS = json.loads((os.getenv("ALLOWED_USERS")))

APP_NAME = "DPR-AI"
CONFIG_DIR = user_config_dir(APP_NAME)
ENV_FILE = os.path.join(CONFIG_DIR, ".env")

# Initialize logger before any usage
logger = get_logger(__name__)

# Load .env from the user config directory
load_dotenv(dotenv_path=ENV_FILE)

# Get EXCEL_FILE_PATH and validate it
excel_file_path = os.getenv("EXCEL_FILE_PATH")
if excel_file_path is None or excel_file_path.strip() == "":
    logger.error("EXCEL_FILE_PATH is not set in the .env file. Please configure it in the GUI.")
    print("ERROR: Excel file path is not configured. Please run the DPR-AI application and set the Excel file path in the Configuration tab.", flush=True)
    # Set a placeholder to prevent crashes, though functionality will be limited
    PATH = ""
else:
    # Since EXCEL_FILE_PATH is an absolute path from the GUI, use it directly
    PATH = excel_file_path

app = FastAPI()

# Configure CORS with explicit methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=600,  # Cache preflight response for 10 minutes
)

# Global variable to store ngrok URL
ngrok_url = None


# Add OPTIONS handler for CORS preflight
@app.options("/get_credentials", response_model=dict)
async def options_get_credentials():
    return {}

@app.get("/get_credentials")
async def get_credentials():
    return {
        "GROQ_API_KEY": GROQ_API_KEY,
        "AVAILABLE_SHEETS": get_available_sheets(PATH),
        "AUTHRISED_USERS": AUTHRISED_USERS
    }

@app.options("/process", response_model=dict)
async def options_process():
    return {}

@app.post("/process")
async def process_data(
    transcription: str,
    sheet_name: Optional[str] = "",
    name: Optional[str] = "",
    location: Optional[str] = "",
):
    try:
        output = await updated_quantity_in_sheet(
            PATH, transcription, sheet_name, name, location
        )
        return {"conclution": output[1]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.options("/get_history", response_model=dict)
async def options_get_history():
    return {}

@app.post("/get_history")
async def get_history_data(name: Optional[str] = "", location: Optional[str] = ""):
    logger.info(f"name: {name}, location: {location}")
    return get_history(PATH, name, location)


def get_ngrok_url_from_api():
    """Get ngrok URL from the local API"""
    try:
        response = requests.get("http://localhost:4040/api/tunnels")
        if response.status_code == 200:
            tunnels = response.json()
            for tunnel in tunnels.get("tunnels", []):
                if tunnel.get("proto") == "https":
                    return tunnel.get("public_url")
    except Exception as e:
        logger.error(f"Error getting ngrok URL from API: {e}")
    return None


from pyngrok import ngrok, conf

def start_ngrok(port: int = 8000, authtoken: Optional[str] = "2xiK1xyNghtbbCpMgq2YPycQey5_5UfqRmx2JiD8p1jRrNv51"):
    global ngrok_url

    try:
        # Optional: Set authtoken if you have one
        if authtoken:
            conf.get_default().auth_token = authtoken

        # Kill any previous tunnels just in case
        ngrok.kill()

        # Start a new HTTPS tunnel
        tunnel = ngrok.connect(port, bind_tls=True)
        ngrok_url = tunnel.public_url

        print(f"ngrok tunnel started at: {ngrok_url}", flush=True)
        logger.info(f"ngrok tunnel started at: {ngrok_url}")

        # Extract and display APP PASSWORD from URL
        match = re.search(r"https://([a-zA-Z0-9]+)\.ngrok(-free)?\.app", ngrok_url)
        if match:
            print(f"APP PASSWORD: {match.group(1)}", flush=True)
            logger.info(f"APP PASSWORD: {match.group(1)}")
        else:
            logger.warning("Couldn't extract APP PASSWORD from ngrok URL.")

    except Exception as e:
        logger.error(f"Error starting ngrok: {e}")



if __name__ == "__main__":

    ngrok_thread = threading.Thread(target=start_ngrok, daemon=True)
    ngrok_thread.start()

    uvicorn.run(app, host="0.0.0.0", port=8000)
