"""Tests for the updated crud_tools module with surreal_query and guardrails."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.graphs.crud_tools import (
    _extract_search_value,
    _fallback_query,
    _pending_writes,
    execute_pending_write,
    get_crud_context,
    preview_write,
    set_crud_context,
    surreal_query,
)


class TestCrudContext:
    """Tests for CRUD context management."""

    def test_set_and_get(self):
        set_crud_context("source:abc123")
        assert get_crud_context() == "source:abc123"

    def test_default_empty(self):
        from open_notebook.graphs.tool_context import set_tool_scope

        set_tool_scope(source_id=None, notebook_id=None)
        assert get_crud_context() == ""


class TestFallbackQuery:
    """Tests for the keyword-based fallback query generator."""

    def test_count_query(self):
        q = _fallback_query("how many records?")
        assert "count()" in q
        assert "GROUP ALL" in q

    def test_buildings_query(self):
        q = _fallback_query("list all buildings")
        assert "DISTINCT" in q
        assert "building" in q.lower()

    def test_no_access_query(self):
        q = _fallback_query("show no access records")
        assert "no_access = true" in q

    def test_friable_query(self):
        q = _fallback_query("find friable items")
        assert "Friable" in q

    def test_high_risk_query(self):
        q = _fallback_query("high risk records")
        assert "Positive" in q

    def test_risk_breakdown(self):
        q = _fallback_query("risk breakdown by sample_result")
        assert "GROUP BY" in q

    def test_generic_fallback(self):
        q = _fallback_query("something random")
        assert "LIMIT" in q
        assert "source_id = $sid" in q


class TestExtractSearchValue:
    """Tests for search value extraction from natural language."""

    def test_quoted_string(self):
        assert _extract_search_value('find records in "Building A"') == "Building A"

    def test_single_quoted_string(self):
        assert _extract_search_value("find records in 'Main Block'") == "Main Block"

    def test_building_reference(self):
        val = _extract_search_value("show records in Building A")
        assert "Building A" in val

    def test_bld_reference(self):
        val = _extract_search_value("show BLD#001 details")
        assert "BLD#001" in val

    def test_in_pattern(self):
        val = _extract_search_value("records in Room 5")
        assert "Room 5" in val


class TestPreviewWrite:
    """Tests for preview_write tool (async)."""

    def setup_method(self):
        set_crud_context("source:test123")
        _pending_writes.clear()

    @pytest.mark.asyncio
    async def test_valid_update_preview(self):
        result_str = await preview_write.ainvoke(
            {
                "operation": "UPDATE",
                "record_id": "acm_record:abc",
                "field": "risk_status",
                "new_value": "High",
                "reason": "Manual correction",
            }
        )
        result = json.loads(result_str)
        assert result["type"] == "preview_write"
        assert result["operation"] == "UPDATE"
        assert result["field"] == "risk_status"
        assert result["operation_id"] in _pending_writes

    @pytest.mark.asyncio
    async def test_blocked_field(self):
        result_str = await preview_write.ainvoke(
            {
                "operation": "UPDATE",
                "record_id": "acm_record:abc",
                "field": "id",
                "new_value": "hacked",
                "reason": "Trying to modify ID",
            }
        )
        result = json.loads(result_str)
        assert "error" in result
        assert "Write blocked" in result["error"]

    @pytest.mark.asyncio
    async def test_blocked_table(self):
        result_str = await preview_write.ainvoke(
            {
                "operation": "UPDATE",
                "record_id": "source:abc",
                "field": "title",
                "new_value": "hacked",
                "reason": "Trying to modify source",
            }
        )
        # source: prefix doesn't start with building_record: so defaults to acm_record
        # The field "title" is not in ALLOWED_ACM_FIELDS
        result = json.loads(result_str)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_no_context(self):
        from open_notebook.graphs.tool_context import set_tool_scope

        set_tool_scope(source_id=None, notebook_id=None)
        result_str = await preview_write.ainvoke(
            {
                "operation": "UPDATE",
                "record_id": "acm_record:abc",
                "field": "risk_status",
                "new_value": "High",
                "reason": "test",
            }
        )
        result = json.loads(result_str)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_delete_preview(self):
        set_crud_context("source:test123")
        result_str = await preview_write.ainvoke(
            {
                "operation": "DELETE",
                "record_id": "acm_record:abc",
                "field": None,
                "new_value": None,
                "reason": "Remove duplicate",
            }
        )
        result = json.loads(result_str)
        assert result["type"] == "preview_write"
        assert result["operation"] == "DELETE"

    @pytest.mark.asyncio
    async def test_blocked_operation(self):
        result_str = await preview_write.ainvoke(
            {
                "operation": "DROP",
                "record_id": "acm_record:abc",
                "field": None,
                "new_value": None,
                "reason": "bad intent",
            }
        )
        result = json.loads(result_str)
        assert "error" in result


class TestSurrealQueryNoDb:
    """Tests for surreal_query that don't require a running DB."""

    @pytest.mark.asyncio
    async def test_no_context_returns_error(self):
        from open_notebook.graphs.tool_context import set_tool_scope

        set_tool_scope(source_id=None, notebook_id=None)
        result_str = await surreal_query.ainvoke({"question": "how many records?"})
        result = json.loads(result_str)
        assert result["type"] == "surreal_query"
        assert "error" in result
        assert "No job context" in result["error"]
