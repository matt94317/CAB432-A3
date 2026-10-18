"""Creator roster: add, edit, remove and list (US-07, US-08)."""

import uuid
from collections import Counter
from dataclasses import replace

from hookd_api.errors import Conflict, NotFound
from hookd_api.schemas.campaign import campaign_phase
from hookd_api.schemas.creator import (
    CreatorCampaign,
    CreatorCreate,
    CreatorRead,
    CreatorUpdate,
    profile_url,
)
from hookd_core.repositories.assignments import AssignmentRepository
from hookd_core.repositories.campaigns import CampaignRepository
from hookd_core.repositories.creators import Creator, CreatorRepository


class CreatorNotFound(NotFound):
    def __init__(self) -> None:
        super().__init__("Creator not found")


class HandleTaken(Conflict):
    def __init__(self, handle: str) -> None:
        super().__init__(f"@{handle} is already in your roster")


def to_read(creator: Creator, campaign_count: int) -> CreatorRead:
    return CreatorRead(
        id=creator.id,
        name=creator.name,
        platform=creator.platform,
        handle=creator.handle,
        profile_url=profile_url(creator.handle),
        niche=creator.niche,
        email=creator.email,
        phone=creator.phone,
        campaign_count=campaign_count,
        created_at=creator.created_at,
        updated_at=creator.updated_at,
    )


def get(repo: CreatorRepository, organisation_id: uuid.UUID, creator_id: uuid.UUID) -> Creator:
    creator = repo.get(organisation_id, creator_id)
    if creator is None:
        raise CreatorNotFound
    return creator


def read(
    repo: CreatorRepository,
    assignments: AssignmentRepository,
    organisation_id: uuid.UUID,
    creator_id: uuid.UUID,
) -> CreatorRead:
    creator = get(repo, organisation_id, creator_id)
    return to_read(creator, len(assignments.list(organisation_id, creator_id=creator_id)))


def list_creators(
    repo: CreatorRepository,
    assignments: AssignmentRepository,
    organisation_id: uuid.UUID,
    search: str | None = None,
) -> list[CreatorRead]:
    creators = repo.list(organisation_id)
    if search and (needle := search.strip().lstrip("@").lower()):
        creators = [
            c
            for c in creators
            if needle in c.name.lower()
            or needle in c.handle
            or (c.niche is not None and needle in c.niche.lower())
        ]
    counts = Counter(a.creator_id for a in assignments.list(organisation_id))
    return [to_read(c, counts[c.id]) for c in creators]


def _check_handle_free(
    repo: CreatorRepository, creator: Creator, exclude_id: uuid.UUID | None = None
) -> None:
    existing = repo.get_by_handle(creator.organisation_id, creator.platform, creator.handle)
    if existing is not None and existing.id != exclude_id:
        raise HandleTaken(creator.handle)


def create(repo: CreatorRepository, organisation_id: uuid.UUID, data: CreatorCreate) -> Creator:
    creator = Creator(organisation_id=organisation_id, **data.model_dump())
    _check_handle_free(repo, creator)
    return repo.add(creator)


def update(
    repo: CreatorRepository,
    organisation_id: uuid.UUID,
    creator_id: uuid.UUID,
    changes: CreatorUpdate,
) -> Creator:
    creator = get(repo, organisation_id, creator_id)
    updated = replace(creator, **changes.model_dump(exclude_unset=True))
    if updated.handle != creator.handle:
        _check_handle_free(repo, updated, exclude_id=creator.id)
    return repo.save(updated)


def delete(
    repo: CreatorRepository,
    assignments: AssignmentRepository,
    organisation_id: uuid.UUID,
    creator_id: uuid.UUID,
) -> None:
    """Remove a creator from the roster, along with every campaign assignment they have."""
    get(repo, organisation_id, creator_id)
    assignments.delete_where(organisation_id, creator_id=creator_id)
    repo.delete(organisation_id, creator_id)


def list_campaigns(
    repo: CreatorRepository,
    assignments: AssignmentRepository,
    campaigns: CampaignRepository,
    organisation_id: uuid.UUID,
    creator_id: uuid.UUID,
) -> list[CreatorCampaign]:
    """The campaigns a creator is assigned to, by name, with their target in each."""
    get(repo, organisation_id, creator_id)
    rows = []
    for assignment in assignments.list(organisation_id, creator_id=creator_id):
        campaign = campaigns.get(organisation_id, assignment.campaign_id)
        if campaign is None:
            continue
        rows.append(
            CreatorCampaign(
                campaign_id=campaign.id,
                name=campaign.name,
                brand=campaign.brand,
                status=campaign.status,
                phase=campaign_phase(campaign.start_date, campaign.end_date),
                target_posts=assignment.target_posts,
                target_period=assignment.target_period,
            )
        )
    return sorted(rows, key=lambda r: r.name.lower())
