"""
Tests for document content tools.
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_outline.features.documents.common import OutlineClientError

# Valid UUIDs for testing (Outline API requires UUID format)
COLLECTION_ID = "580b8429-8da4-4409-a2ad-f86e194074b6"
DOCUMENT_ID = "8610a622-afb5-4ebe-92d7-cdd58fb1aaa5"


# Mock FastMCP for registering tools
class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, **kwargs):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


# Sample response data
SAMPLE_CREATE_DOCUMENT_RESPONSE = {
    "data": {
        "id": "doc123",
        "title": "Test Document",
        "text": "This is a test document.",
        "updatedAt": "2023-01-01T12:00:00Z",
        "createdAt": "2023-01-01T12:00:00Z",
    }
}

SAMPLE_UPDATE_DOCUMENT_RESPONSE = {
    "data": {
        "id": "doc123",
        "title": "Updated Document",
        "text": "This document has been updated.",
        "updatedAt": "2023-01-02T12:00:00Z",
    }
}

SAMPLE_COMMENT_RESPONSE = {
    "data": {
        "id": "comment123",
        "documentId": "doc123",
        "createdById": "user123",
        "createdAt": "2023-01-01T12:00:00Z",
        "body": "This is a comment",
    }
}


@pytest.fixture
def mcp():
    """Fixture to provide mock MCP instance."""
    return MockMCP()


@pytest.fixture
def register_content_tools(mcp):
    """Fixture to register document content tools."""
    from mcp_outline.features.documents.document_content import register_tools

    register_tools(mcp)
    return mcp


class TestDocumentContentTools:
    """Tests for document content tools."""

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_content.get_outline_client"
    )
    async def test_create_document_success(
        self, mock_get_client, register_content_tools
    ):
        """Test create_document tool success case."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_CREATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_content_tools.tools["create_document"](
            title="Test Document",
            collection_id=COLLECTION_ID,
            text="This is a test document.",
        )

        # Verify client was called correctly
        mock_client.post.assert_called_once_with(
            "documents.create",
            {
                "title": "Test Document",
                "text": "This is a test document.",
                "collectionId": COLLECTION_ID,
                "publish": True,
            },
        )

        # Verify result contains expected information
        assert "Document created successfully" in result
        assert "Test Document" in result
        assert "doc123" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_content.get_outline_client"
    )
    async def test_create_document_with_parent(
        self, mock_get_client, register_content_tools
    ):
        """Test create_document tool with parent document ID."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_CREATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        # Call the tool with parent document ID
        _ = await register_content_tools.tools["create_document"](
            title="Test Document",
            collection_id=COLLECTION_ID,
            text="This is a test document.",
            parent_document_id="580b8429-8da4-4409-a2ad-f86e194074b6",
        )

        # Verify parent document ID was included in the call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args[0]

        assert call_args[0] == "documents.create"
        assert "parentDocumentId" in call_args[1]
        assert call_args[1]["parentDocumentId"] == (
            "580b8429-8da4-4409-a2ad-f86e194074b6"
        )

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_content.get_outline_client"
    )
    async def test_create_document_failure(
        self, mock_get_client, register_content_tools
    ):
        """Test create_document tool with empty response."""
        # Set up mock client with empty response
        mock_client = AsyncMock()
        mock_client.post.return_value = {"data": None}
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_content_tools.tools["create_document"](
            title="Test Document", collection_id=COLLECTION_ID
        )

        # Verify result contains error message
        assert "Failed to create document" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_content.get_outline_client"
    )
    async def test_create_document_client_error(
        self, mock_get_client, register_content_tools
    ):
        """Test create_document tool with client error."""
        # Set up mock client to raise an error
        mock_client = AsyncMock()
        mock_client.post.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_content_tools.tools["create_document"](
            title="Test Document", collection_id=COLLECTION_ID
        )

        # Verify error is handled and returned
        assert "Error creating document" in result
        assert "API error" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_content.get_outline_client"
    )
    async def test_update_document_success(
        self, mock_get_client, register_content_tools
    ):
        """Test update_document tool success case."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_UPDATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_content_tools.tools["update_document"](
            document_id=DOCUMENT_ID,
            title="Updated Document",
            text="This document has been updated.",
        )

        # Verify client was called correctly
        mock_client.post.assert_called_once_with(
            "documents.update",
            {
                "id": DOCUMENT_ID,
                "title": "Updated Document",
                "text": "This document has been updated.",
                "append": False,
            },
        )

        # Verify result contains expected information
        assert "Document updated successfully" in result
        assert "Updated Document" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_content.get_outline_client"
    )
    async def test_update_document_passes_content_unchanged(
        self, mock_get_client, register_content_tools
    ):
        """Regression: time strings in content pass through unchanged.

        Bug report: content like (12:30 - 1:15 PM) was corrupted when sent
        via MCP. This verifies our server passes it through correctly.
        """
        corruption_prone_content = """# Clean Agenda: People Team AI Academy

**Date:** March 26, 2026
**Time:** 10:00 AM

## Morning Session

### (12:30 - 1:15 PM) Welcome
*   **Note:** Please arrive early.

### (1:15 - 1:30 PM) AI Academy Overview

### (1:30 - 2:00 PM) External Perspective:

### (3:20 - 3:45 PM) Creative Application Challenge

### (3:45 - 4:00 PM) Skill Takeaway
"""
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_UPDATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        result = await register_content_tools.tools["update_document"](
            document_id=DOCUMENT_ID,
            text=corruption_prone_content,
        )

        call_args = mock_client.post.call_args[0]
        assert call_args[0] == "documents.update"
        sent_text = call_args[1]["text"]
        assert "(12:30 - 1:15 PM)" in sent_text
        assert "(1:15 - 1:30 PM) AI Academy Overview" in sent_text
        assert "(1:30 - 2:00 PM) External Perspective:" in sent_text
        assert "(3:20 - 3:45 PM) Creative Application Challenge" in sent_text
        assert "(3:45 - 4:00 PM) Skill Takeaway" in sent_text
        assert "*   **Note:**" in sent_text
        assert "Document updated successfully" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_content.get_outline_client"
    )
    async def test_update_document_rejects_non_string_text(
        self, mock_get_client, register_content_tools
    ):
        """Reject non-string text to prevent type coercion corruption."""
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await register_content_tools.tools["update_document"](
            document_id=DOCUMENT_ID,
            text=12345,  # type: ignore[arg-type]
        )

        assert "Validation error" in result
        assert "must be a string" in result
        assert "int" in result
        mock_client.post.assert_not_called()

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_content.get_outline_client"
    )
    async def test_update_document_append(
        self, mock_get_client, register_content_tools
    ):
        """Test update_document tool with append flag."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_UPDATE_DOCUMENT_RESPONSE
        mock_get_client.return_value = mock_client

        # Call the tool with append flag
        _ = await register_content_tools.tools["update_document"](
            document_id=DOCUMENT_ID, text="Additional text.", append=True
        )

        # Verify append flag was included in the call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args[0]

        assert call_args[0] == "documents.update"
        assert "append" in call_args[1]
        assert call_args[1]["append"] is True

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_content.get_outline_client"
    )
    async def test_add_comment_success(
        self, mock_get_client, register_content_tools
    ):
        """Test add_comment tool success case."""
        # Set up mock client
        mock_client = AsyncMock()
        mock_client.post.return_value = SAMPLE_COMMENT_RESPONSE
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_content_tools.tools["add_comment"](
            document_id=DOCUMENT_ID, text="This is a comment"
        )

        # Verify client was called correctly
        mock_client.post.assert_called_once_with(
            "comments.create",
            {"documentId": DOCUMENT_ID, "text": "This is a comment"},
        )

        # Verify result contains expected information
        assert "Comment added successfully" in result
        assert "comment123" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_content.get_outline_client"
    )
    async def test_add_comment_failure(
        self, mock_get_client, register_content_tools
    ):
        """Test add_comment tool with empty response."""
        # Set up mock client with empty response
        mock_client = AsyncMock()
        mock_client.post.return_value = {"data": None}
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_content_tools.tools["add_comment"](
            document_id=DOCUMENT_ID, text="This is a comment"
        )

        # Verify result contains error message
        assert "Failed to create comment" in result

    @pytest.mark.asyncio
    @patch(
        "mcp_outline.features.documents.document_content.get_outline_client"
    )
    async def test_add_comment_client_error(
        self, mock_get_client, register_content_tools
    ):
        """Test add_comment tool with client error."""
        # Set up mock client to raise an error
        mock_client = AsyncMock()
        mock_client.post.side_effect = OutlineClientError("API error")
        mock_get_client.return_value = mock_client

        # Call the tool
        result = await register_content_tools.tools["add_comment"](
            document_id=DOCUMENT_ID, text="This is a comment"
        )

        # Verify error is handled and returned
        assert "Error adding comment" in result
        assert "API error" in result
