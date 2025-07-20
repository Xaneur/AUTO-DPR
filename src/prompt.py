from config.configuration import FILE_PATH, SHEET_NAME
from src.sheet_data_fetch import get_descriptions_with_index 
from utils.logger import get_logger
logger = get_logger(__name__)

def prompt_builder(search_description: str, path: str = FILE_PATH, sheet_name: str = SHEET_NAME):
    description_list = get_descriptions_with_index(path, sheet_name)

    PROMPT = f"""SHEET DATA:
{description_list}
__________________________
SEARCH: 
{search_description}

TASK: Extract and match work items.

STEPS:
1. Find work items in search text
2. Match with sheet descriptions (fuzzy matching OK)
3. Extract quantities (convert to float)
4. Get sheet indexes for matches
5. Extract dates (DD-MM-YYYY format)

EXAMPLE:
Search: "25 kgs structural steel at 05-07-2025"
Sheet: "30: Structural Steel"
Output: found_descriptions_list=["Structural Steel"], relevant_indexes=[30], updated_quantity=[25.0], dates=["05-07-2025"]

RULES:
- All output arrays must be same length
- Use sheet descriptions for found_descriptions_list
- If single date mentioned, use for all items
- Convert quantities to float values
- Date format: DD-MM-YYYY

Call final_result function with the extracted data."""

    logger.info(f"prompt created with length: {len(PROMPT)}")
    return PROMPT

if __name__ == "__main__":
    prompt = prompt_builder("Excavation for foundation of all type of soil 1.5 mt to 3.0 mt depth")
    print(prompt)