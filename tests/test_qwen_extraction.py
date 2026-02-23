"""Unit tests for Qwen2.5 extraction helpers.

Tests _is_qwen_model() detection and parse_json_response() parsing.
"""

import pytest


class TestIsQwenModel:
    """Test _is_qwen_model() helper function."""

    def _make_model(self, model_name=None, model=None):
        """Create a mock model object with optional attributes."""

        class MockModel:
            pass

        m = MockModel()
        if model_name is not None:
            m.model_name = model_name
        if model is not None:
            m.model = model
        return m

    def test_ollama_qwen25(self):
        from open_notebook.graphs.acm_extraction import _is_qwen_model

        model = self._make_model(model_name="qwen2.5:32b")
        assert _is_qwen_model(model) is True

    def test_openrouter_qwen25(self):
        from open_notebook.graphs.acm_extraction import _is_qwen_model

        model = self._make_model(model="qwen/qwen2.5-32b-instruct")
        assert _is_qwen_model(model) is True

    def test_qwen3_not_matched(self):
        from open_notebook.graphs.acm_extraction import _is_qwen_model

        model = self._make_model(model_name="qwen3:72b")
        assert _is_qwen_model(model) is False

    def test_claude_not_matched(self):
        from open_notebook.graphs.acm_extraction import _is_qwen_model

        model = self._make_model(model_name="claude-3-5-haiku-20241022")
        assert _is_qwen_model(model) is False

    def test_empty_model(self):
        from open_notebook.graphs.acm_extraction import _is_qwen_model

        model = self._make_model()
        assert _is_qwen_model(model) is False

    def test_model_attr_fallback(self):
        """When model_name is empty, falls back to model attr."""
        from open_notebook.graphs.acm_extraction import _is_qwen_model

        model = self._make_model(model_name="", model="qwen2.5:32b-instruct")
        assert _is_qwen_model(model) is True


class TestParseJsonResponse:
    """Test parse_json_response() utility function."""

    def test_fenced_json_block(self):
        from open_notebook.graphs.utils import parse_json_response

        text = 'Some preamble\n```json\n{"records": [], "status": "valid"}\n```\nSome suffix'
        result = parse_json_response(text)
        assert result == {"records": [], "status": "valid"}

    def test_fenced_without_json_label(self):
        from open_notebook.graphs.utils import parse_json_response

        text = '```\n{"records": [{"building_id": "B1"}], "status": "valid"}\n```'
        result = parse_json_response(text)
        assert result["records"][0]["building_id"] == "B1"

    def test_raw_json(self):
        from open_notebook.graphs.utils import parse_json_response

        text = '{"records": [], "status": "no_acm_data", "extraction_notes": null}'
        result = parse_json_response(text)
        assert result["status"] == "no_acm_data"

    def test_json_with_preamble(self):
        from open_notebook.graphs.utils import parse_json_response

        text = 'Here is the extraction result:\n{"records": [], "status": "valid"}'
        result = parse_json_response(text)
        assert result["status"] == "valid"

    def test_nested_json(self):
        from open_notebook.graphs.utils import parse_json_response

        text = '{"records": [{"building_id": "B1", "data_issues": []}], "status": "valid"}'
        result = parse_json_response(text)
        assert len(result["records"]) == 1

    def test_no_json_raises(self):
        from open_notebook.graphs.utils import parse_json_response

        with pytest.raises(ValueError, match="No JSON object found"):
            parse_json_response("This has no JSON content at all.")

    def test_empty_string_raises(self):
        from open_notebook.graphs.utils import parse_json_response

        with pytest.raises(ValueError, match="No JSON object found"):
            parse_json_response("")
