"""FastAPI dependencies: storage, the signed-in user and sync.

Every query must be scoped to the current user's organisation_id
(use `user.organisation_id` from `CurrentUser`).
"""

from collections.abc import Callable
from datetime import tzinfo
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from hookd_api.config import settings
from hookd_api.queue import make_publisher
from hookd_api.security import (
    AuthError,
    CognitoProfile,
    CognitoTokenVerifier,
    fetch_cognito_profile,
)
from hookd_api.services import users as users_service
from hookd_api.services.sync import InlineSync, QueuedSync, SyncRunner
from hookd_core.fetchers import make_fetcher
from hookd_core.repositories.assignments import AssignmentRepository
from hookd_core.repositories.campaigns import CampaignRepository
from hookd_core.repositories.creators import CreatorRepository
from hookd_core.repositories.posts import PostRepository
from hookd_core.repositories.users import User, UserRepository
from hookd_core.storage import Storage, make_storage
from hookd_core.sync import Stores

ProfileFetcher = Callable[[str], CognitoProfile]

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_storage() -> Storage:
    return make_storage(
        settings.storage,
        table_name=settings.dynamodb_table,
        region=settings.aws_region,
        endpoint_url=settings.dynamodb_endpoint_url,
        create_table=settings.dynamodb_create_table,
    )


StorageDep = Annotated[Storage, Depends(get_storage)]


def get_user_repository(storage: StorageDep) -> UserRepository:
    return storage.users


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
    users: Annotated[UserRepository, Depends(get_user_repository)],
    verifier: Annotated[CognitoTokenVerifier, Depends(get_token_verifier)],
    fetch_profile: Annotated[ProfileFetcher, Depends(get_profile_fetcher)],
) -> User:
    if credentials is None:
        raise _unauthorized("Not authenticated")
    try:
        claims = verifier.verify(credentials.credentials)
    except AuthError as exc:
        raise _unauthorized("Invalid or expired token") from exc

    user = users_service.get_by_cognito_sub(users, claims.sub)
    if user is None:
        # First request after sign-up: create the user and their organisation
        profile = fetch_profile(credentials.credentials)
        user = users_service.provision(users, cognito_sub=claims.sub, profile=profile)
    return user


def get_campaign_repository(storage: StorageDep) -> CampaignRepository:
    return storage.stores.campaigns


def get_creator_repository(storage: StorageDep) -> CreatorRepository:
    return storage.stores.creators


def get_assignment_repository(storage: StorageDep) -> AssignmentRepository:
    return storage.stores.assignments


def get_post_repository(storage: StorageDep) -> PostRepository:
    return storage.stores.posts


def get_stores(storage: StorageDep) -> Stores:
    """All four stores, for services that work across them (posts, sync, cascading deletes)."""
    return storage.stores


def get_campaign_tz() -> tzinfo:
    return settings.campaign_tz


@lru_cache
def get_sync_runner() -> SyncRunner:
    if settings.sync_mode == "queue":
        return QueuedSync(make_publisher())
    fetcher = make_fetcher(
        settings.tiktok_mode, settings.tiktok_client_key, settings.tiktok_client_secret
    )
    return InlineSync(fetcher, settings.campaign_tz, settings.sync_lookback_days)


CurrentUser = Annotated[User, Depends(get_current_user)]
CampaignRepo = Annotated[CampaignRepository, Depends(get_campaign_repository)]
CreatorRepo = Annotated[CreatorRepository, Depends(get_creator_repository)]
AssignmentRepo = Annotated[AssignmentRepository, Depends(get_assignment_repository)]
PostRepo = Annotated[PostRepository, Depends(get_post_repository)]
AllStores = Annotated[Stores, Depends(get_stores)]
CampaignTz = Annotated[tzinfo, Depends(get_campaign_tz)]
Syncer = Annotated[SyncRunner, Depends(get_sync_runner)]
