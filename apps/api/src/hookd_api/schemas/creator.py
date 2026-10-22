"""Creator roster request and response models (US-07, US-08)."""

import re
import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Field,
    StringConstraints,
    model_validator,
)

from hookd_api.schemas.campaign import CampaignPhase, Name
from hookd_core.enums import CampaignStatus, Platform, TargetPeriod

# TikTok usernames: letters, numbers, underscores and periods, up to 24 characters
_HANDLE = re.compile(r"^[a-z0-9_.]{2,24}$")
_PROFILE_URL = re.compile(r"tiktok\.com/@([^/?#\s]+)", re.IGNORECASE)
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalise_handle(raw: str) -> str:
    """'@Lumi.Lou', 'https://www.tiktok.com/@lumi.lou?lang=en' -> 'lumi.lou'."""
    text = raw.strip()
    if match := _PROFILE_URL.search(text):
        text = match.group(1)
    handle = text.lstrip("@").lower()
    if not _HANDLE.match(handle):
        raise ValueError("Enter a TikTok handle (2 to 24 letters, numbers, underscores or periods)")
    return handle


def _blank_to_none(value: object) -> object:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def _check_email(value: str | None) -> str | None:
    if value is not None and not _EMAIL.match(value):
        raise ValueError("Enter a valid email address")
    return value.lower() if value else value


# Optional free text: blank strings become None
BlankToNone = BeforeValidator(_blank_to_none)

Handle = Annotated[str, AfterValidator(normalise_handle)]
Niche = Annotated[Annotated[str, StringConstraints(max_length=80)] | None, BlankToNone]
Phone = Annotated[Annotated[str, StringConstraints(max_length=40)] | None, BlankToNone]
Email = Annotated[
    Annotated[str, StringConstraints(max_length=320)] | None,
    BlankToNone,
    AfterValidator(_check_email),
]


def profile_url(handle: str) -> str:
    return f"https://www.tiktok.com/@{handle}"


class CreatorCreate(BaseModel):
    name: Name
    handle: Handle = Field(description="TikTok handle, with or without '@', or a profile link")
    niche: Niche = None
    email: Email = None
    phone: Phone = None


class CreatorUpdate(BaseModel):
    """Partial update: only the fields sent are changed. Send null to clear an optional field."""

    name: Name | None = None
    handle: Handle | None = None
    niche: Niche = None
    email: Email = None
    phone: Phone = None

    @model_validator(mode="after")
    def required_fields_not_cleared(self) -> Self:
        for required in ("name", "handle"):
            if required in self.model_fields_set and getattr(self, required) is None:
                raise ValueError(f"{required} can't be empty")
        return self


class CreatorRead(BaseModel):
    id: uuid.UUID
    name: str
    platform: Platform
    handle: str
    profile_url: str
    niche: str | None
    email: str | None
    phone: str | None
    campaign_count: int = Field(description="Campaigns this creator is assigned to")
    created_at: datetime
    updated_at: datetime


class CreatorCampaign(BaseModel):
    """One campaign a creator is assigned to, with their target in it."""

    campaign_id: uuid.UUID
    name: str
    brand: str
    status: CampaignStatus
    phase: CampaignPhase
    target_posts: int
    target_period: TargetPeriod
