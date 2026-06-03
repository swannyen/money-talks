from datetime import datetime
from typing import Optional, Tuple

SAVED_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
UI_DATE_FORMAT = "%Y-%m-%d"


def get_date_year(date_str: str) -> Optional[Tuple[str, int]]:
    today = datetime.today()
    today_str = today.strftime(SAVED_DATE_FORMAT)
    today_year = today.year

    if not date_str or not isinstance(date_str, str):
        return today_str, today_year

    try:
        dt = datetime.strptime(date_str, UI_DATE_FORMAT)
        return dt.strftime(SAVED_DATE_FORMAT), dt.year
    except ValueError:
        return today_str, today_year
