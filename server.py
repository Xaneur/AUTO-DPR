import logging
from fastapi import FastAPI, Request, HTTPException 
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

load_dotenv()
PATH = os.getenv("EXCEL_FILE_PATH")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

request_queue = Queue()
app = FastAPI()
logger = get_logger(__name__)
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


def start_localtunnel():
    try:
        # Delay slightly to ensure server starts before tunnel
        time.sleep(2)
        subprocess.run(["lt", "--port", "8000"])
    except Exception as e:
        logger.error(f"Error starting localtunnel: {e}")

if __name__ == "__main__":
    # Start localtunnel in a separate thread
    tunnel_thread = threading.Thread(target=start_localtunnel, daemon=True)
    tunnel_thread.start()

    # Start FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)
