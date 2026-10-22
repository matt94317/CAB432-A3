"""Creator roster storage interface and an in-memory implementation."""

import uuid
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from threading import Lock
from typing import Protocol

from hookd_core.enums import Platform


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class Creator:
    organisation_id: uuid.UUID
    name: str
    handle: str  # lowercase, no '@'
    niche: str | None = None
    email: str | None = None
    phone: str | None = None
    platform: Platform = Platform.TIKTOK
    last_synced_at: datetime | None = None  # last successful post sync (US-18)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


class CreatorRepository(Protocol):
    """Every method is scoped to one organisation, so one Host can never reach another's data."""

    def add(self, creator: Creator) -> Creator: ...

    def get(self, organisation_id: uuid.UUID, creator_id: uuid.UUID) -> Creator | None: ...

    def get_by_handle(
        self, organisation_id: uuid.UUID, platform: Platform, handle: str
    ) -> Creator | None: ...

    def list(self, organisation_id: uuid.UUID) -> list[Creator]: ...

    def save(self, creator: Creator) -> Creator: ...

    def delete(self, organisation_id: uuid.UUID, creator_id: uuid.UUID) -> bool: ...


class InMemoryCreatorRepository:
    """Process-local store. Data is lost on restart and not shared between API tasks."""

    def __init__(self) -> None:
        self._items: dict[uuid.UUID, Creator] = {}
        self._lock = Lock()

    def add(self, creator: Creator) -> Creator:
        with self._lock:
            self._items[creator.id] = creator
        return creator

    def get(self, organisation_id: uuid.UUID, creator_id: uuid.UUID) -> Creator | None:
        creator = self._items.get(creator_id)
        if creator is None or creator.organisation_id != organisation_id:
            return None
        return creator

    def get_by_handle(
        self, organisation_id: uuid.UUID, platform: Platform, handle: str
    ) -> Creator | None:
        return next(
            (
                c
                for c in self._items.values()
                if c.organisation_id == organisation_id
                and c.platform == platform
                and c.handle == handle
            ),
            None,
        )

    def list(self, organisation_id: uuid.UUID) -> list[Creator]:
        creators = [c for c in self._items.values() if c.organisation_id == organisation_id]
        return sorted(creators, key=lambda c: (c.name.lower(), c.handle))

    def save(self, creator: Creator) -> Creator:
        saved = replace(creator, updated_at=_now())
        with self._lock:
            self._items[creator.id] = saved
        return saved

    def delete(self, organisation_id: uuid.UUID, creator_id: uuid.UUID) -> bool:
        with self._lock:
            if self.get(organisation_id, creator_id) is None:
                return False
            del self._items[creator_id]
        return True
