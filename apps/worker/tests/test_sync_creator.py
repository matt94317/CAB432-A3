"""Tests for the worker: dispatch, scheduled fan-out, sync_creator (with the mock
fetcher) and the SQS consumer."""

import uuid
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from hookd_core.enums import TargetPeriod
from hookd_core.fetchers import FetchError, MockFetcher
from hookd_core.jobs import ScheduledSyncJob, SyncCreatorJob
from hookd_core.repositories.assignments import Assignment, InMemoryAssignmentRepository
from hookd_core.repositories.campaigns import Campaign, InMemoryCampaignRepository
from hookd_core.repositories.creators import Creator, InMemoryCreatorRepository
from hookd_core.repositories.posts import InMemoryPostRepository
from hookd_core.sync import Stores
from hookd_worker.consumer import SqsConsumer
from hookd_worker.context import WorkerContext
from hookd_worker.handlers import dispatch

NOW = datetime(2026, 10, 18, 2, tzinfo=UTC)
TODAY = date(2026, 10, 18)


class FakePublisher:
    def __init__(self):
        self.jobs = []

    def publish(self, jobs):
        self.jobs.extend(jobs)


@pytest.fixture
def stores():
    return Stores(
        campaigns=InMemoryCampaignRepository(),
        creators=InMemoryCreatorRepository(),
        assignments=InMemoryAssignmentRepository(),
        posts=InMemoryPostRepository(),
    )


def context(stores, fetcher=None):
    return WorkerContext(
        stores=stores,
        fetcher=fetcher or MockFetcher(posts_per_week=7, match_rate=1),
        publisher=FakePublisher(),
        tz=ZoneInfo("Australia/Brisbane"),
        lookback_days=30,
        now=lambda: NOW,
    )


def on_campaign(stores, handle, org=None):
    org = org or uuid.uuid4()
    creator = stores.creators.add(Creator(organisation_id=org, name=handle, handle=handle))
    campaign = stores.campaigns.add(
        Campaign(
            organisation_id=org,
            name="Summer",
            brand="Lumi",
            start_date=TODAY - timedelta(days=14),
            end_date=TODAY + timedelta(days=14),
            tracking_hashtags=("lumiglow",),
        )
    )
    stores.assignments.add_many(
        [Assignment(org, campaign.id, creator.id, target_posts=3, target_period=TargetPeriod.WEEK)]
    )
    return creator, campaign


def test_scheduled_tick_queues_every_creator(stores):
    lou, _ = on_campaign(stores, "lou")
    amy, _ = on_campaign(stores, "amy")
    ctx = context(stores)

    dispatch(ctx, ScheduledSyncJob().to_message())

    queued = {(j.organisation_id, j.creator_id) for j in ctx.publisher.jobs}
    assert queued == {(lou.organisation_id, lou.id), (amy.organisation_id, amy.id)}


def test_sync_creator_job_with_mock_fetcher(stores):
    lou, summer = on_campaign(stores, "lou")
    job = SyncCreatorJob(lou.organisation_id, lou.id)

    dispatch(context(stores), job.to_message())
    posts = stores.posts.list(lou.organisation_id, campaign_id=summer.id)
    assert posts
    assert all("lumiglow" in p.hashtags for p in posts)
    assert stores.creators.get(lou.organisation_id, lou.id).last_synced_at == NOW

    # Idempotent: running the same job again adds nothing
    dispatch(context(stores), job.to_message())
    assert len(stores.posts.list(lou.organisation_id)) == len(posts)


def test_job_for_a_deleted_creator_is_a_no_op(stores):
    dispatch(context(stores), SyncCreatorJob(uuid.uuid4(), uuid.uuid4()).to_message())


def test_fetch_errors_propagate_for_retry(stores):
    class Down:
        def fetch_posts(self, *args, **kwargs):
            raise FetchError("TikTok is down")

    lou, _ = on_campaign(stores, "lou")
    with pytest.raises(FetchError):
        dispatch(context(stores, Down()), SyncCreatorJob(lou.organisation_id, lou.id).to_message())


class FakeSqs:
    def __init__(self, bodies):
        self.messages = [{"Body": b, "ReceiptHandle": f"r{i}"} for i, b in enumerate(bodies)]
        self.deleted = []

    def receive_message(self, **kwargs):
        messages, self.messages = self.messages, []
        return {"Messages": messages}

    def delete_message(self, QueueUrl, ReceiptHandle):  # noqa: N803 (boto3 argument names)
        self.deleted.append(ReceiptHandle)


def test_consumer_deletes_only_handled_messages():
    sqs = FakeSqs(["ok", "boom", "ok"])

    def handle(body):
        if body == "boom":
            raise RuntimeError("failed")

    assert SqsConsumer(sqs, "q").poll_once(handle) == 2
    assert sqs.deleted == ["r0", "r2"]  # r1 stays for retry, then the DLQ
