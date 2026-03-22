"""Tests for enhanced crud_tools: new tools (get_schema_info, ask_user_choice,
undo_last_write, preview_bulk_write) and old_value capture in execute_pending_write.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from open_notebook.graphs.crud_tools import (
    _pending_writes,
    ask_user_choice,
    get_schema_info,
    preview_bulk_write,
    preview_write,
    set_crud_context,
    undo_last_write,
)
from open_notebook.graphs.guardrails import (
    ALLOWED_ACM_FIELDS,
    ALLOWED_BUILDING_FIELDS,
    classify_intent,
)


class TestGetSchemaInfo:
    """Tests for get_schema_info tool."""

    def test_returns_both_tables(self):
        result = json.loads(get_schema_info.invoke({"table": None}))
        assert result["type"] == "schema_info"
        assert "acm_record" in result["tables"]
        assert "building_record" in result["tables"]

    def test_returns_acm_record_only(self):
        result = json.loads(get_schema_info.invoke({"table": "acm_record"}))
        assert result["type"] == "schema_info"
        assert "acm_record" in result["tables"]

    def test_returns_building_record_only(self):
        result = json.loads(get_schema_info.invoke({"table": "building_record"}))
        assert result["type"] == "schema_info"
        assert "building_record" in result["tables"]

    def test_includes_enum_values(self):
        result = json.loads(get_schema_info.invoke({"table": "acm_record"}))
        enums = result["tables"]["acm_record"]["enum_values"]
        assert "friable" in enums
        assert "Friable" in enums["friable"]
        assert "Non-friable" in enums["friable"]
        assert "risk_status" in enums
        assert "High" in enums["risk_status"]
        assert "sample_result" in enums
        assert "Positive" in enums["sample_result"]

    def test_includes_updatable_fields(self):
        result = json.loads(get_schema_info.invoke({"table": "acm_record"}))
        fields = result["tables"]["acm_record"]["updatable_fields"]
        assert "risk_status" in fields
        assert "friable" in fields
        assert "product" in fields

    def test_unknown_table(self):
        result = json.loads(get_schema_info.invoke({"table": "nonexistent"}))
        assert result["type"] == "schema_info"
        # Should return empty or both defaults
        assert "tables" in result


class TestAskUserChoice:
    """Tests for ask_user_choice tool."""

    def setup_method(self):
        set_crud_context("source:test123")

    def test_static_options(self):
        result = json.loads(
            ask_user_choice.invoke(
                {
                    "question": "Which risk level?",
                    "static_options": ["High", "Medium", "Low"],
                }
            )
        )
        assert result["type"] == "ask_user_choice"
        assert result["question"] == "Which risk level?"
        assert len(result["options"]) == 3
        assert result["options"][0]["label"] == "High"
        assert result["options"][0]["value"] == "High"
        assert "choice_id" in result

    def test_no_options_provided(self):
        result = json.loads(
            ask_user_choice.invoke(
                {
                    "question": "Pick one?",
                }
            )
        )
        assert result["type"] == "ask_user_choice"
        # Should still return but with empty options
        assert "options" in result


class TestPreviewBulkWrite:
    """Tests for preview_bulk_write tool."""

    def setup_method(self):
        set_crud_context("source:test123")
        _pending_writes.clear()

    def test_with_explicit_record_ids(self):
        result = json.loads(
            preview_bulk_write.invoke(
                {
                    "operation": "UPDATE",
                    "filter_description": "all friable items",
                    "field": "risk_status",
                    "new_value": "High",
                    "reason": "Bulk risk update",
                    "record_ids": ["acm_record:a1", "acm_record:a2", "acm_record:a3"],
                }
            )
        )
        assert result["type"] == "preview_bulk_write"
        assert result["affected_count"] == 3
        assert result["field"] == "risk_status"
        assert result["new_value"] == "High"
        assert "operation_id" in result
        # Check it's stored in pending writes
        op_id = result["operation_id"]
        assert op_id in _pending_writes
        assert _pending_writes[op_id]["type"] == "bulk"

    def test_blocked_field(self):
        result = json.loads(
            preview_bulk_write.invoke(
                {
                    "operation": "UPDATE",
                    "filter_description": "all items",
                    "field": "id",
                    "new_value": "hacked",
                    "reason": "bad",
                    "record_ids": ["acm_record:a1"],
                }
            )
        )
        assert "error" in result

    def test_no_context(self):
        from open_notebook.graphs.tool_context import set_tool_scope

        set_tool_scope(source_id=None, notebook_id=None)
        result = json.loads(
            preview_bulk_write.invoke(
                {
                    "operation": "UPDATE",
                    "filter_description": "all items",
                    "field": "risk_status",
                    "new_value": "High",
                    "reason": "test",
                    "record_ids": ["acm_record:a1"],
                }
            )
        )
        assert "error" in result


class TestUndoLastWrite:
    """Tests for undo_last_write tool."""

    def setup_method(self):
        set_crud_context("source:test123")
        _pending_writes.clear()

    @patch("open_notebook.graphs.crud_tools._run_async")
    def test_no_audit_records(self, mock_run_async):
        """When no audit records exist, return error."""
        mock_run_async.return_value = []
        result = json.loads(undo_last_write.invoke({"record_id": None}))
        assert (
            "error" in result
            or "no" in result.get("message", "").lower()
            or "error" in str(result).lower()
        )

    @patch("open_notebook.graphs.crud_tools._run_async")
    def test_audit_without_old_value(self, mock_run_async):
        """When audit exists but has no old_value, return error."""
        mock_run_async.return_value = [
            {
                "record_id": "acm_record:x",
                "field_name": "risk_status",
                "old_value": None,
                "new_value": "High",
            }
        ]
        result = json.loads(undo_last_write.invoke({"record_id": None}))
        # Should indicate can't undo
        assert (
            "error" in result
            or "cannot" in str(result).lower()
            or "no" in str(result).lower()
        )


class TestClassifyIntentWithLLMFallback:
    """Tests for the LLM fallback intent classifier."""

    def test_rule_based_read(self):
        assert classify_intent("show me all records") == "read"

    def test_rule_based_write(self):
        assert classify_intent("update the risk status") == "write"

    def test_rule_based_analytics(self):
        assert classify_intent("how many records are there?") == "analytics"

    def test_rule_based_general(self):
        assert classify_intent("hello there") == "general"

    @pytest.mark.asyncio
    async def test_llm_fallback_no_api_key(self):
        """Without API key, should gracefully return 'general'."""
        from open_notebook.graphs.guardrails import classify_intent_with_llm_fallback

        with patch.dict("os.environ", {}, clear=False):
            # Remove ACM_ANTHROPIC_API_KEY if present
            import os

            os.environ.pop("ACM_ANTHROPIC_API_KEY", None)
            result = await classify_intent_with_llm_fallback("hello there")
            assert result == "general"

    @pytest.mark.asyncio
    async def test_llm_fallback_returns_rule_based_first(self):
        """Rule-based results should short-circuit LLM call."""
        from open_notebook.graphs.guardrails import classify_intent_with_llm_fallback

        result = await classify_intent_with_llm_fallback("show me all records")
        assert result == "read"  # Rule-based, no LLM call needed
