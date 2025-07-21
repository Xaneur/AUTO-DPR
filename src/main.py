import datetime

from src.llm_result import get_llm_result
from src.sheet_data_fetch import get_date_column, put_logs_in_file, update_sheet
from utils.logger import get_logger

logger = get_logger(__name__)


async def updated_quantity_in_sheet(file_path,
description: str, sheet_name: str, name: str = "User", location: str = "Home"
):
    """
    Update the quantity in the specified sheet based on the description.

    Args:
        description (str): The description to process
        sheet_name (str): The name of the sheet to update
        name (str, optional): Name of the person making the update
        location (str, optional): Location where the update is being made
    """
    try:
        (
            found_descriptions_list,
            _,
            relevant_indexes,
            updated_quantity,
            dates,
            conclution,
        ) = await get_llm_result(description, file_path, sheet_name)

        if not dates:
            dates = [datetime.date.today()] * len(found_descriptions_list)

        elif len(dates) > 0:
            dates = [
                datetime.datetime.strptime(date, "%d-%m-%Y").date() for date in dates
            ]

        for found_description, row_index, updated_quantity, date in zip(
            found_descriptions_list, relevant_indexes, updated_quantity, dates
        ):

            col_index = get_date_column(file_path, sheet_name, date)

            if not col_index:
                raise ValueError(f"Could not find today's date in sheet: {sheet_name}")

            logger.info(
                f"Updating sheet: {sheet_name}, row: {row_index}, col: {col_index}, value: {updated_quantity}"
            )

            update_sheet(
                file_path=file_path,
                sheet_name=sheet_name,
                row_index=row_index,
                column_index=col_index,
                value=updated_quantity,
            )

            put_logs_in_file(
                file_path=file_path,
                sheet_name=sheet_name,
                description=description,
                found_description=found_description,
                row_index=row_index,
                column_index=col_index,
                value=updated_quantity,
                name=name,
                location=location,
                remark=conclution,
            )

        logger.info(f"Successfully updated sheet: {sheet_name}")
        return True, conclution

    except Exception as e:
        logger.error(f"Error updating sheet {sheet_name}: {str(e)}")
        raise  # Re-raise the exception to be handled by the caller
