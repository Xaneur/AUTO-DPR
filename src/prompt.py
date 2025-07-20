from config.configuration import FILE_PATH, SHEET_NAME
from src.sheet_data_fetch import get_descriptions_with_index 
from utils.logger import get_logger
logger = get_logger(__name__)

def prompt_builder(search_description: str, path: str = FILE_PATH, sheet_name: str = SHEET_NAME):
    description_list = get_descriptions_with_index(path, sheet_name)

    PROMPT = f"""**REACT FRAMEWORK ANALYSIS**

**SHEET DATA:**
{description_list}

**SEARCH TEXT:** 
{search_description}

**INSTRUCTIONS:** Use ReAct methodology - Think step by step, then Act.

**FEW-SHOT EXAMPLES:**

**EXAMPLE 1:**
Search: "25 kgs structural steel at 05-07-2025"
Sheet: "30: Structural Steel"
Output:
found_descriptions_list=["Structural Steel"],
not_found_descriptions_list=[],
relevant_indexes=[30],
updated_quantity=[25.0],
dates=["05-07-2025"],
conclution="Structural Steel is updated with 25.0 at 05-07-2025"

**EXAMPLE 2:**
Search: "Structural Steel done on 13th July"
Sheet: "30: Structural Steel"
Output:
found_descriptions_list=[],
not_found_descriptions_list=["Structural Steel"],
relevant_indexes=[],
updated_quantity=[],
dates=[],
conclution="Structural Steel - quantity is missing"

**EXAMPLE 3:**
Search: "25 kgs of structural steel work is done and excavation has been done on 5-07-2025"
Sheet: "30: Structural Steel, 6: Excavation for foundation..."
Expected Output:
found_descriptions_list=["Structural Steel"],
not_found_descriptions_list=["Excavation for foundation of all type of soil upto1.5 mt depth"],
relevant_indexes=[30],
updated_quantity=[25.0],
dates=["05-07-2025"],
conclution="Structural Steel is updated with 25.0 at 05-07-2025 but Excavation for foundation of all type of soil upto1.5 mt depth - quantity is missing"

**THOUGHT PROCESS - Complete this reasoning:**

**STEP 1 - IDENTIFY ITEMS:**
Think: "What work items are mentioned in the search text?"
List each item separately.

**STEP 2 - QUANTITY ANALYSIS:**  
For each item, think:
- "What is the EXPLICIT quantity mentioned for [ITEM NAME]?"
- "Is this quantity a real number with units, or just words like 'done'?"
- "If I see 'done/completed/finished' without numbers, this means NO QUANTITY"

**STEP 3 - SHEET MATCHING:**
For each item, think:
- "Does [ITEM NAME] exist in the provided sheet data?"
- "What is the closest match and its index?"

**STEP 4 - VALIDATION DECISION:**
For each item, validate:
- ✅ Has explicit quantity (real number > 0) AND exists in sheet → FOUND
- ❌ Missing quantity OR not in sheet OR quantity is 0 → NOT FOUND

**STEP 5 - CLASSIFICATION:**
Based on validation, classify each item into appropriate list.

**DETAILED REASONING EXAMPLE:**
Search: "25 kgs of structural steel work is done and excavation has been done"

THOUGHT: I see two items:
1. "structural steel work" - has "25 kgs" explicitly mentioned ✅
2. "excavation" - only says "has been done", no quantity mentioned ❌

THOUGHT: Checking sheet data:
1. "Structural Steel" exists at index 30 ✅  
2. "Excavation for foundation..." exists at index 6 ✅

VALIDATION:
1. Structural steel: Has quantity (25.0) + exists in sheet → FOUND
2. Excavation: No quantity (only "done") → NOT FOUND

ACTION: 
- found_descriptions_list = ["Structural Steel"]
- not_found_descriptions_list = ["Excavation for foundation of all type of soil upto1.5 mt depth"]
- relevant_indexes = [30]
- updated_quantity = [25.0]
- conclution = "Structural Steel is updated with 25.0 at 05-07-2025 but Excavation for foundation of all type of soil upto1.5 mt depth - quantity is missing"

**NOW ANALYZE THE CURRENT SEARCH TEXT:**
Apply the same ReAct process to: "{search_description}"

**REASONING CHECKPOINT:**
Before generating final output, verify:
- Did I find explicit quantities (numbers + units) for each found item?
- Did I put any 0.0 quantities in found_descriptions_list? (This should be NO)
- Are all found items backed by real numbers from the search text?

**GENERATE OUTPUT ONLY AFTER COMPLETING THIS REASONING**

"""


    logger.info(f"prompt created with length: {len(PROMPT)}")
    return PROMPT

if __name__ == "__main__":
    prompt = prompt_builder("Excavation for foundation of all type of soil 1.5 mt to 3.0 mt depth")
    print(prompt)