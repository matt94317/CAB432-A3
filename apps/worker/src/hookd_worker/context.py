"""What every job handler can use."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, tzinfo

from hookd_core.cache import DashboardCache, NullCache
from hookd_core.fetchers import PostFetcher
from hookd_core.jobs import JobPublisher
from hookd_core.sync import Stores


@dataclass(frozen=True)
class WorkerContext:
    stores: Stores
    fetcher: PostFetcher
    publisher: JobPublisher
    tz: tzinfo
    lookback_days: int
    cache: DashboardCache = field(default_factory=NullCache)
    now: Callable[[], datetime] = field(default=lambda: datetime.now(UTC))
