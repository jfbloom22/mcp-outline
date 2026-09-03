"""Authentication diagnostic tools."""

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


def register_tools(mcp) -> None:
    """Register auth diagnostic tools."""

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
        meta={
            "endpoint": "auth.info",
            "min_role": "viewer",
        },
    )
    async def whoami_outline(ctx: Context) -> str:
        """Return Outline identity details for current credentials."""
        try:
            client = await get_outline_client(ctx=ctx)
            info = await client.auth_info()
            team = info.get("team", {})
            user = info.get("user", {})
            return (
                "Outline auth OK\n"
                f"Team: {team.get('name', 'Unknown')}\n"
                f"User: {user.get('name', 'Unknown')}\n"
                f"Email: {user.get('email', 'Unknown')}"
            )
        except OutlineClientError as e:
            return f"Authentication error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
