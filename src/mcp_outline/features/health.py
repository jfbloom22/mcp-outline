"""
Health check endpoints for MCP server.

Provides liveness and readiness probes for Docker/Kubernetes deployments.
"""

import os

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_outline.utils.outline_client import _sanitize_value


def _get_outline_base_url() -> str:
    """Return the Outline base URL (without ``/api`` suffix)."""
    raw = _sanitize_value(os.getenv("OUTLINE_API_URL"))
    if not raw:
        return "https://app.getoutline.com"
    url = raw.rstrip("/")
    if url.lower().endswith("/api"):
        return url[: -len("/api")]
    return url


def _sanitize_error_message(message: str) -> str:
    """Redact sensitive auth values from error messages."""
    if "Bearer " in message:
        return "Authentication failed."
    return message


def register_routes(mcp) -> None:
    """Register health check routes with the MCP server."""

    @mcp.custom_route(path="/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({"status": "healthy"})

    @mcp.custom_route(path="/ready", methods=["GET"])
    async def ready_check(request: Request) -> JSONResponse:
        if os.getenv("OUTLINE_REQUIRE_PASSTHROUGH", "").lower() in (
            "true",
            "1",
            "yes",
        ):
            return JSONResponse(
                {
                    "status": "ready",
                    "service": "mcp-outline",
                    "api_accessible": "per-request",
                }
            )
        return await check_readiness()

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


async def check_readiness() -> JSONResponse:
    """Check whether the Outline instance is reachable."""
    try:
        base_url = _get_outline_base_url()
        async with httpx.AsyncClient() as client:
            await client.head(base_url, timeout=5.0)

        return JSONResponse(
            {
                "status": "ready",
                "outline": "connected",
                "api_accessible": True,
            }
        )

    except Exception as e:
        return JSONResponse(
            {
                "status": "not_ready",
                "outline": "disconnected",
                "api_accessible": False,
                "error": str(e),
            },
            status_code=503,
        )
