"""Assign creators to a campaign, set and change their targets, unassign (US-09 to US-12)."""

import uuid
from dataclasses import replace

from hookd_api.errors import Conflict, NotFound
from hookd_api.repositories.assignments import Assignment, AssignmentRepository
from hookd_api.repositories.campaigns import CampaignRepository
from hookd_api.repositories.creators import Creator, CreatorRepository
from hookd_api.schemas.assignment import (
    AssignedCreator,
    AssignmentCreate,
    AssignmentRead,
    AssignmentUpdate,
)
from hookd_api.services import campaigns as campaigns_service
from hookd_api.services.campaigns import CampaignArchived
from hookd_api.services.creators import CreatorNotFound
from hookd_core.enums import CampaignStatus


class AssignmentNotFound(NotFound):
    def __init__(self) -> None:
        super().__init__("This creator isn't assigned to the campaign")


class AlreadyAssigned(Conflict):
    def __init__(self, handles: list[str]) -> None:
        names = ", ".join(f"@{h}" for h in handles)
        super().__init__(f"Already assigned to this campaign: {names}")


def to_read(assignment: Assignment, creator: Creator) -> AssignmentRead:
    return AssignmentRead(
        id=assignment.id,
        campaign_id=assignment.campaign_id,
        creator=AssignedCreator(
            id=creator.id,
            name=creator.name,
            platform=creator.platform,
            handle=creator.handle,
            niche=creator.niche,
        ),
        target_posts=assignment.target_posts,
        target_period=assignment.target_period,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
    )


def _editable_campaign(
    campaigns: CampaignRepository, organisation_id: uuid.UUID, campaign_id: uuid.UUID
) -> None:
    """Archived campaigns are read-only, including who is on them and their targets."""
    campaign = campaigns_service.get(campaigns, organisation_id, campaign_id)
    if campaign.status == CampaignStatus.ARCHIVED:
        raise CampaignArchived


def list_for_campaign(
    assignments: AssignmentRepository,
    campaigns: CampaignRepository,
    creators: CreatorRepository,
    organisation_id: uuid.UUID,
    campaign_id: uuid.UUID,
) -> list[AssignmentRead]:
    campaigns_service.get(campaigns, organisation_id, campaign_id)
    rows = []
    for assignment in assignments.list(organisation_id, campaign_id=campaign_id):
        creator = creators.get(organisation_id, assignment.creator_id)
        if creator is not None:
            rows.append(to_read(assignment, creator))
    return sorted(rows, key=lambda r: r.creator.name.lower())


def assign(
    assignments: AssignmentRepository,
    campaigns: CampaignRepository,
    creators: CreatorRepository,
    organisation_id: uuid.UUID,
    campaign_id: uuid.UUID,
    data: AssignmentCreate,
) -> list[AssignmentRead]:
    """Assign every creator in the request, or none of them if any can't be assigned."""
    _editable_campaign(campaigns, organisation_id, campaign_id)

    roster = []
    for creator_id in data.creator_ids:
        creator = creators.get(organisation_id, creator_id)
        if creator is None:
            raise CreatorNotFound
        roster.append(creator)

    taken = [
        c.handle for c in roster if assignments.get(organisation_id, campaign_id, c.id) is not None
    ]
    if taken:
        raise AlreadyAssigned(taken)

    added = assignments.add_many(
        [
            Assignment(
                organisation_id=organisation_id,
                campaign_id=campaign_id,
                creator_id=c.id,
                target_posts=data.target_posts,
                target_period=data.target_period,
            )
            for c in roster
        ]
    )
    return [to_read(a, c) for a, c in zip(added, roster, strict=True)]


def update_target(
    assignments: AssignmentRepository,
    campaigns: CampaignRepository,
    creators: CreatorRepository,
    organisation_id: uuid.UUID,
    campaign_id: uuid.UUID,
    creator_id: uuid.UUID,
    changes: AssignmentUpdate,
) -> AssignmentRead:
    _editable_campaign(campaigns, organisation_id, campaign_id)
    assignment = assignments.get(organisation_id, campaign_id, creator_id)
    creator = creators.get(organisation_id, creator_id)
    if assignment is None or creator is None:
        raise AssignmentNotFound
    updated = assignments.save(
        replace(assignment, **changes.model_dump(exclude_unset=True, exclude_none=True))
    )
    return to_read(updated, creator)


def unassign(
    assignments: AssignmentRepository,
    campaigns: CampaignRepository,
    organisation_id: uuid.UUID,
    campaign_id: uuid.UUID,
    creator_id: uuid.UUID,
) -> None:
    """Take a creator off a campaign. They stay in the roster (US-12)."""
    _editable_campaign(campaigns, organisation_id, campaign_id)
    if not assignments.delete(organisation_id, campaign_id, creator_id):
        raise AssignmentNotFound
