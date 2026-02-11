# MCP Outline Server

[![PyPI](https://img.shields.io/pypi/v/mcp-outline)](https://pypi.org/project/mcp-outline/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Vortiago/mcp-outline/actions/workflows/ci.yml/badge.svg)](https://github.com/Vortiago/mcp-outline/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/docker-ghcr.io-blue)](https://github.com/Vortiago/mcp-outline/pkgs/container/mcp-outline)

A Model Context Protocol server for interacting with Outline document management.

## Features

- **Document operations**: Search, read, create, edit, archive documents
- **Collections**: List, create, manage document hierarchies
- **Comments**: Add and view threaded comments
- **Backlinks**: Find documents referencing a specific document
- **MCP Resources**: Direct content access via URIs (outline://document/{id}, outline://collection/{id}, etc.)
- **Automatic rate limiting**: Transparent handling of API limits with retry logic

## Prerequisites

Before using this MCP server, you need:

- An [Outline](https://www.getoutline.com/) account (cloud hosted or self-hosted)
- API key from Outline web UI: **Settings → API Keys → Create New**
- Python 3.10+ (for non-Docker installations)

> **Getting your API key**: Log into Outline → Click your profile → Settings → API Keys → "New API Key". Copy the generated token.

## Installation

### Using uv (Recommended)

```bash
uvx mcp-outline
```

### Using pip

```bash
pip install mcp-outline
```

### Using Docker

```bash
docker run -e OUTLINE_API_KEY=<your-key> ghcr.io/vortiago/mcp-outline:latest
```

Or build from source:
```bash
docker buildx build -t mcp-outline .
docker run -e OUTLINE_API_KEY=<your-key> mcp-outline
```

## Configuration

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `OUTLINE_API_KEY` | Yes | - | Get from Outline web UI: Settings → API Keys → Create New |
| `OUTLINE_API_URL` | No | `https://app.getoutline.com/api` | For self-hosted: `https://your-domain/api` |
| `OUTLINE_DISABLE_AI_TOOLS` | No | `false` | `true` = disable AI tools (for Outline instances without OpenAI) |
| `MCP_TRANSPORT` | No | `stdio` | Transport mode: `stdio` (local), `sse` or `streamable-http` (remote) |
| `MCP_HOST` | No | `127.0.0.1` | Server host. Use `0.0.0.0` in Docker for external connections |
| `MCP_PORT` | No | `3000` | HTTP server port (only for `sse` and `streamable-http` modes) |
| `MCP_STREAMABLE_HTTP_PATH` | No | `/mcp` | HTTP path for streamable transport (e.g. `/outline`) |
| `MCP_STATELESS_HTTP` | No | `false` | Set `true` for hosted multi-tenant isolation |
| `OUTLINE_REQUIRE_PASSTHROUGH` | No | `false` | Set `true` to require header-based tenant credentials |
| `OUTLINE_ALLOWED_API_URL_HOSTS` | No | - | Comma-separated allowlist for `X-Outline-Api-Url` hosts |
| `OUTLINE_DEFAULT_API_URL` | No | `https://app.getoutline.com/api` | Default API URL when header URL is omitted |

## Access Control

The server relies on Outline's native API key scopes and permissions. To restrict operations, use an API key with limited permissions in the Outline web UI.

### AI tools missing?

- Check if `OUTLINE_DISABLE_AI_TOOLS=true` is disabling AI features
- Restart your MCP client after changing environment variables

### API rate limiting errors?

The server automatically handles rate limiting with retry logic. If you see persistent rate limit errors:
- Reduce concurrent operations
- Check if multiple clients are using the same API key
- Contact Outline support if limits are too restrictive for your use case

### Docker container issues?

**Container won't start:**
- Ensure `OUTLINE_API_KEY` is set: `docker run -e OUTLINE_API_KEY=your_key ...`
- Check logs: `docker logs <container-id>`

**Can't connect from client:**
- Use `0.0.0.0` for MCP_HOST: `-e MCP_HOST=0.0.0.0`
- Verify port mapping: `-p 3000:3000`
- Check transport mode: `-e MCP_TRANSPORT=streamable-http`

### Need more help?

- 📖 [MCP Documentation](https://modelcontextprotocol.io/)
- 🐛 [Report an issue](https://github.com/Vortiago/mcp-outline/issues)

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions.

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for the current roadmap and upcoming
refactor milestones.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Uses [Outline API](https://getoutline.com) for document management
