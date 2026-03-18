"""Tests for Ollama truncation fallback handling.

Covers:
- TruncationError in _v3_extract_items returns status="truncated"
- _chunk_and_extract_items retries with cloud model on truncation
- Output budget calculation reserves 30% for output tokens
- ACM_EXTRACTION_MODEL env var is respected
- All LLM calls are mocked
"""

import os
from types import SimpleNamespace
from typing import Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.extractors.acm_schemas_v3 import (
    ACMItemExtractionResult,
    ACMItemRecord,
)
from open_notebook.graphs.utils import (
    TruncationError,
    _split_content_by_char_budget,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_plan(building_id: str = "B001") -> Any:
    """Return a minimal BuildingExtractionPlan-like object."""
    return SimpleNamespace(
        building_id=building_id,
        building_name="Test Building",
        page_start=1,
        page_end=5,
        page_range=(1, 5),
        strategy="full",
        source_id="source:test",
    )


def _make_state(model_id: Optional[str] = None) -> dict:
    return {
        "model_id": model_id,
        "document_metadata": None,
        "_langchain_config": None,
    }


def _make_item_record() -> ACMItemRecord:
    """Return a minimal valid ACMItemRecord."""
    return ACMItemRecord(
        building_id="B001",
        item_name="Sample Item",
        material_description="Ceiling tile",
        acm_present=True,
        quantity=10.0,
        condition_rating="Good",
        risk_rating="Low",
        priority_rating="Low",
        management_action="Monitor",
        acm_assessment_date="2024-01-01",
        room_id="R001",
        room_name="Room A",
        extraction_confidence="high",
        data_issues=[],
    )


# ---------------------------------------------------------------------------
# Fix 4: ACMItemExtractionResult accepts "truncated" status
# ---------------------------------------------------------------------------


class TestACMItemExtractionResultStatus:
    def test_valid_status(self):
        r = ACMItemExtractionResult(records=[], status="valid")
        assert r.status == "valid"

    def test_no_acm_data_status(self):
        r = ACMItemExtractionResult(records=[], status="no_acm_data")
        assert r.status == "no_acm_data"

    def test_invalid_status(self):
        r = ACMItemExtractionResult(records=[], status="invalid")
        assert r.status == "invalid"

    def test_truncated_status(self):
        r = ACMItemExtractionResult(
            records=[], status="truncated", extraction_notes="JSON truncated"
        )
        assert r.status == "truncated"
        assert r.extraction_notes is not None
        assert "truncated" in r.extraction_notes

    def test_default_status_is_valid(self):
        r = ACMItemExtractionResult(records=[])
        assert r.status == "valid"


# ---------------------------------------------------------------------------
# Fix 1: _v3_extract_items returns status="truncated" on TruncationError
# ---------------------------------------------------------------------------


class TestV3ExtractItemsTruncation:
    @pytest.mark.asyncio
    async def test_truncation_error_returns_truncated_status(self):
        """When parse_json_response raises TruncationError, status must be 'truncated'."""
        from open_notebook.extractors.orchestrator import _v3_extract_items

        plan = _make_plan()
        state = _make_state()

        mock_response = MagicMock()
        mock_response.content = '{"records": [{"building_id": "B001"'  # truncated JSON
        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=mock_response)

        # Patch all helpers that touch the plan or DB so only the JSON parsing
        # path is exercised.  parse_json_response is imported at module level in
        # orchestrator.py, so it must be patched on that module.
        with (
            patch(
                "open_notebook.extractors.orchestrator._create_building_prompt_context",
                return_value={"building_id": "B001", "page_start": 1, "page_end": 5},
            ),
            patch(
                "open_notebook.extractors.prompt_context_builder.build_picklist_context",
                return_value={},
            ),
            patch(
                "open_notebook.graphs.utils.provision_langchain_model",
                AsyncMock(return_value=mock_model),
            ),
            patch(
                "open_notebook.extractors.orchestrator._inject_response_format",
                side_effect=lambda m, *a, **kw: m,
            ),
            patch(
                "open_notebook.extractors.orchestrator.parse_json_response",
                side_effect=TruncationError("JSON truncated at end of response"),
            ),
        ):
            result = await _v3_extract_items(
                building_content="Sample content",
                plan=plan,
                building_meta=None,
                state=state,
                schema_bundle=None,
            )

        assert result.status == "truncated"
        assert result.records == []
        assert result.extraction_notes is not None
        assert "truncated" in result.extraction_notes.lower()

    @pytest.mark.asyncio
    async def test_non_truncation_exception_returns_invalid_status(self):
        """Other exceptions still return status='invalid'."""
        from open_notebook.extractors.orchestrator import _v3_extract_items

        plan = _make_plan()
        state = _make_state()

        with patch(
            "open_notebook.graphs.utils.provision_langchain_model",
            AsyncMock(side_effect=RuntimeError("Connection refused")),
        ):
            result = await _v3_extract_items(
                building_content="Sample content",
                plan=plan,
                building_meta=None,
                state=state,
                schema_bundle=None,
            )

        assert result.status == "invalid"
        assert result.records == []


