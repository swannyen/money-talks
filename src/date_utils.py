from datetime import datetime
from typing import Optional, Tuple

SAVED_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
UI_DATE_FORMAT = "%Y-%m-%d"

def get_date_year(date_str: str) -> Optional[Tuple[str, int]]:
    # Implement date conversion logic here
    # For example, you can use datetime.strptime to parse and reformat the date
    today_datetime = datetime.today()
    today_str = today_datetime.strftime(SAVED_DATE_FORMAT)
    today_year = today_datetime.year

    if not date_str or not isinstance(date_str, str):
        return today_str, today_year

    try:
        print(date_str)
        dt = datetime.strptime(date_str, UI_DATE_FORMAT)
        return dt.strftime(SAVED_DATE_FORMAT), dt.year
    except ValueError:
        print("issue with date time")
    return today_str, today_year
