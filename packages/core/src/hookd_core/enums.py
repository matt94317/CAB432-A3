"""Shared enums. Still to add: MatchSource (hashtag/manual, later ai)."""

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
