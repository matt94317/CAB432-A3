"""EventBridge tick: enqueue one SyncCreatorJob per creator on an active campaign.

One job per creator, not per campaign-creator pair: one fetch covers every
campaign a creator is on. Workers then scale out on queue depth.
"""

import logging

from hookd_core.jobs import ScheduledSyncJob, SyncCreatorJob
from hookd_core.sync import creators_to_sync
from hookd_worker.context import WorkerContext

log = logging.getLogger(__name__)


def handle(job: ScheduledSyncJob, context: WorkerContext) -> None:
    today = context.now().astimezone(context.tz).date()
    pairs = creators_to_sync(context.stores, today, context.lookback_days)
    context.publisher.publish([SyncCreatorJob(org, creator) for org, creator in pairs])
    log.info("Scheduled sync: queued %d creators", len(pairs))
