"""Tests for request-aware client factory behavior."""

from unittest.mock import patch

import pytest
from starlette.requests import Request

from mcp_outline.features.documents.common import (
    OutlineClientError,
    get_outline_client,
)


def _make_request(headers: dict[str, str]) -> Request:
    raw_headers = [
        (k.lower().encode("latin-1"), v.encode("latin-1"))
        for k, v in headers.items()
    ]
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/mcp",
        "headers": raw_headers,
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_get_outline_client_uses_header_credentials():
    request = _make_request(
        {
            "Authorization": "Bearer request-token",
            "X-Outline-Api-Url": "https://tenant.example.com",
        }
    )
    with patch.dict(
        "os.environ",
        {
            "OUTLINE_REQUIRE_PASSTHROUGH": "true",
            "OUTLINE_ALLOWED_API_URL_HOSTS": "tenant.example.com",
            "OUTLINE_API_KEY": "env-token",
            "OUTLINE_API_URL": "https://env.example.com/api",
        },
        clear=False,
    ):
        client = await get_outline_client(request=request)
        assert client.api_key == "request-token"
        assert client.api_url == "https://tenant.example.com/api"


@pytest.mark.asyncio
async def test_get_outline_client_uses_env_fallback_when_allowed():
    with patch.dict(
        "os.environ",
        {
            "OUTLINE_REQUIRE_PASSTHROUGH": "false",
            "OUTLINE_API_KEY": "env-token",
            "OUTLINE_API_URL": "https://env.example.com/api",
        },
        clear=False,
    ):
        client = await get_outline_client()
        assert client.api_key == "env-token"
        assert client.api_url == "https://env.example.com/api"


@pytest.mark.asyncio
async def test_get_outline_client_rejects_env_fallback_when_required():
    with patch.dict(
        "os.environ",
        {
            "OUTLINE_REQUIRE_PASSTHROUGH": "true",
            "OUTLINE_ALLOWED_API_URL_HOSTS": "tenant.example.com",
            "OUTLINE_API_KEY": "env-token",
            "OUTLINE_API_URL": "https://env.example.com/api",
        },
        clear=False,
    ):
        with pytest.raises(OutlineClientError):
            await get_outline_client()
