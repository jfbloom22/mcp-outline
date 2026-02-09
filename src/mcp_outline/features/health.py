"""
Health check endpoints for MCP server.

Provides liveness and readiness probes for Docker/Kubernetes deployments.
"""

from starlette.requests import Request
from starlette.responses import JSONResponse


def _sanitize_error_message(message: str) -> str:
    """Redact sensitive auth values from error messages."""
    if "Bearer " in message:
        return "Authentication failed."
    return message


def register_routes(mcp) -> None:
    """
    Register health check routes with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.custom_route(path="/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        """
        Liveness check endpoint.

        Returns 200 OK if the server is running. Used by container
        orchestration systems to detect if the process is alive.

        Returns:
            JSON response with status "healthy"
        """
        return JSONResponse({"status": "healthy"})

    @mcp.custom_route(path="/ready", methods=["GET"])
    async def ready_check(request: Request) -> JSONResponse:
        """
        Readiness check endpoint.

        Verifies process-level readiness for deployment.

        Returns:
            JSON response with server readiness details
        """
        return JSONResponse(
            {
                "status": "ready",
                "service": "mcp-outline",
                "api_accessible": "per-request",
            }
        )

    @mcp.custom_route(path="/auth/whoami", methods=["GET"])
    async def auth_whoami(request: Request) -> JSONResponse:
        """Validate request-scoped Outline credentials and return identity."""
        try:
            from mcp_outline.features.documents.common import (
                get_outline_client,
            )

            client = await get_outline_client(request=request)
            info = await client.auth_info()
            team = info.get("team", {})
            user = info.get("user", {})
            return JSONResponse(
                {
                    "status": "ok",
                    "team": team.get("name"),
                    "user": user.get("name"),
                    "email": user.get("email"),
                }
            )
        except Exception as e:
            return JSONResponse(
                {
                    "status": "error",
                    "error": _sanitize_error_message(str(e)),
                },
                status_code=401,
            )
