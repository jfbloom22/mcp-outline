"""Optional live smoke test against the hosted WL MCP gateway.

Requires OUTLINE_API_KEY (and optionally OUTLINE_API_URL for the Outline
instance). Does not print secrets. Skips when the key is unset.

Run manually:

    uv run pytest tests/test_hosted_smoke.py -v

Or with env from a dotenv file:

    set -a && source /path/to/.env && set +a
    uv run pytest tests/test_hosted_smoke.py -v
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import TextContent

HOSTED_MCP_URL = os.getenv(
    "MCP_HOSTED_SMOKE_URL",
    "https://mcp.workplacelabs.io/outline",
)
DEFAULT_OUTLINE_API_URL = os.getenv(
    "OUTLINE_API_URL",
    "https://docs.workplacelabs.io/api",
)


def _load_dotenv_if_present() -> None:
    """Load OUTLINE_API_KEY from common local env files when unset."""
    if os.getenv("OUTLINE_API_KEY"):
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    candidates = [
        Path.cwd() / ".env",
        Path.cwd() / ".mcp-outline.env",
        Path.home() / ".config" / "mcp-outline" / ".env",
        Path(
            "/Users/jfhome/devProjects/workplace-labs/wl-workspace/.env"
        ),
    ]
    for path in candidates:
        if path.is_file():
            load_dotenv(path, override=False)
            if os.getenv("OUTLINE_API_KEY"):
                return


@pytest.fixture(scope="module", autouse=True)
def _ensure_env() -> None:
    _load_dotenv_if_present()


pytestmark = pytest.mark.integration


@pytest.mark.anyio
async def test_hosted_mcp_initialize_list_tools_and_search_short_id():
    api_key = os.getenv("OUTLINE_API_KEY")
    if not api_key:
        pytest.skip("OUTLINE_API_KEY not set; skipping hosted smoke test")

    outline_api_url = os.getenv("OUTLINE_API_URL", DEFAULT_OUTLINE_API_URL)

    http_client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {api_key}",
            "X-Outline-Api-Url": outline_api_url,
        },
        timeout=httpx.Timeout(30.0, read=300.0),
    )

    async with streamable_http_client(
        url=HOSTED_MCP_URL,
        http_client=http_client,
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = {t.name for t in tools.tools}
            assert "search_documents" in tool_names
            assert "whoami_outline" in tool_names

            whoami = await session.call_tool("whoami_outline", arguments={})
            whoami_text = whoami.content[0]
            assert isinstance(whoami_text, TextContent)
            assert "Outline auth OK" in whoami_text.text

            search = await session.call_tool(
                "search_documents",
                arguments={"query": "Cursor", "limit": 5},
            )
            search_text = search.content[0]
            assert isinstance(search_text, TextContent)
            assert "Error" not in search_text.text[:200]
            assert "Short ID:" in search_text.text, (
                "Expected urlId formatting (Short ID) in search_documents output"
            )

    await http_client.aclose()
