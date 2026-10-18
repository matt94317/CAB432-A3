"""Creator roster CRUD (US-07, US-08) and the campaigns each creator is on.

Every route is scoped to the signed-in user's organisation.
"""

import uuid

from fastapi import APIRouter, Response, status

from hookd_api.deps import AssignmentRepo, CampaignRepo, CreatorRepo, CurrentUser, PostRepo
from hookd_api.schemas.creator import CreatorCampaign, CreatorCreate, CreatorRead, CreatorUpdate
from hookd_api.services import creators as service

router = APIRouter(prefix="/creators", tags=["creators"])

NOT_FOUND = {404: {"description": "Creator not found in your organisation"}}
HANDLE_TAKEN = {409: {"description": "Another creator in your roster has this handle"}}


@router.get("", response_model=list[CreatorRead])
def list_creators(
    user: CurrentUser,
    repo: CreatorRepo,
    assignments: AssignmentRepo,
    search: str | None = None,
) -> list[CreatorRead]:
    """The roster, by name. `search` matches name, handle or niche."""
    return service.list_creators(repo, assignments, user.organisation_id, search)


@router.post(
    "", response_model=CreatorRead, status_code=status.HTTP_201_CREATED, responses=HANDLE_TAKEN
)
def create_creator(data: CreatorCreate, user: CurrentUser, repo: CreatorRepo) -> CreatorRead:
    return service.to_read(service.create(repo, user.organisation_id, data), campaign_count=0)


@router.get("/{creator_id}", response_model=CreatorRead, responses=NOT_FOUND)
def get_creator(
    creator_id: uuid.UUID, user: CurrentUser, repo: CreatorRepo, assignments: AssignmentRepo
) -> CreatorRead:
    return service.read(repo, assignments, user.organisation_id, creator_id)


@router.patch("/{creator_id}", response_model=CreatorRead, responses={**NOT_FOUND, **HANDLE_TAKEN})
def update_creator(
    creator_id: uuid.UUID,
    changes: CreatorUpdate,
    user: CurrentUser,
    repo: CreatorRepo,
    assignments: AssignmentRepo,
) -> CreatorRead:
    service.update(repo, user.organisation_id, creator_id, changes)
    return service.read(repo, assignments, user.organisation_id, creator_id)


@router.delete("/{creator_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_creator(
    creator_id: uuid.UUID,
    user: CurrentUser,
    repo: CreatorRepo,
    assignments: AssignmentRepo,
    posts: PostRepo,
) -> Response:
    """Remove from the roster, with their campaign assignments and tracked posts."""
    service.delete(repo, assignments, posts, user.organisation_id, creator_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{creator_id}/campaigns", response_model=list[CreatorCampaign], responses=NOT_FOUND)
def list_creator_campaigns(
    creator_id: uuid.UUID,
    user: CurrentUser,
    repo: CreatorRepo,
    assignments: AssignmentRepo,
    campaigns: CampaignRepo,
) -> list[CreatorCampaign]:
    return service.list_campaigns(repo, assignments, campaigns, user.organisation_id, creator_id)
