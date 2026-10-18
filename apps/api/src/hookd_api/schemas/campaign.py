"""Campaign request and response models (US-03 to US-06)."""

import re
import uuid
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, Field, StringConstraints, model_validator

from hookd_core.enums import CampaignStatus

_HASHTAG = re.compile(r"^\w{1,100}$")
MAX_HASHTAGS = 20

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


def normalise_hashtags(tags: list[str]) -> list[str]:
    """'#Summer24', ' summer24 ' -> 'summer24'. Lowercase, no '#', no duplicates, order kept."""
    seen: dict[str, None] = {}
    for raw in tags:
        tag = raw.strip().lstrip("#").lower()
        if not tag:
            continue
        if not _HASHTAG.match(tag):
            raise ValueError(f"'{raw}' is not a valid hashtag (letters, numbers and _ only)")
        seen[tag] = None
    if len(seen) > MAX_HASHTAGS:
        raise ValueError(f"Use at most {MAX_HASHTAGS} tracking hashtags")
    return list(seen)


Hashtags = Annotated[list[str], AfterValidator(normalise_hashtags)]


class CampaignPhase(StrEnum):
    UPCOMING = "upcoming"
    LIVE = "live"
    ENDED = "ended"


def campaign_phase(start: date, end: date, today: date | None = None) -> CampaignPhase:
    today = today or datetime.now(UTC).date()
    if today < start:
        return CampaignPhase.UPCOMING
    if today > end:
        return CampaignPhase.ENDED
    return CampaignPhase.LIVE


def _check_dates(start: date | None, end: date | None) -> None:
    if start and end and end < start:
        raise ValueError("End date must be on or after the start date")


class CampaignCreate(BaseModel):
    name: Name
    brand: Name
    start_date: date
    end_date: date
    tracking_hashtags: Hashtags = Field(
        min_length=1, description="Posts with any of these hashtags count toward the campaign"
    )

    @model_validator(mode="after")
    def dates_in_order(self) -> Self:
        _check_dates(self.start_date, self.end_date)
        return self


class CampaignUpdate(BaseModel):
    """Partial update: only the fields sent are changed."""

    name: Name | None = None
    brand: Name | None = None
    start_date: date | None = None
    end_date: date | None = None
    tracking_hashtags: Hashtags | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def dates_in_order(self) -> Self:
        _check_dates(self.start_date, self.end_date)
        return self


class CampaignProgress(BaseModel):
    """Posts vs target across assigned creators, for each creator's current target period."""

    creators: int
    posts: int
    target_posts: int = Field(description="Sum of every assigned creator's per-period target")
    behind: int = Field(default=0, description="Creators behind target this period")


class CampaignRead(BaseModel):
    id: uuid.UUID
    name: str
    brand: str
    start_date: date
    end_date: date
    tracking_hashtags: list[str]
    status: CampaignStatus
    phase: CampaignPhase
    created_at: datetime
    updated_at: datetime


class CampaignListItem(CampaignRead):
    progress: CampaignProgress | None = Field(
        default=None, description="Null until creators are assigned"
    )
