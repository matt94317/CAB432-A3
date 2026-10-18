"""Assign creators to a campaign, set and change targets, unassign (US-09 to US-12).

Every route is scoped to the signed-in user's organisation.
"""

import uuid

from fastapi import APIRouter, Response, status

from hookd_api.deps import AssignmentRepo, CampaignRepo, CreatorRepo, CurrentUser
from hookd_api.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentUpdate
from hookd_api.services import assignments as service

router = APIRouter(prefix="/campaigns/{campaign_id}/creators", tags=["assignments"])

NOT_FOUND = {404: {"description": "Campaign, creator or assignment not found"}}
ARCHIVED = {409: {"description": "Campaign is archived"}}


@router.get("", response_model=list[AssignmentRead], responses=NOT_FOUND)
def list_assignments(
    campaign_id: uuid.UUID,
    user: CurrentUser,
    repo: AssignmentRepo,
    campaigns: CampaignRepo,
    creators: CreatorRepo,
) -> list[AssignmentRead]:
    """Creators on this campaign with their targets, by name."""
    return service.list_for_campaign(repo, campaigns, creators, user.organisation_id, campaign_id)


@router.post(
    "",
    response_model=list[AssignmentRead],
    status_code=status.HTTP_201_CREATED,
    responses={
        **NOT_FOUND,
        409: {"description": "Campaign is archived, or a creator is already assigned"},
    },
)
def assign_creators(
    campaign_id: uuid.UUID,
    data: AssignmentCreate,
    user: CurrentUser,
    repo: AssignmentRepo,
    campaigns: CampaignRepo,
    creators: CreatorRepo,
) -> list[AssignmentRead]:
    """Assign roster creators with a starting target. All or nothing."""
    return service.assign(repo, campaigns, creators, user.organisation_id, campaign_id, data)


@router.patch("/{creator_id}", response_model=AssignmentRead, responses={**NOT_FOUND, **ARCHIVED})
def update_target(
    campaign_id: uuid.UUID,
    creator_id: uuid.UUID,
    changes: AssignmentUpdate,
    user: CurrentUser,
    repo: AssignmentRepo,
    campaigns: CampaignRepo,
    creators: CreatorRepo,
) -> AssignmentRead:
    """Change a creator's target in this campaign when the deal changes."""
    return service.update_target(
        repo, campaigns, creators, user.organisation_id, campaign_id, creator_id, changes
    )


@router.delete(
    "/{creator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**NOT_FOUND, **ARCHIVED},
)
def unassign_creator(
    campaign_id: uuid.UUID,
    creator_id: uuid.UUID,
    user: CurrentUser,
    repo: AssignmentRepo,
    campaigns: CampaignRepo,
) -> Response:
    """Take a creator off this campaign. They stay in the roster."""
    service.unassign(repo, campaigns, user.organisation_id, campaign_id, creator_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
