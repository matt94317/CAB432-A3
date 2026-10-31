"""OpenRouter provider: translation to and from the Converse message format, and errors
(fake OpenRouter)."""

import json
from types import SimpleNamespace

import httpx
import pytest

from hookd_mcp import llm
from hookd_mcp.llm import ModelError, OpenRouterModel, from_openai, to_openai

TOOLS = [
    SimpleNamespace(
        name="list_creators", description="List creators", input_schema={"type": "object"}
    )
]

CONVERSATION = [
    {"role": "user", "content": [{"text": "Who is behind?"}]},
    {
        "role": "assistant",
        "content": [
            {"text": "Checking."},
            {"toolUse": {"toolUseId": "call_1", "name": "list_creators", "input": {"a": 1}}},
        ],
    },
    {
        "role": "user",
        "content": [
            {
                "toolResult": {
                    "toolUseId": "call_1",
                    "status": "error",
                    "content": [{"text": "Not found"}],
                }
            }
        ],
    },
]


def test_converse_messages_become_openai_messages():
    assert to_openai(CONVERSATION) == [
        {"role": "user", "content": "Who is behind?"},
        {
            "role": "assistant",
            "content": "Checking.",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "list_creators", "arguments": '{"a": 1}'},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": "Error: Not found"},
    ]


def test_an_openai_tool_call_becomes_a_converse_tool_use():
    reply = from_openai(
        {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_2",
                                "function": {"name": "list_creators", "arguments": '{"x": 2}'},
                            }
                        ],
                    }
                }
            ]
        }
    )

    assert reply["stopReason"] == "tool_use"
    assert reply["output"]["message"]["content"] == [
        {"toolUse": {"toolUseId": "call_2", "name": "list_creators", "input": {"x": 2}}}
    ]


def test_an_openai_answer_becomes_a_converse_answer():
    reply = from_openai({"choices": [{"message": {"content": "All on track."}}]})

    assert reply["stopReason"] == "end_turn"
    assert reply["output"]["message"]["content"] == [{"text": "All on track."}]


@pytest.fixture
def openrouter(monkeypatch):
    """Fake OpenRouter: set `fake.reply = (status, body)`; requests land in `fake.calls`."""
    fake = SimpleNamespace(reply=(200, {}), calls=[])

    def handle(request: httpx.Request) -> httpx.Response:
        fake.calls.append(request)
        status, body = fake.reply
        return httpx.Response(status, json=body)

    monkeypatch.setattr(llm, "transport", httpx.MockTransport(handle))
    monkeypatch.setattr(llm.settings, "openrouter_api_key", "or-key")
    return fake


@pytest.mark.anyio
async def test_sends_the_tools_system_prompt_and_key(openrouter):
    openrouter.reply = (200, {"choices": [{"message": {"content": "Hi"}}]})

    reply = await OpenRouterModel().converse("Be brief.", CONVERSATION[:1], TOOLS)

    assert reply["output"]["message"]["content"] == [{"text": "Hi"}]
    (call,) = openrouter.calls
    assert call.headers["authorization"] == "Bearer or-key"
    body = json.loads(call.content)
    assert body["messages"][0] == {"role": "system", "content": "Be brief."}
    assert body["tools"][0]["function"]["name"] == "list_creators"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("reply", "throttled"),
    [
        ((429, {"error": "slow down"}), True),
        ((401, {"error": {"message": "No auth"}}), False),
        ((200, {"error": {"message": "Upstream failed"}}), False),
    ],
)
async def test_failures_raise_model_error(openrouter, reply, throttled):
    openrouter.reply = reply

    with pytest.raises(ModelError) as error:
        await OpenRouterModel().converse("", CONVERSATION[:1], TOOLS)
    assert error.value.throttled is throttled
