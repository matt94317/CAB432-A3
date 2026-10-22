"""Trigger a manual sync (US-13). Last-synced times are on each assigned creator and
post (US-18)."""

import uuid
from datetime import datetime

from fastapi import APIRouter

from hookd_api.config import settings
from hookd_api.deps import AllStores, CampaignTz, CurrentUser, Syncer
from hookd_api.schemas.sync import SyncRun
from hookd_api.services import sync as service

router = APIRouter(tags=["sync"])


@router.post("/sync", response_model=SyncRun)
def sync_workspace(user: CurrentUser, stores: AllStores, runner: Syncer, tz: CampaignTz) -> SyncRun:
    """Pull the latest posts and metrics for every creator on a campaign being tracked now."""
    today = datetime.now(tz).date()
    return service.sync_workspace(
        stores, runner, user.organisation_id, today, settings.sync_lookback_days
    )


@router.post(
    "/campaigns/{campaign_id}/sync",
    response_model=SyncRun,
    responses={
        404: {"description": "Campaign not found in your organisation"},
        409: {"description": "Campaign is archived"},
    },
)
def sync_campaign(
    campaign_id: uuid.UUID, user: CurrentUser, stores: AllStores, runner: Syncer
) -> SyncRun:
    """Pull the latest posts and metrics for every creator on this campaign now."""
    return service.sync_campaign(stores, runner, user.organisation_id, campaign_id)
