"""Mock fetcher returning fake posts. Demo fallback if TikTok access is denied.

Deterministic: the same handle and day always give the same post, so repeated
syncs update posts instead of adding new ones. Metrics grow as a post ages, so
each sync shows fresher numbers.

`delay_seconds` stands in for the real API's response time, so load tests keep
the worker busy the way live syncs would.
"""

import hashlib
import random
from collections.abc import Sequence
from datetime import UTC, datetime, time, timedelta
from time import sleep

from hookd_core.fetchers.base import FetchedPost

_GENERIC_TAGS = ("fyp", "foryou", "ugc", "grwm", "review", "dayinmylife", "tiktokmademebuyit")


def _rng(*parts: object) -> random.Random:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


class MockFetcher:
    def __init__(
        self, posts_per_week: float = 3, match_rate: float = 0.7, delay_seconds: float = 0
    ) -> None:
        self.posts_per_week = posts_per_week
        self.match_rate = match_rate
        self.delay_seconds = delay_seconds

    def fetch_posts(
        self,
        handle: str,
        since: datetime,
        until: datetime,
        hashtags: Sequence[str] = (),
    ) -> list[FetchedPost]:
        if self.delay_seconds:
            sleep(self.delay_seconds)
        tracked = sorted(hashtags)
        posts = []
        day = since.astimezone(UTC).date()
        while day <= until.astimezone(UTC).date():
            rng = _rng(handle, day)
            # Draw every value in a fixed order so a post doesn't change between syncs
            posts_today = rng.random() < self.posts_per_week / 7
            posted_at = datetime.combine(day, time(rng.randint(0, 23), rng.randint(0, 59)), UTC)
            base_views = rng.randint(800, 60_000)
            like_rate, comment_rate, share_rate = (
                rng.uniform(0.04, 0.12),
                rng.uniform(0.02, 0.08),
                rng.uniform(0.01, 0.06),
            )
            generic = rng.choice(_GENERIC_TAGS)
            uses_campaign_tag = rng.random() < self.match_rate
            tag_pick = rng.random()
            external_id = str(7_000_000_000_000_000_000 + rng.randrange(10**18))
            day += timedelta(days=1)

            if not posts_today or not since <= posted_at <= until:
                continue
            tags = [generic]
            if tracked and uses_campaign_tag:
                tags.insert(0, tracked[int(tag_pick * len(tracked))])
            age_hours = (until - posted_at).total_seconds() / 3600
            views = int(base_views * min(1.0, 0.2 + age_hours / 96))
            likes = int(views * like_rate)
            posts.append(
                FetchedPost(
                    external_id=external_id,
                    url=f"https://www.tiktok.com/@{handle}/video/{external_id}",
                    posted_at=posted_at,
                    caption="New video! " + " ".join(f"#{t}" for t in tags),
                    hashtags=tuple(tags),
                    views=views,
                    likes=likes,
                    comments=int(likes * comment_rate),
                    shares=int(likes * share_rate),
                )
            )
        return posts
