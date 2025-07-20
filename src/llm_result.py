"""
this is the file containing Tools & Dependency Injection Example using pydantic 
"""

import asyncio
from pydantic_ai import Agent
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel, Field
from src.prompt import prompt_builder
from utils.logger import get_logger
import datetime
logger = get_logger(__name__)

load_dotenv()

class SupportResult(BaseModel):
    found_descriptions_list: list[str] = Field(description="List of descriptions from search that are available in sheet data")
    not_found_descriptions_list: list[str] = Field(description="List of descriptions from search that are NOT available in sheet data")
    relevant_indexes: list[int] = Field(description="Indexes of found descriptions from the sheet data")
    updated_quantity: list[float] = Field(description="Quantities of work done for found descriptions which is mentioned in the search description")
    dates: list[str] = Field(default=[], description="List of date strings in DD-MM-YYYY format. Use current date if not specified. Current year is 2025.")

support_agent = Agent(
    "groq:meta-llama/llama-4-scout-17b-16e-instruct",
    output_type=SupportResult, 
    output_retries=6,  # Reduced from 10
    system_prompt=(
        "You are a data extraction expert. Analyze search descriptions and match them with sheet data.\n\n"
        "Rules:\n"
        "- Match search items with sheet descriptions (fuzzy matching allowed)\n"
        "- Extract quantities as floats\n"
        "- All output lists must have equal length\n"
        "- Use DD-MM-YYYY date format\n"
        "- If one date given, use for all items\n"
    )
)

async def get_llm_result(search_description):
    try:
        prompt = prompt_builder(search_description) 
        response = await support_agent.run(prompt)
        logger.info(f"response output is : {response.output}")
        return (
            response.output.found_descriptions_list, 
            response.output.not_found_descriptions_list, 
            response.output.relevant_indexes, 
            response.output.updated_quantity, 
            response.output.dates
        )
    except Exception as e:
        logger.error(f"Error in get_llm_result: {e}")
        raise

if __name__ == "__main__": 
    asyncio.run(get_llm_result("25 kgs of structural steel work is done and 7 cubic meter galvanized work has been done at 25-07-2025"))