"""Tests for MCP tools (mock the API client)."""

import json
import uuid
from types import SimpleNamespace

import pytest
from mcp import Client
from mcp.server.mcpserver.exceptions import ToolError

from hookd_mcp.server import mcp
from hookd_mcp.tools import campaigns, creators

CAMPAIGN_ID = uuid.uuid4()
CREATOR_ID = uuid.uuid4()


def ctx(authorization: str | None = "Bearer user-token"):
    headers = {} if authorization is None else {"authorization": authorization}
    return SimpleNamespace(headers=headers)


@pytest.mark.anyio
async def test_all_tools_are_registered():
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    assert set(tools) == {
        "list_campaigns",
        "get_campaign_progress",
        "list_behind_target_creators",
        "list_creators",
        "get_creator_performance",
        "update_creator_target",
    }
    assert tools["list_campaigns"].annotations.read_only_hint is True
    assert tools["update_creator_target"].annotations.read_only_hint is False


@pytest.mark.anyio
async def test_a_call_without_a_token_is_refused_before_reaching_the_api(api):
    async with Client(mcp) as client:
        result = await client.call_tool("list_behind_target_creators", {})

    assert result.is_error
    assert "Authorization: Bearer" in result.content[0].text
    assert api.calls == []


@pytest.mark.anyio
@pytest.mark.parametrize("header", [None, "", "Basic abc", "Bearer ", "user-token"])
async def test_only_a_bearer_token_is_accepted(api, header):
    with pytest.raises(ToolError, match="No sign-in token"):
        await campaigns.list_behind_target_creators(ctx(header))
    assert api.calls == []


@pytest.mark.anyio
async def test_the_users_token_is_passed_through_to_the_api(api):
    api.responses[("GET", "/api/campaigns")] = (200, [{"id": str(CAMPAIGN_ID)}])

    result = await campaigns.list_campaigns(ctx(), status="all")

    assert result == [{"id": str(CAMPAIGN_ID)}]
    (call,) = api.calls
    assert call.headers["authorization"] == "Bearer user-token"
    assert call.url.params["status"] == "all"


@pytest.mark.anyio
async def test_campaign_progress_leaves_out_the_daily_series(api):
    api.responses[("GET", f"/api/campaigns/{CAMPAIGN_ID}/dashboard")] = (
        200,
        {"behind_count": 1, "creators": [], "daily": [{"date": "2026-10-01"}]},
    )

    result = await campaigns.get_campaign_progress(ctx(), CAMPAIGN_ID)

    assert result == {"behind_count": 1, "creators": []}


@pytest.mark.anyio
async def test_behind_target_creators(api):
    api.responses[("GET", "/api/behind-target")] = (200, [{"remaining": 3}])

    assert await campaigns.list_behind_target_creators(ctx()) == [{"remaining": 3}]


@pytest.mark.anyio
async def test_creator_performance_keeps_the_newest_posts(api):
    posts = [{"id": n} for n in range(25)]
    api.responses[("GET", f"/api/creators/{CREATOR_ID}/performance")] = (
        200,
        {"creator_id": str(CREATOR_ID), "campaigns": [], "posts": posts},
    )

    result = await creators.get_creator_performance(ctx(), CREATOR_ID)

    assert result["post_count"] == 25
    assert result["posts"] == posts[: creators.RECENT_POSTS]


@pytest.mark.anyio
async def test_update_target_sends_only_the_fields_given(api):
    path = f"/api/campaigns/{CAMPAIGN_ID}/creators/{CREATOR_ID}"
    api.responses[("PATCH", path)] = (200, {"target_posts": 5, "target_period": "week"})

    result = await creators.update_creator_target(ctx(), CAMPAIGN_ID, CREATOR_ID, target_posts=5)

    assert result["target_posts"] == 5
    (call,) = api.calls
    assert json.loads(call.content) == {"target_posts": 5}


@pytest.mark.anyio
async def test_api_not_found_reaches_the_model_as_a_tool_error(api):
    api.responses[("GET", f"/api/creators/{CREATOR_ID}/performance")] = (
        404,
        {"detail": "Creator not found"},
    )

    with pytest.raises(ToolError, match="Creator not found"):
        await creators.get_creator_performance(ctx(), CREATOR_ID)


@pytest.mark.anyio
async def test_a_rejected_token_asks_for_a_fresh_one(api):
    api.responses[("GET", "/api/behind-target")] = (401, {"detail": "Token expired"})

    with pytest.raises(ToolError, match="fresh token"):
        await campaigns.list_behind_target_creators(ctx())
