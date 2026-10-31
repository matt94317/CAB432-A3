"""Tools: list_campaigns, get_campaign_progress, list_behind_target_creators (US-24, US-25)."""

from typing import Any, Literal
from uuid import UUID

from mcp.server.mcpserver import Context

from hookd_mcp.api_client import api_for


async def list_campaigns(
    ctx: Context, status: Literal["active", "archived", "all"] = "active"
) -> list[dict[str, Any]]:
    """List your campaigns with their dates, tracking hashtags and posts vs target this
    period. Use it to find a campaign's id by name."""
    return await api_for(ctx).get("/campaigns", status=status)


async def get_campaign_progress(ctx: Context, campaign_id: UUID) -> dict[str, Any]:
    """A campaign's dashboard: every creator's posts vs target this period (behind
    first), the campaign's total views and engagement, and when it was last synced."""
    dashboard = await api_for(ctx).get(f"/campaigns/{campaign_id}/dashboard")
    # The day-by-day chart series is long and the totals already summarise it
    dashboard.pop("daily", None)
    return dashboard


async def list_behind_target_creators(ctx: Context) -> list[dict[str, Any]]:
    """Creators behind target this period on any live campaign, most behind first, with
    how many posts they still owe and their email to chase them."""
    return await api_for(ctx).get("/behind-target")


TOOLS = [list_campaigns, get_campaign_progress, list_behind_target_creators]
