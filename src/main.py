from src.sheet_data_fetch import get_date_column, update_sheet, put_logs_in_file
from src.llm_result import get_llm_result
from asyncio import run
from config.configuration import FILE_PATH
from utils.logger import get_logger
import datetime

logger = get_logger(__name__)

def updated_quantity_in_sheet(description: str, sheet_name: str, name: str = None, location: str = None):
    """
    Update the quantity in the specified sheet based on the description.
    
    Args:
        description (str): The description to process
        sheet_name (str): The name of the sheet to update
        name (str, optional): Name of the person making the update
        location (str, optional): Location where the update is being made
    """
    try:
        # Get the row and updated quantity from LLM
        row_index, updated_quantity, date = run(get_llm_result(description))
        
        # Get the column for today's date in the specified sheet
        col_index = get_date_column(FILE_PATH, sheet_name, date)
        
        if not col_index:
            raise ValueError(f"Could not find today's date in sheet: {sheet_name}")
            
        logger.info(f"Updating sheet: {sheet_name}, row: {row_index}, col: {col_index}, value: {updated_quantity}")
        
        # Update the sheet with the new quantity
        update_sheet(
            file_path=FILE_PATH,
            sheet_name=sheet_name,
            row_index=row_index,
            column_index=col_index,
            value=updated_quantity
        )
        
        # Log the update with additional metadata
        put_logs_in_file(
            file_path=FILE_PATH,
            sheet_name="LOGS",
            description=description,
            row_index=row_index,
            column_index=col_index,
            value=updated_quantity,
            name=name,
            location=location
        )
        
        logger.info(f"Successfully updated sheet: {sheet_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating sheet {sheet_name}: {str(e)}")
        raise  # Re-raise the exception to be handled by the caller

