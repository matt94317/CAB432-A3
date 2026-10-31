"""In-app assistant: the tool-use loop, write confirmation and auth (fake model and
fake API)."""

import json
import uuid

import pytest
from starlette.testclient import TestClient

from hookd_mcp import chat
from hookd_mcp.llm import ModelError
from hookd_mcp.server import mcp

CAMPAIGN_ID = str(uuid.uuid4())
CREATOR_ID = str(uuid.uuid4())
AUTH = {"Authorization": "Bearer user-token"}
QUESTION = [{"role": "user", "content": [{"text": "Who needs attention?"}]}]


def tool_use(name, tool_input=None, use_id="t1"):
    return {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {"toolUse": {"toolUseId": use_id, "name": name, "input": tool_input or {}}}
                ],
            }
        },
    }


def answer(text):
    return {
        "stopReason": "end_turn",
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
    }


class FakeModel:
    """Answers each converse() call with the next scripted response."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    async def converse(self, system, messages, tools):
        # Copy, since the server keeps appending to the same list
        self.calls.append({"messages": json.loads(json.dumps(messages)), "tools": tools})
        response = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture
def fake_model(monkeypatch):
    def use(*responses):
        fake = FakeModel(*responses)
        monkeypatch.setattr(chat, "model", lambda: fake)
        return fake

    return use


@pytest.fixture
def client():
    with TestClient(mcp.streamable_http_app()) as test_client:
        yield test_client


def post(client, messages, decision=None, headers=AUTH):
    return client.post(
        "/mcp/chat", json={"messages": messages, "decision": decision}, headers=headers
    )


def test_answers_from_tool_results_with_the_users_token(client, api, fake_model):
    api.responses[("GET", "/api/behind-target")] = (200, [{"creator": {"name": "Liam"}}])
    model = fake_model(tool_use("list_behind_target_creators"), answer("Liam is behind."))

    response = post(client, QUESTION)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["pending"] is None
    assert body["messages"][-1]["content"][0]["text"] == "Liam is behind."
    # The tool ran against the API as the signed-in user...
    behind = [c for c in api.calls if c.url.path == "/api/behind-target"]
    assert behind[0].headers["authorization"] == "Bearer user-token"
    # ...and the model saw its result
    result = model.calls[1]["messages"][-1]["content"][0]["toolResult"]
    assert "Liam" in result["content"][0]["text"]
    # Every MCP tool is offered to the model
    offered = {t.name for t in model.calls[0]["tools"]}
    assert "update_creator_target" in offered


def test_a_target_change_waits_for_confirmation(client, api, fake_model):
    path = f"/api/campaigns/{CAMPAIGN_ID}/creators/{CREATOR_ID}"
    api.responses[("PATCH", path)] = (200, {"target_posts": 5})
    change = {"campaign_id": CAMPAIGN_ID, "creator_id": CREATOR_ID, "target_posts": 5}
    fake_model(tool_use("update_creator_target", change), answer("Done: 5 posts."))

    first = post(client, QUESTION).json()

    assert first["pending"][0]["name"] == "update_creator_target"
    assert not [c for c in api.calls if c.method == "PATCH"]

    second = post(client, first["messages"], decision="confirm").json()

    (patch,) = [c for c in api.calls if c.method == "PATCH"]
    assert json.loads(patch.content) == {"target_posts": 5}
    assert second["changed"] is True
    assert second["messages"][-1]["content"][0]["text"] == "Done: 5 posts."


def test_a_cancelled_change_is_never_made(client, api, fake_model):
    change = {"campaign_id": CAMPAIGN_ID, "creator_id": CREATOR_ID, "target_posts": 5}
    model = fake_model(tool_use("update_creator_target", change), answer("OK, left it."))

    first = post(client, QUESTION).json()
    second = post(client, first["messages"], decision="cancel").json()

    assert not [c for c in api.calls if c.method == "PATCH"]
    assert second["changed"] is False
    result = model.calls[-1]["messages"][-1]["content"][0]["toolResult"]
    assert result["status"] == "error"
    assert result["content"][0]["text"] == chat.CANCELLED


def test_tool_errors_go_back_to_the_model(client, api, fake_model):
    model = fake_model(
        tool_use("get_creator_performance", {"creator_id": CREATOR_ID}),
        answer("I couldn't find that creator."),
    )
    api.responses[("GET", f"/api/creators/{CREATOR_ID}/performance")] = (
        404,
        {"detail": "Creator not found"},
    )

    assert post(client, QUESTION).status_code == 200
    result = model.calls[1]["messages"][-1]["content"][0]["toolResult"]
    assert result["status"] == "error"
    assert "Creator not found" in result["content"][0]["text"]


def test_a_runaway_tool_loop_is_cut_off(client, api, fake_model):
    api.responses[("GET", "/api/behind-target")] = (200, [])
    model = fake_model(tool_use("list_behind_target_creators"))

    body = post(client, QUESTION).json()

    assert len(model.calls) == chat.settings.chat_max_steps
    assert body["messages"][-1]["content"][0]["text"] == chat.TOO_MANY_STEPS


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Basic abc"}])
def test_needs_a_bearer_token(client, api, fake_model, headers):
    model = fake_model(answer("hi"))

    assert post(client, QUESTION, headers=headers).status_code == 401
    assert model.calls == []


def test_an_expired_token_is_refused_before_calling_fake_model(client, api, fake_model):
    api.responses[("GET", "/api/me")] = (401, {"detail": "Token expired"})
    model = fake_model(answer("hi"))

    assert post(client, QUESTION).status_code == 401
    assert model.calls == []


def test_model_errors_become_a_friendly_502(client, api, fake_model):
    fake_model(ModelError("Bedrock: AccessDeniedException"))

    response = post(client, QUESTION)

    assert response.status_code == 502
    assert "unavailable" in response.json()["detail"]


def test_a_throttled_model_is_a_429(client, api, fake_model):
    fake_model(ModelError("OpenRouter: rate limited", throttled=True))

    assert post(client, QUESTION).status_code == 429
