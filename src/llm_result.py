"""
this is the file containig Tools & Dependency Injection Example usign pydantic 
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
    relvant_index: int = Field(description="provided index of the serachable description from the given list of the descriptions")
    updated_quantity: float = Field(description="updated quantity of the work done which provided in the search description")
    date: Optional[datetime.date] = Field(default=datetime.date.today(), description="date of the work done, current year is 2025, None if date is not provided, if given today in description then go with default value.")

support_agent = Agent("groq:llama-3.3-70b-versatile",
    output_type=SupportResult, 
    output_retries=3,
    system_prompt=(
        "you are an expert in index extracting we'll provide the list of description with index and search description "
        "and you have to findout the index of the description"
        "index which is best match or complete match with the search description"
        "also provide the date of the work done also if only date is provided remember current year is 2025, None if date is not provided"
    )
)


async def get_llm_result(search_description):
    prompt = prompt_builder(search_description) 
    response = await support_agent.run(prompt)
    logger.info(f"response is : {response}")
    logger.info(f"response output is : {response.output}")
    return response.output.relvant_index, response.output.updated_quantity, response.output.date


if __name__ == "__main__": 
    asyncio.run(get_llm_result("25 kgs of structural steel work is done")) 