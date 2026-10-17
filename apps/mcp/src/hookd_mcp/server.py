"""MCP server entry point (MCP Python SDK v2 MCPServer over streamable HTTP)."""

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Hookd Tracker")

# TODO: register tools from hookd_mcp.tools.campaigns and hookd_mcp.tools.creators


def main() -> None:
    # Stateless so any Fargate task can serve any request behind the ALB
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001, stateless_http=True)


if __name__ == "__main__":
    main()
