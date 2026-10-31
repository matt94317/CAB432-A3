"""MCP server entry point (MCP Python SDK v2 MCPServer over streamable HTTP)."""

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations

from hookd_mcp.chat import Assistant
from hookd_mcp.config import settings
from hookd_mcp.tools import campaigns, creators

mcp = MCPServer(
    "Hookd Tracker",
    instructions=(
        "Campaign and creator data from Hookd Tracker, scoped to the signed-in user's "
        "organisation. Look up ids with list_campaigns or list_creators first."
    ),
)

READ = ToolAnnotations(read_only_hint=True, open_world_hint=False)
WRITE = ToolAnnotations(
    read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False
)

for tool in [*campaigns.TOOLS, *creators.TOOLS]:
    mcp.tool(annotations=READ)(tool)
for tool in creators.WRITE_TOOLS:
    mcp.tool(annotations=WRITE)(tool)

# The web app's chat panel; the ALB routes /mcp/* here
mcp.custom_route("/mcp/chat", methods=["POST"])(Assistant(mcp).handle)


def main() -> None:
    # Stateless so any Fargate task can serve any request behind the ALB
    mcp.run(transport="streamable-http", host="0.0.0.0", port=settings.port, stateless_http=True)


if __name__ == "__main__":
    main()
