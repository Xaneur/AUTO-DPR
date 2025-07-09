from config.configuration import FILE_PATH, SHEET_NAME
from  src.sheet_data_fetch import get_descriptions_with_index 
from utils.logger import get_logger
logger = get_logger(__name__)

def prompt_builder(search_description:str,path:str=FILE_PATH, sheet_name:str=SHEET_NAME):
    description_list = get_descriptions_with_index(path,sheet_name)

    PROMPT = f"""
    here is description list with it's index : 
    {description_list}
    
    and you have to find that below serach descrittion is having excat match with any description from the list
    search description : {search_description}

    proivded search descriptino is's the norma query that what thing has done we need to extract the quantity of work done
    in result provide the 2 thing one is the best fit search description's index and 
    second is the values in float which is quantity of work done or updated quantity of work don
    quantyty should be described in ( kg, cubic, mtr, cubic meter, cubic feet, cubic yards, etc.)"""

    logger.info(f"prompt is created : {PROMPT}")
    return PROMPT


if __name__ == "__main__":
    prompt = prompt_builder("Excavation for foundation of all type of soil 1.5 mt to 3.0 mt depth")
    print(prompt)

    
    
       