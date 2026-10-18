"""SQS consumer: receive, delete on success, leave for retry/DLQ on failure.

A message whose handler raises stays on the queue. SQS makes it visible again
after the visibility timeout, and the queue's redrive policy moves it to the
dead-letter queue after too many attempts.
"""

import logging
import threading
from collections.abc import Callable
from typing import Any

log = logging.getLogger(__name__)


class SqsConsumer:
    def __init__(
        self, client: Any, queue_url: str, wait_seconds: int = 20, batch_size: int = 10
    ) -> None:
        self._client = client
        self._queue_url = queue_url
        self._wait_seconds = wait_seconds
        self._batch_size = batch_size

    def poll_once(self, handle: Callable[[str], None]) -> int:
        """Long-poll once and handle what arrives. Returns how many messages succeeded."""
        response = self._client.receive_message(
            QueueUrl=self._queue_url,
            MaxNumberOfMessages=self._batch_size,
            WaitTimeSeconds=self._wait_seconds,
        )
        done = 0
        for message in response.get("Messages", []):
            try:
                handle(message["Body"])
            except Exception:
                log.exception("Sync job failed; leaving it for retry: %s", message["Body"][:200])
                continue
            self._client.delete_message(
                QueueUrl=self._queue_url, ReceiptHandle=message["ReceiptHandle"]
            )
            done += 1
        return done

    def run(self, handle: Callable[[str], None], stop: threading.Event) -> None:
        """Poll until `stop` is set. A poll in progress finishes first (at most wait_seconds)."""
        while not stop.is_set():
            try:
                self.poll_once(handle)
            except Exception:
                log.exception("Couldn't receive from SQS; retrying shortly")
                stop.wait(5)
