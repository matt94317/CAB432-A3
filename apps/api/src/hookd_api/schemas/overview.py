"""Workspace overview: the page a manager lands on after logging in."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from hookd_api.schemas.dashboard import DailyMetrics, Metrics


class AttentionItem(BaseModel):
    kind: Literal["behind", "ending_soon", "no_creators", "not_synced"]
    title: str = Field(description="e.g. '2 creators behind target'")
    detail: str = Field(description="Usually the campaign name")
    campaign_id: uuid.UUID | None = None


class ActiveCampaign(BaseModel):
    id: uuid.UUID
    name: str
    brand: str
    start_date: date
    end_date: date
    creators: int
    posts: int = Field(description="Posts this period, each creator capped at their target")
    target_posts: int
    behind: int


class Milestone(BaseModel):
    campaign_id: uuid.UUID
    name: str
    end_date: date


class StandoutCreator(BaseModel):
    id: uuid.UUID
    name: str
    handle: str
    posts: int
    views: int
    engagement_rate: float | None


class Overview(BaseModel):
    month: str = Field(description="YYYY-MM")
    period_start: date
    period_end: date = Field(description="Last day counted: today for the current month")
    compare_start: date
    compare_end: date
    comparing: Literal["same_days", "full_month"] = Field(
        description="same_days: month to date vs the same days last month"
    )
    today: date
    totals: Metrics = Field(description="Posts published in the period")
    previous: Metrics = Field(description="The comparison period")
    active_creators: int = Field(description="Creators on campaigns running in the period")
    previous_active_creators: int
    new_creators: int = Field(description="Creators first assigned in the period")
    daily: list[DailyMetrics]
    previous_daily: list[DailyMetrics] = Field(description="The whole previous month")
    needs_attention: list[AttentionItem]
    active_campaigns: list[ActiveCampaign] = Field(description="Live now, ending soonest first")
    next_milestone: Milestone | None
    standout_creators: list[StandoutCreator] = Field(description="Top 3 by views in the period")
    last_synced_at: datetime | None = Field(description="Most recent creator sync")
    generated_at: datetime
