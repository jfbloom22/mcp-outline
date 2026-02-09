# VPS Deployment (Light Production)

This profile runs `mcp-outline` behind Nginx with header passthrough for
multi-tenant Cursor connections.

## 1) Configure host allowlist

Edit `deploy/docker-compose.hosted.yml`:

- `OUTLINE_ALLOWED_API_URL_HOSTS`
- `OUTLINE_DEFAULT_API_URL`

## 2) Start services

```bash
cd deploy
docker compose -f docker-compose.hosted.yml up -d --build
```

## 3) Probe health and auth

```bash
curl http://localhost/health
curl -H "Authorization: Bearer <outline_api_key>" \
  -H "X-Outline-Api-Url: https://outline.example.com/api" \
  http://localhost/auth/whoami
```

## 4) Cursor config

Use URL `https://<your-domain>/outline` and passthrough headers:

```json
{
  "mcpServers": {
    "outline-shared": {
      "url": "https://mcp.example.com/outline",
      "headers": {
        "Authorization": "Bearer ${env:OUTLINE_API_KEY}",
        "X-Outline-Api-Url": "${env:OUTLINE_API_URL}"
      }
    }
  }
}
```
