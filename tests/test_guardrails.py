"""Tests for the SurrealQL guardrails module."""

import pytest

from open_notebook.graphs.guardrails import (
    ALLOWED_ACM_FIELDS,
    ALLOWED_BUILDING_FIELDS,
    ALLOWED_READ_TABLES,
    ALLOWED_WRITE_TABLES,
    cap_results,
    classify_intent,
    validate_read_query,
    validate_write_operation,
)


class TestValidateReadQuery:
    """Tests for validate_read_query."""

    def test_valid_select(self):
        q = "SELECT * FROM acm_record WHERE source_id = $sid LIMIT 10;"
        result = validate_read_query(q)
        assert result.allowed is True
        assert result.sanitized_query.endswith(";")

    def test_valid_count(self):
        q = "SELECT count() as total FROM acm_record WHERE source_id = $sid GROUP ALL"
        result = validate_read_query(q)
        assert result.allowed is True

    def test_valid_distinct(self):
        q = "SELECT DISTINCT building_name FROM acm_record WHERE source_id = $sid"
        result = validate_read_query(q)
        assert result.allowed is True

    def test_block_update(self):
        q = "UPDATE acm_record SET risk_status = 'High' WHERE source_id = $sid"
        result = validate_read_query(q)
        assert result.allowed is False
        assert "SELECT" in result.reason

    def test_block_delete(self):
        q = "DELETE FROM acm_record WHERE source_id = $sid"
        result = validate_read_query(q)
        assert result.allowed is False

    def test_block_drop(self):
        q = "SELECT * FROM acm_record; DROP TABLE acm_record;"
        result = validate_read_query(q)
        assert result.allowed is False
        assert "DROP" in result.reason

    def test_block_remove(self):
        q = "SELECT * FROM acm_record; REMOVE TABLE acm_record;"
        result = validate_read_query(q)
        assert result.allowed is False

    def test_block_define(self):
        q = "DEFINE TABLE hacked SCHEMALESS;"
        result = validate_read_query(q)
        assert result.allowed is False

    def test_block_disallowed_table(self):
        q = "SELECT * FROM model WHERE id = $mid"
        result = validate_read_query(q)
        assert result.allowed is False
        assert "model" in result.reason

    def test_allow_all_read_tables(self):
        for table in ALLOWED_READ_TABLES:
            q = f"SELECT * FROM {table} WHERE source_id = $sid LIMIT 10"
            result = validate_read_query(q)
            assert result.allowed is True, f"Table {table} should be allowed"

    def test_warn_no_limit(self):
        q = "SELECT * FROM acm_record WHERE source_id = $sid"
        result = validate_read_query(q)
        assert result.allowed is True
        assert len(result.warnings) > 0
        assert "LIMIT" in result.warnings[0]

    def test_block_embedded_write_in_select(self):
        q = "SELECT * FROM acm_record WHERE source_id = $sid; INSERT INTO hacked {x: 1}"
        result = validate_read_query(q)
        assert result.allowed is False

    def test_sanitized_query_has_semicolon(self):
        q = "SELECT * FROM acm_record WHERE source_id = $sid LIMIT 10"
        result = validate_read_query(q)
        assert result.sanitized_query.endswith(";")


class TestValidateWriteOperation:
    """Tests for validate_write_operation."""

    def test_valid_update_acm(self):
        result = validate_write_operation("acm_record", "UPDATE", "risk_status")
        assert result.allowed is True

    def test_valid_update_building(self):
        result = validate_write_operation("building_record", "UPDATE", "building_name")
        assert result.allowed is True

    def test_valid_delete(self):
        result = validate_write_operation("acm_record", "DELETE")
        assert result.allowed is True

    def test_block_disallowed_table(self):
        result = validate_write_operation("source", "UPDATE", "title")
        assert result.allowed is False
        assert "source" in result.reason

    def test_block_disallowed_operation(self):
        result = validate_write_operation("acm_record", "DROP")
        assert result.allowed is False

    def test_block_disallowed_field_acm(self):
        result = validate_write_operation("acm_record", "UPDATE", "id")
        assert result.allowed is False
        assert "id" in result.reason

    def test_block_disallowed_field_building(self):
        result = validate_write_operation("building_record", "UPDATE", "source_id")
        assert result.allowed is False

    def test_all_acm_fields_allowed(self):
        for field in ALLOWED_ACM_FIELDS:
            result = validate_write_operation("acm_record", "UPDATE", field)
            assert result.allowed is True, f"ACM field {field} should be allowed"

    def test_all_building_fields_allowed(self):
        for field in ALLOWED_BUILDING_FIELDS:
            result = validate_write_operation("building_record", "UPDATE", field)
            assert result.allowed is True, f"Building field {field} should be allowed"


class TestCapResults:
    """Tests for cap_results."""

    def test_cap_at_max(self):
        rows = [{"id": str(i), "name": f"row_{i}"} for i in range(200)]
        capped = cap_results(rows, max_rows=50)
        assert len(capped) == 50

    def test_strips_embedding_fields(self):
        rows = [{"id": "1", "name": "test", "embedding": [0.1, 0.2], "embedding_text": "foo"}]
        capped = cap_results(rows)
        assert len(capped) == 1
        assert "embedding" not in capped[0]
        assert "embedding_text" not in capped[0]
        assert capped[0]["name"] == "test"

    def test_empty_input(self):
        assert cap_results([]) == []


class TestClassifyIntent:
    """Tests for classify_intent."""

    def test_read_intents(self):
        assert classify_intent("show me all buildings") == "read"
        assert classify_intent("find friable records") == "read"
        assert classify_intent("list records in Building A") == "read"
        assert classify_intent("which rooms have high risk?") == "read"
        assert classify_intent("what is the risk status of room 101?") == "read"

    def test_write_intents(self):
        assert classify_intent("update the risk status to High") == "write"
        assert classify_intent("change building name to Main Block") == "write"
        assert classify_intent("delete record acm_record:abc123") == "write"
        assert classify_intent("mark as friable") == "write"
        assert classify_intent("set no_access to true") == "write"

    def test_analytics_intents(self):
        assert classify_intent("how many records are there?") == "analytics"
        assert classify_intent("count all friable records") == "analytics"
        assert classify_intent("give me a summary of risk levels") == "analytics"
        assert classify_intent("what is the total number of buildings?") == "analytics"
        assert classify_intent("show me the breakdown by risk status") == "analytics"

    def test_general_intents(self):
        assert classify_intent("hello") == "general"
        assert classify_intent("thank you") == "general"
        assert classify_intent("what can you do?") == "read"  # "what" triggers read

    def test_empty_input(self):
        assert classify_intent("") == "general"
