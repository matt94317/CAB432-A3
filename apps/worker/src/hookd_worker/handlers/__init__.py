"""Maps job type -> handler function."""

from collections.abc import Callable

from hookd_core.jobs import Job, ScheduledSyncJob, SyncCreatorJob, parse_job
from hookd_worker.context import WorkerContext
from hookd_worker.handlers import schedule_fanout, sync_creator

HANDLERS: dict[type, Callable[[Job, WorkerContext], None]] = {
    ScheduledSyncJob: schedule_fanout.handle,
    SyncCreatorJob: sync_creator.handle,
}


def dispatch(context: WorkerContext, body: str) -> None:
    """Handle one queue message. Raises if it should be retried."""
    job = parse_job(body)
    HANDLERS[type(job)](job, context)
