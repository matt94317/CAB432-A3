"""Post storage interface and an in-memory implementation.

A post belongs to one creator and one campaign. A post the manager removes is
kept, flagged `removed`, so the next sync doesn't add it back.

A post's id is derived from its natural key (organisation, creator, platform,
platform id), so the same TikTok video always has the same id. Looking it up by
platform id is then a plain key lookup in any store, and two syncs racing on the
same video write the same record instead of a duplicate.
"""

import uuid
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from threading import Lock
from typing import Protocol

from hookd_core.enums import MatchSource, Platform

_POST_NAMESPACE = uuid.UUID("5b0f1c4e-7d0a-4c8e-9a51-2f3d6b8e1a77")


def _now() -> datetime:
    return datetime.now(UTC)


def post_id(
    organisation_id: uuid.UUID, creator_id: uuid.UUID, platform: Platform, external_id: str
) -> uuid.UUID:
    return uuid.uuid5(_POST_NAMESPACE, f"{organisation_id}/{creator_id}/{platform}/{external_id}")


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
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    @property
    def id(self) -> uuid.UUID:
        return post_id(self.organisation_id, self.creator_id, self.platform, self.external_id)


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
        return self.get(
            organisation_id, post_id(organisation_id, creator_id, platform, external_id)
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
