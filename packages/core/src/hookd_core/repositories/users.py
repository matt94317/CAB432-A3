"""User and organisation storage interface and an in-memory implementation.

Identity lives in Cognito; `cognito_sub` links a Cognito user to their User.
Each user gets their own Organisation on first login (teams come later, US-35).
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Protocol


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class Organisation:
    """Owns all campaign data. In product terms, the Host."""

    name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class User:
    organisation_id: uuid.UUID
    name: str
    email: str
    cognito_sub: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=_now)


class UserRepository(Protocol):
    def get_by_cognito_sub(self, cognito_sub: str) -> User | None: ...

    def create(self, user: User, organisation: Organisation) -> User:
        """Store a new user with their organisation.

        Two first requests from one user can race; if a user with this
        cognito_sub already exists, nothing is written and that user is returned.
        """
        ...


class InMemoryUserRepository:
    """Process-local store. Data is lost on restart."""

    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._organisations: dict[uuid.UUID, Organisation] = {}
        self._lock = Lock()

    def get_by_cognito_sub(self, cognito_sub: str) -> User | None:
        return self._users.get(cognito_sub)

    def create(self, user: User, organisation: Organisation) -> User:
        with self._lock:
            if existing := self._users.get(user.cognito_sub):
                return existing
            self._organisations[organisation.id] = organisation
            self._users[user.cognito_sub] = user
        return user
