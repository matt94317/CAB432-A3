"""Run "Sync now" for a campaign's creators: in this process, or by queueing jobs for
the worker (SYNC_MODE)."""

import uuid
from collections.abc import Sequence
from datetime import UTC, date, datetime, tzinfo
from typing import Protocol

from hookd_api.schemas.sync import SyncFailure, SyncRun
from hookd_api.services import campaigns as campaigns_service
from hookd_api.services.campaigns import CampaignArchived
from hookd_core.enums import CampaignStatus
from hookd_core.fetchers import FetchError, PostFetcher
from hookd_core.jobs import JobPublisher, SyncCreatorJob
from hookd_core.sync import Stores, is_syncable, sync_creator


class SyncRunner(Protocol):
    def run(
        self, stores: Stores, organisation_id: uuid.UUID, creator_ids: Sequence[uuid.UUID]
    ) -> SyncRun: ...


class InlineSync:
    """Sync in the request. One creator failing doesn't stop the others."""

    def __init__(self, fetcher: PostFetcher, tz: tzinfo, lookback_days: int) -> None:
        self.fetcher = fetcher
        self.tz = tz
        self.lookback_days = lookback_days

    def run(
        self, stores: Stores, organisation_id: uuid.UUID, creator_ids: Sequence[uuid.UUID]
    ) -> SyncRun:
        run = SyncRun(mode="inline", creators=0)
        for creator_id in creator_ids:
            try:
                result = sync_creator(
                    stores,
                    self.fetcher,
                    organisation_id,
                    creator_id,
                    now=datetime.now(UTC),
                    tz=self.tz,
                    lookback_days=self.lookback_days,
                )
            except FetchError as exc:
                creator = stores.creators.get(organisation_id, creator_id)
                handle = creator.handle if creator else "?"
                run.failed.append(SyncFailure(creator_id=creator_id, handle=handle, error=str(exc)))
                continue
            if result is not None:
                run.creators += 1
                run.added += result.added
                run.updated += result.updated
                run.removed += result.removed
        run.finished_at = datetime.now(UTC)
        return run


class QueuedSync:
    """Hand the work to the sync worker over SQS."""

    def __init__(self, publisher: JobPublisher) -> None:
        self.publisher = publisher

    def run(
        self, stores: Stores, organisation_id: uuid.UUID, creator_ids: Sequence[uuid.UUID]
    ) -> SyncRun:
        self.publisher.publish([SyncCreatorJob(organisation_id, c) for c in creator_ids])
        return SyncRun(mode="queued", creators=len(creator_ids))


def sync_workspace(
    stores: Stores,
    runner: SyncRunner,
    organisation_id: uuid.UUID,
    today: date,
    lookback_days: int,
) -> SyncRun:
    """Sync every creator on a campaign that's being tracked now (each creator once)."""
    creator_ids: dict[uuid.UUID, None] = {}
    for a in stores.assignments.list(organisation_id):
        campaign = stores.campaigns.get(organisation_id, a.campaign_id)
        if campaign is not None and is_syncable(campaign, today, lookback_days):
            creator_ids[a.creator_id] = None
    return runner.run(stores, organisation_id, list(creator_ids))


def sync_campaign(
    stores: Stores, runner: SyncRunner, organisation_id: uuid.UUID, campaign_id: uuid.UUID
) -> SyncRun:
    """Sync every creator on the campaign (their other campaigns get refreshed too)."""
    campaign = campaigns_service.get(stores.campaigns, organisation_id, campaign_id)
    if campaign.status == CampaignStatus.ARCHIVED:
        raise CampaignArchived
    assigned = stores.assignments.list(organisation_id, campaign_id=campaign_id)
    return runner.run(stores, organisation_id, [a.creator_id for a in assigned])
