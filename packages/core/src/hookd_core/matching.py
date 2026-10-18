"""Match a post to campaigns by tracking hashtags (US-14).

Pure functions, no DB access, so they are easy to unit test."""

import re
from collections.abc import Iterable, Sequence
from datetime import date

from hookd_core.repositories.campaigns import Campaign

_HASHTAG = re.compile(r"#(\w+)")


def extract_hashtags(caption: str) -> tuple[str, ...]:
    """'Glow up #LumiGlow #ad #lumiglow' -> ('lumiglow', 'ad'). Lowercase, unique, in order."""
    return tuple(dict.fromkeys(tag.lower() for tag in _HASHTAG.findall(caption)))


def normalise_hashtags(tags: Iterable[str]) -> tuple[str, ...]:
    """Platform hashtag lists ('LumiGlow', '#ad') in the same form as campaign hashtags."""
    return tuple(dict.fromkeys(t.strip().lstrip("#").lower() for t in tags if t.strip("# ")))


def match_campaign(
    hashtags: Sequence[str], posted_on: date, campaigns: Iterable[Campaign]
) -> Campaign | None:
    """The campaign a post counts toward, or None.

    A campaign matches when the post uses any of its tracking hashtags and was
    posted within its dates. If several match, the one sharing the most hashtags
    wins, then the one that started most recently (the more specific campaign).
    """
    tags = set(hashtags)
    candidates = [
        (len(tags.intersection(c.tracking_hashtags)), c.start_date, str(c.id), c)
        for c in campaigns
        if c.start_date <= posted_on <= c.end_date
    ]
    best = max((c for c in candidates if c[0] > 0), default=None, key=lambda c: c[:3])
    return best[3] if best else None
