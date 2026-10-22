"""Tests for the shared sync pipeline: fetch, match by hashtag, upsert (US-13, US-14, US-17)."""

import uuid
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from hookd_core.enums import CampaignStatus, MatchSource, TargetPeriod
from hookd_core.fetchers import FetchedPost
from hookd_core.repositories.assignments import Assignment, InMemoryAssignmentRepository
from hookd_core.repositories.campaigns import Campaign, InMemoryCampaignRepository
from hookd_core.repositories.creators import Creator, InMemoryCreatorRepository
from hookd_core.repositories.posts import InMemoryPostRepository
from hookd_core.sync import Stores, creators_to_sync, sync_creator

BRISBANE = ZoneInfo("Australia/Brisbane")
NOW = datetime(2026, 10, 18, 2, 0, tzinfo=UTC)  # 12pm in Brisbane
TODAY = date(2026, 10, 18)


class FakeFetcher:
    def __init__(self, posts=()):
        self.posts = list(posts)
        self.calls = []

    def fetch_posts(self, handle, since, until, hashtags=()):
        self.calls.append((handle, since, until, tuple(hashtags)))
        return list(self.posts)


def fetched(external_id, *tags, posted_at=NOW - timedelta(days=1), views=100):
    return FetchedPost(
        external_id=external_id,
        url=f"https://www.tiktok.com/@lou/video/{external_id}",
        posted_at=posted_at,
        caption=" ".join(f"#{t}" for t in tags),
        views=views,
    )


@pytest.fixture
def stores():
    return Stores(
        campaigns=InMemoryCampaignRepository(),
        creators=InMemoryCreatorRepository(),
        assignments=InMemoryAssignmentRepository(),
        posts=InMemoryPostRepository(),
    )


@pytest.fixture
def creator(stores):
    return stores.creators.add(Creator(organisation_id=uuid.uuid4(), name="Lou", handle="lou"))


def add_campaign(stores, creator, name, tags, start=TODAY - timedelta(days=10), **kwargs):
    campaign = stores.campaigns.add(
        Campaign(
            organisation_id=creator.organisation_id,
            name=name,
            brand="Lumi",
            start_date=start,
            end_date=kwargs.pop("end", TODAY + timedelta(days=20)),
            tracking_hashtags=tuple(tags),
            **kwargs,
        )
    )
    stores.assignments.add_many(
        [
            Assignment(
                organisation_id=creator.organisation_id,
                campaign_id=campaign.id,
                creator_id=creator.id,
                target_posts=3,
                target_period=TargetPeriod.WEEK,
            )
        ]
    )
    return campaign


def run(stores, fetcher, creator):
    return sync_creator(stores, fetcher, creator.organisation_id, creator.id, now=NOW, tz=BRISBANE)


def test_adds_matching_posts_and_skips_the_rest(stores, creator):
    summer = add_campaign(stores, creator, "Summer", ["lumiglow"])
    fetcher = FakeFetcher([fetched("1", "lumiglow", "fyp"), fetched("2", "fyp")])

    result = run(stores, fetcher, creator)

    assert (result.fetched, result.added, result.updated, result.removed) == (2, 1, 0, 0)
    [post] = stores.posts.list(creator.organisation_id, campaign_id=summer.id)
    assert post.external_id == "1"
    assert post.match_source == MatchSource.HASHTAG
    assert post.hashtags == ("lumiglow", "fyp")
    assert post.last_synced_at == NOW
    assert stores.creators.get(creator.organisation_id, creator.id).last_synced_at == NOW


def test_fetch_window_and_hashtags(stores, creator):
    add_campaign(stores, creator, "Summer", ["lumiglow"], start=TODAY - timedelta(days=3))
    add_campaign(stores, creator, "Old", ["old"], start=TODAY - timedelta(days=90))
    fetcher = FakeFetcher()
    run(stores, fetcher, creator)

    handle, since, until, hashtags = fetcher.calls[0]
    assert handle == "lou"
    assert since == NOW - timedelta(days=30)  # capped at the lookback window
    assert until == NOW
    assert hashtags == ("lumiglow", "old")


def test_window_starts_at_local_midnight_of_the_first_day(stores, creator):
    add_campaign(stores, creator, "Summer", ["lumiglow"], start=TODAY)
    fetcher = FakeFetcher()
    run(stores, fetcher, creator)
    assert fetcher.calls[0][1] == datetime(2026, 10, 18, tzinfo=BRISBANE)


