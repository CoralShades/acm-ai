"""E29-S1: Comprehensive tests for parse_json_response() resilient parser.

Covers AC-1 through AC-5:
  AC-1: Markdown fence stripping
  AC-2: Preamble/suffix handling
  AC-3: Multi-block largest-object selection
  AC-4: TruncationError on incomplete JSON
  AC-5: Backward compatibility with existing patterns
"""

import pytest

from open_notebook.graphs.utils import TruncationError, parse_json_response

# ---------------------------------------------------------------------------
# AC-1: Markdown fence stripping
# ---------------------------------------------------------------------------


class TestFenceStripping:
    """AC-1: Markdown fences stripped before brace-depth scan."""

    def test_fenced_json_simple(self):
        text = '```json\n{"a": 1}\n```'
        assert parse_json_response(text) == {"a": 1}

    def test_fenced_json_with_surrounding_text(self):
        text = 'Some preamble\n```json\n{"records": [], "status": "valid"}\n```\nSome suffix'
        assert parse_json_response(text) == {"records": [], "status": "valid"}

    def test_fenced_without_json_label(self):
        text = '```\n{"records": [{"building_id": "B1"}], "status": "valid"}\n```'
        result = parse_json_response(text)
        assert result["records"][0]["building_id"] == "B1"

    def test_fenced_nested_json(self):
        """Regression: old regex used non-greedy {.*?} which failed on nested objects."""
        text = '```json\n{"a": {"b": {"c": 1}}, "d": 2}\n```'
        result = parse_json_response(text)
        assert result == {"a": {"b": {"c": 1}}, "d": 2}

    def test_fenced_json_uppercase_label(self):
        text = '```JSON\n{"key": "value"}\n```'
        assert parse_json_response(text) == {"key": "value"}

    def test_fenced_multiline_json(self):
        text = '```json\n{\n  "records": [\n    {"id": 1},\n    {"id": 2}\n  ],\n  "status": "valid"\n}\n```'
        result = parse_json_response(text)
        assert len(result["records"]) == 2


# ---------------------------------------------------------------------------
# AC-2: Preamble/suffix handling
# ---------------------------------------------------------------------------


class TestPreambleHandling:
    """AC-2: Conversational preamble does not affect extraction."""

    def test_preamble_before_json(self):
        text = 'Here is the extraction result:\n{"records": [], "status": "valid"}'
        assert parse_json_response(text)["status"] == "valid"

    def test_preamble_and_suffix(self):
        text = (
            "The output is:\n\n"
            '{"records": [{"a": 1}], "status": "valid"}\n\n'
            "Hope that helps!"
        )
        result = parse_json_response(text)
        assert result["status"] == "valid"
        assert len(result["records"]) == 1

    def test_multiline_preamble(self):
        text = (
            "I've analyzed the document carefully.\n"
            "The ACM register contains the following data.\n"
            "Please find the extracted records below:\n\n"
            '{"records": [], "status": "no_acm_data"}'
        )
        assert parse_json_response(text)["status"] == "no_acm_data"

    def test_preamble_with_colon_and_newlines(self):
        text = 'Based on the document:\n\n\n{"key": "val"}'
        assert parse_json_response(text) == {"key": "val"}


# ---------------------------------------------------------------------------
# AC-3: Multi-block selection (largest valid object)
# ---------------------------------------------------------------------------


class TestMultiBlock:
    """AC-3: Multiple JSON blocks select largest valid complete object."""

    def test_two_blocks_returns_larger(self):
        small = '{"a": 1}'
        large = '{"records": [{"building_id": "B1"}, {"building_id": "B2"}], "status": "valid"}'
        text = f"First: {small}\nSecond: {large}"
        result = parse_json_response(text)
        assert "records" in result
        assert len(result["records"]) == 2

    def test_three_blocks_returns_largest(self):
        tiny = '{"x": 1}'
        medium = '{"a": 1, "b": 2, "c": 3}'
        large = '{"records": [{"id": 1}, {"id": 2}, {"id": 3}], "status": "valid", "notes": "test"}'
        text = f"{tiny}\n{medium}\n{large}"
        result = parse_json_response(text)
        assert "records" in result
        assert result["status"] == "valid"

    def test_valid_and_invalid_returns_valid(self):
        """One parseable + one malformed → returns the valid one."""
        valid = '{"records": [], "status": "valid"}'
        # Invalid: has a trailing comma (not valid JSON)
        invalid_json = '{"records": [{"a": 1,}]}'
        text = f"{invalid_json}\n{valid}"
        result = parse_json_response(text)
        assert result["status"] == "valid"

    def test_largest_by_raw_length(self):
        """Selection is by raw string length, not key count."""
        short_keys = '{"a": 1, "b": 2}'
        long_value = (
            '{"x": "this is a much longer string value that makes the object bigger"}'
        )
        text = f"{short_keys}\n{long_value}"
        result = parse_json_response(text)
        assert "x" in result


# ---------------------------------------------------------------------------
# AC-4: Truncation detection
# ---------------------------------------------------------------------------


