"""Campaign create, update, archive, delete and list (US-03 to US-06)."""

import uuid
from dataclasses import replace

from hookd_api.errors import Conflict, InvalidRequest, NotFound
from hookd_api.repositories.campaigns import Campaign, CampaignRepository
from hookd_api.schemas.campaign import (
    CampaignCreate,
    CampaignListItem,
    CampaignRead,
    CampaignUpdate,
    campaign_phase,
)
from hookd_core.enums import CampaignStatus


class CampaignNotFound(NotFound):
    def __init__(self) -> None:
        super().__init__("Campaign not found")


class CampaignArchived(Conflict):
    """Archived campaigns are read-only until restored."""

    def __init__(self) -> None:
        super().__init__("Archived campaigns can't be edited. Restore it first.")


def to_read(campaign: Campaign) -> CampaignRead:
    return CampaignRead(
        id=campaign.id,
        name=campaign.name,
        brand=campaign.brand,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        tracking_hashtags=list(campaign.tracking_hashtags),
        status=campaign.status,
        phase=campaign_phase(campaign.start_date, campaign.end_date),
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


def to_list_item(campaign: Campaign) -> CampaignListItem:
    # TODO(Epic 3/4): fill progress from assignments and posts
    return CampaignListItem(**to_read(campaign).model_dump(), progress=None)


def get(repo: CampaignRepository, organisation_id: uuid.UUID, campaign_id: uuid.UUID) -> Campaign:
    campaign = repo.get(organisation_id, campaign_id)
    if campaign is None:
        raise CampaignNotFound
    return campaign


def list_campaigns(
    repo: CampaignRepository, organisation_id: uuid.UUID, status: CampaignStatus | None
) -> list[Campaign]:
    return repo.list(organisation_id, status)


def create(repo: CampaignRepository, organisation_id: uuid.UUID, data: CampaignCreate) -> Campaign:
    return repo.add(
        Campaign(
            organisation_id=organisation_id,
            name=data.name,
            brand=data.brand,
            start_date=data.start_date,
            end_date=data.end_date,
            tracking_hashtags=tuple(data.tracking_hashtags),
        )
    )


def update(
    repo: CampaignRepository,
    organisation_id: uuid.UUID,
    campaign_id: uuid.UUID,
    changes: CampaignUpdate,
) -> Campaign:
    campaign = get(repo, organisation_id, campaign_id)
    if campaign.status == CampaignStatus.ARCHIVED:
        raise CampaignArchived

    fields = changes.model_dump(exclude_unset=True, exclude_none=True)
    if "tracking_hashtags" in fields:
        fields["tracking_hashtags"] = tuple(fields["tracking_hashtags"])
    updated = replace(campaign, **fields)
    # Dates may only be valid together, e.g. a new end date before the existing start date
    if updated.end_date < updated.start_date:
        raise InvalidRequest("End date must be on or after the start date")
    return repo.save(updated)


def set_status(
    repo: CampaignRepository,
    organisation_id: uuid.UUID,
    campaign_id: uuid.UUID,
    status: CampaignStatus,
) -> Campaign:
    campaign = get(repo, organisation_id, campaign_id)
    if campaign.status == status:
        return campaign
    return repo.save(replace(campaign, status=status))


def delete(repo: CampaignRepository, organisation_id: uuid.UUID, campaign_id: uuid.UUID) -> None:
    # TODO(Epic 3/4): also delete the campaign's assignments and posts
    if not repo.delete(organisation_id, campaign_id):
        raise CampaignNotFound
