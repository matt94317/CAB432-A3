"""Sync request results (US-13, US-18)."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SyncFailure(BaseModel):
    creator_id: uuid.UUID
    handle: str
    error: str


class SyncRun(BaseModel):
    mode: Literal["inline", "queued"] = Field(
        description="inline: done now, counts are final. queued: the worker will sync shortly"
    )
    creators: int = Field(description="Creators synced (inline) or queued")
    added: int = 0
    updated: int = 0
    removed: int = Field(default=0, description="Posts that no longer match a campaign")
    failed: list[SyncFailure] = []
    finished_at: datetime | None = None