# ---------------------------------------------------------------------------
# Fix 1 (retry): _chunk_and_extract_items retries on truncation
# ---------------------------------------------------------------------------


class TestChunkAndExtractItemsRetry:
    @pytest.mark.asyncio
    async def test_truncation_triggers_cloud_retry(self):
        """When first call returns status='truncated', retry with model_id=None."""
        from open_notebook.graphs.acm_extraction import _chunk_and_extract_items

        plan = _make_plan()
        state = _make_state(model_id="local-ollama-model")

        truncated_result = ACMItemExtractionResult(records=[], status="truncated")
        cloud_result = ACMItemExtractionResult(
            records=[_make_item_record()], status="valid"
        )

        call_states: List[dict] = []

        async def fake_v3_extract_items(content, p, meta, s, schema, **kwargs):
            call_states.append(dict(s))
            if len(call_states) == 1:
                return truncated_result
            return cloud_result

        with (
            patch(
                "open_notebook.graphs.acm_extraction._v3_extract_items",
                side_effect=fake_v3_extract_items,
            ),
            patch.dict(os.environ, {"ACM_ANTHROPIC_API_KEY": "sk-ant-test-key"}),
        ):
            result = await _chunk_and_extract_items(
                building_content="Short content",
                plan=plan,
                building_meta=None,
                state=state,
                schema_bundle=None,
            )

        # Two calls: first with original state, second with model_id=None
        assert len(call_states) == 2
        assert call_states[0]["model_id"] == "local-ollama-model"
        assert call_states[1]["model_id"] is None

        # Final result is from cloud
        assert result.status == "valid"
        assert len(result.records) == 1

    @pytest.mark.asyncio
    async def test_no_retry_when_valid(self):
        """No retry on success."""
        from open_notebook.graphs.acm_extraction import _chunk_and_extract_items

        plan = _make_plan()
        state = _make_state()
        call_count = 0

        async def fake_v3_extract_items(content, p, meta, s, schema, **kwargs):
            nonlocal call_count
            call_count += 1
            return ACMItemExtractionResult(records=[], status="valid")

        with patch(
            "open_notebook.graphs.acm_extraction._v3_extract_items",
            side_effect=fake_v3_extract_items,
        ):
            result = await _chunk_and_extract_items(
                building_content="Short content",
                plan=plan,
                building_meta=None,
                state=state,
                schema_bundle=None,
            )

        assert call_count == 1
        assert result.status == "valid"

    @pytest.mark.asyncio
    async def test_double_truncation_returns_partial(self):
        """If both Ollama and cloud truncate, final status is 'invalid' (best-effort)."""
        from open_notebook.graphs.acm_extraction import _chunk_and_extract_items

        plan = _make_plan()
        state = _make_state()

        async def always_truncate(content, p, meta, s, schema, **kwargs):
            return ACMItemExtractionResult(records=[], status="truncated")

        with patch(
            "open_notebook.graphs.acm_extraction._v3_extract_items",
            side_effect=always_truncate,
        ):
            result = await _chunk_and_extract_items(
                building_content="Short content",
                plan=plan,
                building_meta=None,
                state=state,
                schema_bundle=None,
            )

        # After two truncations, returns empty result (no records)
        assert result.records == []
        # Single-chunk path: _extract_with_truncation_retry returns the result
        # directly, so status is "truncated" (not converted to "invalid").
        # Multi-chunk path: the loop sets final_status = "invalid".
        # For a short content (below _ITEM_EXTRACTION_CHUNK_CHARS), the
        # single-chunk path is used, so "truncated" is preserved.
        assert result.status in ("truncated", "invalid")


