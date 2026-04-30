"""Pure recurrence date math. No DB access."""
from __future__ import annotations

import calendar
from datetime import date, timedelta

from app.models import RecurrenceFreq


def _last_day_of_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _add_months(start: date, months: int) -> date:
    total = start.month - 1 + months
    year = start.year + total // 12
    month = total % 12 + 1
    day = min(start.day, _last_day_of_month(year, month))
    return date(year, month, day)


def dates_in_range(
    freq: RecurrenceFreq | str,
    start_date: date,
    range_start: date,
    range_end: date,
) -> list[date]:
    """Return every occurrence date in [range_start, range_end] (inclusive).

    For monthly chores whose start day-of-month doesn't exist in a target
    month (e.g. Jan 31 -> Feb), the date clamps to the last day of that month.
    """
    if range_end < range_start or range_end < start_date:
        return []

    freq = RecurrenceFreq(freq) if not isinstance(freq, RecurrenceFreq) else freq

    if freq in (RecurrenceFreq.DAILY, RecurrenceFreq.WEEKLY, RecurrenceFreq.BIWEEKLY):
        step = {
            RecurrenceFreq.DAILY: 1,
            RecurrenceFreq.WEEKLY: 7,
            RecurrenceFreq.BIWEEKLY: 14,
        }[freq]
        if range_start <= start_date:
            cursor = start_date
        else:
            delta = (range_start - start_date).days
            jumps = (delta + step - 1) // step
            cursor = start_date + timedelta(days=jumps * step)
        out: list[date] = []
        while cursor <= range_end:
            out.append(cursor)
            cursor += timedelta(days=step)
        return out

    # Monthly: walk month-by-month from start_date until past range_end.
    out = []
    months = 0
    while True:
        candidate = _add_months(start_date, months)
        if candidate > range_end:
            break
        if candidate >= range_start:
            out.append(candidate)
        months += 1
    return out
