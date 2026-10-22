"""Posts vs target for a creator's current period, and whether they're behind
(US-19, US-22).

Pure functions, so the API, the MCP server and future alerts agree on who is behind.

"Behind" is judged on pace, not the final count: on a Monday nobody is behind a
weekly target yet. Posts due by today = target x share of the period elapsed,
rounded down, so a creator is only behind once they've missed a whole post's
worth. When a period overlaps the campaign's start or end, only the days inside
the campaign count.
"""

import math
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, tzinfo
from enum import StrEnum

from hookd_core.enums import TargetPeriod
from hookd_core.periods import current_period
from hookd_core.repositories.assignments import Assignment
from hookd_core.repositories.campaigns import Campaign
from hookd_core.repositories.posts import Post


class ProgressStatus(StrEnum):
    MET = "met"  # target reached this period
    ON_TRACK = "on_track"
    BEHIND = "behind"
    UPCOMING = "upcoming"  # the campaign hasn't started


@dataclass(frozen=True)
class CreatorProgress:
    creator_id: uuid.UUID
    target_posts: int
    target_period: TargetPeriod
    period_start: date
    period_end: date
    posts: int  # in this period
    expected_by_today: int
    status: ProgressStatus

    @property
    def remaining(self) -> int:
        return max(0, self.target_posts - self.posts)

    @property
    def is_behind(self) -> bool:
        return self.status == ProgressStatus.BEHIND


def creator_progress(
    assignment: Assignment,
    campaign: Campaign,
    posts: Iterable[Post],
    today: date,
    tz: tzinfo,
) -> CreatorProgress:
    """`posts` may include other creators' or campaigns'; only this assignment's count."""
    start, end = current_period(
        assignment.target_period, today, campaign.start_date, campaign.end_date
    )
    counted = sum(
        1
        for p in posts
        if p.creator_id == assignment.creator_id
        and p.campaign_id == assignment.campaign_id
        and not p.removed
        and start <= p.posted_at.astimezone(tz).date() <= end
    )
    target = assignment.target_posts

    if today < campaign.start_date:
        expected, status = 0, ProgressStatus.UPCOMING
    else:
        active_start = max(start, campaign.start_date)
        active_end = min(end, campaign.end_date)
        elapsed = (min(today, active_end) - active_start).days + 1
        total = (active_end - active_start).days + 1
        expected = math.floor(target * elapsed / total)
        if counted >= target:
            status = ProgressStatus.MET
        elif counted < expected:
            status = ProgressStatus.BEHIND
        else:
            status = ProgressStatus.ON_TRACK

    return CreatorProgress(
        creator_id=assignment.creator_id,
        target_posts=target,
        target_period=assignment.target_period,
        period_start=start,
        period_end=end,
        posts=counted,
        expected_by_today=expected,
        status=status,
    )
