"""Campaign CRUD, archive and list (US-03 to US-06).

Every route is scoped to the signed-in user's organisation.
"""

import uuid
from enum import StrEnum

from fastapi import APIRouter, Response, status

from hookd_api.deps import AssignmentRepo, CampaignRepo, CampaignTz, CurrentUser, PostRepo
from hookd_api.schemas.campaign import (
    CampaignCreate,
    CampaignListItem,
    CampaignRead,
    CampaignUpdate,
)
from hookd_api.services import campaigns as service
from hookd_core.enums import CampaignStatus

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

NOT_FOUND = {404: {"description": "Campaign not found in your organisation"}}


class StatusFilter(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    ALL = "all"


@router.get("", response_model=list[CampaignListItem])
def list_campaigns(
    user: CurrentUser,
    repo: CampaignRepo,
    assignments: AssignmentRepo,
    posts: PostRepo,
    tz: CampaignTz,
    status: StatusFilter = StatusFilter.ACTIVE,
) -> list[CampaignListItem]:
    wanted = None if status == StatusFilter.ALL else CampaignStatus(status.value)
    return service.list_campaigns(repo, assignments, posts, user.organisation_id, wanted, tz)


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
def create_campaign(data: CampaignCreate, user: CurrentUser, repo: CampaignRepo) -> CampaignRead:
    return service.to_read(service.create(repo, user.organisation_id, data))


@router.get("/{campaign_id}", response_model=CampaignRead, responses=NOT_FOUND)
def get_campaign(campaign_id: uuid.UUID, user: CurrentUser, repo: CampaignRepo) -> CampaignRead:
    return service.to_read(service.get(repo, user.organisation_id, campaign_id))


@router.patch(
    "/{campaign_id}",
    response_model=CampaignRead,
    responses={**NOT_FOUND, 409: {"description": "Campaign is archived"}},
)
def update_campaign(
    campaign_id: uuid.UUID, changes: CampaignUpdate, user: CurrentUser, repo: CampaignRepo
) -> CampaignRead:
    return service.to_read(service.update(repo, user.organisation_id, campaign_id, changes))


@router.post("/{campaign_id}/archive", response_model=CampaignRead, responses=NOT_FOUND)
def archive_campaign(campaign_id: uuid.UUID, user: CurrentUser, repo: CampaignRepo) -> CampaignRead:
    campaign = service.set_status(repo, user.organisation_id, campaign_id, CampaignStatus.ARCHIVED)
    return service.to_read(campaign)


@router.post("/{campaign_id}/restore", response_model=CampaignRead, responses=NOT_FOUND)
def restore_campaign(campaign_id: uuid.UUID, user: CurrentUser, repo: CampaignRepo) -> CampaignRead:
    campaign = service.set_status(repo, user.organisation_id, campaign_id, CampaignStatus.ACTIVE)
    return service.to_read(campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_campaign(
    campaign_id: uuid.UUID,
    user: CurrentUser,
    repo: CampaignRepo,
    assignments: AssignmentRepo,
    posts: PostRepo,
) -> Response:
    """Delete the campaign with its assignments and posts."""
    service.delete(repo, assignments, posts, user.organisation_id, campaign_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
