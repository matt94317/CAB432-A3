"""Sync one creator's posts and metrics (US-13, US-14, US-17, US-18).

Shared by the worker (scheduled syncs from SQS) and the API ("Sync now"). Safe
to run twice: posts are upserted by their platform id.

Who owns a post's campaign link:
- MatchSource.HASHTAG posts belong to sync. Each sync re-matches them, so they
  follow campaign hashtag and date changes, and are deleted once they no longer
  match any campaign.
- MatchSource.MANUAL posts (added, moved or removed by the manager) keep their
  campaign. Sync only refreshes their caption and metrics.
"""

import uuid
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta, tzinfo

from hookd_core.enums import CampaignStatus, MatchSource
from hookd_core.fetchers.base import FetchedPost, PostFetcher
from hookd_core.matching import extract_hashtags, match_campaign, normalise_hashtags
from hookd_core.repositories.assignments import AssignmentRepository
from hookd_core.repositories.campaigns import Campaign, CampaignRepository
from hookd_core.repositories.creators import CreatorRepository
from hookd_core.repositories.posts import Post, PostRepository

DEFAULT_LOOKBACK_DAYS = 30


@dataclass(frozen=True)
class Stores:
    campaigns: CampaignRepository
    creators: CreatorRepository
    assignments: AssignmentRepository
    posts: PostRepository


@dataclass(frozen=True)
class SyncResult:
    creator_id: uuid.UUID
    fetched: int
    added: int
    updated: int
    removed: int  # hashtag-matched posts that no longer match a campaign


def is_syncable(campaign: Campaign, today: date, lookback_days: int) -> bool:
    """Active, started, and not ended so long ago that its posts are outside the window."""
    return (
        campaign.status == CampaignStatus.ACTIVE
        and campaign.start_date <= today
        and campaign.end_date >= today - timedelta(days=lookback_days)
    )


def creators_to_sync(
    stores: Stores, today: date, lookback_days: int = DEFAULT_LOOKBACK_DAYS
) -> list[tuple[uuid.UUID, uuid.UUID]]:
    """(organisation_id, creator_id) for everyone on at least one syncable campaign.

    Each creator is listed once, however many campaigns they're on, because one
    fetch covers all of them.
    """
    pairs: dict[tuple[uuid.UUID, uuid.UUID], None] = {}
    for assignment in stores.assignments.list_all():
        campaign = stores.campaigns.get(assignment.organisation_id, assignment.campaign_id)
        if campaign is not None and is_syncable(campaign, today, lookback_days):
            pairs[(assignment.organisation_id, assignment.creator_id)] = None
    return list(pairs)


def sync_creator(
    stores: Stores,
    fetcher: PostFetcher,
    organisation_id: uuid.UUID,
    creator_id: uuid.UUID,
    *,
    now: datetime,
    tz: tzinfo,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> SyncResult | None:
    """Fetch, match and upsert one creator's posts. None if there's nothing to sync.

    `tz` is the timezone campaign dates are in, so a post made early on a
    campaign's first day (local time) counts toward it.
    """
    creator = stores.creators.get(organisation_id, creator_id)
    if creator is None:
        return None  # removed after the job was queued

    assigned = [
        campaign
        for a in stores.assignments.list(organisation_id, creator_id=creator_id)
        if (campaign := stores.campaigns.get(organisation_id, a.campaign_id)) is not None
    ]
    today = now.astimezone(tz).date()
    candidates = [c for c in assigned if is_syncable(c, today, lookback_days)]
    if not candidates:
        return None

    earliest = datetime.combine(min(c.start_date for c in candidates), time.min, tz)
    since = max(earliest, now - timedelta(days=lookback_days))
    hashtags = sorted({t for c in candidates for t in c.tracking_hashtags})
    fetched = fetcher.fetch_posts(creator.handle, since, now, hashtags)

    candidate_ids = {c.id for c in candidates}
    added = updated = removed = 0
    for item in fetched:
        hashtags_used = normalise_hashtags(item.hashtags) or extract_hashtags(item.caption)
        existing = stores.posts.get_by_external_id(
            organisation_id, creator_id, creator.platform, item.external_id
        )
        if existing is not None and (
            existing.match_source == MatchSource.MANUAL
            or existing.removed
            or existing.campaign_id not in candidate_ids  # e.g. its campaign was archived
        ):
            stores.posts.save(_refresh(existing, item, hashtags_used, now))
            updated += 1
            continue

        match = match_campaign(hashtags_used, item.posted_at.astimezone(tz).date(), candidates)
        if match is None:
            if existing is not None:
                stores.posts.delete(organisation_id, existing.id)
                removed += 1
            continue

        if existing is None:
            stores.posts.add(
                Post(
                    organisation_id=organisation_id,
                    creator_id=creator_id,
                    campaign_id=match.id,
                    platform=creator.platform,
                    external_id=item.external_id,
                    url=item.url,
                    posted_at=item.posted_at,
                    match_source=MatchSource.HASHTAG,
                    caption=item.caption,
                    hashtags=hashtags_used,
                    views=item.views,
                    likes=item.likes,
                    comments=item.comments,
                    shares=item.shares,
                    last_synced_at=now,
                )
            )
            added += 1
        else:
            refreshed = _refresh(existing, item, hashtags_used, now)
            stores.posts.save(replace(refreshed, campaign_id=match.id))
            updated += 1

    stores.creators.save(replace(creator, last_synced_at=now))
    return SyncResult(
        creator_id=creator_id, fetched=len(fetched), added=added, updated=updated, removed=removed
    )


def _refresh(post: Post, item: FetchedPost, hashtags: tuple[str, ...], now: datetime) -> Post:
    return replace(
        post,
        url=item.url,
        posted_at=item.posted_at,
        caption=item.caption,
        hashtags=hashtags,
        views=item.views,
        likes=item.likes,
        comments=item.comments,
        shares=item.shares,
        last_synced_at=now,
    )
