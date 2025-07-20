"""
this is the file containing Tools & Dependency Injection Example using pydantic 
"""

import asyncio
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel, Field
from src.prompt import prompt_builder
from utils.logger import get_logger
from agno.agent import Agent
from agno.models.groq import Groq

logger = get_logger(__name__)

load_dotenv()

class SupportResult(BaseModel):
    found_descriptions_list: list[str] = Field(description="List of descriptions from search that are available in sheet data")
    not_found_descriptions_list: list[str] = Field(description="List of descriptions from search that are NOT available in sheet data")
    relevant_indexes: list[int] = Field(description="Indexes of found descriptions from the sheet data")
    updated_quantity: list[float] = Field(description="Quantities of work done for found descriptions which is mentioned in the search description")
    dates: list[str] = Field(default=[], description="List of date strings in DD-MM-YYYY format. Use current date if not specified. Current year is 2025.")
    # remarks: list[str] = Field(default=[], description="List of remarks for each item")
    conclution: str = Field(description="precise and small Conclution of the which search has found or which is't")


support_agent = Agent(
    model = Groq(id = "meta-llama/llama-4-scout-17b-16e-instruct"),
    system_message="""
    You are a data extraction expert using ReAct (Reason + Act) methodology. 
    You MUST think step-by-step and validate each decision before acting.

    **REACT PROCESS - Follow this EXACT sequence:**

    **THOUGHT**: First, identify all work items mentioned in the search text
    **THOUGHT**: For each item, ask yourself these validation questions:
    1. "Is there an explicit quantity with units mentioned for this specific item?"
    2. "Does this description exist in the sheet data?"
    3. "Can I extract a concrete number (not 0, not assumed)?"
    
    **ACTION**: Based on thoughts, classify each item:
    - If answers to ALL 3 questions are YES → found_descriptions_list
    - If ANY answer is NO → not_found_descriptions_list

    **CRITICAL VALIDATION RULES:**
    - NEVER put items with 0.0 quantity in found_descriptions_list
    - NEVER assume quantities for terms like "done", "completed", "finished"
    - If you cannot extract a real number > 0, the item is NOT FOUND
    - Each item must have its OWN explicit quantity mention

    **STEP-BY-STEP REASONING REQUIRED:**
    Before generating output, you must mentally process each item:
    1. Extract the item name
    2. Look for its specific quantity in the search text  
    3. Check if quantity is explicit and > 0
    4. Verify item exists in sheet data
    5. Make classification decision
    6. Generate appropriate conclution what happend 
""",
    markdown=False,
    response_model=SupportResult,
    retries=10,
    add_datetime_to_instructions=True,
)

    

async def get_llm_result(search_description):
    try:
        prompt = prompt_builder(search_description) 
        response = support_agent.run(prompt)
        logger.info(f"response output is : {response.content}")
        return (
            response.content.found_descriptions_list, 
            response.content.not_found_descriptions_list, 
            response.content.relevant_indexes, 
            response.content.updated_quantity, 
            response.content.dates,
            response.content.conclution
        )
    except Exception as e:
        logger.error(f"Error in get_llm_result: {e}")
        raise

if __name__ == "__main__": 
    asyncio.run(get_llm_result("25 kgs of structural steel work is done and 7 cubic meter galvanized work has been done at 25-07-2025"))