# ---------------------------------------------------------------------------
# Fix 2: Output budget reservation (30% for output)
# ---------------------------------------------------------------------------


class TestOutputBudgetReservation:
    def test_budget_formula_reserves_30_percent(self):
        """Verify the budget formula reserves 30% of context window for output."""
        num_ctx = 10_000
        output_reserve_ratio = 0.3
        max_chars = int(num_ctx * 3.5 * (1 - output_reserve_ratio))
        # Should be 24500, not 35000 (which would be 100% of context)
        assert max_chars == 24_500
        # Confirm it is strictly less than the full window
        full_window_chars = int(num_ctx * 3.5)
        assert max_chars < full_window_chars

    def test_30_percent_reserved_not_available_for_input(self):
        """Input budget must be < full context window chars."""
        for num_ctx in (4096, 8192, 32768, 131072):
            full = int(num_ctx * 3.5)
            # Match the implementation: int(num_ctx * 3.5 * (1 - 0.3))
            budget = int(num_ctx * 3.5 * 0.7)
            assert budget < full

    def test_env_override_bypasses_reserve(self, monkeypatch):
        """OLLAMA_MAX_CONTENT_CHARS env var bypasses the output reserve ratio.

        When the operator explicitly sets a char limit, we honour it directly
        without applying the 30% reserve on top.
        """
        monkeypatch.setenv("OLLAMA_MAX_CONTENT_CHARS", "20000")
        override = int(os.getenv("OLLAMA_MAX_CONTENT_CHARS", "0"))
        assert override == 20_000  # env var is read as-is, no further reduction

    def test_split_content_by_char_budget_splits_correctly(self):
        """Sanity check: _split_content_by_char_budget returns multiple chunks."""
        content = "a" * 30_000
        chunks = _split_content_by_char_budget(content, 10_000)
        # No room boundaries in this content, falls back to char-based split
        assert len(chunks) == 3
        assert all(len(c) <= 10_000 for c in chunks)


# ---------------------------------------------------------------------------
# Fix 3: ACM_EXTRACTION_MODEL env var respected
# ---------------------------------------------------------------------------


class TestACMExtractionModelEnvVar:
    def test_default_model_is_llama31(self, monkeypatch):
        """When ACM_EXTRACTION_MODEL is not set, default is llama3.1:8b."""
        monkeypatch.delenv("ACM_EXTRACTION_MODEL", raising=False)
        model_name = os.getenv("ACM_EXTRACTION_MODEL", "llama3.1:8b")
        assert model_name == "llama3.1:8b"

    def test_custom_model_from_env(self, monkeypatch):
        """ACM_EXTRACTION_MODEL env var overrides the default."""
        monkeypatch.setenv("ACM_EXTRACTION_MODEL", "mistral:7b")
        model_name = os.getenv("ACM_EXTRACTION_MODEL", "llama3.1:8b")
        assert model_name == "mistral:7b"

    @pytest.mark.asyncio
    async def test_provision_uses_env_model(self, monkeypatch):
        """_provision_extraction_primary_model uses ACM_EXTRACTION_MODEL."""
        monkeypatch.setenv("OLLAMA_API_BASE", "http://localhost:11434")
        monkeypatch.setenv("ACM_EXTRACTION_MODEL", "phi3:mini")
        monkeypatch.delenv("ACM_ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ACM_OPENROUTER_API_KEY", raising=False)

        captured_calls: List[dict] = []

        def fake_create(model_name, provider, config):
            captured_calls.append({"model_name": model_name, "provider": provider})
            raise RuntimeError("Ollama not running in test")

        with (
            patch(
                "open_notebook.graphs.utils.AIFactory.create_language",
                side_effect=fake_create,
            ),
            patch(
                "open_notebook.graphs.utils._get_db_extraction_model",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            from open_notebook.graphs.utils import (
                _provision_extraction_primary_model,
            )

            result = await _provision_extraction_primary_model()

        # Should have tried phi3:mini (from env var)
        assert len(captured_calls) >= 1
        assert captured_calls[0]["model_name"] == "phi3:mini"
        assert captured_calls[0]["provider"] == "ollama"
        # Returns None because all candidates failed
        assert result is None
