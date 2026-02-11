"""Tests for shared document utilities."""

import pytest

from mcp_outline.features.documents.common import ensure_uuid_string


class TestEnsureUuidString:
    """Tests for ensure_uuid_string validation helper."""

    def test_valid_uuid_returns_canonical_form(self):
        """Valid UUID returns hyphenated canonical string."""
        result = ensure_uuid_string(
            "580b8429-8da4-4409-a2ad-f86e194074b6", "param"
        )
        assert result == "580b8429-8da4-4409-a2ad-f86e194074b6"

    def test_valid_uuid_without_hyphens_normalized(self):
        """UUID without hyphens is normalized to canonical form."""
        result = ensure_uuid_string(
            "580b84298da44409a2adf86e194074b6", "param"
        )
        assert result == "580b8429-8da4-4409-a2ad-f86e194074b6"

    def test_none_returns_none(self):
        """None input returns None."""
        assert ensure_uuid_string(None, "param") is None

    def test_empty_string_returns_none(self):
        """Empty string returns None."""
        assert ensure_uuid_string("", "param") is None

    def test_whitespace_only_returns_none(self):
        """Whitespace-only string returns None."""
        assert ensure_uuid_string("   ", "param") is None

    def test_invalid_uuid_raises_value_error(self):
        """Invalid UUID format raises ValueError with clear message."""
        with pytest.raises(ValueError) as exc_info:
            ensure_uuid_string("580", "parent_document_id")
        assert "parent_document_id" in str(exc_info.value)
        assert "valid UUID" in str(exc_info.value)

    def test_truncated_uuid_raises_value_error(self):
        """Truncated UUID (e.g. from type coercion) raises ValueError."""
        with pytest.raises(ValueError):
            ensure_uuid_string("580b8429-8da4", "param")

    def test_int_coerced_to_string_raises_value_error(self):
        """Integer (e.g. from JSON) coerced to str raises when invalid."""
        with pytest.raises(ValueError):
            ensure_uuid_string(580, "param")

    def test_non_uuid_string_raises_value_error(self):
        """Non-UUID string raises ValueError."""
        with pytest.raises(ValueError):
            ensure_uuid_string("not-a-uuid", "param")
