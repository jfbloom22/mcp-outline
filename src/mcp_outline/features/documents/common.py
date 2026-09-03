"""Common utilities shared by tools and resources."""

import json
import os
import uuid
from typing import Any

from mcp.server.fastmcp import Context
from starlette.requests import Request

from mcp_outline.auth import AuthConfig, AuthConfigError, RequestAuthError
from mcp_outline.auth.request_auth import build_request_auth
from mcp_outline.utils.outline_client import OutlineClient, OutlineError


class OutlineClientError(Exception):
    """Exception raised for errors in document outline client operations."""

    pass


def format_documents_list(documents: list[dict[str, Any]], title: str) -> str:
    """Format a list of documents into readable text."""
    if not documents:
        return f"No {title.lower()} found."

    output = f"# {title}\n\n"

    for i, document in enumerate(documents, 1):
        doc_title = document.get("title", "Untitled")
        doc_id = document.get("id", "")
        doc_url_id = document.get("urlId", "")
        updated_at = document.get("updatedAt", "")

        output += f"## {i}. {doc_title}\n"
        output += f"ID: {doc_id}\n"
        if doc_url_id:
            output += f"Short ID: {doc_url_id}\n"
        if updated_at:
            output += f"Last Updated: {updated_at}\n"
        output += "\n"

    return output


def format_comment_data(data: dict[str, Any]) -> str:
    """Serialize a comment data object to a display string."""
    try:
        return json.dumps(data, indent=2)
    except Exception:
        return str(data)


def ensure_text_is_str(value: Any, param_name: str = "text") -> str:
    """Ensure text parameter is a proper string when provided.

    Rejects non-string values (e.g. numbers, truncated/corrupted) that could
    cause content corruption. Only call when text is being updated.

    Args:
        value: Raw value from tool arguments.
        param_name: Name for error messages.

    Returns:
        The text as a string.

    Raises:
        TypeError: If value is not a string.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"{param_name} must be a string, got {type(value).__name__}"
        )
    return value


def require_uuid_string(value: Any, param_name: str) -> str:
    """Validate a required UUID parameter. Raises for None, empty, or invalid.

    Use for document_id, collection_id, etc. when the param is required.

    Raises:
        ValueError: If value is missing or not a valid UUID.
    """
    result = ensure_uuid_string(value, param_name)
    if result is None:
        raise ValueError(f"{param_name} is required")
    return result


def ensure_uuid_string(value: Any, param_name: str) -> str | None:
    """
    Normalize and validate a UUID parameter for Outline API.

    MCP clients may pass UUIDs as different types (e.g. int from JSON
    coercion). The Outline API requires a proper UUID string. This ensures we
    always send a valid string and fail fast with a clear error when invalid.

    Args:
        value: Raw value (may be str, int, etc. from JSON).
        param_name: Name for error messages.

    Returns:
        Validated UUID string in canonical form, or None if value is
        None/empty.

    Raises:
        ValueError: If value is non-empty but not a valid UUID.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        return str(uuid.UUID(s))
    except ValueError:
        raise ValueError(
            f"{param_name} must be a valid UUID "
            "(e.g. 580b8429-8da4-4409-a2ad-f86e194074b6), "
            f"received: {value!r} (type: {type(value).__name__})"
        )


def _get_request_from_context(ctx: Context | None) -> Request | None:
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


def _get_request_from_request_ctx() -> Request | None:
    """Extract HTTP request from MCP SDK request_ctx (streamable-http/SSE)."""
    try:
        from mcp.server.lowlevel.server import request_ctx

        ctx = request_ctx.get()
        req = ctx.request
        if isinstance(req, Request):
            return req
    except (LookupError, ImportError, AttributeError, ValueError):
        pass
    return None


async def get_outline_client(
    ctx: Context | None = None, request: Request | None = None
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
        resolved_request = (
            request
            or _get_request_from_context(ctx)
            or _get_request_from_request_ctx()
        )
        auth_ctx = build_request_auth(resolved_request, config)

        if auth_ctx is not None:
            return OutlineClient(
                api_key=auth_ctx.api_key, api_url=auth_ctx.api_url
            )

        if config.require_passthrough:
            raise OutlineClientError(
                "Passthrough auth is required in this environment."
            )

        header_api_key = None
        if resolved_request is not None:
            from mcp_outline.utils.outline_client import _sanitize_value

            header_api_key = _sanitize_value(
                resolved_request.headers.get("x-outline-api-key")
            )

        api_key = header_api_key or os.getenv("OUTLINE_API_KEY")
        api_url = os.getenv("OUTLINE_API_URL")
        return OutlineClient(api_key=api_key, api_url=api_url)
    except (RequestAuthError, AuthConfigError) as e:
        raise OutlineClientError(f"Authentication error: {str(e)}")
    except OutlineError as e:
        raise OutlineClientError(f"Outline client error: {str(e)}")
    except Exception as e:
        raise OutlineClientError(f"Unexpected error: {str(e)}")
