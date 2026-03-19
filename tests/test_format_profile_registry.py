"""Tests for Multi-Consultant Story 3: Consultant Format Profile Registry.

Tests cover:
- Header signature hashing (determinism, order-independence, collision resistance)
- Format profile repository CRUD operations
- Cache hit/miss logic in schema inference
- FastAPI format-profiles endpoints
"""

import hashlib
from unittest.mock import AsyncMock, patch

import pytest

from open_notebook.extractors.schema_inference import (
    InferredSchema,
    compute_header_signature,
)

# =============================================================================
# 1. Header Signature Hashing
# =============================================================================


class TestHeaderSignature:
    """Test header signature computation for cache keying."""

    def test_deterministic_same_input(self):
        """Same headers produce the same signature."""
        headers = ["Room/Area", "Item Name", "Friability"]
        sig1 = compute_header_signature(headers)
        sig2 = compute_header_signature(headers)
        assert sig1 == sig2

    def test_order_independent(self):
        """Different header orderings produce the same signature."""
        sig1 = compute_header_signature(["Room/Area", "Item Name", "Friability"])
        sig2 = compute_header_signature(["Friability", "Room/Area", "Item Name"])
        assert sig1 == sig2

    def test_case_insensitive(self):
        """Signatures are case-insensitive."""
        sig1 = compute_header_signature(["Room/Area", "ITEM NAME"])
        sig2 = compute_header_signature(["room/area", "item name"])
        assert sig1 == sig2

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace is stripped."""
        sig1 = compute_header_signature(["Room/Area", "Item Name"])
        sig2 = compute_header_signature(["  Room/Area  ", " Item Name "])
        assert sig1 == sig2

    def test_empty_headers_excluded(self):
        """Empty/whitespace-only headers are excluded."""
        sig1 = compute_header_signature(["Room/Area", "Item Name"])
        sig2 = compute_header_signature(["Room/Area", "", "  ", "Item Name"])
        assert sig1 == sig2

    def test_different_headers_different_signature(self):
        """Different header sets produce different signatures."""
        sig1 = compute_header_signature(["Room/Area", "Item Name", "Friability"])
        sig2 = compute_header_signature(["Room/Area", "Condition", "Result"])
        assert sig1 != sig2

    def test_signature_is_16_char_hex(self):
        """Signature is a 16-character hex string."""
        sig = compute_header_signature(["Room/Area", "Item Name"])
        assert len(sig) == 16
        assert all(c in "0123456789abcdef" for c in sig)

    def test_subset_headers_different_signature(self):
        """Subset of headers produces different signature."""
        sig1 = compute_header_signature(["Room/Area", "Item Name", "Friability"])
        sig2 = compute_header_signature(["Room/Area", "Item Name"])
        assert sig1 != sig2


# =============================================================================
# 2. Format Profile Repository
# =============================================================================


class TestFormatProfileRepository:
    """Test DB CRUD for format profiles."""

    @pytest.mark.asyncio
    async def test_get_profile_by_signature_returns_none_on_miss(self):
        """Cache miss returns None."""
        from open_notebook.extractors.format_profile_repository import (
            get_profile_by_signature,
        )

        with patch(
            "open_notebook.extractors.format_profile_repository.repo_query",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await get_profile_by_signature("nonexistent_sig")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_profile_by_signature_returns_profile_on_hit(self):
        """Cache hit returns the profile dict."""
        from open_notebook.extractors.format_profile_repository import (
            get_profile_by_signature,
        )

        mock_profile = {
            "id": "consultant_format_profile:abc123",
            "header_signature": "abcdef1234567890",
            "consultant_name": "Prensa Pty Ltd",
            "column_mapping": {"Room/Area": "Room_or_Area__c"},
            "canonical_mapping": {"Room/Area": "room_location"},
            "confidence": 0.92,
            "verified_by_user": False,
            "sample_count": 3,
        }

        with patch(
            "open_notebook.extractors.format_profile_repository.repo_query",
            new_callable=AsyncMock,
            return_value=[mock_profile],
        ):
            result = await get_profile_by_signature("abcdef1234567890")
            assert result is not None
            assert result["header_signature"] == "abcdef1234567890"
            assert result["consultant_name"] == "Prensa Pty Ltd"

    @pytest.mark.asyncio
    async def test_save_profile_calls_repo_create(self):
        """Saving a new profile calls repo_create with correct data."""
        from open_notebook.extractors.format_profile_repository import save_profile

        profile_data = {
            "header_signature": "abcdef1234567890",
            "consultant_name": "Greencap",
            "column_mapping": {"Room/Area": "Room_or_Area__c"},
            "canonical_mapping": {"Room/Area": "room_location"},
            "confidence": 0.85,
        }

        with patch(
            "open_notebook.extractors.format_profile_repository.repo_create",
            new_callable=AsyncMock,
            return_value=[{"id": "consultant_format_profile:xyz"}],
        ) as mock_create:
            result = await save_profile(profile_data)
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args[0][0] == "consultant_format_profile"
            assert call_args[0][1]["header_signature"] == "abcdef1234567890"

    @pytest.mark.asyncio
    async def test_increment_sample_count(self):
        """Incrementing sample_count updates the record."""
        from open_notebook.extractors.format_profile_repository import (
            increment_sample_count,
        )

        with patch(
            "open_notebook.extractors.format_profile_repository.repo_query",
            new_callable=AsyncMock,
            return_value=[{"sample_count": 4}],
        ) as mock_query:
            await increment_sample_count("consultant_format_profile:abc123")
            mock_query.assert_called_once()
            # Verify the UPDATE query increments sample_count
            query = mock_query.call_args[0][0]
            assert "sample_count" in query
            assert "UPDATE" in query

    @pytest.mark.asyncio
    async def test_delete_profile(self):
        """Deleting a profile calls repo_delete."""
        from open_notebook.extractors.format_profile_repository import delete_profile

        with patch(
            "open_notebook.extractors.format_profile_repository.repo_delete",
            new_callable=AsyncMock,
        ) as mock_delete:
            await delete_profile("consultant_format_profile:abc123")
            mock_delete.assert_called_once_with("consultant_format_profile:abc123")

    @pytest.mark.asyncio
    async def test_list_profiles(self):
        """Listing profiles returns all records."""
        from open_notebook.extractors.format_profile_repository import list_profiles

        mock_profiles = [
            {"id": "consultant_format_profile:1", "consultant_name": "Prensa"},
            {"id": "consultant_format_profile:2", "consultant_name": "Greencap"},
        ]

        with patch(
            "open_notebook.extractors.format_profile_repository.repo_query",
            new_callable=AsyncMock,
            return_value=mock_profiles,
        ):
            result = await list_profiles()
            assert len(result) == 2
            assert result[0]["consultant_name"] == "Prensa"


# =============================================================================
# 3. Cache Hit/Miss in Schema Inference
# =============================================================================


MOCK_TABLES = [
    {
        "docling_document_json": {
            "table_cells": [
                {"text": "Room/Area", "column_header": True, "start_col_offset_idx": 0},
                {"text": "Item Name", "column_header": True, "start_col_offset_idx": 1},
                {"text": "101", "column_header": False, "start_row_offset_idx": 1, "start_col_offset_idx": 0},
                {"text": "Ceiling tiles", "column_header": False, "start_row_offset_idx": 1, "start_col_offset_idx": 1},
            ]
        }
    }
]

CACHED_PROFILE = {
    "id": "consultant_format_profile:cached1",
    "header_signature": "abcdef1234567890",
    "consultant_name": "Prensa Pty Ltd",
    "column_mapping": {"Room/Area": "Room_or_Area__c", "Item Name": "Item_Name__c"},
    "canonical_mapping": {"Room/Area": "room_location", "Item Name": "item_description"},
    "level_regex": None,
    "recovery_config": None,
    "confidence": 0.92,
    "verified_by_user": True,
    "sample_count": 5,
}


class TestSchemaInferenceCaching:
    """Test that schema inference checks format profile cache.

    Uses side_effect on repo_query to route different SurrealQL queries
    to different mock responses, since schema_inference_node uses lazy imports.
    """

    @pytest.mark.asyncio
    async def test_cache_hit_skips_llm(self):
        """When a format profile exists for the header signature, LLM is NOT called."""
        from open_notebook.extractors.schema_inference import schema_inference_node

        mock_source = type("Source", (), {"id": "source:test123"})()
        repo_query_log = []

        async def mock_repo_query(query_str, vars=None):
            repo_query_log.append(query_str)
            if "acm_table_section" in query_str:
                return MOCK_TABLES
            if "consultant_format_profile" in query_str and "SELECT" in query_str:
                return [CACHED_PROFILE]
            if "UPDATE" in query_str:
                return [{"sample_count": 6}]
            return []

        with (
            patch(
                "open_notebook.database.repository.repo_query",
                side_effect=mock_repo_query,
            ),
            patch(
                "open_notebook.extractors.format_profile_repository.repo_query",
                side_effect=mock_repo_query,
            ),
            patch(
                "open_notebook.database.repository.ensure_record_id",
                side_effect=lambda x: x,
            ),
            patch(
                "open_notebook.graphs.utils.provision_langchain_model",
                new_callable=AsyncMock,
            ) as mock_llm,
        ):
            result = await schema_inference_node({"source": mock_source})

            # LLM was NOT called (cache hit skips inference)
            mock_llm.assert_not_called()
            # InferredSchema was built from cache
            schema = result.get("inferred_schema")
            assert schema is not None
            assert schema.confidence == 0.92
            assert schema.consultant_name == "Prensa Pty Ltd"
            assert schema.profile_id == "consultant_format_profile:cached1"
            assert schema.column_mapping == {"Room/Area": "Room_or_Area__c", "Item Name": "Item_Name__c"}
            # sample_count was incremented
            assert any("UPDATE" in q for q in repo_query_log)

    @pytest.mark.asyncio
    async def test_cache_miss_calls_llm_and_saves_profile(self):
        """When no format profile exists, LLM runs and profile is saved."""
        from open_notebook.extractors.schema_inference import schema_inference_node

        mock_source = type("Source", (), {"id": "source:test456"})()
        repo_query_log = []
        created_records = []

        async def mock_repo_query(query_str, vars=None):
            repo_query_log.append(query_str)
            if "acm_table_section" in query_str:
                return MOCK_TABLES
            if "consultant_format_profile" in query_str and "SELECT" in query_str:
                return []  # Cache miss
            return []

        async def mock_repo_create(table, data):
            created_records.append({"table": table, "data": data})
            return [{"id": "consultant_format_profile:new1"}]

        llm_response = """{
            "mappings": [
                {"pdf_header": "Room/Area", "sf_field": "Room_or_Area__c", "confidence": 0.95},
                {"pdf_header": "Item Name", "sf_field": "Item_Name__c", "confidence": 0.90}
            ],
            "unmapped_headers": [],
            "overall_confidence": 0.92,
            "detected_consultant": "Test Consultant"
        }"""

        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = type("Resp", (), {"content": llm_response})()

        with (
            patch(
                "open_notebook.database.repository.repo_query",
                side_effect=mock_repo_query,
            ),
            patch(
                "open_notebook.extractors.format_profile_repository.repo_query",
                side_effect=mock_repo_query,
            ),
            patch(
                "open_notebook.extractors.format_profile_repository.repo_create",
                side_effect=mock_repo_create,
            ),
            patch(
                "open_notebook.database.repository.ensure_record_id",
                side_effect=lambda x: x,
            ),
            patch(
                "open_notebook.graphs.utils.provision_langchain_model",
                new_callable=AsyncMock,
                return_value=mock_model,
            ) as mock_provision,
            patch("ai_prompter.Prompter") as mock_prompter_cls,
        ):
            mock_prompter_cls.return_value.render.return_value = "test prompt"

            result = await schema_inference_node({"source": mock_source})

            # LLM WAS called
            mock_provision.assert_called_once()
            mock_model.ainvoke.assert_called_once()
            # Profile WAS saved to DB
            assert len(created_records) == 1
            assert created_records[0]["table"] == "consultant_format_profile"
            assert created_records[0]["data"]["consultant_name"] == "Test Consultant"
            assert created_records[0]["data"]["confidence"] == 0.92
            # Result has inferred schema
            schema = result.get("inferred_schema")
            assert schema is not None
            assert schema.confidence == 0.92
            assert schema.profile_id == "consultant_format_profile:new1"