class TestTruncation:
    """AC-4: Truncated JSON raises explicit TruncationError."""

    def test_truncated_array(self):
        text = '{"records": [{"a": 1}, {"b": 2'
        with pytest.raises(TruncationError, match="truncated"):
            parse_json_response(text)

    def test_truncated_nested(self):
        text = '{"records": [{"a": 1}, {"b":'
        with pytest.raises(TruncationError, match="truncated"):
            parse_json_response(text)

    def test_truncated_mid_key(self):
        text = '{"records": [{"building_id": "B1"}, {"building_i'
        with pytest.raises(TruncationError, match="truncated"):
            parse_json_response(text)

    def test_truncation_error_is_value_error_subclass(self):
        """TruncationError must be a ValueError subclass for backward-compat."""
        assert issubclass(TruncationError, ValueError)

    def test_truncation_error_caught_by_value_error(self):
        """Callers using except ValueError must still catch TruncationError."""
        text = '{"records": [{"a": 1}, {"b": 2'
        with pytest.raises(ValueError):
            parse_json_response(text)

    def test_complete_plus_truncated_returns_complete(self):
        """If there's a valid complete object AND a truncated one, return the valid one."""
        complete = '{"status": "valid", "records": []}'
        truncated = '{"partial": [{"a": 1}, {"b":'
        text = f"{complete}\n{truncated}"
        result = parse_json_response(text)
        assert result["status"] == "valid"


# ---------------------------------------------------------------------------
# AC-5: Backward compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompat:
    """AC-5: All existing test_qwen_extraction.py patterns still pass."""

    def test_fenced_json_block(self):
        """Mirrors test_qwen_extraction.py::test_fenced_json_block."""
        text = 'Some preamble\n```json\n{"records": [], "status": "valid"}\n```\nSome suffix'
        result = parse_json_response(text)
        assert result == {"records": [], "status": "valid"}

    def test_fenced_without_json_label(self):
        """Mirrors test_qwen_extraction.py::test_fenced_without_json_label."""
        text = '```\n{"records": [{"building_id": "B1"}], "status": "valid"}\n```'
        result = parse_json_response(text)
        assert result["records"][0]["building_id"] == "B1"

    def test_raw_json(self):
        """Mirrors test_qwen_extraction.py::test_raw_json."""
        text = '{"records": [], "status": "no_acm_data", "extraction_notes": null}'
        result = parse_json_response(text)
        assert result["status"] == "no_acm_data"

    def test_json_with_preamble(self):
        """Mirrors test_qwen_extraction.py::test_json_with_preamble."""
        text = 'Here is the extraction result:\n{"records": [], "status": "valid"}'
        result = parse_json_response(text)
        assert result["status"] == "valid"

    def test_nested_json(self):
        """Mirrors test_qwen_extraction.py::test_nested_json."""
        text = (
            '{"records": [{"building_id": "B1", "data_issues": []}], "status": "valid"}'
        )
        result = parse_json_response(text)
        assert len(result["records"]) == 1

    def test_no_json_raises(self):
        """Mirrors test_qwen_extraction.py::test_no_json_raises."""
        with pytest.raises(ValueError, match="No JSON object found"):
            parse_json_response("This has no JSON content at all.")

    def test_empty_string_raises(self):
        """Mirrors test_qwen_extraction.py::test_empty_string_raises."""
        with pytest.raises(ValueError, match="No JSON object found"):
            parse_json_response("")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Additional edge cases for robustness."""

    def test_json_with_braces_in_strings(self):
        """Braces inside JSON string values must not confuse the scanner."""
        text = '{"template": "use {name} for {purpose}", "count": 1}'
        result = parse_json_response(text)
        assert result["template"] == "use {name} for {purpose}"
        assert result["count"] == 1

    def test_json_with_escaped_quotes_in_strings(self):
        """Escaped quotes inside strings must not break scanning."""
        text = '{"msg": "He said \\"hello\\"", "ok": true}'
        result = parse_json_response(text)
        assert result["msg"] == 'He said "hello"'
        assert result["ok"] is True

    def test_unicode_values(self):
        text = '{"name": "Caf\\u00e9", "emoji": "\\ud83d\\ude00"}'
        result = parse_json_response(text)
        assert result["name"] == "Caf\u00e9"

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="No JSON object found"):
            parse_json_response("   \n\t  \n  ")

    def test_just_braces_invalid_json(self):
        """A single pair of braces with invalid content inside."""
        text = "{not valid json at all}"
        # Brace scan extracts it, json.loads fails, no valid objects → ValueError
        with pytest.raises(ValueError, match="No JSON object found"):
            parse_json_response(text)

    def test_deeply_nested(self):
        text = '{"a": {"b": {"c": {"d": {"e": 5}}}}}'
        result = parse_json_response(text)
        assert result["a"]["b"]["c"]["d"]["e"] == 5

    def test_json_with_array_values(self):
        """JSON objects containing arrays should work fine."""
        text = '{"items": [1, 2, 3], "nested": [{"x": 1}, {"x": 2}]}'
        result = parse_json_response(text)
        assert result["items"] == [1, 2, 3]
        assert len(result["nested"]) == 2
