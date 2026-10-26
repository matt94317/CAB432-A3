"""Post fetchers: where sync gets a creator's posts and metrics from.

`make_fetcher` picks one by TIKTOK_MODE. New platforms (Instagram, YouTube)
implement `PostFetcher` too.
"""

from hookd_core.fetchers.base import FetchedPost, FetchError, PostFetcher
from hookd_core.fetchers.mock import MockFetcher
from hookd_core.fetchers.tiktok import TikTokResearchFetcher


def make_fetcher(
    mode: str, client_key: str = "", client_secret: str = "", mock_delay_ms: int = 0
) -> PostFetcher:
    if mode == "mock":
        return MockFetcher(delay_seconds=mock_delay_ms / 1000)
    if mode == "live":
        if not client_key or not client_secret:
            raise ValueError("TIKTOK_MODE=live needs TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET")
        return TikTokResearchFetcher(client_key, client_secret)
    raise ValueError(f"Unknown TIKTOK_MODE {mode!r}; use 'mock' or 'live'")


__all__ = [
    "FetchError",
    "FetchedPost",
    "MockFetcher",
    "PostFetcher",
    "TikTokResearchFetcher",
    "make_fetcher",
]
