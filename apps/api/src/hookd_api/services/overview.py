"""Workspace overview: totals vs last month, performance, to-dos, live campaigns and
standout creators. Cached per organisation like the campaign dashboard."""

import calendar
import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta, tzinfo

from hookd_api.errors import InvalidRequest
from hookd_api.schemas.overview import (
    ActiveCampaign,
    AttentionItem,
    Milestone,
    Overview,
    StandoutCreator,
)
from hookd_api.services import campaigns as campaigns_service
from hookd_api.services.dashboard import daily_metrics, metrics
from hookd_core.cache import DashboardCache
from hookd_core.enums import CampaignStatus
from hookd_core.repositories.assignments import Assignment
from hookd_core.repositories.campaigns import Campaign
from hookd_core.repositories.posts import Post
from hookd_core.sync import Stores

ENDING_SOON_DAYS = 7


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def _parse_month(month: str | None, today: date) -> tuple[int, int]:
    if month is None:
        return today.year, today.month
    try:
        year, number = (int(part) for part in month.split("-"))
        date(year, number, 1)
    except ValueError as exc:
        raise InvalidRequest("month must look like 2026-10") from exc
    return year, number


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _ends_in(days: int) -> str:
    return {0: "wraps today", 1: "wraps tomorrow"}.get(days, f"wraps in {days} days")


def overview(
    stores: Stores,
    cache: DashboardCache,
    organisation_id: uuid.UUID,
    tz: tzinfo,
    month: str | None = None,
) -> tuple[Overview, bool]:
    """The overview and whether it came from the cache."""
    today = datetime.now(tz).date()
    year, number = _parse_month(month, today)
    start, month_end = _month_bounds(year, number)
    current = start <= today <= month_end
    end = today if current else month_end

    previous_month = start - timedelta(days=1)
    compare_start, previous_end = _month_bounds(previous_month.year, previous_month.month)
    days_so_far = (end - start).days + 1
    compare_end = (
        min(previous_end, compare_start + timedelta(days=days_so_far - 1))
        if current
        else previous_end
    )

    key = f"overview:{year}-{number:02d}:{today.isoformat()}"
    if cached := cache.get(organisation_id, key):
        return Overview.model_validate_json(cached), True

    def posted_on(post: Post) -> date:
        return post.posted_at.astimezone(tz).date()

    posts = stores.posts.list(organisation_id)
    period_posts = [p for p in posts if start <= posted_on(p) <= end]
    compare_posts = [p for p in posts if compare_start <= posted_on(p) <= compare_end]

    campaigns = {c.id: c for c in stores.campaigns.list(organisation_id)}
    assignments = stores.assignments.list(organisation_id)
    creators = {c.id: c for c in stores.creators.list(organisation_id)}

    def running(a: Assignment, first: date, last: date) -> bool:
        c = campaigns.get(a.campaign_id)
        return (
            c is not None
            and c.status == CampaignStatus.ACTIVE
            and c.start_date <= last
            and c.end_date >= first
        )

    first_assigned: dict[uuid.UUID, date] = {}
    for a in assignments:
        assigned_on = a.created_at.astimezone(tz).date()
        first_assigned[a.creator_id] = min(
            first_assigned.get(a.creator_id, assigned_on), assigned_on
        )

    by_campaign: dict[uuid.UUID, list[Assignment]] = defaultdict(list)
    for a in assignments:
        by_campaign[a.campaign_id].append(a)
    posts_by_campaign: dict[uuid.UUID, list[Post]] = defaultdict(list)
    for p in posts:
        posts_by_campaign[p.campaign_id].append(p)

    live = sorted(
        (
            c
            for c in campaigns.values()
            if c.status == CampaignStatus.ACTIVE and c.start_date <= today <= c.end_date
        ),
        key=lambda c: (c.end_date, c.name.lower()),
    )
    active_rows = []
    for c in live:
        progress = campaigns_service.progress(
            c, by_campaign[c.id], posts_by_campaign[c.id], today, tz
        )
        active_rows.append(
            ActiveCampaign(
                id=c.id,
                name=c.name,
                brand=c.brand,
                start_date=c.start_date,
                end_date=c.end_date,
                creators=progress.creators if progress else 0,
                posts=progress.posts if progress else 0,
                target_posts=progress.target_posts if progress else 0,
                behind=progress.behind if progress else 0,
            )
        )

    overview = Overview(
        month=f"{year}-{number:02d}",
        period_start=start,
        period_end=end,
        compare_start=compare_start,
        compare_end=compare_end,
        comparing="same_days" if current else "full_month",
        today=today,
        totals=metrics(period_posts),
        previous=metrics(compare_posts),
        active_creators=len({a.creator_id for a in assignments if running(a, start, end)}),
        previous_active_creators=len(
            {a.creator_id for a in assignments if running(a, compare_start, compare_end)}
        ),
        new_creators=sum(1 for d in first_assigned.values() if start <= d <= end),
        daily=daily_metrics(period_posts, start, end, tz) if end >= start else [],
        previous_daily=daily_metrics(
            [p for p in posts if compare_start <= posted_on(p) <= previous_end],
            compare_start,
            previous_end,
            tz,
        ),
        needs_attention=_needs_attention(
            campaigns, live, active_rows, by_campaign, creators, today
        ),
        active_campaigns=active_rows,
        next_milestone=Milestone(
            campaign_id=live[0].id, name=live[0].name, end_date=live[0].end_date
        )
        if live
        else None,
        standout_creators=_standouts(period_posts, creators),
        last_synced_at=max(
            (c.last_synced_at for c in creators.values() if c.last_synced_at), default=None
        ),
        generated_at=datetime.now(UTC),
    )
    cache.set(organisation_id, key, overview.model_dump_json())
    return overview, False


