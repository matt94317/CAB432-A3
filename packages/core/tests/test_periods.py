"""Tests for week/month period boundaries."""

from datetime import date

import pytest

from hookd_core.enums import TargetPeriod
from hookd_core.periods import current_period, period_bounds


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 10, 19), (date(2026, 10, 19), date(2026, 10, 25))),  # Monday
        (date(2026, 10, 25), (date(2026, 10, 19), date(2026, 10, 25))),  # Sunday
        (date(2026, 12, 31), (date(2026, 12, 28), date(2027, 1, 3))),  # across a year
    ],
)
def test_week_runs_monday_to_sunday(day, expected):
    assert period_bounds(TargetPeriod.WEEK, day) == expected


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 10, 18), (date(2026, 10, 1), date(2026, 10, 31))),
        (date(2028, 2, 10), (date(2028, 2, 1), date(2028, 2, 29))),  # leap year
    ],
)
def test_month_is_the_calendar_month(day, expected):
    assert period_bounds(TargetPeriod.MONTH, day) == expected


def test_current_period_is_clamped_to_the_campaign():
    start, end = date(2026, 11, 2), date(2026, 11, 30)
    week = TargetPeriod.WEEK
    # Before it starts: its first week. After it ends: its last week
    assert current_period(week, date(2026, 10, 1), start, end) == (start, date(2026, 11, 8))
    assert current_period(week, date(2027, 1, 1), start, end)[0] == date(2026, 11, 30)
    assert current_period(week, date(2026, 11, 12), start, end)[0] == date(2026, 11, 9)
