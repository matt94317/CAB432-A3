"""Target period helpers: start/end of the current week or month for a date.

Used to count posts vs target for the current period (US-19, US-22). Weeks run
Monday to Sunday; months are calendar months. Both ends are inclusive."""

import calendar
from datetime import date, timedelta

from hookd_core.enums import TargetPeriod


def period_bounds(period: TargetPeriod, day: date) -> tuple[date, date]:
    if period == TargetPeriod.WEEK:
        start = day - timedelta(days=day.weekday())
        return start, start + timedelta(days=6)
    last = calendar.monthrange(day.year, day.month)[1]
    return day.replace(day=1), day.replace(day=last)


def current_period(
    period: TargetPeriod, today: date, campaign_start: date, campaign_end: date
) -> tuple[date, date]:
    """The period to report for a campaign today.

    Before the campaign starts this is its first period; after it ends, its last.
    """
    reference = min(max(today, campaign_start), campaign_end)
    return period_bounds(period, reference)
