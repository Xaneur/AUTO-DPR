import os
import re
from typing import Optional
import json
from PyQt5.QtCore import flush
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.main import updated_quantity_in_sheet
from src.sheet_data_fetch import get_available_sheets, get_history
from utils.logger import get_logger
from pyngrok import ngrok, conf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok, conf
import atexit


load_dotenv()
PATH = os.getenv("EXCEL_FILE_PATH")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
AUTHRISED_USERS = json.loads(os.getenv("ALLOWED_USERS"))

tunnel = None 

# Initialize logger before any usage
logger = get_logger(__name__)

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


def start_ngrok_and_print_password(port: int = 8000, authtoken: Optional[str] = None):
    global ngrok_url, tunnel

    try:
        if authtoken:
            conf.get_default().auth_token = authtoken

        ngrok.kill()
        tunnel = ngrok.connect(port, bind_tls=True)
        ngrok_url = tunnel.public_url

        logger.info(f"ngrok tunnel started at: {ngrok_url}")

        match = re.search(r"https://([a-zA-Z0-9]+)\.ngrok(-free)?\.app", ngrok_url)
        if match:
            app_password = match.group(1)
            logger.info(f"APP PASSWORD: {app_password}")
            print(f"APP PASSWORD: {app_password}", flush=True)
        else:
            logger.warning("Couldn't extract APP PASSWORD from ngrok URL.")
    except Exception as e:
        logger.error(f"Error starting ngrok: {e}")


def stop_ngrok():
    global tunnel
    try:
        if tunnel:
            ngrok.disconnect(tunnel.public_url)
            tunnel = None
        ngrok.kill()
        logger.info("ngrok tunnel stopped.")
    except Exception as e:
        logger.error(f"Error stopping ngrok: {e}")


def main():
    start_ngrok_and_print_password(port=8000, authtoken=NGROK_AUTH_TOKEN)

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        stop_ngrok()


if __name__ == "__main__":
    main()
