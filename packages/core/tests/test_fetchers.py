"""Tests for the mock and TikTok Research API fetchers."""

import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from hookd_core.fetchers import FetchError, MockFetcher, TikTokResearchFetcher, make_fetcher
from hookd_core.fetchers.tiktok import QUERY_URL, TOKEN_URL

NOW = datetime(2026, 10, 18, 12, tzinfo=UTC)


def test_mock_is_deterministic_and_metrics_grow():
    fetcher = MockFetcher(posts_per_week=7)
    since = NOW - timedelta(days=14)
    first = fetcher.fetch_posts("lou", since, NOW, ["lumiglow"])
    later = fetcher.fetch_posts("lou", since, NOW + timedelta(hours=12), ["lumiglow"])

    assert first
    assert all(since <= p.posted_at <= NOW for p in first)
    assert [p.external_id for p in first] == [p.external_id for p in later][: len(first)]
    assert sum(p.views for p in later[: len(first)]) >= sum(p.views for p in first)
    assert any("lumiglow" in p.hashtags for p in first)


def test_mock_posts_differ_by_creator():
    since = NOW - timedelta(days=14)
    lou = {p.external_id for p in MockFetcher(posts_per_week=7).fetch_posts("lou", since, NOW)}
    amy = {p.external_id for p in MockFetcher(posts_per_week=7).fetch_posts("amy", since, NOW)}
    assert lou.isdisjoint(amy)


def test_mock_delay(monkeypatch):
    slept = []
    monkeypatch.setattr("hookd_core.fetchers.mock.sleep", slept.append)
    make_fetcher("mock", mock_delay_ms=1500).fetch_posts("lou", NOW - timedelta(days=1), NOW)
    MockFetcher().fetch_posts("lou", NOW - timedelta(days=1), NOW)
    assert slept == [1.5]


def test_make_fetcher():
    assert isinstance(make_fetcher("mock"), MockFetcher)
    assert isinstance(make_fetcher("live", "key", "secret"), TikTokResearchFetcher)
    with pytest.raises(ValueError):
        make_fetcher("live")
    with pytest.raises(ValueError):
        make_fetcher("other")


class FakeTikTok:
    """Records requests and answers like the Research API."""

    def __init__(self, pages, token_status=200, fail_first=0):
        self.pages = list(pages)
        self.token_status = token_status
        self.fail_first = fail_first
        self.queries = []
        self.token_calls = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if str(request.url) == TOKEN_URL:
            self.token_calls += 1
            if self.token_status != 200:
                return httpx.Response(self.token_status, json={"error": "invalid_client"})
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 7200})
        assert str(request.url).startswith(QUERY_URL)
        assert request.headers["Authorization"] == "Bearer tok"
        if self.fail_first:
            self.fail_first -= 1
            return httpx.Response(429, headers={"Retry-After": "0"})
        self.queries.append(json.loads(request.content))
        videos, has_more = self.pages.pop(0) if self.pages else ([], False)
        data = {"videos": videos, "has_more": has_more, "cursor": 100, "search_id": "s1"}
        return httpx.Response(200, json={"data": data, "error": {"code": "ok"}})


def video(video_id, created, **fields):
    return {
        "id": video_id,
        "create_time": int(created.timestamp()),
        "username": "lou",
        "video_description": "Love it #LumiGlow",
        "hashtag_names": ["LumiGlow"],
        "view_count": 1200,
        "like_count": 80,
        "comment_count": 5,
        "share_count": 3,
        **fields,
    }


def fetcher_for(fake):
    http = httpx.Client(transport=httpx.MockTransport(fake))
    return TikTokResearchFetcher("key", "secret", http=http, sleep=lambda _: None)


def test_tiktok_fetches_and_paginates():
    created = NOW - timedelta(days=2)
    fake = FakeTikTok([([video(1, created)], True), ([video(2, created)], False)])

    posts = fetcher_for(fake).fetch_posts("lou", NOW - timedelta(days=5), NOW)

    assert [p.external_id for p in posts] == ["1", "2"]
    first = posts[0]
    assert first.url == "https://www.tiktok.com/@lou/video/1"
    assert (first.views, first.likes, first.comments, first.shares) == (1200, 80, 5, 3)
    assert first.hashtags == ("LumiGlow",)
    assert first.posted_at == created.replace(microsecond=0)
    query = fake.queries[0]
    assert query["query"]["and"][0]["field_values"] == ["lou"]
    assert (query["start_date"], query["end_date"]) == ("20261013", "20261018")
    assert (fake.queries[1]["cursor"], fake.queries[1]["search_id"]) == (100, "s1")
    assert fake.token_calls == 1  # reused across pages


def test_tiktok_splits_long_windows_into_30_days():
    fake = FakeTikTok([])
    fetcher_for(fake).fetch_posts("lou", NOW - timedelta(days=45), NOW)
    windows = [(q["start_date"], q["end_date"]) for q in fake.queries]
    assert windows == [("20260903", "20261002"), ("20261003", "20261018")]


def test_tiktok_drops_posts_outside_the_window():
    fake = FakeTikTok([([video(1, NOW - timedelta(days=10))], False)])
    assert fetcher_for(fake).fetch_posts("lou", NOW - timedelta(days=5), NOW) == []


def test_tiktok_retries_rate_limits():
    fake = FakeTikTok([([video(1, NOW - timedelta(days=1))], False)], fail_first=2)
    assert len(fetcher_for(fake).fetch_posts("lou", NOW - timedelta(days=2), NOW)) == 1


def test_tiktok_gives_up_after_repeated_rate_limits():
    fake = FakeTikTok([], fail_first=10)
    with pytest.raises(FetchError):
        fetcher_for(fake).fetch_posts("lou", NOW - timedelta(days=2), NOW)


def test_tiktok_bad_credentials():
    with pytest.raises(FetchError, match="token"):
        fetcher_for(FakeTikTok([], token_status=401)).fetch_posts("lou", NOW, NOW)
