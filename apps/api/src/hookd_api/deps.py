"""FastAPI dependencies: database session and the signed-in user.

Every query must be scoped to the current user's organisation_id
(use `user.organisation_id` from `CurrentUser`).
"""

from collections.abc import Callable, Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from hookd_api.config import settings
from hookd_api.db import SessionLocal
from hookd_api.repositories.campaigns import CampaignRepository, InMemoryCampaignRepository
from hookd_api.security import (
    AuthError,
    CognitoProfile,
    CognitoTokenVerifier,
    fetch_cognito_profile,
)
from hookd_api.services import users as users_service
from hookd_core.models import User

ProfileFetcher = Callable[[str], CognitoProfile]

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


@lru_cache
def _verifier() -> CognitoTokenVerifier:
    return CognitoTokenVerifier(settings.cognito_user_pool_id, settings.cognito_app_client_id)


def get_token_verifier() -> CognitoTokenVerifier:
    if not settings.cognito_user_pool_id or not settings.cognito_app_client_id:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Authentication is not configured")
    return _verifier()


def get_profile_fetcher() -> ProfileFetcher:
    return lambda token: fetch_cognito_profile(token, settings.cognito_user_pool_id)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"}
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
    verifier: Annotated[CognitoTokenVerifier, Depends(get_token_verifier)],
    fetch_profile: Annotated[ProfileFetcher, Depends(get_profile_fetcher)],
) -> User:
    if credentials is None:
        raise _unauthorized("Not authenticated")
    try:
        claims = verifier.verify(credentials.credentials)
    except AuthError as exc:
        raise _unauthorized("Invalid or expired token") from exc

    user = users_service.get_by_cognito_sub(db, claims.sub)
    if user is None:
        # First request after sign-up: create the user and their organisation
        profile = fetch_profile(credentials.credentials)
        user = users_service.provision(db, cognito_sub=claims.sub, profile=profile)
    return user


@lru_cache
def get_campaign_repository() -> CampaignRepository:
    # TODO: return the real store once the A3 database is chosen (RDS or DynamoDB)
    return InMemoryCampaignRepository()


DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CampaignRepo = Annotated[CampaignRepository, Depends(get_campaign_repository)]