def _needs_attention(
    campaigns: dict[uuid.UUID, Campaign],
    live: list[Campaign],
    rows: list[ActiveCampaign],
    by_campaign: dict[uuid.UUID, list[Assignment]],
    creators: dict,
    today: date,
) -> list[AttentionItem]:
    """To-dos from the current state: who's behind, what's wrapping up, what's unstaffed,
    who has never been synced. Most urgent first."""
    items = [
        AttentionItem(
            kind="behind",
            title=f"{_plural(row.behind, 'creator')} behind target",
            detail=row.name,
            campaign_id=row.id,
        )
        for row in rows
        if row.behind
    ]
    for c, row in zip(live, rows, strict=True):
        days_left = (c.end_date - today).days
        if days_left <= ENDING_SOON_DAYS:
            progress = (
                f" · {row.posts} / {row.target_posts} posts this period" if row.target_posts else ""
            )
            items.append(
                AttentionItem(
                    kind="ending_soon",
                    title=f"{c.name} {_ends_in(days_left)}",
                    detail=f"{c.brand}{progress}",
                    campaign_id=c.id,
                )
            )
    for c in sorted(campaigns.values(), key=lambda c: c.start_date):
        if c.status == CampaignStatus.ACTIVE and c.end_date >= today and not by_campaign[c.id]:
            items.append(
                AttentionItem(
                    kind="no_creators",
                    title=f"No creators on {c.name}",
                    detail="Assign creators to start tracking",
                    campaign_id=c.id,
                )
            )
    unsynced: dict[uuid.UUID, uuid.UUID] = {}  # creator -> a live campaign they're on
    live_ids = {c.id for c in live}
    for campaign_id in live_ids:
        for a in by_campaign[campaign_id]:
            creator = creators.get(a.creator_id)
            if creator is not None and creator.last_synced_at is None:
                unsynced.setdefault(a.creator_id, campaign_id)
    if unsynced:
        campaign = campaigns[next(iter(unsynced.values()))]
        items.append(
            AttentionItem(
                kind="not_synced",
                title=f"{_plural(len(unsynced), 'creator')} not synced yet",
                detail=f"Sync now on {campaign.name}",
                campaign_id=campaign.id,
            )
        )
    return items


def _standouts(posts: list[Post], creators: dict) -> list[StandoutCreator]:
    by_creator: dict[uuid.UUID, list[Post]] = defaultdict(list)
    for p in posts:
        by_creator[p.creator_id].append(p)
    rows = []
    for creator_id, own in by_creator.items():
        creator = creators.get(creator_id)
        if creator is None:
            continue
        m = metrics(own)
        rows.append(
            StandoutCreator(
                id=creator.id,
                name=creator.name,
                handle=creator.handle,
                posts=m.posts,
                views=m.views,
                engagement_rate=m.engagement_rate,
            )
        )
    return sorted(rows, key=lambda r: (-r.views, r.name.lower()))[:3]
