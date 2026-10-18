"""Assignment request and response models: creators on a campaign and their targets
(US-09 to US-12)."""

import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, Field, model_validator

from hookd_core.enums import Platform, TargetPeriod

MAX_TARGET_POSTS = 100
MAX_ASSIGN_AT_ONCE = 100

TargetPosts = Annotated[
    int,
    Field(ge=1, le=MAX_TARGET_POSTS, description="Posts the creator should publish per period"),
]


def _unique(ids: list[uuid.UUID]) -> list[uuid.UUID]:
    return list(dict.fromkeys(ids))


class AssignmentCreate(BaseModel):
    """Assign one or more roster creators, all starting with the same target."""

    creator_ids: Annotated[
        list[uuid.UUID],
        Field(min_length=1, max_length=MAX_ASSIGN_AT_ONCE),
        AfterValidator(_unique),
    ]
    target_posts: TargetPosts
    target_period: TargetPeriod


class AssignmentUpdate(BaseModel):
    """Change a creator's target in this campaign. Only the fields sent are changed."""

    target_posts: TargetPosts | None = None
    target_period: TargetPeriod | None = None

    @model_validator(mode="after")
    def something_to_change(self) -> Self:
        if self.target_posts is None and self.target_period is None:
            raise ValueError("Send target_posts, target_period or both")
        return self


class AssignedCreator(BaseModel):
    id: uuid.UUID
    name: str
    platform: Platform
    handle: str
    niche: str | None
    last_synced_at: datetime | None = Field(description="Null until their posts are first synced")


class AssignmentRead(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    creator: AssignedCreator
    target_posts: int
    target_period: TargetPeriod
    created_at: datetime
    updated_at: datetime
