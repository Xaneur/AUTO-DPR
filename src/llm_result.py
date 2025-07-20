"""
this is the file containing Tools & Dependency Injection Example using pydantic 
"""

import asyncio
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel, Field
import prompt
from src.prompt import prompt_builder
from utils.logger import get_logger
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.thinking import ThinkingTools

import datetime
logger = get_logger(__name__)

load_dotenv()

class SupportResult(BaseModel):
    found_descriptions_list: list[str] = Field(description="List of descriptions from search that are available in sheet data")
    not_found_descriptions_list: list[str] = Field(description="List of descriptions from search that are NOT available in sheet data")
    relevant_indexes: list[int] = Field(description="Indexes of found descriptions from the sheet data")
    updated_quantity: list[float] = Field(description="Quantities of work done for found descriptions which is mentioned in the search description")
    dates: list[str] = Field(default=[], description="List of date strings in DD-MM-YYYY format. Use current date if not specified. Current year is 2025.")
    remarks: list[str] = Field(default=[], description="List of remarks for each item")


support_agent = Agent(
    model = Groq(id = "meta-llama/llama-4-scout-17b-16e-instruct"),
    system_message="""
    THOUGHT PHASE 1 - ITEM CONSOLIDATION:
First, identify the UNIQUE work concepts (not just text variations):

Read the entire search text
Group related terms that refer to the SAME work activity
Create consolidated work concepts, not separate items for each phrase

THOUGHT PHASE 2 - SEMANTIC MATCHING:
For each consolidated work concept:

"What is the core work activity being described?"
"What are all the different ways this same work is mentioned?"
"Which single sheet entry best matches this work concept?"

THOUGHT PHASE 3 - QUANTITY VALIDATION:
For each unique work concept:

"Is there ANY explicit quantity mentioned for this work concept?"
"Does this work concept have a match in sheet data?"
"Can I extract a concrete number > 0 for this work?"

ACTION PHASE - SINGLE CLASSIFICATION:
Each work concept goes to EXACTLY ONE list:

If ALL validation questions = YES → found_descriptions_list (ONE entry only)
If ANY validation question = NO → not_found_descriptions_list (ONE entry only)


CRITICAL CONSOLIDATION RULES:
RULE 1 - SEMANTIC GROUPING:
❌ WRONG: Treat these as separate items:
- "galvanization work" 
- "hot galvanizing"
- "steel galvanization"

✅ CORRECT: Consolidate as ONE concept:
- Core concept: "Galvanizing Work"
- Match to: "Hot Deep Galvanizing Work" (index 31)
- Result: ONE entry in found_descriptions_list
RULE 2 - SINGLE QUANTITY RULE:
❌ WRONG: 
Search: "25 tons galvanizing and hot dip galvanization completed"
Output: found=["Galvanizing"], not_found=["hot dip galvanization"]

✅ CORRECT:
Search: "25 tons galvanizing and hot dip galvanization completed"  
Output: found=["Hot Deep Galvanizing Work"], not_found=[]
Reasoning: Both phrases refer to same work with same quantity
RULE 3 - NO REDUNDANCY:

Each physical work activity = ONE classification only
Never split the same work into found + not_found
Use the BEST matching sheet description name


STEP-BY-STEP CONSOLIDATION PROCESS:
STEP 1 - CONCEPT EXTRACTION:
Think: "How many DIFFERENT physical work activities are described?"

Group synonymous terms together
Identify unique work concepts

STEP 2 - QUANTITY MAPPING:
Think: "What quantity applies to each work concept?"

Map quantities to work concepts, not individual phrases
One work concept = one quantity (if mentioned)

STEP 3 - SHEET MATCHING:
Think: "What's the BEST single match for each work concept?"

Find closest semantic match in sheet data
Use exact sheet description name in output

STEP 4 - SINGLE DECISION:
Think: "Based on the work concept, does it qualify as FOUND or NOT_FOUND?"

Make ONE decision per work concept
No splitting into both lists


ENHANCED EXAMPLES:
EXAMPLE 1 - CONSOLIDATION SUCCESS:
Search: "25 kgs hot galvanizing and galvanization of steel completed"
Sheet: "31: Hot Deep Galvanizing Work"

THOUGHT: This describes ONE work concept - galvanizing work
- Terms: "hot galvanizing" + "galvanization of steel" = same work
- Quantity: 25 kgs applies to the entire galvanizing concept
- Sheet match: "Hot Deep Galvanizing Work" (index 31)

ACTION:
found_descriptions_list=["Hot Deep Galvanizing Work"]
not_found_descriptions_list=[]
relevant_indexes=[31]
updated_quantity=[25.0]
remarks=["Hot Deep Galvanizing Work is updated with 25.0"]
EXAMPLE 2 - MIXED SCENARIO:
Search: "25 kgs structural steel work done and excavation completed"
Sheet: "30: Structural Steel", "6: Excavation for foundation..."

THOUGHT: Two DISTINCT work concepts:
1. Structural steel work - has 25 kgs quantity ✅
2. Excavation work - only "completed", no quantity ❌

ACTION:
found_descriptions_list=["Structural Steel"]
not_found_descriptions_list=["Excavation for foundation of all type of soil upto1.5 mt depth"]
relevant_indexes=[30]
updated_quantity=[25.0]
remarks=["Structural Steel is updated with 25.0", "Excavation for foundation of all type of soil upto1.5 mt depth - quantity is missing"]

VALIDATION CHECKLIST:
Before final output, verify:
✅ Each work concept appears in EXACTLY ONE list (found OR not_found, never both)
✅ No redundant entries for the same physical work activity
✅ Quantities are mapped to work concepts, not individual phrases
✅ Sheet description names are used exactly as they appear in sheet data
✅ No 0.0 quantities in found_descriptions_list
DEBUGGING QUESTIONS:

"Am I treating synonyms as separate work items?" → Should be NO
"Does any work concept appear in both lists?" → Should be NO
"Are all found items backed by explicit quantities?" → Should be YES
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
            response.content.remarks
        )
    except Exception as e:
        logger.error(f"Error in get_llm_result: {e}")
        raise

if __name__ == "__main__": 
    asyncio.run(get_llm_result("25 kgs of structural steel work is done and 7 cubic meter galvanized work has been done at 25-07-2025"))