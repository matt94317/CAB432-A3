"""Campaign dashboard, creator performance and behind-target lists (US-19 to US-22).

The campaign dashboard is cached per organisation (see hookd_core.cache).
"""

import uuid
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta, tzinfo

from hookd_api.schemas.dashboard import (
    BehindTargetItem,
    CampaignDashboard,
    CreatorCampaignPerformance,
    CreatorPerformance,
    CreatorProgressRow,
    DailyMetrics,
    Metrics,
)
from hookd_api.services import campaigns as campaigns_service
from hookd_api.services import creators as creators_service
from hookd_api.services import posts as posts_service
from hookd_api.services.assignments import to_read as assignment_to_read
from hookd_core.cache import DashboardCache
from hookd_core.enums import CampaignStatus
from hookd_core.progress import CreatorProgress, ProgressStatus, creator_progress
from hookd_core.repositories.posts import Post
from hookd_core.sync import Stores

_STATUS_ORDER = {
    ProgressStatus.BEHIND: 0,
    ProgressStatus.ON_TRACK: 1,
    ProgressStatus.MET: 2,
    ProgressStatus.UPCOMING: 3,
}


def metrics(posts: Iterable[Post]) -> Metrics:
    posts = list(posts)
    views = sum(p.views for p in posts)
    likes = sum(p.likes for p in posts)
    comments = sum(p.comments for p in posts)
    shares = sum(p.shares for p in posts)
    engagement = likes + comments + shares
    return Metrics(
        posts=len(posts),
        views=views,
        likes=likes,
        comments=comments,
        shares=shares,
        engagement=engagement,
        engagement_rate=round(engagement / views, 4) if views else None,
    )


def _period_fields(progress: CreatorProgress) -> dict:
    return {
        "target_posts": progress.target_posts,
        "target_period": progress.target_period,
        "period_start": progress.period_start,
        "period_end": progress.period_end,
        "posts_this_period": progress.posts,
        "expected_by_today": progress.expected_by_today,
        "remaining": progress.remaining,
        "status": progress.status,
    }


def daily_metrics(posts: list[Post], start: date, end: date, tz: tzinfo) -> list[DailyMetrics]:
    by_day: dict[date, list[Post]] = defaultdict(list)
    for p in posts:
        by_day[p.posted_at.astimezone(tz).date()].append(p)
    days = []
    day = start
    while day <= end:
        m = metrics(by_day.get(day, []))
        days.append(DailyMetrics(date=day, posts=m.posts, views=m.views, engagement=m.engagement))
        day += timedelta(days=1)
    return days


def campaign_dashboard(
    stores: Stores,
    cache: DashboardCache,
    organisation_id: uuid.UUID,
    campaign_id: uuid.UUID,
    tz: tzinfo,
) -> tuple[CampaignDashboard, bool]:
    """The dashboard and whether it came from the cache."""
    campaign = campaigns_service.get(stores.campaigns, organisation_id, campaign_id)
    today = datetime.now(tz).date()
    key = f"campaign:{campaign_id}:{today.isoformat()}"
    if cached := cache.get(organisation_id, key):
        return CampaignDashboard.model_validate_json(cached), True

    posts = stores.posts.list(organisation_id, campaign_id=campaign_id)
    creators = {c.id: c for c in stores.creators.list(organisation_id)}
    rows = []
    for a in stores.assignments.list(organisation_id, campaign_id=campaign_id):
        creator = creators.get(a.creator_id)
        if creator is None:
            continue
        progress = creator_progress(a, campaign, posts, today, tz)
        rows.append(
            CreatorProgressRow(
                creator=assignment_to_read(a, creator).creator,
                totals=metrics(p for p in posts if p.creator_id == a.creator_id),
                **_period_fields(progress),
            )
        )
    rows.sort(key=lambda r: (_STATUS_ORDER[r.status], r.creator.name.lower()))

    synced = [r.creator.last_synced_at for r in rows]
    dashboard = CampaignDashboard(
        campaign=campaigns_service.to_read(campaign),
        today=today,
        creators=rows,
        behind_count=sum(r.status == ProgressStatus.BEHIND for r in rows),
        totals=metrics(posts),
        daily=daily_metrics(posts, campaign.start_date, min(today, campaign.end_date), tz),
        last_synced_at=min(synced) if synced and None not in synced else None,  # type: ignore[type-var]
        generated_at=datetime.now(UTC),
    )
    cache.set(organisation_id, key, dashboard.model_dump_json())
    return dashboard, False


def behind_target(stores: Stores, organisation_id: uuid.UUID, tz: tzinfo) -> list[BehindTargetItem]:
    """Everyone behind on a live, active campaign this period: who to chase, most behind first."""
    today = datetime.now(tz).date()
    campaigns = {
        c.id: c
        for c in stores.campaigns.list(organisation_id, CampaignStatus.ACTIVE)
        if c.start_date <= today <= c.end_date
    }
    creators = {c.id: c for c in stores.creators.list(organisation_id)}
    posts = stores.posts.list(organisation_id)
    items = []
    for a in stores.assignments.list(organisation_id):
        campaign = campaigns.get(a.campaign_id)
        creator = creators.get(a.creator_id)
        if campaign is None or creator is None:
            continue
        progress = creator_progress(a, campaign, posts, today, tz)
        if progress.is_behind:
            items.append(
                BehindTargetItem(
                    campaign_id=campaign.id,
                    campaign_name=campaign.name,
                    brand=campaign.brand,
                    creator=assignment_to_read(a, creator).creator,
                    email=creator.email,
                    **_period_fields(progress),
                )
            )
    return sorted(
        items,
        key=lambda i: (
            -(i.expected_by_today - i.posts_this_period),
            i.creator.name.lower(),
            i.campaign_name.lower(),
        ),
    )


def creator_performance(
    stores: Stores, organisation_id: uuid.UUID, creator_id: uuid.UUID, tz: tzinfo
) -> CreatorPerformance:
    """One creator across every campaign they're on (US-21)."""
    creator = creators_service.get(stores.creators, organisation_id, creator_id)
    today = datetime.now(tz).date()
    posts = stores.posts.list(organisation_id, creator_id=creator_id)
    rows = []
    for a in stores.assignments.list(organisation_id, creator_id=creator_id):
        campaign = stores.campaigns.get(organisation_id, a.campaign_id)
        if campaign is None:
            continue
        progress = creator_progress(a, campaign, posts, today, tz)
        rows.append(
            CreatorCampaignPerformance(
                campaign_id=campaign.id,
                name=campaign.name,
                brand=campaign.brand,
                campaign_status=campaign.status,
                phase=campaigns_service.to_read(campaign).phase,
                totals=metrics(p for p in posts if p.campaign_id == campaign.id),
                **_period_fields(progress),
            )
        )
    rows.sort(key=lambda r: (r.campaign_status == CampaignStatus.ARCHIVED, r.name.lower()))
    return CreatorPerformance(
        creator_id=creator.id,
        today=today,
        totals=metrics(posts),
        campaigns=rows,
        posts=[posts_service.to_read(p, creator) for p in posts],
    )
