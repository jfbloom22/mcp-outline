"""Request-scoped authentication parsing and validation."""

import ipaddress
import os
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlparse

from starlette.requests import Request

from mcp_outline.utils.strings import sanitize_value as _sanitize_value


class RequestAuthError(Exception):
    """Raised when request-scoped authentication is invalid."""


class AuthConfigError(Exception):
    """Raised when authentication configuration is invalid."""


@dataclass(frozen=True)
class AuthConfig:
    """Configuration for request-scoped authentication behavior."""

    require_passthrough: bool
    allowed_api_url_hosts: frozenset[str]
    default_api_url: str

    @classmethod
    def from_env(cls) -> "AuthConfig":
        """Load auth config from environment variables."""
        require_passthrough = _is_truthy(
            os.getenv("OUTLINE_REQUIRE_PASSTHROUGH", "")
        )
        raw_hosts = os.getenv("OUTLINE_ALLOWED_API_URL_HOSTS", "")
        hosts = frozenset(
            h.strip().lower() for h in raw_hosts.split(",") if h.strip()
        )
        default_api_url = (
            os.getenv("OUTLINE_DEFAULT_API_URL")
            or os.getenv("OUTLINE_API_URL")
            or "https://app.getoutline.com/api"
        )

        if require_passthrough and not hosts:
            raise AuthConfigError(
                "OUTLINE_ALLOWED_API_URL_HOSTS must be configured when "
                "OUTLINE_REQUIRE_PASSTHROUGH=true."
            )

        return cls(
            require_passthrough=require_passthrough,
            allowed_api_url_hosts=hosts,
            default_api_url=default_api_url,
        )


@dataclass(frozen=True)
class RequestAuthContext:
    """Resolved request-scoped Outline credentials."""

    api_key: str
    api_url: str
    source: str
    caller_id: str | None = None


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes")


def _normalize_outline_api_url(raw_url: str) -> str:
    candidate = _sanitize_value(raw_url) or ""
    candidate = candidate.rstrip("/")
    if not candidate:
        raise RequestAuthError("Outline API URL is empty.")
    if not candidate.lower().endswith("/api"):
        candidate = f"{candidate}/api"
    return candidate


def _extract_bearer_token(headers: Mapping[str, str]) -> str | None:
    auth_header = _sanitize_value(headers.get("authorization"))
    if not auth_header:
        return None

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise RequestAuthError("Authorization header must use Bearer token.")

    token = _sanitize_value(parts[1])
    if not token:
        raise RequestAuthError("Bearer token is empty.")
    return token


def _validate_outline_api_url(url: str, allowed_hosts: frozenset[str]) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()

    if not host:
        raise RequestAuthError("Outline API URL host is missing.")

    if parsed.username or parsed.password:
        raise RequestAuthError(
            "Outline API URL must not include user credentials."
        )

    if parsed.fragment:
        raise RequestAuthError("Outline API URL must not include fragments.")

    if parsed.query:
        raise RequestAuthError(
            "Outline API URL must not include query params."
        )

    if parsed.path.rstrip("/") != "/api":
        raise RequestAuthError("Outline API URL must end with /api.")

    if scheme != "https":
        raise RequestAuthError("Outline API URL must use https.")

    if allowed_hosts and host not in allowed_hosts:
        raise RequestAuthError(
            "Outline API URL host is not allowed for this server."
        )

    # Block local/private IP targets unless explicitly allowlisted.
    try:
        ip = ipaddress.ip_address(host)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
        ) and host not in allowed_hosts:
            raise RequestAuthError(
                "Outline API URL resolves to a non-public IP address."
            )
    except ValueError:
        # Host is a domain name; allowlist controls scope when configured.
        pass

    return url


def build_request_auth(
    request: Request | None, config: AuthConfig
) -> RequestAuthContext | None:
    """Build request-scoped auth context from HTTP headers."""
    if request is None:
        return None

    headers = request.headers
    token = _extract_bearer_token(headers)
    raw_api_url = _sanitize_value(headers.get("x-outline-api-url"))

    if not token:
        if config.require_passthrough:
            raise RequestAuthError(
                "Missing Authorization bearer token for passthrough mode."
            )
        return None

    if raw_api_url:
        api_url = _normalize_outline_api_url(raw_api_url)
    else:
        api_url = _normalize_outline_api_url(config.default_api_url)

    api_url = _validate_outline_api_url(api_url, config.allowed_api_url_hosts)

    return RequestAuthContext(
        api_key=token,
        api_url=api_url,
        source="headers",
        caller_id=request.headers.get("x-forwarded-for"),
    )
