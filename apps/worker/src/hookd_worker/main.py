"""Worker entry point: long-poll SQS and dispatch each message to a handler."""

import logging
import signal
import threading
from functools import partial

import boto3

from hookd_core.cache import make_cache
from hookd_core.fetchers import make_fetcher
from hookd_core.jobs import SqsJobPublisher
from hookd_core.storage import make_storage
from hookd_worker.config import settings
from hookd_worker.consumer import SqsConsumer
from hookd_worker.context import WorkerContext
from hookd_worker.handlers import dispatch

log = logging.getLogger("hookd_worker")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if not settings.sync_queue_url:
        raise SystemExit("SYNC_QUEUE_URL is not set")

    sqs = boto3.client(
        "sqs", region_name=settings.aws_region, endpoint_url=settings.aws_endpoint_url
    )
    if settings.storage == "memory":
        log.warning("STORAGE=memory: the worker can't see the API's data, so syncs do nothing")
    storage = make_storage(
        settings.storage,
        table_name=settings.dynamodb_table,
        region=settings.aws_region,
        endpoint_url=settings.dynamodb_endpoint_url,
        create_table=settings.dynamodb_create_table,
    )
    context = WorkerContext(
        stores=storage.stores,
        fetcher=make_fetcher(
            settings.tiktok_mode, settings.tiktok_client_key, settings.tiktok_client_secret
        ),
        publisher=SqsJobPublisher(sqs, settings.sync_queue_url),
        tz=settings.campaign_tz,
        lookback_days=settings.sync_lookback_days,
        cache=make_cache(settings.redis_url),
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
