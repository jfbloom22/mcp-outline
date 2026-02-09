# Document Outline MCP features package
from mcp_outline.features import auth_tools, documents, health, resources


def register_all(mcp):
    """
    Register all features with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """
    # Register health check routes
    health.register_routes(mcp)
    auth_tools.register_tools(mcp)

    # Register document management features
    documents.register(mcp)

    # Register MCP resources
    resources.register(mcp)
