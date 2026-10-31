"""In-app assistant (US-24 to US-27): a chat model (Bedrock or OpenRouter, see llm.py)
calling this server's own MCP tools.

The chat panel and external MCP clients share one set of tools, and every tool call
goes to the API with the signed-in user's token, so the assistant only sees that
user's organisation.

The server keeps no state. The browser sends the whole conversation (Bedrock message
format) with each request and gets it back with the new turns appended. When the model
asks for a tool that changes data, the server stops before running it and returns it as
`pending`; the next request carries the user's decision, and only then does it run.
"""

import json
import logging
from datetime import datetime
from typing import Any, Literal
from zoneinfo import ZoneInfo

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from hookd_mcp.api_client import HookdApi
from hookd_mcp.auth import chat_token, parse_bearer
from hookd_mcp.config import settings
from hookd_mcp.llm import ModelError, model

log = logging.getLogger(__name__)

MAX_BODY_BYTES = 256_000
MAX_TOOL_RESULT_CHARS = 12_000
TOO_MANY_STEPS = "Sorry, that needed more steps than I'm allowed. Try a narrower question."
CANCELLED = "The user cancelled this change. Nothing was changed."

SYSTEM_PROMPT = """You are the assistant inside Hookd Tracker, an app where a UGC \
campaign manager tracks TikTok creators against posting targets. Today is {today} \
({timezone}).

- Answer only from tool results. Never guess or invent numbers, names or dates.
- Find ids yourself with list_campaigns, list_creators or get_campaign_progress. \
Never ask the user for an id, and never show ids in your answer.
- Lead with the answer in one or two sentences, then at most five short bullet points \
starting with "- ". Plain text only: no tables, headings or bold.
- "Needs attention" means creators behind target this period.
- To change a target, say in one sentence which creator, campaign and new target, then \
call update_creator_target in the same reply. The app shows the user a confirm button \
before it runs, so don't ask for confirmation in text.
- If asked about anything other than their campaigns, creators and posts, say briefly \
what you can help with."""


class ChatRequest(BaseModel):
    messages: list[dict[str, Any]] = Field(min_length=1, max_length=80)
    decision: Literal["confirm", "cancel"] | None = None


class Assistant:
    def __init__(self, server: MCPServer) -> None:
        self.server = server

    async def handle(self, request: Request) -> JSONResponse:
        token = parse_bearer(request.headers.get("authorization", ""))
        if not token:
            return _error(401, "Log in to use the assistant.")
        # Check the token before spending model tokens on it
        try:
            await HookdApi(token).get("/me")
        except ToolError:
            return _error(401, "Your session has expired. Log in again.")

        body = await request.body()
        if len(body) > MAX_BODY_BYTES:
            return _error(413, "This conversation is too long. Start a new chat.")
        try:
            chat = ChatRequest.model_validate_json(body)
        except ValidationError:
            return _error(422, "Malformed chat request.")

        chat_token.set(token)
        try:
            return JSONResponse(await self.reply(chat.messages, chat.decision))
        except ModelError as error:
            log.exception("Chat model call failed")
            if error.throttled:
                return _error(429, "The assistant is busy. Try again in a moment.")
            return _error(502, "The assistant is unavailable right now. Try again later.")

    async def reply(
        self, messages: list[dict[str, Any]], decision: Literal["confirm", "cancel"] | None
    ) -> dict[str, Any]:
        tools = await self.server.list_tools()
        writes = {t.name for t in tools if not (t.annotations and t.annotations.read_only_hint)}
        changed = False

        if decision is not None:
            uses = _tool_uses(messages[-1]) if messages[-1].get("role") == "assistant" else []
            if not uses:
                return {"messages": messages, "pending": None, "changed": False}
            results, changed = await self.run_tools(
                uses, writes, allow_writes=decision == "confirm"
            )
            messages.append({"role": "user", "content": results})

        for _ in range(settings.chat_max_steps):
            response = await model().converse(_system_prompt(), messages, tools)
            message = response["output"]["message"]
            messages.append(message)
            uses = _tool_uses(message)
            if response.get("stopReason") != "tool_use" or not uses:
                return {"messages": messages, "pending": None, "changed": changed}
            pending = [use for use in uses if use["name"] in writes]
            if pending:
                return {"messages": messages, "pending": pending, "changed": changed}
            results, _ = await self.run_tools(uses, writes, allow_writes=False)
            messages.append({"role": "user", "content": results})

        messages.append({"role": "assistant", "content": [{"text": TOO_MANY_STEPS}]})
        return {"messages": messages, "pending": None, "changed": changed}

    async def run_tools(
        self, uses: list[dict[str, Any]], writes: set[str], *, allow_writes: bool
    ) -> tuple[list[dict[str, Any]], bool]:
        """Run every tool the model asked for in one turn (Bedrock needs a result for
        each). Returns the results and whether any change was made."""
        results, changed = [], False
        for use in uses:
            is_write = use["name"] in writes
            if is_write and not allow_writes:
                text, ok = CANCELLED, False
            else:
                text, ok = await self.call(use["name"], use.get("input") or {})
                changed = changed or (is_write and ok)
            result: dict[str, Any] = {"toolUseId": use["toolUseId"], "content": [{"text": text}]}
            if not ok:
                result["status"] = "error"
            results.append({"toolResult": result})
        return results, changed

    async def call(self, name: str, arguments: dict[str, Any]) -> tuple[str, bool]:
        try:
            result = await self.server.call_tool(name, arguments)
        except ToolError as error:
            return str(error), False
        if getattr(result, "is_error", False):
            return " ".join(getattr(c, "text", "") for c in result.content), False
        data = getattr(result, "structured_content", None)
        text = json.dumps(data, separators=(",", ":"), default=str)
        if len(text) > MAX_TOOL_RESULT_CHARS:
            text = text[:MAX_TOOL_RESULT_CHARS] + "... (truncated)"
        return text, True


def _tool_uses(message: dict[str, Any]) -> list[dict[str, Any]]:
    return [block["toolUse"] for block in message.get("content", []) if "toolUse" in block]


def _system_prompt() -> str:
    tz = ZoneInfo(settings.campaign_timezone)
    return SYSTEM_PROMPT.format(today=datetime.now(tz).strftime("%A %d %B %Y"), timezone=tz)


def _error(status: int, detail: str) -> JSONResponse:
    return JSONResponse({"detail": detail}, status_code=status)
