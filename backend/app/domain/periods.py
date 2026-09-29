"""Budget months are periods, not calendar months.

A couple's month starts on the day of the first full salary, which can be any day: the
September budget may run from 5 September to 4 October, or start as early as 28 August.
A period ends the day before the next month's period starts; the latest month is open
until the next one is created.
"""

import calendar
from datetime import date, timedelta


def default_start(year: int, month: int) -> date:
    return date(year, month, 1)


def allowed_start_range(year: int, month: int) -> tuple[date, date]:
    """From the 1st of the previous calendar month to the last day of the month itself."""
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    return date(prev_year, prev_month, 1), date(year, month, calendar.monthrange(year, month)[1])


def estimated_end(start: date) -> date:
    """For a month with no next one yet: a day before the same date a month later."""
    year, month = (start.year + 1, 1) if start.month == 12 else (start.year, start.month + 1)
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day) - timedelta(days=1)
