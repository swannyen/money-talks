from datetime import datetime
from typing import Optional, Tuple

DATE_FORMAT = "%d %b %Y"


def get_date_year(date_str: str) -> Optional[Tuple[str, int]]:
    # Implement date conversion logic here
    # For example, you can use datetime.strptime to parse and reformat the date
    today_datetime = datetime.today()
    today_str = today_datetime.strftime(DATE_FORMAT)
    today_year = today_datetime.year

    if not date_str or not isinstance(date_str, str):
        return today_str, today_year

    known_formats = ["%Y-%m-%d", DATE_FORMAT]

    for fmt in known_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime(DATE_FORMAT), dt.year
        except ValueError:
            continue

    return today_str, today_year
