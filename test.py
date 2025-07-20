import asyncio
from pydantic_ai import Agent
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel, Field
from src.prompt import prompt_builder
from utils.logger import get_logger
from src.llm_result import get_llm_result
from src.sheet_data_fetch import get_history
from src.main import updated_quantity_in_sheet
from dotenv import load_dotenv
import os
load_dotenv()

FILE_PATH = os.getenv("EXCEL_FILE_PATH")

if __name__ == "__main__": 
    # output = asyncio.run(get_llm_result("25 kgs of structural steel work is done and excavation has been done on 5-07-2025 "))
    # output = asyncio.run(get_llm_result("25 kgs of structural steel work is done and 30 cubic meter excavation has been done on 5-07-2025 "))
    # output = asyncio.run(get_llm_result("Structureal steel done and excavation has been done on 13th july.")) 

    # print(output)

    output = asyncio.run(updated_quantity_in_sheet(description="25 kgs of structural steel work is done and excavation has been done on 5-07-2025 ", sheet_name="July.25", name="test", location="dev"))
