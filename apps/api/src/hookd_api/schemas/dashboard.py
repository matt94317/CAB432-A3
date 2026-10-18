"""Campaign dashboard, creator performance and behind-target models (US-19 to US-22)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from hookd_api.schemas.assignment import AssignedCreator
from hookd_api.schemas.campaign import CampaignPhase, CampaignRead
from hookd_api.schemas.post import PostRead
from hookd_core.enums import CampaignStatus, TargetPeriod
from hookd_core.progress import ProgressStatus


class Metrics(BaseModel):
    posts: int
    views: int
    likes: int
    comments: int
    shares: int
    engagement: int = Field(description="likes + comments + shares")
    engagement_rate: float | None = Field(
        description="engagement / views, 0 to 1. Null when there are no views"
    )


class PeriodProgress(BaseModel):
    """A creator's posts vs target for their current week or month."""

    target_posts: int
    target_period: TargetPeriod
    period_start: date
    period_end: date
    posts_this_period: int
    expected_by_today: int = Field(description="Posts due so far at an even pace (rounded down)")
    remaining: int
    status: ProgressStatus = Field(
        description="met, on_track, behind (fewer posts than expected by today) or upcoming"
    )


class CreatorProgressRow(PeriodProgress):
    creator: AssignedCreator
    totals: Metrics = Field(description="All of this creator's posts in the campaign")


class DailyMetrics(BaseModel):
    date: date
    posts: int
    views: int = Field(description="Current views of the posts made that day")
    engagement: int


class CampaignDashboard(BaseModel):
    campaign: CampaignRead
    today: date = Field(description="In the campaign timezone")
    creators: list[CreatorProgressRow] = Field(description="Behind first, then by name")
    behind_count: int
    totals: Metrics
    daily: list[DailyMetrics] = Field(description="Campaign start to today (or its end)")
    last_synced_at: datetime | None = Field(
        description="Least recently synced creator. Null if any creator hasn't synced yet"
    )
    generated_at: datetime


class BehindTargetItem(PeriodProgress):
    campaign_id: uuid.UUID
    campaign_name: str
    brand: str
    creator: AssignedCreator
    email: str | None


class CreatorCampaignPerformance(PeriodProgress):
    campaign_id: uuid.UUID
    name: str
    brand: str
    campaign_status: CampaignStatus
    phase: CampaignPhase
    totals: Metrics


class CreatorPerformance(BaseModel):
    creator_id: uuid.UUID
    today: date
    totals: Metrics = Field(description="Across every campaign")
    campaigns: list[CreatorCampaignPerformance]
    posts: list[PostRead] = Field(description="Every tracked post, newest first")
