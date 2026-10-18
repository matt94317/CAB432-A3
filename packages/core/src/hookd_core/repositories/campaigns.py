"""Campaign storage interface and an in-memory implementation."""

import uuid
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime
from threading import Lock
from typing import Protocol

from hookd_core.enums import CampaignStatus


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class Campaign:
    organisation_id: uuid.UUID
    name: str
    brand: str
    start_date: date
    end_date: date
    tracking_hashtags: tuple[str, ...]
    status: CampaignStatus = CampaignStatus.ACTIVE
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


class CampaignRepository(Protocol):
    """Every method is scoped to one organisation, so one Host can never reach another's data."""

    def add(self, campaign: Campaign) -> Campaign: ...

    def get(self, organisation_id: uuid.UUID, campaign_id: uuid.UUID) -> Campaign | None: ...

    def list(
        self, organisation_id: uuid.UUID, status: CampaignStatus | None = None
    ) -> list[Campaign]: ...

    def save(self, campaign: Campaign) -> Campaign: ...

    def delete(self, organisation_id: uuid.UUID, campaign_id: uuid.UUID) -> bool: ...


class InMemoryCampaignRepository:
    """Process-local store. Data is lost on restart and not shared between API tasks."""

    def __init__(self) -> None:
        self._items: dict[uuid.UUID, Campaign] = {}
        self._lock = Lock()

    def add(self, campaign: Campaign) -> Campaign:
        with self._lock:
            self._items[campaign.id] = campaign
        return campaign

    def get(self, organisation_id: uuid.UUID, campaign_id: uuid.UUID) -> Campaign | None:
        campaign = self._items.get(campaign_id)
        if campaign is None or campaign.organisation_id != organisation_id:
            return None
        return campaign

    def list(
        self, organisation_id: uuid.UUID, status: CampaignStatus | None = None
    ) -> list[Campaign]:
        campaigns = [
            c
            for c in self._items.values()
            if c.organisation_id == organisation_id and (status is None or c.status == status)
        ]
        return sorted(campaigns, key=lambda c: (c.start_date, c.created_at), reverse=True)

    def save(self, campaign: Campaign) -> Campaign:
        saved = replace(campaign, updated_at=_now())
        with self._lock:
            self._items[campaign.id] = saved
        return saved

    def delete(self, organisation_id: uuid.UUID, campaign_id: uuid.UUID) -> bool:
        with self._lock:
            if self.get(organisation_id, campaign_id) is None:
                return False
            del self._items[campaign_id]
        return True
