"""Workspace overview, campaign dashboard (US-19, US-20), creator performance (US-21)
and who's behind target (US-22).

Every route is scoped to the signed-in user's organisation.
"""

import uuid

from fastapi import APIRouter, Response

from hookd_api.deps import AllStores, Cache, CampaignTz, CurrentUser
from hookd_api.schemas.dashboard import BehindTargetItem, CampaignDashboard, CreatorPerformance
from hookd_api.schemas.overview import Overview
from hookd_api.services import dashboard as service
from hookd_api.services import overview as overview_service

router = APIRouter(tags=["dashboard"])


@router.get(
    "/overview",
    response_model=Overview,
    responses={422: {"description": "month isn't YYYY-MM"}},
)
def workspace_overview(
    response: Response,
    user: CurrentUser,
    stores: AllStores,
    cache: Cache,
    tz: CampaignTz,
    month: str | None = None,
) -> Overview:
    """Everything at a glance for one month (default: this month), compared with the
    month before. For the current month, the comparison is the same days last month.

    Cached; any change to your data refreshes it. `X-Cache: hit|miss` says which.
    """
    overview, hit = overview_service.overview(stores, cache, user.organisation_id, tz, month)
    response.headers["X-Cache"] = "hit" if hit else "miss"
    return overview


@router.get(
    "/campaigns/{campaign_id}/dashboard",
    response_model=CampaignDashboard,
    responses={404: {"description": "Campaign not found in your organisation"}},
)
def campaign_dashboard(
    campaign_id: uuid.UUID,
    response: Response,
    user: CurrentUser,
    stores: AllStores,
    cache: Cache,
    tz: CampaignTz,
) -> CampaignDashboard:
    """Every creator's posts vs target this period, campaign totals and daily performance.

    Cached; any change to your data refreshes it. `X-Cache: hit|miss` says which.
    """
    dashboard, hit = service.campaign_dashboard(
        stores, cache, user.organisation_id, campaign_id, tz
    )
    response.headers["X-Cache"] = "hit" if hit else "miss"
    return dashboard


@router.get("/behind-target", response_model=list[BehindTargetItem])
def behind_target(user: CurrentUser, stores: AllStores, tz: CampaignTz) -> list[BehindTargetItem]:
    """Creators behind target this period on any live campaign, most behind first."""
    return service.behind_target(stores, user.organisation_id, tz)


@router.get(
    "/creators/{creator_id}/performance",
    response_model=CreatorPerformance,
    responses={404: {"description": "Creator not found in your organisation"}},
)
def creator_performance(
    creator_id: uuid.UUID, user: CurrentUser, stores: AllStores, tz: CampaignTz
) -> CreatorPerformance:
    """One creator's posts and performance across all their campaigns."""
    return service.creator_performance(stores, user.organisation_id, creator_id, tz)
