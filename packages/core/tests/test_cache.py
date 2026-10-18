"""Tests for the dashboard cache and its per-organisation invalidation."""

import uuid

import pytest

from hookd_core.cache import InMemoryCache, NullCache, RedisCache, make_cache

ORG, OTHER = uuid.uuid4(), uuid.uuid4()


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.down = False
        self.calls = 0

    def _check(self):
        self.calls += 1
        if self.down:
            raise ConnectionError("redis is down")

    def get(self, key):
        self._check()
        return self.data.get(key)

    def set(self, key, value, ex=None):
        self._check()
        self.data[key] = value

    def incr(self, key):
        self._check()
        self.data[key] = str(int(self.data.get(key, 0)) + 1)


@pytest.fixture(params=["memory", "redis"])
def cache(request):
    return InMemoryCache() if request.param == "memory" else RedisCache(FakeRedis())


def test_set_get_and_invalidate_per_organisation(cache):
    cache.set(ORG, "campaign:1", "a")
    cache.set(OTHER, "campaign:1", "b")
    assert cache.get(ORG, "campaign:1") == "a"

    cache.invalidate(ORG)
    assert cache.get(ORG, "campaign:1") is None
    assert cache.get(OTHER, "campaign:1") == "b"  # untouched

    cache.set(ORG, "campaign:1", "c")
    assert cache.get(ORG, "campaign:1") == "c"


def test_redis_outage_is_a_miss_and_backs_off():
    redis = FakeRedis()
    cache = RedisCache(redis)
    redis.down = True
    assert cache.get(ORG, "k") is None
    calls = redis.calls
    cache.set(ORG, "k", "v")
    assert cache.get(ORG, "k") is None
    assert redis.calls == calls  # not retried during the back-off


def test_make_cache():
    assert isinstance(make_cache(""), NullCache)
    assert isinstance(make_cache("redis://localhost:6379/0"), RedisCache)
    assert NullCache().get(ORG, "k") is None
