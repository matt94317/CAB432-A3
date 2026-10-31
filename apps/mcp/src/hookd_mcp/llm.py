"""Chat model providers for the in-app assistant.

The conversation is kept in Bedrock Converse's message format, which the web app also
reads. Bedrock takes it as is; OpenRouter speaks the OpenAI chat format, so its
requests and replies are translated to and from it. Bedrock is the intended provider;
the CAB432 account denies bedrock:InvokeModel by organisation policy, so the A3
deployment uses OpenRouter (LLM_PROVIDER).
"""

import json
from functools import cache, partial
from typing import Any, Protocol

import anyio
import boto3
import httpx
from botocore.exceptions import BotoCoreError, ClientError

from hookd_mcp.config import settings

Message = dict[str, Any]

# Tests swap in an httpx.MockTransport
transport: httpx.AsyncBaseTransport | None = None


class ModelError(Exception):
    """The provider failed. `throttled` means trying again soon may work."""

    def __init__(self, detail: str, *, throttled: bool = False) -> None:
        super().__init__(detail)
        self.throttled = throttled


class ToolDef(Protocol):
    name: str
    description: str | None
    input_schema: dict[str, Any]


class ChatModel(Protocol):
    async def converse(
        self, system: str, messages: list[Message], tools: list[ToolDef]
    ) -> dict[str, Any]:
        """One model call. Returns a Converse-shaped response: `stopReason` and
        `output.message`."""
        ...


class BedrockModel:
    def __init__(self) -> None:
        # Explicit endpoint: local .env sets AWS_ENDPOINT_URL to ElasticMQ for SQS
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            endpoint_url=f"https://bedrock-runtime.{settings.aws_region}.amazonaws.com",
        )

    async def converse(
        self, system: str, messages: list[Message], tools: list[ToolDef]
    ) -> dict[str, Any]:
        specs = [
            {
                "toolSpec": {
                    "name": t.name,
                    "description": t.description or t.name,
                    "inputSchema": {"json": t.input_schema},
                }
            }
            for t in tools
        ]
        try:
            return await anyio.to_thread.run_sync(
                partial(
                    self.client.converse,
                    modelId=settings.bedrock_model_id,
                    system=[{"text": system}],
                    messages=messages,
                    toolConfig={"tools": specs},
                    inferenceConfig={"maxTokens": settings.chat_max_tokens},
                )
            )
        except ClientError as error:
            code = error.response["Error"]["Code"]
            raise ModelError(f"Bedrock: {code}", throttled=code == "ThrottlingException") from error
        except BotoCoreError as error:
            raise ModelError(f"Bedrock: {error}") from error


class OpenRouterModel:
    url = "https://openrouter.ai/api/v1/chat/completions"

    async def converse(
        self, system: str, messages: list[Message], tools: list[ToolDef]
    ) -> dict[str, Any]:
        body = {
            "model": settings.openrouter_model,
            "max_tokens": settings.chat_max_tokens,
            "messages": [{"role": "system", "content": system}, *to_openai(messages)],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or t.name,
                        "parameters": t.input_schema,
                    },
                }
                for t in tools
            ],
        }
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "X-Title": "Hookd Tracker",
        }
        try:
            async with httpx.AsyncClient(timeout=45, transport=transport) as client:
                response = await client.post(self.url, json=body, headers=headers)
        except httpx.HTTPError as error:
            raise ModelError(f"OpenRouter: {error!r}") from error
        if response.status_code == 429:
            raise ModelError("OpenRouter: rate limited", throttled=True)
        try:
            data = response.json()
        except ValueError:
            data = {}
        # Errors can also arrive with a 200 status
        if response.status_code >= 400 or not data.get("choices"):
            raise ModelError(f"OpenRouter {response.status_code}: {data.get('error', data)}")
        return from_openai(data)


def to_openai(messages: list[Message]) -> list[dict[str, Any]]:
    """Converse messages -> OpenAI chat messages."""
    out: list[dict[str, Any]] = []
    for message in messages:
        blocks = message.get("content", [])
        text = "\n".join(b["text"] for b in blocks if "text" in b)
        if message.get("role") == "assistant":
            calls = [
                {
                    "id": b["toolUse"]["toolUseId"],
                    "type": "function",
                    "function": {
                        "name": b["toolUse"]["name"],
                        "arguments": json.dumps(b["toolUse"].get("input") or {}),
                    },
                }
                for b in blocks
                if "toolUse" in b
            ]
            entry: dict[str, Any] = {"role": "assistant", "content": text or None}
            if calls:
                entry["tool_calls"] = calls
            out.append(entry)
            continue
        for b in blocks:
            if "toolResult" in b:
                result = b["toolResult"]
                content = "\n".join(c.get("text", "") for c in result.get("content", []))
                if result.get("status") == "error":
                    content = f"Error: {content}"
                out.append(
                    {"role": "tool", "tool_call_id": result["toolUseId"], "content": content}
                )
        if text:
            out.append({"role": "user", "content": text})
    return out


def from_openai(data: dict[str, Any]) -> dict[str, Any]:
    """OpenAI chat completion -> Converse-shaped response."""
    choice = data["choices"][0]
    message = choice.get("message") or {}
    content: list[dict[str, Any]] = []
    if message.get("content"):
        content.append({"text": message["content"]})
    for call in message.get("tool_calls") or []:
        try:
            arguments = json.loads(call["function"].get("arguments") or "{}")
        except ValueError:
            arguments = {}
        content.append(
            {
                "toolUse": {
                    "toolUseId": call["id"],
                    "name": call["function"]["name"],
                    "input": arguments,
                }
            }
        )
    if not content:
        content.append({"text": ""})
    has_tools = any("toolUse" in c for c in content)
    return {
        "stopReason": "tool_use" if has_tools else "end_turn",
        "output": {"message": {"role": "assistant", "content": content}},
    }


@cache
def model() -> ChatModel:
    if settings.llm_provider == "openrouter":
        return OpenRouterModel()
    return BedrockModel()
