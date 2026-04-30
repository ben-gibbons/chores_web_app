from datetime import date

import pytest

from app.models import RecurrenceFreq
from app.services.recurrence import dates_in_range


def test_daily_within_range():
    out = dates_in_range(RecurrenceFreq.DAILY, date(2026, 4, 1), date(2026, 4, 1), date(2026, 4, 4))
    assert out == [date(2026, 4, 1), date(2026, 4, 2), date(2026, 4, 3), date(2026, 4, 4)]


def test_weekly_preserves_weekday():
    out = dates_in_range(
        RecurrenceFreq.WEEKLY, date(2026, 4, 7), date(2026, 4, 1), date(2026, 5, 5)
    )
    assert out == [date(2026, 4, 7), date(2026, 4, 14), date(2026, 4, 21), date(2026, 4, 28), date(2026, 5, 5)]


def test_biweekly_skips_weeks():
    out = dates_in_range(
        RecurrenceFreq.BIWEEKLY, date(2026, 4, 1), date(2026, 4, 1), date(2026, 5, 31)
    )
    assert out == [date(2026, 4, 1), date(2026, 4, 15), date(2026, 4, 29), date(2026, 5, 13), date(2026, 5, 27)]


def test_monthly_clamps_to_short_month():
    # Jan 31 starting -> Feb should land on the 28th (2026 is not a leap year).
    out = dates_in_range(
        RecurrenceFreq.MONTHLY, date(2026, 1, 31), date(2026, 1, 1), date(2026, 4, 30)
    )
    assert out == [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30)]


def test_monthly_clamps_in_leap_year():
    out = dates_in_range(
        RecurrenceFreq.MONTHLY, date(2024, 1, 31), date(2024, 2, 1), date(2024, 2, 29)
    )
    assert out == [date(2024, 2, 29)]


def test_range_before_start_is_empty():
    out = dates_in_range(
        RecurrenceFreq.DAILY, date(2026, 4, 10), date(2026, 4, 1), date(2026, 4, 5)
    )
    assert out == []


def test_range_partially_before_start():
    out = dates_in_range(
        RecurrenceFreq.WEEKLY, date(2026, 4, 7), date(2026, 3, 1), date(2026, 4, 21)
    )
    assert out == [date(2026, 4, 7), date(2026, 4, 14), date(2026, 4, 21)]


def test_inverted_range_returns_empty():
    out = dates_in_range(
        RecurrenceFreq.DAILY, date(2026, 4, 1), date(2026, 4, 10), date(2026, 4, 5)
    )
    assert out == []


def test_string_frequency_accepted():
    out = dates_in_range("daily", date(2026, 4, 1), date(2026, 4, 1), date(2026, 4, 2))
    assert out == [date(2026, 4, 1), date(2026, 4, 2)]


def test_invalid_frequency_string_raises():
    with pytest.raises(ValueError):
        dates_in_range("yearly", date(2026, 4, 1), date(2026, 4, 1), date(2026, 4, 2))
