"""Tests for posts vs target and the pace-based behind-target rule (US-19, US-22)."""

import uuid
from datetime import UTC, date, datetime, time

import pytest

from hookd_core.enums import MatchSource, TargetPeriod
from hookd_core.progress import ProgressStatus, creator_progress
from hookd_core.repositories.assignments import Assignment
from hookd_core.repositories.campaigns import Campaign
from hookd_core.repositories.posts import Post

ORG, CREATOR = uuid.uuid4(), uuid.uuid4()
# Weeks of October 2026: Mon 12 to Sun 18, Mon 19 to Sun 25
CAMPAIGN = Campaign(
    organisation_id=ORG,
    name="Summer",
    brand="Lumi",
    start_date=date(2026, 10, 1),
    end_date=date(2026, 11, 30),
    tracking_hashtags=("lumiglow",),
)


def assignment(target=3, period=TargetPeriod.WEEK, campaign=CAMPAIGN):
    return Assignment(ORG, campaign.id, CREATOR, target_posts=target, target_period=period)


def posts_on(*days, creator=CREATOR, campaign=CAMPAIGN, removed=False):
    return [
        Post(
            organisation_id=ORG,
            creator_id=creator,
            campaign_id=campaign.id,
            external_id=f"{d}-{i}",
            url="https://www.tiktok.com/@lou/video/1",
            posted_at=datetime.combine(d, time(12), UTC),
            match_source=MatchSource.HASHTAG,
            removed=removed,
        )
        for i, d in enumerate(days)
    ]


def progress(today, posts=(), **kwargs):
    return creator_progress(
        assignment(**kwargs), kwargs.get("campaign", CAMPAIGN), posts, today, UTC
    )


@pytest.mark.parametrize(
    ("today", "expected"),
    [
        (date(2026, 10, 19), 0),  # Monday: 3 x 1/7, nothing due yet
        (date(2026, 10, 21), 1),  # Wednesday: 3 x 3/7 = 1.3
        (date(2026, 10, 23), 2),  # Friday: 3 x 5/7 = 2.1
        (date(2026, 10, 25), 3),  # Sunday: all of it
    ],
)
def test_posts_due_follow_the_week(today, expected):
    p = progress(today)
    assert p.expected_by_today == expected
    assert p.status == (ProgressStatus.BEHIND if expected else ProgressStatus.ON_TRACK)
    assert (p.period_start, p.period_end) == (date(2026, 10, 19), date(2026, 10, 25))


def test_counts_only_this_period_campaign_and_creator():
    other_campaign = Campaign(
        organisation_id=ORG,
        name="Other",
        brand="X",
        start_date=CAMPAIGN.start_date,
        end_date=CAMPAIGN.end_date,
        tracking_hashtags=("x",),
    )
    posts = [
        *posts_on(date(2026, 10, 18)),  # last week
        *posts_on(date(2026, 10, 20)),  # counts
        *posts_on(date(2026, 10, 20), creator=uuid.uuid4()),
        *posts_on(date(2026, 10, 20), campaign=other_campaign),
        *posts_on(date(2026, 10, 21), removed=True),
    ]
    p = progress(date(2026, 10, 21), posts)
    assert (p.posts, p.expected_by_today, p.status) == (1, 1, ProgressStatus.ON_TRACK)
    assert p.remaining == 2


def test_met_once_target_is_reached():
    p = progress(date(2026, 10, 20), posts_on(*[date(2026, 10, 19)] * 3))
    assert (p.status, p.remaining) == (ProgressStatus.MET, 0)


def test_monthly_target():
    p = progress(
        date(2026, 10, 16), posts_on(date(2026, 10, 2)), target=4, period=TargetPeriod.MONTH
    )
    # 4 x 16/31 = 2.06 due, 1 posted
    assert (p.period_start, p.period_end) == (date(2026, 10, 1), date(2026, 10, 31))
    assert (p.expected_by_today, p.status) == (2, ProgressStatus.BEHIND)


def test_pace_counts_only_campaign_days_in_a_partial_week():
    # Starts Thursday 22nd: the week has 4 campaign days, so by Friday 3 x 2/4 = 1.5 -> 1 due
    late = Campaign(
        organisation_id=ORG,
        name="Late",
        brand="L",
        start_date=date(2026, 10, 22),
        end_date=date(2026, 11, 30),
        tracking_hashtags=("l",),
    )
    p = progress(date(2026, 10, 23), campaign=late)
    assert p.expected_by_today == 1


def test_before_the_campaign_starts():
    p = progress(date(2026, 9, 20))
    assert (p.status, p.expected_by_today) == (ProgressStatus.UPCOMING, 0)
    assert p.period_start == date(2026, 9, 28)  # its first week


def test_after_the_campaign_ends_judges_its_last_period():
    p = progress(date(2027, 1, 10), posts_on(date(2026, 11, 30)))
    assert (p.period_start, p.period_end) == (date(2026, 11, 30), date(2026, 12, 6))
    # Only Monday 30th was in the campaign, so the whole target was due by then
    assert (p.posts, p.expected_by_today, p.status) == (1, 3, ProgressStatus.BEHIND)
