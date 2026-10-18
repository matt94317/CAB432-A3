"""Shared API test fixtures: in-memory database and locally signed Cognito-style tokens."""

import time
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from hookd_api.deps import (
    get_assignment_repository,
    get_campaign_repository,
    get_creator_repository,
    get_db,
    get_post_repository,
    get_profile_fetcher,
    get_sync_runner,
    get_token_verifier,
)
from hookd_api.main import app
from hookd_api.security import CognitoProfile, CognitoTokenVerifier
from hookd_api.services.sync import InlineSync
from hookd_core.fetchers import FetchedPost, FetchError
from hookd_core.models import Base
from hookd_core.repositories.assignments import InMemoryAssignmentRepository
from hookd_core.repositories.campaigns import InMemoryCampaignRepository
from hookd_core.repositories.creators import InMemoryCreatorRepository
from hookd_core.repositories.posts import InMemoryPostRepository

USER_POOL_ID = "ap-southeast-2_TestPool"
APP_CLIENT_ID = "test-client-id"
ISSUER = f"https://cognito-idp.ap-southeast-2.amazonaws.com/{USER_POOL_ID}"

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class StaticKeySource:
    def get_signing_key_from_jwt(self, token: str) -> Any:
        return SimpleNamespace(key=_private_key.public_key())


def _make_token(sub: str = "user-sub-1", private_key: Any = None, **overrides: Any) -> str:
    now = int(time.time())
    claims = {
        "sub": sub,
        "iss": ISSUER,
        "client_id": APP_CLIENT_ID,
        "token_use": "access",
        "username": sub,
        "iat": now,
        "exp": now + 3600,
        **overrides,
    }
    return jwt.encode(claims, private_key or _private_key, algorithm="RS256")


@pytest.fixture
def make_token() -> Any:
    """Build a signed Cognito-style access token; pass claim overrides as kwargs."""
    return _make_token


@pytest.fixture
def verifier() -> CognitoTokenVerifier:
    return CognitoTokenVerifier(USER_POOL_ID, APP_CLIENT_ID, key_source=StaticKeySource())


@pytest.fixture
def db_session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def profiles() -> dict[str, CognitoProfile]:
    """Cognito profiles by access token; tests register the tokens they use."""
    return {}


class FakeTikTok:
    """Stands in for TikTok: tests set each handle's posts, or make it fail."""

    def __init__(self) -> None:
        self.posts: dict[str, list[FetchedPost]] = {}
        self.failing: set[str] = set()

    def post(self, handle: str, external_id: str, caption: str, **fields: Any) -> FetchedPost:
        post = FetchedPost(
            external_id=external_id,
            url=f"https://www.tiktok.com/@{handle}/video/{external_id}",
            posted_at=fields.pop("posted_at", datetime.now(UTC) - timedelta(minutes=5)),
            caption=caption,
            **fields,
        )
        self.posts.setdefault(handle, []).append(post)
        return post

    def fetch_posts(
        self, handle: str, since: datetime, until: datetime, hashtags: Any = ()
    ) -> list[FetchedPost]:
        if handle in self.failing:
            raise FetchError("TikTok is down")
        return [p for p in self.posts.get(handle, []) if since <= p.posted_at <= until]


@pytest.fixture
def tiktok() -> FakeTikTok:
    return FakeTikTok()


@pytest.fixture
def client(
    db_session_factory: sessionmaker[Session],
    verifier: CognitoTokenVerifier,
    profiles: dict[str, CognitoProfile],
    tiktok: FakeTikTok,
) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_token_verifier] = lambda: verifier
    app.dependency_overrides[get_profile_fetcher] = lambda: profiles.__getitem__

    # Fresh stores per test (a lambda default argument would become a query parameter)
    def provide(store: object) -> Any:
        return lambda: store

    app.dependency_overrides[get_campaign_repository] = provide(InMemoryCampaignRepository())
    app.dependency_overrides[get_creator_repository] = provide(InMemoryCreatorRepository())
    app.dependency_overrides[get_assignment_repository] = provide(InMemoryAssignmentRepository())
    app.dependency_overrides[get_post_repository] = provide(InMemoryPostRepository())
    runner = InlineSync(tiktok, ZoneInfo("Australia/Brisbane"), lookback_days=30)
    app.dependency_overrides[get_sync_runner] = provide(runner)
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def login(make_token: Any, profiles: dict[str, CognitoProfile]) -> Any:
    """login("alex") -> auth headers for a manager; the first API call provisions them."""

    def _login(name: str = "alex") -> dict[str, str]:
        token = _make_token(sub=f"sub-{name}")
        profiles[token] = CognitoProfile(email=f"{name}@example.com", name=name.title())
        return {"Authorization": f"Bearer {token}"}

    return _login


@pytest.fixture
def alex(login: Any) -> dict[str, str]:
    return login("alex")


@pytest.fixture
def make_campaign(client: TestClient) -> Any:
    """make_campaign(headers, **overrides) -> created campaign JSON (live, 30 days)."""

    def _make(headers: dict[str, str], **overrides: Any) -> dict[str, Any]:
        today = datetime.now(UTC).date()
        body = {
            "name": "Summer Glow",
            "brand": "Lumi Skincare",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat(),
            "tracking_hashtags": ["lumiglow"],
            **overrides,
        }
        response = client.post("/api/campaigns", json=body, headers=headers)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_creator(client: TestClient) -> Any:
    """make_creator(headers, handle, **overrides) -> created creator JSON."""

    def _make(headers: dict[str, str], handle: str = "lumi.lou", **overrides: Any) -> dict:
        body = {"name": handle.title(), "handle": handle, **overrides}
        response = client.post("/api/creators", json=body, headers=headers)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def assign(client: TestClient) -> Any:
    """assign(headers, campaign, *creators, target_posts=3, target_period="week") -> response."""

    def _assign(
        headers: dict[str, str],
        campaign: dict,
        *creators: dict,
        target_posts: int = 3,
        target_period: str = "week",
    ) -> Any:
        return client.post(
            f"/api/campaigns/{campaign['id']}/creators",
            json={
                "creator_ids": [c["id"] for c in creators],
                "target_posts": target_posts,
                "target_period": target_period,
            },
            headers=headers,
        )

    return _assign
