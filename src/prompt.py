from config.configuration import FILE_PATH, SHEET_NAME
from src.sheet_data_fetch import get_descriptions_with_index 
from utils.logger import get_logger
logger = get_logger(__name__)

def prompt_builder(search_description: str, path: str = FILE_PATH, sheet_name: str = SHEET_NAME):
    description_list = get_descriptions_with_index(path, sheet_name)

    PROMPT = f"""**MANDATORY CONSOLIDATION FRAMEWORK - NO EXCEPTIONS**

**SHEET DATA:**
{description_list}

**SEARCH TEXT:** 
{search_description}

**CRITICAL INSTRUCTION:** 
You MUST consolidate synonymous terms into single work concepts. NEVER create separate entries for the same physical work activity.

**FORCED CONSOLIDATION PROCESS:**

**STEP 1 - MANDATORY GROUPING:**
Before analyzing anything else, answer this:
"What are ALL the different ways the SAME work activity is mentioned in the search text?"

Group these terms together:
- galvanizing, galvanization, hot galvanizing, steel galvanization → ALL = "galvanizing work"
- excavation, excavating, digging → ALL = "excavation work"  
- steel work, structural steel, steel construction → ALL = "steel work"

**STEP 2 - COUNT UNIQUE WORK ACTIVITIES:**
Ask: "How many DIFFERENT physical work activities are mentioned?" (Not how many terms, but how many actual work types)

**STEP 3 - ONE QUANTITY PER WORK ACTIVITY:**
For each unique work activity, ask: "What quantity applies to this entire work activity?"

**STEP 4 - ONE CLASSIFICATION PER WORK ACTIVITY:**
Each work activity gets EXACTLY ONE classification - never split the same work into both lists.

**MANDATORY EXAMPLES:**

**EXAMPLE A - SINGLE WORK ACTIVITY:**
```
Search: "25 kgs hot galvanizing and galvanization of steel completed"
Sheet: "31: Hot Deep Galvanizing Work"

FORCED ANALYSIS:
- Terms mentioned: "hot galvanizing" + "galvanization of steel"
- CONSOLIDATION: Both terms refer to the SAME work activity = galvanizing work
- Unique work activities: 1 (only galvanizing work)
- Quantity for galvanizing work: 25 kgs
- Sheet match: "Hot Deep Galvanizing Work" (index 31)
- Classification: Has quantity + exists in sheet = FOUND

MANDATORY OUTPUT:
found_descriptions_list=["Hot Deep Galvanizing Work"]
not_found_descriptions_list=[]
relevant_indexes=[31]
updated_quantity=[25.0]
remarks=["Hot Deep Galvanizing Work is updated with 25.0"]
```

**EXAMPLE B - MULTIPLE WORK ACTIVITIES:**
```
Search: "25 kgs structural steel work and excavation completed"  
Sheet: "30: Structural Steel", "6: Excavation for foundation..."

FORCED ANALYSIS:
- Terms mentioned: "structural steel work" + "excavation"
- CONSOLIDATION: These are 2 DIFFERENT work activities
- Unique work activities: 2 (steel work + excavation work)
- Quantities: Steel work has 25 kgs, excavation has no quantity
- Classifications:
  1. Steel work: Has quantity + exists = FOUND
  2. Excavation: No quantity = NOT FOUND

MANDATORY OUTPUT:
found_descriptions_list=["Structural Steel"]
not_found_descriptions_list=["Excavation for foundation of all type of soil upto1.5 mt depth"]
relevant_indexes=[30]
updated_quantity=[25.0]
remarks=["Structural Steel is updated with 25.0", "Excavation for foundation of all type of soil upto1.5 mt depth - quantity is missing"]
```

**PROHIBITION RULES:**
❌ NEVER do this: found=["Hot Deep Galvanizing Work"], not_found=["galvanization of steel"]
❌ NEVER split the same work activity into both lists
❌ NEVER treat synonymous terms as separate work activities
❌ NEVER create redundant entries

✅ ALWAYS do this: Consolidate first, then classify once

**FORCED REASONING TEMPLATE:**
You MUST complete this exact reasoning:

```
CONSOLIDATION ANALYSIS:
- Terms in search text: [list all work-related terms]
- Synonymous groupings: [group terms that refer to same work]
- Unique work activities identified: [number]
- For each unique work activity:
  * Name: [consolidated name]
  * Quantity mentioned: [number or "none"]
  * Sheet match: [best match and index]
  * Classification: [FOUND or NOT_FOUND with reason]
```

**DECISION TREE - FOLLOW EXACTLY:**

For the search text: "{search_description}"

**DECISION POINT 1:** Are there multiple terms that refer to galvanizing work?
- If YES → Group them as ONE work activity called "galvanizing work"
- If NO → Treat as separate activities

**DECISION POINT 2:** For the galvanizing work activity:
- Does it have an explicit quantity (number + units)? 
- Does it match any sheet entry?
- If BOTH YES → Put in found_descriptions_list ONLY
- If ANY NO → Put in not_found_descriptions_list ONLY

**FORCED SINGLE OUTPUT RULE:**
The consolidated "galvanizing work" activity goes to EXACTLY ONE list:
- Either found_descriptions_list = ["Hot Deep Galvanizing Work"] + not_found_descriptions_list = []
- OR found_descriptions_list = [] + not_found_descriptions_list = ["Hot Deep Galvanizing Work"]

**NEVER BOTH LISTS FOR THE SAME WORK!**

**NOW GENERATE OUTPUT FOLLOWING DECISION TREE**
"""


    logger.info(f"prompt created with length: {len(PROMPT)}")
    return PROMPT

if __name__ == "__main__":
    prompt = prompt_builder("Excavation for foundation of all type of soil 1.5 mt to 3.0 mt depth")
    print(prompt)