"""TikTok Research API fetcher (rate limits, retries with backoff).

Reads other accounts' public videos, which needs an approved Research API app:
https://developers.tiktok.com/doc/research-api-specs-query-videos
The API takes date ranges of at most 30 days, so longer windows are split.
"""

import time
from collections.abc import Callable, Iterator, Sequence
from datetime import UTC, date, datetime, timedelta

import httpx

from hookd_core.fetchers.base import FetchedPost, FetchError

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
QUERY_URL = "https://open.tiktokapis.com/v2/research/video/query/"
FIELDS = (
    "id,create_time,username,video_description,hashtag_names,"
    "view_count,like_count,comment_count,share_count"
)
MAX_WINDOW_DAYS = 30
PAGE_SIZE = 100
RETRY_STATUSES = {429, 500, 502, 503, 504}


class TikTokResearchFetcher:
    def __init__(
        self,
        client_key: str,
        client_secret: str,
        http: httpx.Client | None = None,
        max_attempts: int = 4,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client_key = client_key
        self._client_secret = client_secret
        self._http = http or httpx.Client(timeout=30)
        self._max_attempts = max_attempts
        self._sleep = sleep
        self._token: str | None = None
        self._token_expires = 0.0

    def fetch_posts(
        self,
        handle: str,
        since: datetime,
        until: datetime,
        hashtags: Sequence[str] = (),
    ) -> list[FetchedPost]:
        posts: dict[str, FetchedPost] = {}
        start = since.astimezone(UTC).date()
        last = until.astimezone(UTC).date()
        while start <= last:
            end = min(start + timedelta(days=MAX_WINDOW_DAYS - 1), last)
            for post in self._query(handle, start, end):
                if since <= post.posted_at <= until:
                    posts[post.external_id] = post
            start = end + timedelta(days=1)
        return sorted(posts.values(), key=lambda p: p.posted_at)

    # --- Research API ---

    def _query(self, handle: str, start: date, end: date) -> Iterator[FetchedPost]:
        by_username = {"operation": "EQ", "field_name": "username", "field_values": [handle]}
        body: dict = {
            "query": {"and": [by_username]},
            "start_date": start.strftime("%Y%m%d"),
            "end_date": end.strftime("%Y%m%d"),
            "max_count": PAGE_SIZE,
        }
        while True:
            payload = self._post_query(body)
            data = payload.get("data") or {}
            for video in data.get("videos") or []:
                yield _to_post(video, handle)
            if not data.get("has_more"):
                return
            body = {**body, "cursor": data.get("cursor"), "search_id": data.get("search_id")}

    def _post_query(self, body: dict) -> dict:
        for refreshed in (False, True):
            response = self._send(
                "POST",
                QUERY_URL,
                params={"fields": FIELDS},
                json=body,
                headers={"Authorization": f"Bearer {self._access_token()}"},
            )
            if response.status_code == 401 and not refreshed:
                self._token = None  # expired early; get a new one and try once more
                continue
            break
        payload = _json(response)
        error = payload.get("error") or {}
        if response.is_error or error.get("code", "ok") != "ok":
            message = error.get("message") or error.get("code") or response.reason_phrase
            raise FetchError(f"TikTok video query failed ({response.status_code}): {message}")
        return payload

    def _access_token(self) -> str:
        if self._token and time.monotonic() < self._token_expires:
            return self._token
        response = self._send(
            "POST",
            TOKEN_URL,
            data={
                "client_key": self._client_key,
                "client_secret": self._client_secret,
                "grant_type": "client_credentials",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        payload = _json(response)
        if response.is_error or "access_token" not in payload:
            message = payload.get("error_description") or payload.get("error")
            message = message or response.status_code
            raise FetchError(f"TikTok token request failed: {message}")
        self._token = payload["access_token"]
        # Refresh a minute early so a token never expires mid-sync
        self._token_expires = time.monotonic() + float(payload.get("expires_in", 7200)) - 60
        return self._token

    def _send(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        """Send with retries: exponential backoff on rate limits, server and network errors."""
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = self._http.request(method, url, **kwargs)  # type: ignore[arg-type]
            except httpx.TransportError as exc:
                if attempt == self._max_attempts:
                    raise FetchError(f"Couldn't reach TikTok: {exc}") from exc
                self._sleep(2 ** (attempt - 1))
                continue
            if response.status_code not in RETRY_STATUSES or attempt == self._max_attempts:
                return response
            self._sleep(_retry_after(response) or 2 ** (attempt - 1))
        raise AssertionError("unreachable")


def _json(response: httpx.Response) -> dict:
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _retry_after(response: httpx.Response) -> float | None:
    try:
        return min(float(response.headers["Retry-After"]), 60)
    except (KeyError, ValueError):
        return None


def _to_post(video: dict, handle: str) -> FetchedPost:
    external_id = str(video["id"])
    username = video.get("username") or handle
    return FetchedPost(
        external_id=external_id,
        url=f"https://www.tiktok.com/@{username}/video/{external_id}",
        posted_at=datetime.fromtimestamp(int(video["create_time"]), UTC),
        caption=video.get("video_description") or "",
        hashtags=tuple(video.get("hashtag_names") or ()),
        views=int(video.get("view_count") or 0),
        likes=int(video.get("like_count") or 0),
        comments=int(video.get("comment_count") or 0),
        shares=int(video.get("share_count") or 0),
    )
