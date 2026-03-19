# Outline MCP Agent Guide

Optimized for AI coding assistants working with this Outline MCP server.

## API Quirk & Implementation Notes

### 1. Documents Info & Comment Count
- **Finding**: The `commentCount` field in `documents.info` response is currently unreliable (often returns `null`/`None` even when comments exist).
- **Best Practice**: To get an accurate count, use the `comments.list` endpoint and check `pagination.total`.
- **Implementation**: The `OutlineClient` has a `get_comment_count(document_id)` method that handles this workaround.

### 2. Document Updates (Append Mode)
- **Finding**: The `editMode: "append"` parameter is unreliable and may result in data loss.
- **Best Practice**: Use `append: true` (boolean) in the `documents.update` payload to safely add content to the end of a document while preserving existing content and comment anchors.
- **Implementation**: All update tools in this MCP server (`update_document`, `batch_update_documents`) correctly use the `append` flag.

## Development Patterns

### 1. Document Nesting
- Always use the **full UUID string** for `parentDocumentId`. Truncated or numeric values will fail validation.

### 2. Mermaid Diagrams
- Use ` ```mermaidjs ` (not ` ```mermaid `) for code fence language identifiers to ensure proper rendering in Outline.

### 3. Rate Limiting
- The `OutlineClient` automatically handles rate limiting using the headers from the Outline API and implements exponential backoff.

---
*Follow these patterns to ensure reliable integration with the Outline API.*
