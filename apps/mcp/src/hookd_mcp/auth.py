"""Take the caller's Cognito token from the request so it can be passed through to the
API (US-23).

The MCP server has no data access of its own: the API verifies the token and scopes
every read and write to the caller's organisation, so the assistant sees only what the
signed-in user could see in the web app.
"""

from contextvars import ContextVar

from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError

MISSING_TOKEN = (
    "No sign-in token. Connect this MCP server with the header "
    "'Authorization: Bearer <your Hookd access token>'."
)

# Set by the in-app chat, which calls the tools in-process rather than over MCP
chat_token: ContextVar[str | None] = ContextVar("chat_token", default=None)


def parse_bearer(authorization: str) -> str | None:
    scheme, _, token = authorization.partition(" ")
    return token.strip() if scheme.lower() == "bearer" and token.strip() else None


def bearer_token(ctx: Context) -> str:
    try:
        headers = ctx.headers or {}
    except ValueError:  # an in-process call has no MCP request
        headers = {}
    token = parse_bearer(headers.get("authorization", "")) or chat_token.get()
    if not token:
        raise ToolError(MISSING_TOKEN)
    return token
