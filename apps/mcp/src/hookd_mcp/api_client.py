"""httpx client for the Hookd API, called with the user's token."""

from typing import Any

import httpx
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError

from hookd_mcp.auth import bearer_token
from hookd_mcp.config import settings

# Tests swap in an httpx.MockTransport
transport: httpx.AsyncBaseTransport | None = None

EXPIRED = "Your Hookd sign-in token was rejected or has expired. Reconnect with a fresh token."


class HookdApi:
    def __init__(self, token: str) -> None:
        self._token = token

    async def get(self, path: str, **params: Any) -> Any:
        return await self._request("GET", path, params=params or None)

    async def patch(self, path: str, body: dict[str, Any]) -> Any:
        return await self._request("PATCH", path, json=body)

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        async with httpx.AsyncClient(
            base_url=settings.hookd_api_url.rstrip("/"),
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=15,
            transport=transport,
        ) as client:
            response = await client.request(method, path, **kwargs)
        if response.status_code == 401:
            raise ToolError(EXPIRED)
        # Not found, conflict and validation errors are for the model to read and act on
        if response.status_code in (404, 409, 422):
            raise ToolError(_detail(response))
        response.raise_for_status()
        return response.json()


def api_for(ctx: Context) -> HookdApi:
    return HookdApi(bearer_token(ctx))


def _detail(response: httpx.Response) -> str:
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None
    return detail if isinstance(detail, str) else f"{response.status_code}: {response.text}"
