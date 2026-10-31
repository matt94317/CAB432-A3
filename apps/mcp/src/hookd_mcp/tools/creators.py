"""Tools: list_creators, get_creator_performance, update_creator_target (US-26, US-27)."""

from typing import Annotated, Any, Literal
from uuid import UUID

from mcp.server.mcpserver import Context
from pydantic import Field

from hookd_mcp.api_client import api_for

RECENT_POSTS = 10


async def list_creators(ctx: Context) -> list[dict[str, Any]]:
    """List the creators on your roster with their handles and how many campaigns each
    is on. Use it to find a creator's id by name or handle."""
    return await api_for(ctx).get("/creators")


async def get_creator_performance(ctx: Context, creator_id: UUID) -> dict[str, Any]:
    """One creator's totals across every campaign, their posts vs target in each, and
    their most recent posts."""
    performance = await api_for(ctx).get(f"/creators/{creator_id}/performance")
    posts = performance.get("posts", [])
    performance["post_count"] = len(posts)
    performance["posts"] = posts[:RECENT_POSTS]  # newest first
    return performance


async def update_creator_target(
    ctx: Context,
    campaign_id: UUID,
    creator_id: UUID,
    target_posts: Annotated[int | None, Field(ge=1, le=100, description="Posts per period")] = None,
    target_period: Literal["week", "month"] | None = None,
) -> dict[str, Any]:
    """Change a creator's posting target in one campaign when the deal changes. Send
    target_posts, target_period or both; the other keeps its current value."""
    changes = {"target_posts": target_posts, "target_period": target_period}
    return await api_for(ctx).patch(
        f"/campaigns/{campaign_id}/creators/{creator_id}",
        {k: v for k, v in changes.items() if v is not None},
    )


TOOLS = [list_creators, get_creator_performance]
WRITE_TOOLS = [update_creator_target]
