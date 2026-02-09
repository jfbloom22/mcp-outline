"""Tests for request-scoped authentication parsing."""

import pytest
from starlette.requests import Request

from mcp_outline.auth.request_auth import (
    AuthConfig,
    RequestAuthError,
    build_request_auth,
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


def test_build_request_auth_success_with_bearer_and_url():
    request = _make_request(
        {
            "Authorization": "Bearer test-token",
            "X-Outline-Api-Url": "https://outline.example.com",
        }
    )
    config = AuthConfig(
        require_passthrough=True,
        allowed_api_url_hosts=frozenset({"outline.example.com"}),
        default_api_url="https://app.getoutline.com/api",
    )

    auth = build_request_auth(request, config)
    assert auth is not None
    assert auth.api_key == "test-token"
    assert auth.api_url == "https://outline.example.com/api"


def test_build_request_auth_missing_header_rejected_when_required():
    request = _make_request({})
    config = AuthConfig(
        require_passthrough=True,
        allowed_api_url_hosts=frozenset({"outline.example.com"}),
        default_api_url="https://outline.example.com/api",
    )

    with pytest.raises(RequestAuthError):
        build_request_auth(request, config)


def test_build_request_auth_invalid_bearer_rejected():
    request = _make_request({"Authorization": "Token abc123"})
    config = AuthConfig(
        require_passthrough=True,
        allowed_api_url_hosts=frozenset({"outline.example.com"}),
        default_api_url="https://outline.example.com/api",
    )

    with pytest.raises(RequestAuthError):
        build_request_auth(request, config)


def test_build_request_auth_url_allowlist_rejected():
    request = _make_request(
        {
            "Authorization": "Bearer test-token",
            "X-Outline-Api-Url": "https://evil.example.com/api",
        }
    )
    config = AuthConfig(
        require_passthrough=True,
        allowed_api_url_hosts=frozenset({"outline.example.com"}),
        default_api_url="https://outline.example.com/api",
    )

    with pytest.raises(RequestAuthError):
        build_request_auth(request, config)


def test_build_request_auth_rejects_query_and_fragment():
    config = AuthConfig(
        require_passthrough=True,
        allowed_api_url_hosts=frozenset({"outline.example.com"}),
        default_api_url="https://outline.example.com/api",
    )

    request_with_query = _make_request(
        {
            "Authorization": "Bearer test-token",
            "X-Outline-Api-Url": "https://outline.example.com/api?x=1",
        }
    )
    with pytest.raises(RequestAuthError):
        build_request_auth(request_with_query, config)

    request_with_fragment = _make_request(
        {
            "Authorization": "Bearer test-token",
            "X-Outline-Api-Url": "https://outline.example.com/api#frag",
        }
    )
    with pytest.raises(RequestAuthError):
        build_request_auth(request_with_fragment, config)


def test_build_request_auth_rejects_non_api_path():
    request = _make_request(
        {
            "Authorization": "Bearer test-token",
            "X-Outline-Api-Url": "https://outline.example.com/custom",
        }
    )
    config = AuthConfig(
        require_passthrough=True,
        allowed_api_url_hosts=frozenset({"outline.example.com"}),
        default_api_url="https://outline.example.com/api",
    )

    with pytest.raises(RequestAuthError):
        build_request_auth(request, config)


def test_build_request_auth_rejects_private_ip_target():
    request = _make_request(
        {
            "Authorization": "Bearer test-token",
            "X-Outline-Api-Url": "https://10.0.0.5/api",
        }
    )
    config = AuthConfig(
        require_passthrough=True,
        allowed_api_url_hosts=frozenset(),
        default_api_url="https://outline.example.com/api",
    )

    with pytest.raises(RequestAuthError):
        build_request_auth(request, config)
