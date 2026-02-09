# MCP Outline Roadmap

## High-Level Overview: What We Accomplished

This phase established a light-production-ready foundation for hosted,
multi-tenant MCP usage with request-scoped authentication.

### Delivered

1. Request-scoped auth and tenant passthrough
- Added header-based auth contract support:
  - `Authorization: Bearer <outline_api_key>`
  - `X-Outline-Api-Url: <outline_api_url>` (optional)
- Refactored client resolution from env-scoped to request-scoped for HTTP
  requests.
- Kept env fallback for local/dev paths when passthrough is not required.

2. Security hardening for hosted mode
- Added configurable passthrough enforcement and host allowlisting:
  - `OUTLINE_REQUIRE_PASSTHROUGH`
  - `OUTLINE_ALLOWED_API_URL_HOSTS`
  - `OUTLINE_DEFAULT_API_URL`
- Enforced stricter URL validation for SSRF resistance:
  - `https` only
  - reject query params/fragments
  - require `/api` path
  - reject URL userinfo
  - reject private/loopback/link-local/reserved IP targets unless explicitly
    allowlisted

3. Transport and deployment readiness
- Added hosted transport controls:
  - `MCP_STREAMABLE_HTTP_PATH`
  - `MCP_STATELESS_HTTP`
- Added hosted deployment examples and docs:
  - `deploy/docker-compose.hosted.yml`
  - `deploy/nginx/mcp-outline.conf`
  - `docs/deployment/vps-nginx.md`

4. Operability improvements
- Added MCP auth probe tool: `whoami_outline`
- Added HTTP auth probe endpoint: `GET /auth/whoami`
- Simplified readiness semantics (`/ready` is process readiness; tenant auth is
  validated via probe)

5. Test and reliability improvements
- Added auth unit coverage for bearer parsing, rejection cases, and URL
  validation.
- Added request-aware client factory tests.
- Fixed stdio integration tests to use `sys.executable` instead of hardcoded
  `"python"` for environment portability.
- Current suite status: all tests passing.


## Future Plan

### Phase 1: Error Handling Consistency (Next)

Goal: Standardize safe, predictable error behavior across tools and endpoints.

Planned work:
1. Introduce a shared error formatter/sanitizer utility.
2. Replace ad hoc `str(e)` responses in tools/routes with standardized
   user-facing messages.
3. Ensure sensitive values are never echoed from downstream exceptions.
4. Add focused tests for sanitization across auth and tool failures.

Expected outcome:
- Cleaner client UX, less duplicated logic, and safer default error handling.


### Phase 2: Structured Auth Diagnostics (Next)

Goal: Make auth probe outputs easier for MCP clients to consume.

Planned work:
1. Convert `whoami_outline` output from free-form text to structured JSON-like
   schema (e.g., TypedDict).
2. Keep response fields stable and minimal:
   - team name
   - user name
   - email
   - resolved API host
   - auth source
3. Align `/auth/whoami` payload shape with tool output where practical.

Expected outcome:
- Better machine-readability for agent clients and easier support/debug flows.


### Phase 3: Configuration Lifecycle Optimization (Later)

Goal: Reduce repeated config parsing overhead while preserving testability and
clarity.

Planned work:
1. Add lightweight config caching for `AuthConfig.from_env()`.
2. Keep explicit invalidation/reset path for tests and dev workflows.
3. Document cache behavior and when values are refreshed.

Expected outcome:
- Slightly improved request path efficiency and cleaner config access pattern.


## Suggested Milestone Order

1. Milestone A: Error handling standardization
2. Milestone B: Structured `whoami_outline` output
3. Milestone C: Auth config caching


## Definition of Done for Next Milestones

1. Tests
- New/updated tests cover all new shared utilities and response formats.
- No regression in existing `tests/` suite.

2. Security
- No secret-bearing values appear in user-visible errors or logs.

3. Docs
- README and deployment docs updated if output formats or env semantics change.
