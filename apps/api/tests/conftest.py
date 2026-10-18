"""Shared API test fixtures: in-memory database and locally signed Cognito-style tokens."""

import time
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from hookd_api.deps import get_db, get_profile_fetcher, get_token_verifier
from hookd_api.main import app
from hookd_api.security import CognitoProfile, CognitoTokenVerifier
from hookd_core.models import Base

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


@pytest.fixture
def client(
    db_session_factory: sessionmaker[Session],
    verifier: CognitoTokenVerifier,
    profiles: dict[str, CognitoProfile],
) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_token_verifier] = lambda: verifier
    app.dependency_overrides[get_profile_fetcher] = lambda: profiles.__getitem__
    yield TestClient(app)
    app.dependency_overrides.clear()
