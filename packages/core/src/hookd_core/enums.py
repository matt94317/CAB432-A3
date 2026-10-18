"""Shared enums. Still to add: Platform (tiktok), TargetPeriod (week/month),
AssignmentStatus, MatchSource (hashtag/manual, later ai)."""

from enum import StrEnum


class CampaignStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
