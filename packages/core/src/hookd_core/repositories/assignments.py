"""Campaign–creator assignment storage interface and an in-memory implementation.

An assignment is a "signed" creator on a campaign. Targets live here, not on the
creator, so the same creator can have different targets in different campaigns.
"""

import uuid
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from threading import Lock
from typing import Protocol

from hookd_core.enums import TargetPeriod


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class Assignment:
    organisation_id: uuid.UUID
    campaign_id: uuid.UUID
    creator_id: uuid.UUID
    target_posts: int
    target_period: TargetPeriod
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


class AssignmentRepository(Protocol):
    """Every method is scoped to one organisation. One assignment per campaign–creator pair."""

    def add_many(self, assignments: list[Assignment]) -> list[Assignment]: ...

    def get(
        self, organisation_id: uuid.UUID, campaign_id: uuid.UUID, creator_id: uuid.UUID
    ) -> Assignment | None: ...

    def list(
        self,
        organisation_id: uuid.UUID,
        *,
        campaign_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
    ) -> list[Assignment]: ...

    def save(self, assignment: Assignment) -> Assignment: ...

    def delete(
        self, organisation_id: uuid.UUID, campaign_id: uuid.UUID, creator_id: uuid.UUID
    ) -> bool: ...

    def delete_where(
        self,
        organisation_id: uuid.UUID,
        *,
        campaign_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
    ) -> int:
        """Delete every assignment of a campaign or a creator; returns how many."""
        ...


class InMemoryAssignmentRepository:
    """Process-local store. Data is lost on restart and not shared between API tasks."""

    def __init__(self) -> None:
        self._items: dict[tuple[uuid.UUID, uuid.UUID], Assignment] = {}
        self._lock = Lock()

    def add_many(self, assignments: list[Assignment]) -> list[Assignment]:
        with self._lock:
            for a in assignments:
                self._items[(a.campaign_id, a.creator_id)] = a
        return assignments

    def get(
        self, organisation_id: uuid.UUID, campaign_id: uuid.UUID, creator_id: uuid.UUID
    ) -> Assignment | None:
        assignment = self._items.get((campaign_id, creator_id))
        if assignment is None or assignment.organisation_id != organisation_id:
            return None
        return assignment

    def list(
        self,
        organisation_id: uuid.UUID,
        *,
        campaign_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
    ) -> list[Assignment]:
        assignments = [
            a
            for a in self._items.values()
            if a.organisation_id == organisation_id
            and (campaign_id is None or a.campaign_id == campaign_id)
            and (creator_id is None or a.creator_id == creator_id)
        ]
        return sorted(assignments, key=lambda a: a.created_at)

    def save(self, assignment: Assignment) -> Assignment:
        saved = replace(assignment, updated_at=_now())
        with self._lock:
            self._items[(assignment.campaign_id, assignment.creator_id)] = saved
        return saved

    def delete(
        self, organisation_id: uuid.UUID, campaign_id: uuid.UUID, creator_id: uuid.UUID
    ) -> bool:
        with self._lock:
            if self.get(organisation_id, campaign_id, creator_id) is None:
                return False
            del self._items[(campaign_id, creator_id)]
        return True

    def delete_where(
        self,
        organisation_id: uuid.UUID,
        *,
        campaign_id: uuid.UUID | None = None,
        creator_id: uuid.UUID | None = None,
    ) -> int:
        with self._lock:
            doomed = [
                (a.campaign_id, a.creator_id)
                for a in self.list(organisation_id, campaign_id=campaign_id, creator_id=creator_id)
            ]
            for key in doomed:
                del self._items[key]
        return len(doomed)
