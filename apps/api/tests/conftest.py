"""Shared API test fixtures: fresh stores, a fake TikTok and locally signed
Cognito-style tokens.

Stores are in-memory by default. HOOKD_TEST_STORAGE=dynamodb runs the same tests
against the DynamoDB repositories on moto (CI does both).
"""

import os
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

from hookd_api.deps import (
    get_profile_fetcher,
    get_storage,
    get_sync_runner,
    get_token_verifier,
)
from hookd_api.main import app
from hookd_api.security import CognitoProfile, CognitoTokenVerifier
from hookd_api.services.sync import InlineSync
from hookd_core.fetchers import FetchedPost, FetchError
from hookd_core.storage import Storage, make_storage

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
def storage(monkeypatch: pytest.MonkeyPatch) -> Iterator[Storage]:
    if os.environ.get("HOOKD_TEST_STORAGE", "memory") == "memory":
        yield make_storage("memory")
        return
    from moto import mock_aws

    for var in ("AWS_ENDPOINT_URL", "AWS_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    with mock_aws():
        yield make_storage("dynamodb", table_name="hookd-test", create_table=True)


@pytest.fixture
def client(
    verifier: CognitoTokenVerifier,
    profiles: dict[str, CognitoProfile],
    tiktok: FakeTikTok,
    storage: Storage,
) -> Iterator[TestClient]:
    app.dependency_overrides[get_token_verifier] = lambda: verifier
    app.dependency_overrides[get_profile_fetcher] = lambda: profiles.__getitem__

    app.dependency_overrides[get_storage] = lambda: storage
    runner = InlineSync(tiktok, ZoneInfo("Australia/Brisbane"), lookback_days=30)
    app.dependency_overrides[get_sync_runner] = lambda: runner
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
