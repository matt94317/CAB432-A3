"""Sync job messages on the SQS queue, shared by the API (publishes), EventBridge
(publishes the scheduled tick) and the worker (consumes).

- {"type": "scheduled_sync"}: EventBridge tick; the worker fans out one
  sync_creator job per creator on an active campaign.
- {"type": "sync_creator", "organisation_id": "...", "creator_id": "..."}
"""

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

SCHEDULED_SYNC = "scheduled_sync"
SYNC_CREATOR = "sync_creator"
SQS_BATCH_SIZE = 10


@dataclass(frozen=True)
class ScheduledSyncJob:
    def to_message(self) -> str:
        return json.dumps({"type": SCHEDULED_SYNC})


@dataclass(frozen=True)
class SyncCreatorJob:
    organisation_id: uuid.UUID
    creator_id: uuid.UUID

    def to_message(self) -> str:
        return json.dumps(
            {
                "type": SYNC_CREATOR,
                "organisation_id": str(self.organisation_id),
                "creator_id": str(self.creator_id),
            }
        )


Job = ScheduledSyncJob | SyncCreatorJob


def parse_job(body: str) -> Job:
    """Raise ValueError for anything that isn't a known job."""
    try:
        message = json.loads(body)
        kind = message["type"]
        if kind == SCHEDULED_SYNC:
            return ScheduledSyncJob()
        if kind == SYNC_CREATOR:
            return SyncCreatorJob(
                organisation_id=uuid.UUID(message["organisation_id"]),
                creator_id=uuid.UUID(message["creator_id"]),
            )
    except (TypeError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError(f"Malformed job message: {body[:200]}") from exc
    raise ValueError(f"Unknown job type: {kind!r}")


class JobPublisher(Protocol):
    def publish(self, jobs: Sequence[Job]) -> None: ...


class SqsJobPublisher:
    """Sends jobs with SendMessageBatch. `client` is a boto3 SQS client."""

    def __init__(self, client: Any, queue_url: str) -> None:
        self._client = client
        self._queue_url = queue_url

    def publish(self, jobs: Sequence[Job]) -> None:
        for start in range(0, len(jobs), SQS_BATCH_SIZE):
            batch = jobs[start : start + SQS_BATCH_SIZE]
            response = self._client.send_message_batch(
                QueueUrl=self._queue_url,
                Entries=[
                    {"Id": str(i), "MessageBody": job.to_message()} for i, job in enumerate(batch)
                ],
            )
            if failed := response.get("Failed"):
                raise RuntimeError(f"SQS rejected {len(failed)} sync jobs: {failed[0]}")
