"""Dashboard cache in Redis/Valkey, shared by the API (reads, writes) and the
worker (invalidates after a sync).

Invalidation is by organisation version: every cached dashboard key includes
the organisation's current version, and any change to that organisation's data
bumps it (INCR), so all its dashboards miss at once. Old entries just expire.
This keeps invalidation in two places (API writes, worker syncs) instead of
tracking which change affects which dashboard.

The cache is an optimisation: if Redis is down, reads miss and writes are
skipped, and the app keeps working. After a failure it backs off for a while
instead of paying a connection timeout on every request.
"""

import logging
import time
import uuid
from typing import Any, Protocol

log = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 300
_BACKOFF_SECONDS = 30


class DashboardCache(Protocol):
    def get(self, organisation_id: uuid.UUID, key: str) -> str | None: ...

    def set(self, organisation_id: uuid.UUID, key: str, value: str) -> None: ...

    def invalidate(self, organisation_id: uuid.UUID) -> None:
        """Every cached dashboard of this organisation is stale."""
        ...


class NullCache:
    """No caching (REDIS_URL unset)."""

    def get(self, organisation_id: uuid.UUID, key: str) -> str | None:
        return None

    def set(self, organisation_id: uuid.UUID, key: str, value: str) -> None:
        pass

    def invalidate(self, organisation_id: uuid.UUID) -> None:
        pass


class InMemoryCache:
    """Process-local; for tests."""

    def __init__(self) -> None:
        self._versions: dict[uuid.UUID, int] = {}
        self._items: dict[str, str] = {}

    def _key(self, organisation_id: uuid.UUID, key: str) -> str:
        return f"{organisation_id}:{self._versions.get(organisation_id, 0)}:{key}"

    def get(self, organisation_id: uuid.UUID, key: str) -> str | None:
        return self._items.get(self._key(organisation_id, key))

    def set(self, organisation_id: uuid.UUID, key: str, value: str) -> None:
        self._items[self._key(organisation_id, key)] = value

    def invalidate(self, organisation_id: uuid.UUID) -> None:
        self._versions[organisation_id] = self._versions.get(organisation_id, 0) + 1


class RedisCache:
    def __init__(self, client: Any, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._redis = client
        self._ttl = ttl_seconds
        self._down_until = 0.0

    @classmethod
    def from_url(cls, url: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> "RedisCache":
        import redis

        client = redis.Redis.from_url(
            url, socket_connect_timeout=0.5, socket_timeout=0.5, decode_responses=True
        )
        return cls(client, ttl_seconds)

    @staticmethod
    def _version_key(organisation_id: uuid.UUID) -> str:
        return f"hookd:dash-version:{organisation_id}"

    def _call(self, what: str, fn: Any) -> Any:
        if time.monotonic() < self._down_until:
            return None
        try:
            return fn()
        except Exception as exc:  # any Redis or network error: carry on without the cache
            log.warning(
                "Dashboard cache %s failed, skipping it for %ss: %s", what, _BACKOFF_SECONDS, exc
            )
            self._down_until = time.monotonic() + _BACKOFF_SECONDS
            return None

    def _key(self, organisation_id: uuid.UUID, key: str) -> str | None:
        version = self._call(
            "version read", lambda: self._redis.get(self._version_key(organisation_id))
        )
        if time.monotonic() < self._down_until:
            return None
        return f"hookd:dash:{organisation_id}:{version or 0}:{key}"

    def get(self, organisation_id: uuid.UUID, key: str) -> str | None:
        full = self._key(organisation_id, key)
        return self._call("read", lambda: self._redis.get(full)) if full else None

    def set(self, organisation_id: uuid.UUID, key: str, value: str) -> None:
        full = self._key(organisation_id, key)
        if full:
            self._call("write", lambda: self._redis.set(full, value, ex=self._ttl))

    def invalidate(self, organisation_id: uuid.UUID) -> None:
        # Not subject to the backoff: a missed invalidation would serve stale data
        try:
            self._redis.incr(self._version_key(organisation_id))
        except Exception as exc:
            log.warning("Dashboard cache invalidation failed: %s", exc)


def make_cache(redis_url: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> DashboardCache:
    return RedisCache.from_url(redis_url, ttl_seconds) if redis_url else NullCache()
