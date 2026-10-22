"""Publish sync jobs to SQS (manual 'sync now' requests when SYNC_MODE=queue)."""

import boto3

from hookd_api.config import settings
from hookd_core.jobs import SqsJobPublisher


def make_publisher() -> SqsJobPublisher:
    if not settings.sync_queue_url:
        raise RuntimeError("SYNC_MODE=queue needs SYNC_QUEUE_URL")
    client = boto3.client(
        "sqs", region_name=settings.aws_region, endpoint_url=settings.aws_endpoint_url
    )
    return SqsJobPublisher(client, settings.sync_queue_url)
