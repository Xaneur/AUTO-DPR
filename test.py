import asyncio
from pydantic_ai import Agent
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel, Field
from src.prompt import prompt_builder
from utils.logger import get_logger
from src.llm_result import get_llm_result

if __name__ == "__main__": 
    # output = asyncio.run(get_llm_result("25 kgs of structural steel work is done and Excavation for foundation of all type of soil 1.5 mt to 3.0 mt depth has be done by 30 cubic at 5-07-2025 "))
    output = asyncio.run(get_llm_result("40 cubic of Excavation for foundation of all type of soil 1.5 mt to 3.0 mt depth has be done and 40 kg os structural stell has be done at 10 july 2025")) 

    print(output) 
    