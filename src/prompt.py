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

RULES:
1. Only add to `found_descriptions_list` if BOTH description matches a row in sheet AND 
   a numeric quantity is explicitly given.
2. If no quantity is present, or the description is too generic, treat as `not_found_descriptions_list`.
3. Never default to 0.0 quantity.
4. One output row per search item, no duplication.
5. All output arrays must be the same length.
6. Date format must be DD-MM-YYYY (use today's date if not given).

OUTPUT FORMAT:
Return the data using this structure:
(found_descriptions_list, not_found_descriptions_list, relevant_indexes, updated_quantity, dates, remarks)

EXAMPLE:
Search: "25 kgs structural steel at 05-07-2025"
Sheet: "30: Structural Steel"
Output:
found_descriptions_list=["Structural Steel"],
not_found_descriptions_list=[""],
relevant_indexes=[30],
updated_quantity=[25.0],
dates=["05-07-2025"],
remarks=["Structural Steel is updated with 25.0 at 05-07-2025"]

Search: "Structural Steel done on 13th July"
Sheet: "30: Structural Steel"
Output:
found_descriptions_list=[""],
not_found_descriptions_list=["Structural Steel"],
relevant_indexes=[],
updated_quantity=[],
dates=[],
remarks=["Structural Steel - quantity is missing"]
"""


    logger.info(f"prompt created with length: {len(PROMPT)}")
    return PROMPT

if __name__ == "__main__":
    prompt = prompt_builder("Excavation for foundation of all type of soil 1.5 mt to 3.0 mt depth")
    print(prompt)