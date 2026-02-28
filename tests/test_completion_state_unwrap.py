"""Tests for _unwrap_completion_state() and structured output resilience.

Tests the completionState envelope unwrapping utility and validates
the fallback paths work correctly for both single-building (legacy)
and multi-building (orchestrator) extraction.
"""

import pytest

from open_notebook.graphs.utils import _unwrap_completion_state


class TestUnwrapCompletionState:
    """Tests for the _unwrap_completion_state() utility."""

    def test_unwraps_standard_envelope(self):
        """Standard completionState envelope is unwrapped correctly."""
        envelope = {
            "completionState": "complete",
            "result": {"records": [{"room_name": "Kitchen"}], "stats": {}},
            "type": "Object",
        }
        result = _unwrap_completion_state(envelope)
        assert result == {"records": [{"room_name": "Kitchen"}], "stats": {}}

    def test_passthrough_normal_json(self):
        """Normal JSON without completionState passes through unchanged."""
        normal = {"records": [{"room_name": "Kitchen"}], "stats": {}}
        result = _unwrap_completion_state(normal)
        assert result == normal

    def test_passthrough_list(self):
        """List input passes through unchanged."""
        data = [{"room_name": "Kitchen"}]
        result = _unwrap_completion_state(data)
        assert result == data

    def test_passthrough_non_dict(self):
        """Non-dict input passes through unchanged."""
        assert _unwrap_completion_state("string") == "string"
        assert _unwrap_completion_state(42) == 42
        assert _unwrap_completion_state(None) is None

    def test_completionstate_without_result(self):
        """completionState present but no result key — pass through."""
        data = {"completionState": "complete", "type": "Object"}
        result = _unwrap_completion_state(data)
        assert result == data  # pass-through (safe fallback)

    def test_completionstate_with_non_dict_result(self):
        """completionState with non-dict result — pass through."""
        data = {
            "completionState": "complete",
            "result": "not a dict",
            "type": "Object",
        }
        result = _unwrap_completion_state(data)
        assert result == data  # pass-through (safe fallback)

    def test_empty_dict(self):
        """Empty dict passes through unchanged."""
        assert _unwrap_completion_state({}) == {}

    def test_nested_completionstate_not_unwrapped(self):
        """Nested completionState in result is not double-unwrapped."""
        envelope = {
            "completionState": "complete",
            "result": {
                "completionState": "inner",
                "result": {"data": "deep"},
            },
            "type": "Object",
        }
        result = _unwrap_completion_state(envelope)
        # Should unwrap outer only
        assert result == {"completionState": "inner", "result": {"data": "deep"}}

    def test_preserves_all_result_keys(self):
        """All keys in the result dict are preserved."""
        envelope = {
            "completionState": "complete",
            "result": {
                "records": [],
                "stats": {"total": 0},
                "data_issues": None,
                "extra_field": "preserved",
            },
            "type": "Object",
        }
        result = _unwrap_completion_state(envelope)
        assert "records" in result
        assert "stats" in result
        assert "data_issues" in result
        assert "extra_field" in result

    def test_unwraps_with_different_completionstate_value(self):
        """Envelope with non-'complete' completionState value still unwraps."""
        envelope = {
            "completionState": "partial",
            "result": {"records": []},
            "type": "Object",
        }
        result = _unwrap_completion_state(envelope)
        assert result == {"records": []}
