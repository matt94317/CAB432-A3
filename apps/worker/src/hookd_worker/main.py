"""Worker entry point: long-poll SQS and dispatch each message to a handler."""

import logging
import signal
import threading
from functools import partial

import boto3

from hookd_core.fetchers import make_fetcher
from hookd_core.jobs import SqsJobPublisher
from hookd_core.repositories.assignments import InMemoryAssignmentRepository
from hookd_core.repositories.campaigns import InMemoryCampaignRepository
from hookd_core.repositories.creators import InMemoryCreatorRepository
from hookd_core.repositories.posts import InMemoryPostRepository
from hookd_core.sync import Stores
from hookd_worker.config import settings
from hookd_worker.consumer import SqsConsumer
from hookd_worker.context import WorkerContext
from hookd_worker.handlers import dispatch

log = logging.getLogger("hookd_worker")


def make_stores() -> Stores:
    # TODO: use the API's real stores once the A3 database is chosen (RDS or DynamoDB).
    # In-memory stores are empty here, so until then the API syncs inline (SYNC_MODE).
    return Stores(
        campaigns=InMemoryCampaignRepository(),
        creators=InMemoryCreatorRepository(),
        assignments=InMemoryAssignmentRepository(),
        posts=InMemoryPostRepository(),
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if not settings.sync_queue_url:
        raise SystemExit("SYNC_QUEUE_URL is not set")

    sqs = boto3.client(
        "sqs", region_name=settings.aws_region, endpoint_url=settings.aws_endpoint_url
    )
    context = WorkerContext(
        stores=make_stores(),
        fetcher=make_fetcher(
            settings.tiktok_mode, settings.tiktok_client_key, settings.tiktok_client_secret
        ),
        publisher=SqsJobPublisher(sqs, settings.sync_queue_url),
        tz=settings.campaign_tz,
        lookback_days=settings.sync_lookback_days,
    )

    # ECS stops tasks with SIGTERM: finish the current poll, then exit
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())

    log.info("Polling %s (TikTok mode: %s)", settings.sync_queue_url, settings.tiktok_mode)
    SqsConsumer(sqs, settings.sync_queue_url).run(partial(dispatch, context), stop)
    log.info("Stopped")


if __name__ == "__main__":
    main()
