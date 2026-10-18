"""Tests for sync job messages."""

import json
import uuid

import pytest

from hookd_core.jobs import ScheduledSyncJob, SqsJobPublisher, SyncCreatorJob, parse_job


def test_round_trip():
    job = SyncCreatorJob(organisation_id=uuid.uuid4(), creator_id=uuid.uuid4())
    assert parse_job(job.to_message()) == job
    assert parse_job('{"type":"scheduled_sync"}') == ScheduledSyncJob()  # EventBridge's message


@pytest.mark.parametrize("body", ["not json", "[]", '{"type": "nope"}', '{"type": "sync_creator"}'])
def test_rejects_bad_messages(body):
    with pytest.raises(ValueError):
        parse_job(body)


class FakeSqs:
    def __init__(self):
        self.batches = []

    def send_message_batch(self, QueueUrl, Entries):  # noqa: N803 (boto3 argument names)
        self.batches.append((QueueUrl, Entries))
        return {"Successful": Entries}


def test_publisher_batches_by_ten():
    sqs = FakeSqs()
    jobs = [SyncCreatorJob(uuid.uuid4(), uuid.uuid4()) for _ in range(23)]
    SqsJobPublisher(sqs, "q-url").publish(jobs)
    assert [len(entries) for _, entries in sqs.batches] == [10, 10, 3]
    assert json.loads(sqs.batches[0][1][0]["MessageBody"])["type"] == "sync_creator"
