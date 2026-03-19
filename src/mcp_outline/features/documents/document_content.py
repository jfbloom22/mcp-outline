"""
Document content management for the MCP Outline server.

This module provides MCP tools for creating and updating document content.
"""

from typing import Any

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from mcp_outline.features.documents.common import (
    OutlineClientError,
    ensure_text_is_str,
    ensure_uuid_string,
    get_outline_client,
    require_uuid_string,
)


def register_tools(mcp) -> None:
    """
    Register document content tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
        )
    )
    async def create_document(
        title: str,
        collection_id: str,
        text: str = "",
        parent_document_id: str | None = None,
        publish: bool = True,
        ctx: Context | None = None,
    ) -> str:
        """
        Creates a new document in a specified collection.

        Use this tool when you need to:
        - Add new content to a knowledge base
        - Create documentation, guides, or notes
        - Add a child document to an existing parent
        - Start a new document thread or topic

        Note: For Mermaid diagrams, use ```mermaidjs (not ```mermaid)
        as the code fence language identifier for proper rendering.

        Args:
            title: The document title
            collection_id: The collection ID to create the document in
            text: Optional markdown content for the document
            parent_document_id: Full UUID string (e.g.
                580b8429-8da4-4409-a2ad-f86e194074b6) for nesting. Must be the
                complete UUID, not a truncated value or number.
            publish: Whether to publish the document immediately (True) or
                save as draft (False)

        Returns:
            Result message with the new document ID
        """
        try:
            client = await get_outline_client(ctx=ctx)

            data = {
                "title": ensure_text_is_str(title, "title"),
                "text": ensure_text_is_str(text, "text"),
                "collectionId": require_uuid_string(
                    collection_id, "collection_id"
                ),
                "publish": publish,
            }

            if parent_document_id:
                parsed = ensure_uuid_string(
                    parent_document_id, "parent_document_id"
                )
                if parsed:
                    data["parentDocumentId"] = parsed

            response = await client.post("documents.create", data)
            document = response.get("data", {})

            if not document:
                return "Failed to create document."

            doc_id = document.get("id", "unknown")
            doc_title = document.get("title", "Untitled")

            return f"Document created successfully: {doc_title} (ID: {doc_id})"
        except (TypeError, ValueError) as e:
            return f"Validation error: {e}"
        except OutlineClientError as e:
            return f"Error creating document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
        )
    )
    async def update_document(
        document_id: str,
        title: str | None = None,
        text: str | None = None,
        append: bool = False,
        ctx: Context | None = None,
    ) -> str:
        """
        Modifies an existing document's title or content.

        By default, this tool replaces the document content rather
        than just adding to it. If you want to replace only part
        of a document, you should first read the document, modify
        its content, and then send the complete text.

        To safely add content to the end of a document without reading
        it first, set 'append=True'. This preserves existing content
        and comment anchors.

        Use this tool when you need to:
        - Edit or update document content (with append=False)
        - Change a document's title
        - Append new content to an existing document (with append=True)
        - Fix errors or add information to documents

        Note: For Mermaid diagrams, use ```mermaidjs (not ```mermaid)
        as the code fence language identifier for proper rendering.

        Args:
            document_id: The document ID to update
            title: New title (if None, keeps existing title)
            text: New content (if None, keeps existing content)
            append: If True, adds text to the end of document
                instead of replacing. This is the reliable way
                to perform additive updates.

        Returns:
            Result message confirming update
        """
        try:
            client = await get_outline_client(ctx=ctx)

            data: dict[str, Any] = {"id": require_uuid_string(document_id, "document_id")}

            if title is not None:
                data["title"] = ensure_text_is_str(title, "title")
            if text is not None:
                data["text"] = ensure_text_is_str(text, "text")
                data["append"] = append

            response = await client.post("documents.update", data)
            document = response.get("data", {})

            if not document:
                return "Failed to update document."

            doc_title = document.get("title", "Untitled")

            return f"Document updated successfully: {doc_title}"
        except (TypeError, ValueError) as e:
            return f"Validation error: {e}"
        except OutlineClientError as e:
            return f"Error updating document: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
        )
    )
    async def add_comment(
        document_id: str,
        text: str,
        parent_comment_id: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """
        Adds a comment to a document or replies to an existing comment.

        Use this tool when you need to:
        - Provide feedback on document content
        - Ask questions about specific information
        - Reply to another user's comment
        - Collaborate with others on document development

        Args:
            document_id: The document to comment on
            text: The comment text (supports markdown)
            parent_comment_id: Optional ID of a parent comment (for replies)

        Returns:
            Result message with the new comment ID
        """
        try:
            client = await get_outline_client(ctx=ctx)

            data = {
                "documentId": require_uuid_string(document_id, "document_id"),
                "text": ensure_text_is_str(text, "text"),
            }

            if parent_comment_id:
                parsed = ensure_uuid_string(
                    parent_comment_id, "parent_comment_id"
                )
                if parsed:
                    data["parentCommentId"] = parsed

            response = await client.post("comments.create", data)
            comment = response.get("data", {})

            if not comment:
                return "Failed to create comment."

            comment_id = comment.get("id", "unknown")

            if parent_comment_id:
                return f"Reply added successfully (ID: {comment_id})"
            else:
                return f"Comment added successfully (ID: {comment_id})"
        except (TypeError, ValueError) as e:
            return f"Validation error: {e}"
        except OutlineClientError as e:
            return f"Error adding comment: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
