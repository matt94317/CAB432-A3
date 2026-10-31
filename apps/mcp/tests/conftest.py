"""Shared MCP test fixtures: a fake Hookd API behind the httpx client."""

from types import SimpleNamespace

import httpx
import pytest

from hookd_mcp import api_client


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def api(monkeypatch):
    """A fake Hookd API. Set `api.responses[(method, path)]`; requests land in `api.calls`.
    `GET /api/me` answers 200 unless set otherwise."""
    fake = SimpleNamespace(responses={("GET", "/api/me"): (200, {"id": "me"})}, calls=[])

    def handle(request: httpx.Request) -> httpx.Response:
        fake.calls.append(request)
        status, body = fake.responses.get((request.method, request.url.path), (404, {}))
        return httpx.Response(status, json=body)

    monkeypatch.setattr(api_client, "transport", httpx.MockTransport(handle))
    monkeypatch.setattr(api_client.settings, "hookd_api_url", "http://api.test/api")
    return fake
