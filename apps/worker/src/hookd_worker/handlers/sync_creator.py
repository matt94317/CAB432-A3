"""Fetch a creator's recent posts + metrics, match to campaigns by hashtag,
upsert (idempotent), then invalidate the dashboard cache (US-13, US-14, US-17).

The work itself is hookd_core.sync.sync_creator, shared with the API's inline mode.
"""

import logging

from hookd_core.jobs import SyncCreatorJob
from hookd_core.sync import sync_creator
from hookd_worker.context import WorkerContext

log = logging.getLogger(__name__)


def handle(job: SyncCreatorJob, context: WorkerContext) -> None:
    # A FetchError propagates so SQS retries the job (then the DLQ)
    result = sync_creator(
        context.stores,
        context.fetcher,
        job.organisation_id,
        job.creator_id,
        now=context.now(),
        tz=context.tz,
        lookback_days=context.lookback_days,
    )
    if result is None:
        log.info("Creator %s: nothing to sync", job.creator_id)
        return
    log.info(
        "Creator %s: fetched %d, added %d, updated %d, removed %d",
        job.creator_id,
        result.fetched,
        result.added,
        result.updated,
        result.removed,
    )
    context.cache.invalidate(job.organisation_id)
