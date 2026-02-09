"""Common utilities shared by tools and resources."""

import os
from typing import Optional

from mcp.server.fastmcp import Context
from starlette.requests import Request

from mcp_outline.auth import AuthConfig, AuthConfigError, RequestAuthError
from mcp_outline.auth.request_auth import build_request_auth
from mcp_outline.utils.outline_client import OutlineClient, OutlineError


class OutlineClientError(Exception):
    """Exception raised for errors in document outline client operations."""

    pass


def _get_request_from_context(ctx: Optional[Context]) -> Optional[Request]:
    """Extract HTTP request object from FastMCP context when available."""
    if ctx is None:
        return None

    try:
        req = ctx.request_context.request
    except (LookupError, ValueError):
        return None

    if isinstance(req, Request):
        return req
    return None


async def get_outline_client(
    ctx: Optional[Context] = None, request: Optional[Request] = None
) -> OutlineClient:
    """
    Get the document outline client (async).

    Returns:
        OutlineClient instance

    Raises:
        OutlineClientError: If client creation fails
    """
    try:
        config = AuthConfig.from_env()
        resolved_request = request or _get_request_from_context(ctx)
        auth_ctx = build_request_auth(resolved_request, config)

        if auth_ctx is not None:
            return OutlineClient(
                api_key=auth_ctx.api_key, api_url=auth_ctx.api_url
            )

        if config.require_passthrough:
            raise OutlineClientError(
                "Passthrough auth is required in this environment."
            )

        api_key = os.getenv("OUTLINE_API_KEY")
        api_url = os.getenv("OUTLINE_API_URL")
        return OutlineClient(api_key=api_key, api_url=api_url)
    except (RequestAuthError, AuthConfigError) as e:
        raise OutlineClientError(f"Authentication error: {str(e)}")
    except OutlineError as e:
        raise OutlineClientError(f"Outline client error: {str(e)}")
    except Exception as e:
        raise OutlineClientError(f"Unexpected error: {str(e)}")
