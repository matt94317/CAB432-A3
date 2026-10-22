"""PostFetcher interface. New platforms (Instagram, YouTube) implement this."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class FetchError(Exception):
    """The platform couldn't be reached or refused the request. The sync is retried later."""


@dataclass(frozen=True)
class FetchedPost:
    external_id: str
    url: str
    posted_at: datetime  # timezone-aware
    caption: str = ""
    hashtags: tuple[str, ...] = ()  # as the platform reports them; may be empty
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0


class PostFetcher(Protocol):
    def fetch_posts(
        self,
        handle: str,
        since: datetime,
        until: datetime,
        hashtags: Sequence[str] = (),
    ) -> list[FetchedPost]:
        """A creator's public posts published between `since` and `until`, with current metrics.

        `hashtags` are the tracking hashtags of the creator's campaigns. Real
        fetchers ignore them (matching happens afterwards, in hookd_core.sync);
        the mock uses them so demo posts match.
        """
        ...
