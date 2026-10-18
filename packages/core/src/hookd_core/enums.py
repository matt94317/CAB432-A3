"""Shared enums."""

from enum import StrEnum


class CampaignStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Platform(StrEnum):
    # Instagram and YouTube come later (US-37)
    TIKTOK = "tiktok"


class TargetPeriod(StrEnum):
    WEEK = "week"
    MONTH = "month"


class MatchSource(StrEnum):
    """How a post was linked to its campaign."""

    HASHTAG = "hashtag"  # sync matched a tracking hashtag; sync keeps it up to date
    MANUAL = "manual"  # the manager added, moved or removed it; sync only refreshes metrics
    # AI matching comes later (US-28)
