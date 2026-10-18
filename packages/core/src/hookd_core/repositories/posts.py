"""Post storage interface and an in-memory implementation.

A post belongs to one creator and, at most, one campaign. A post the manager
removes is kept, flagged `removed`, so the next sync doesn't add it back.
"""

import uuid
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from threading import Lock
from typing import Protocol

from hookd_core.enums import MatchSource, Platform


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class Post:
    organisation_id: uuid.UUID
    creator_id: uuid.UUID
    campaign_id: uuid.UUID
    external_id: str  # the platform's video id
    url: str
    posted_at: datetime
    match_source: MatchSource
    platform: Platform = Platform.TIKTOK
    caption: str = ""
    hashtags: tuple[str, ...] = ()
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    removed: bool = False
    last_synced_at: datetime | None = None  # None until sync has seen it (manual posts)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


class PostRepository(Protocol):
    """Every method is scoped to one organisation. One post per creator and external id."""

    def add(self, post: Post) -> Post: ...

    def get(self, organisation_id: uuid.UUID, post_id: uuid.UUID) -> Post | None: ...

    def get_by_external_id(
        self,
        organisation_id: uuid.UUID,
        creator_id: uuid.UUID,
        platform: Platform,
        external_id: str,
    ) -> Post | None:
        """Includes removed posts."""
        ...

    def list(
        self,
        organisation_id: uuid.UUID,
        *,
        campaign_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
    ) -> list[Post]:
        """Posts that count, newest first. Removed posts are left out."""
        ...

    def save(self, post: Post) -> Post: ...

    def delete(self, organisation_id: uuid.UUID, post_id: uuid.UUID) -> bool: ...

    def delete_where(
        self,
        organisation_id: uuid.UUID,
        *,
        campaign_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
    ) -> int:
        """Delete every post (removed ones too) of a campaign, a creator, or both."""
        ...


class InMemoryPostRepository:
    """Process-local store. Data is lost on restart and not shared between processes."""

    def __init__(self) -> None:
        self._items: dict[uuid.UUID, Post] = {}
        self._lock = Lock()

    def add(self, post: Post) -> Post:
        with self._lock:
            self._items[post.id] = post
        return post

    def get(self, organisation_id: uuid.UUID, post_id: uuid.UUID) -> Post | None:
        post = self._items.get(post_id)
        if post is None or post.organisation_id != organisation_id:
            return None
        return post

    def get_by_external_id(
        self,
        organisation_id: uuid.UUID,
        creator_id: uuid.UUID,
        platform: Platform,
        external_id: str,
    ) -> Post | None:
        return next(
            (
                p
                for p in self._items.values()
                if p.organisation_id == organisation_id
                and p.creator_id == creator_id
                and p.platform == platform
                and p.external_id == external_id
            ),
            None,
        )

    def _matching(
        self,
        organisation_id: uuid.UUID,
        campaign_id: uuid.UUID | None,
        creator_id: uuid.UUID | None,
    ) -> list[Post]:
        return [
            p
            for p in self._items.values()
            if p.organisation_id == organisation_id
            and (campaign_id is None or p.campaign_id == campaign_id)
            and (creator_id is None or p.creator_id == creator_id)
        ]

    def list(
        self,
        organisation_id: uuid.UUID,
        *,
        campaign_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
    ) -> list[Post]:
        posts = self._matching(organisation_id, campaign_id, creator_id)
        return sorted((p for p in posts if not p.removed), key=lambda p: p.posted_at, reverse=True)

    def save(self, post: Post) -> Post:
        saved = replace(post, updated_at=_now())
        with self._lock:
            self._items[post.id] = saved
        return saved

    def delete(self, organisation_id: uuid.UUID, post_id: uuid.UUID) -> bool:
        with self._lock:
            if self.get(organisation_id, post_id) is None:
                return False
            del self._items[post_id]
        return True

    def delete_where(
        self,
        organisation_id: uuid.UUID,
        *,
        campaign_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
    ) -> int:
        with self._lock:
            doomed = [p.id for p in self._matching(organisation_id, campaign_id, creator_id)]
            for post_id in doomed:
                del self._items[post_id]
        return len(doomed)