def test_post_date_uses_campaign_timezone(stores, creator):
    # 7am Brisbane on the first day is still the previous day in UTC
    add_campaign(stores, creator, "Summer", ["lumiglow"], start=TODAY)
    early = datetime(2026, 10, 18, 7, 0, tzinfo=BRISBANE)
    result = run(stores, FakeFetcher([fetched("1", "lumiglow", posted_at=early)]), creator)
    assert result.added == 1


def test_resync_updates_metrics_without_duplicates(stores, creator):
    add_campaign(stores, creator, "Summer", ["lumiglow"])
    run(stores, FakeFetcher([fetched("1", "lumiglow", views=100)]), creator)
    result = run(stores, FakeFetcher([fetched("1", "lumiglow", views=250)]), creator)

    assert (result.added, result.updated) == (0, 1)
    [post] = stores.posts.list(creator.organisation_id)
    assert post.views == 250


def test_hashtag_posts_follow_campaign_changes(stores, creator):
    summer = add_campaign(stores, creator, "Summer", ["lumiglow"])
    run(stores, FakeFetcher([fetched("1", "lumiglow")]), creator)

    # The manager changes the tracking hashtag, so the post no longer matches
    stores.campaigns.save(replace(summer, tracking_hashtags=("newtag",)))
    result = run(stores, FakeFetcher([fetched("1", "lumiglow")]), creator)

    assert result.removed == 1
    assert stores.posts.list(creator.organisation_id) == []


def test_manual_changes_stick(stores, creator):
    summer = add_campaign(stores, creator, "Summer", ["lumiglow"])
    autumn = add_campaign(stores, creator, "Autumn", ["autumn"])
    run(stores, FakeFetcher([fetched("1", "lumiglow"), fetched("2", "lumiglow")]), creator)
    moved, removed = sorted(stores.posts.list(creator.organisation_id), key=lambda p: p.external_id)
    stores.posts.save(replace(moved, campaign_id=autumn.id, match_source=MatchSource.MANUAL))
    stores.posts.save(replace(removed, removed=True, match_source=MatchSource.MANUAL))

    run(stores, FakeFetcher([fetched("1", "lumiglow", views=9), fetched("2", "lumiglow")]), creator)

    [post] = stores.posts.list(creator.organisation_id)
    assert (post.external_id, post.campaign_id, post.views) == ("1", autumn.id, 9)
    assert stores.posts.list(creator.organisation_id, campaign_id=summer.id) == []


def test_archived_campaigns_keep_their_posts_but_get_no_new_ones(stores, creator):
    summer = add_campaign(stores, creator, "Summer", ["lumiglow"])
    add_campaign(stores, creator, "Other", ["other"])
    run(stores, FakeFetcher([fetched("1", "lumiglow")]), creator)
    stores.campaigns.save(replace(summer, status=CampaignStatus.ARCHIVED))

    result = run(
        stores, FakeFetcher([fetched("1", "lumiglow", views=7), fetched("2", "lumiglow")]), creator
    )

    assert (result.added, result.updated, result.removed) == (0, 1, 0)
    [post] = stores.posts.list(creator.organisation_id)
    assert (post.campaign_id, post.views) == (summer.id, 7)


def test_nothing_to_sync(stores, creator):
    fetcher = FakeFetcher([fetched("1", "lumiglow")])
    assert run(stores, fetcher, creator) is None  # not on any campaign
    add_campaign(stores, creator, "Later", ["lumiglow"], start=TODAY + timedelta(days=1))
    assert run(stores, fetcher, creator) is None  # not started yet
    assert fetcher.calls == []


def test_creators_to_sync_lists_each_creator_once(stores, creator):
    add_campaign(stores, creator, "Summer", ["a"])
    add_campaign(stores, creator, "Autumn", ["b"])
    archived = add_campaign(stores, creator, "Gone", ["c"], status=CampaignStatus.ARCHIVED)
    assert archived.status == CampaignStatus.ARCHIVED
    assert creators_to_sync(stores, TODAY) == [(creator.organisation_id, creator.id)]


def test_creators_to_sync_skips_long_ended_campaigns(stores, creator):
    ended = TODAY - timedelta(days=31)
    add_campaign(stores, creator, "Old", ["a"], start=TODAY - timedelta(days=90), end=ended)
    assert creators_to_sync(stores, TODAY) == []
