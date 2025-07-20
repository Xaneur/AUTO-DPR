import logging
from fastapi import FastAPI, Request, HTTPException 
from fastapi.middleware.cors import CORSMiddleware  # Add this import
import subprocess
import threading
import time
import json
from dotenv import load_dotenv
import os
from typing import Dict, Any
from streamlit import rerun
import uvicorn
from utils.logger import get_logger
from src.sheet_data_fetch import get_available_sheets
from src.main import updated_quantity_in_sheet
from queue import Queue
import re
import requests

load_dotenv()
PATH = os.getenv("EXCEL_FILE_PATH")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

request_queue = Queue()
app = FastAPI()
logger = get_logger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global variable to store ngrok URL
ngrok_url = None

@app.get("/get_credentials")
async def get_credentials():
    return {"GROQ_API_KEY": GROQ_API_KEY, "AVAILABLE_SHEETS": get_available_sheets(PATH)}

@app.post("/process")
async def process_data(request: Request):
    try:
        # Get raw request body
        body = await request.body()
        data = json.loads(body)
        logger.info(f"data: {data}") 

        transcription_list = data.get("transcription_list",[])
        sheet_name = data.get("sheet_name","")
        name = data.get("name","")
        location = data.get("location","")

        for transcription in transcription_list:
            await updated_quantity_in_sheet(transcription, sheet_name, name, location)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

def start_ngrok():
    global ngrok_url
    try:
        time.sleep(2)
        # Start ngrok process
        process = subprocess.Popen(
            ["ngrok", "http", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for ngrok to start
        time.sleep(5)
        
        # Get URL from ngrok API
        ngrok_url = get_ngrok_url_from_api()
        pattern = re.compile(r'https://([a-zA-Z0-9]+)\.ngrok-free\.app')
        m = pattern.search(ngrok_url)
        if m:
            print(f"APP PASSWORD: {m.group(1)}", flush=True)
            logging.info(f"APP PASSWORD: {m.group(1)}")
        else:
            logger.error("Failed to get ngrok URL")
            
        process.wait()
        
    except Exception as e:
        logger.error(f"Error starting ngrok: {e}")


if __name__ == "__main__":

    ngrok_thread = threading.Thread(target=start_ngrok, daemon=True)    
    ngrok_thread.start()

    
    uvicorn.run(app, host="0.0.0.0", port=8000)