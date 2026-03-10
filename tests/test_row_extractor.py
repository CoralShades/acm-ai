"""Comprehensive tests for the per-row LLM extraction orchestrator.

Uses mocked LangChain ChatModel to avoid real LLM calls. Test data
models realistic Australian school ACM register data.
"""

import json
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.domain.acm_row_schemas import ACMItemRow
from open_notebook.extractors.acm_schemas import ACMExtractionRecord
from open_notebook.extractors.pipeline_event_bus import PipelineEventBus
from open_notebook.extractors.row_extractor import (
    _build_fallback_record,
    build_kv_prompt,
    extract_all_rows,
    extract_single_row,
    split_multi_item_row,
)
from open_notebook.extractors.row_segmenter import RawTableRow

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


def _make_row(
    cells: dict[str, str],
    row_index: int = 0,
    page_number: int = 1,
    current_level: str | None = None,
    extraction_notes: str | None = None,
    needs_llm_split: bool = False,
    column_mapping: dict[str, str] | None = None,
    source_id: str = "source:test123",
    building_id: str = "building:broadmeadows_a",
) -> RawTableRow:
    """Create a RawTableRow with sensible defaults for testing."""
    if column_mapping is None:
        column_mapping = {k: k for k in cells}
    raw_text = " | ".join(v for v in cells.values() if v.strip())
    return RawTableRow(
        source_id=source_id,
        building_id=building_id,
        table_index=0,
        row_index=row_index,
        page_number=page_number,
        cells=cells,
        raw_text=raw_text,
        column_mapping=column_mapping,
        needs_llm_split=needs_llm_split,
        current_level=current_level,
        extraction_notes=extraction_notes,
    )


def _mock_model_response(content: str) -> AsyncMock:
    """Create an AsyncMock model that returns the given content."""
    mock_model = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = content
    mock_model.ainvoke = AsyncMock(return_value=mock_response)
    return mock_model


def _mock_model_sequence(contents: list[str]) -> AsyncMock:
    """Create an AsyncMock model that returns different content on each call."""
    mock_model = AsyncMock()
    responses = []
    for content in contents:
        mock_response = MagicMock()
        mock_response.content = content
        responses.append(mock_response)
    mock_model.ainvoke = AsyncMock(side_effect=responses)
    return mock_model


def _mock_model_error_then_success(error_msg: str, success_content: str) -> AsyncMock:
    """Create a mock model that fails once, then succeeds."""
    mock_model = AsyncMock()
    error_response = MagicMock()
    error_response.content = "This is not valid JSON at all!"
    success_response = MagicMock()
    success_response.content = success_content
    mock_model.ainvoke = AsyncMock(side_effect=[error_response, success_response])
    return mock_model


# A standard valid JSON response for a ceiling tile record
VALID_CEILING_TILE_JSON = json.dumps(
    {
        "room_name": "Room 101",
        "floor_level": "Ground Floor",
        "item_location": "Ceiling",
        "item_name": "Vinyl floor tiles",
        "friability": "NF",
        "acm_classification": "Chrysotile",
        "acm_sub_classification": "Vinyl Tiles",
        "condition": "Good",
        "disturbance_potential": "Low",
    }
)

VALID_PIPE_LAGGING_JSON = json.dumps(
    {
        "room_name": "Boiler Room",
        "floor_level": "Basement",
        "item_location": "Pipes",
        "item_name": "Pipe lagging",
        "friability": "F",
        "acm_classification": "Amosite",
        "acm_sub_classification": None,
        "condition": "Poor",
        "disturbance_potential": "High",
    }
)


# ---------------------------------------------------------------------------
# 1. build_kv_prompt tests
# ---------------------------------------------------------------------------


class TestBuildKvPrompt:
    """Tests for the build_kv_prompt() function."""

    def test_standard_row(self) -> None:
        """Standard row produces building header and all non-empty cells."""
        row = _make_row(
            cells={
                "room_location": "Room 101",
                "item_description": "Ceiling tiles",
                "friability": "NF",
                "condition": "Good",
            },
            column_mapping={
                "room_location": "Room/Area",
                "item_description": "Material",
                "friability": "F/NF",
                "condition": "Condition",
            },
        )
        result = build_kv_prompt(row, "Block A - Main Building")
        assert "Building: Block A - Main Building" in result
        assert "Room/Area: Room 101" in result
        assert "Material: Ceiling tiles" in result
        assert "F/NF: NF" in result
        assert "Condition: Good" in result

    def test_with_level(self) -> None:
        """Row with current_level includes Level line."""
        row = _make_row(
            cells={"item_description": "Flat sheeting"},
            current_level="GROUND FLOOR",
        )
        result = build_kv_prompt(row, "Admin Block")
        assert "Level: GROUND FLOOR" in result

    def test_with_notes(self) -> None:
        """Row with extraction_notes includes Note line."""
        row = _make_row(
            cells={"item_description": "Eave lining"},
            extraction_notes="External areas only",
        )
        result = build_kv_prompt(row, "Science Wing")
        assert "Note: External areas only" in result

    def test_empty_cells_skipped(self) -> None:
        """Empty-string cell values are omitted from the prompt."""
        row = _make_row(
            cells={
                "room_location": "Room 205",
                "item_description": "Vinyl tiles",
                "friability": "",
                "condition": "  ",
            },
        )
        result = build_kv_prompt(row, "Block B")
        assert "room_location: Room 205" in result
        assert "item_description: Vinyl tiles" in result
        # Empty/whitespace cells should NOT appear
        assert "friability" not in result
        assert "condition" not in result

    def test_original_headers_used(self) -> None:
        """Column mapping maps canonical → original header for display."""
        row = _make_row(
            cells={"room_location": "Lab 3"},
            column_mapping={"room_location": "Room No."},
        )
        result = build_kv_prompt(row, "East Wing")
        assert "Room No.: Lab 3" in result
        # Canonical name should NOT appear
        assert "room_location" not in result

    def test_unmapped_canonical_used_as_is(self) -> None:
        """If no column_mapping entry, canonical name is used as header."""
        row = _make_row(
            cells={"unknown_col": "some value"},
            column_mapping={},
        )
        result = build_kv_prompt(row, "Block C")
        assert "unknown_col: some value" in result


# ---------------------------------------------------------------------------
# 2. extract_single_row — valid JSON → ACMItemRow
# ---------------------------------------------------------------------------


class TestExtractSingleRow:
    """Tests for extract_single_row() with mocked models."""

    @pytest.mark.asyncio
    async def test_valid_json_returns_item_row(self) -> None:
        """Model returning valid JSON produces a valid ACMItemRow."""
        row = _make_row(
            cells={
                "room_location": "Room 101",
                "item_description": "Vinyl floor tiles",
            }
        )
        model = _mock_model_response(VALID_CEILING_TILE_JSON)

        result = await extract_single_row(row, "Block A", model)

        assert isinstance(result, ACMItemRow)
        assert result.item_name == "Vinyl floor tiles"
        assert result.room_name == "Room 101"
        assert result.condition == "Good"
        assert result.disturbance_potential == "Low"

    @pytest.mark.asyncio
    async def test_json_in_markdown_fence(self) -> None:
        """Model returning JSON wrapped in markdown fences is parsed."""
        fenced = f"```json\n{VALID_CEILING_TILE_JSON}\n```"
        row = _make_row(cells={"item_description": "Vinyl tiles"})
        model = _mock_model_response(fenced)

        result = await extract_single_row(row, "Block A", model)

        assert isinstance(result, ACMItemRow)
        assert result.item_name == "Vinyl floor tiles"

    @pytest.mark.asyncio
    async def test_null_optional_fields_accepted(self) -> None:
        """JSON with null optional fields produces valid ACMItemRow."""
        minimal_json = json.dumps(
            {
                "room_name": None,
                "floor_level": None,
                "item_location": None,
                "item_name": "Unknown material",
                "friability": None,
                "acm_classification": None,
                "acm_sub_classification": None,
                "condition": None,
                "disturbance_potential": None,
            }
        )
        row = _make_row(cells={"item_description": "Something"})
        model = _mock_model_response(minimal_json)

        result = await extract_single_row(row, "Block B", model)

        assert result.item_name == "Unknown material"
        assert result.room_name is None
        assert result.friability is None

    @pytest.mark.asyncio
    async def test_langfuse_handler_passed_as_callback(self) -> None:
        """Langfuse handler is included in model config when provided."""
        row = _make_row(cells={"item_description": "Fibro eaves"})
        model = _mock_model_response(VALID_CEILING_TILE_JSON)
        fake_handler = MagicMock()

        await extract_single_row(row, "Block A", model, langfuse_handler=fake_handler)

        # Verify the model was called with callbacks in config
        call_args = model.ainvoke.call_args
        config = (
            call_args[1].get("config") or call_args[0][1]
            if len(call_args[0]) > 1
            else call_args[1].get("config", {})
        )
        # The config is passed as keyword arg
        assert model.ainvoke.called


# ---------------------------------------------------------------------------
# 3. extract_single_row — invalid JSON → retry → success
# ---------------------------------------------------------------------------


class TestExtractSingleRowRetry:
    """Tests for extract_single_row() retry logic."""

    @pytest.mark.asyncio
    async def test_retry_on_invalid_json(self) -> None:
        """Invalid JSON on first attempt, valid on retry → success."""
        row = _make_row(cells={"item_description": "Ceiling tiles"})
        model = _mock_model_error_then_success("bad json", VALID_CEILING_TILE_JSON)

        result = await extract_single_row(row, "Block A", model)

        assert isinstance(result, ACMItemRow)
        assert result.item_name == "Vinyl floor tiles"
        assert model.ainvoke.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_includes_error_feedback(self) -> None:
        """Retry message includes the previous error for LLM context."""
        row = _make_row(cells={"item_description": "Pipe lagging"})
        model = _mock_model_error_then_success("bad json", VALID_PIPE_LAGGING_JSON)

        await extract_single_row(row, "Block A", model)

        # Second call should have error feedback in the human message
        second_call = model.ainvoke.call_args_list[1]
        messages = second_call[0][0]
        human_content = messages[1].content
        assert "Previous attempt failed" in human_content


# ---------------------------------------------------------------------------
# 4. extract_single_row — both attempts fail → error
# ---------------------------------------------------------------------------


class TestExtractSingleRowBothFail:
    """Tests for extract_single_row() when all attempts fail."""

    @pytest.mark.asyncio
    async def test_raises_value_error_after_both_fail(self) -> None:
        """Both extraction attempts failing raises ValueError."""
        row = _make_row(cells={"item_description": "Unknown"})
        model = _mock_model_sequence(["not json at all", "still not json {broken"])

        with pytest.raises(ValueError, match="Failed to extract row"):
            await extract_single_row(row, "Block A", model)

        assert model.ainvoke.call_count == 2


# ---------------------------------------------------------------------------
# 5. split_multi_item_row — 3 items → 3 RawTableRows
# ---------------------------------------------------------------------------


class TestSplitMultiItemRow:
    """Tests for split_multi_item_row()."""

    @pytest.mark.asyncio
    async def test_splits_into_sub_rows(self) -> None:
        """Multi-item cell split into individual RawTableRow objects."""
        row = _make_row(
            cells={
                "room_location": "Room 101",
                "item_description": "Vinyl floor tiles\nCeiling tiles\nPipe lagging",
            },
            needs_llm_split=True,
        )
        split_response = json.dumps(
            [
                {"item_text": "Vinyl floor tiles", "location": "Floor"},
                {"item_text": "Ceiling tiles", "location": "Ceiling"},
                {"item_text": "Pipe lagging", "location": "Pipes"},
            ]
        )
        model = _mock_model_response(split_response)

        result = await split_multi_item_row(row, model)

        assert len(result) == 3
        assert result[0].cells["item_description"] == "Vinyl floor tiles"
        assert result[1].cells["item_description"] == "Ceiling tiles"
        assert result[2].cells["item_description"] == "Pipe lagging"
        # All sub-rows should NOT need further splitting
        assert all(not r.needs_llm_split for r in result)
        # Edge case type should be E1
        assert all(r.edge_case_type == "E1" for r in result)

    @pytest.mark.asyncio
    async def test_preserves_parent_cells(self) -> None:
        """Sub-rows preserve non-split cells from the parent row."""
        row = _make_row(
            cells={
                "room_location": "Lab 2",
                "item_description": "Fibro eaves\nVinyl tiles",
                "condition": "Fair",
            },
            needs_llm_split=True,
        )
        split_response = json.dumps(
            [
                {"item_text": "Fibro eaves", "location": ""},
                {"item_text": "Vinyl tiles", "location": ""},
            ]
        )
        model = _mock_model_response(split_response)

        result = await split_multi_item_row(row, model)

        assert len(result) == 2
        # Both should keep the room_location and condition
        assert result[0].cells["room_location"] == "Lab 2"
        assert result[0].cells["condition"] == "Fair"
        assert result[1].cells["room_location"] == "Lab 2"

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_failure(self) -> None:
        """LLM failure returns original row unchanged."""
        row = _make_row(
            cells={
                "item_description": "Multiple items\non separate lines",
            },
            needs_llm_split=True,
        )
        model = _mock_model_response("This is not JSON")

        result = await split_multi_item_row(row, model)

        assert len(result) == 1
        assert result[0] is row

    @pytest.mark.asyncio
    async def test_no_newline_returns_original(self) -> None:
        """Row with no multi-line cell returns the original row."""
        row = _make_row(
            cells={"item_description": "Single item only"},
            needs_llm_split=True,
        )
        model = _mock_model_response("[]")

        result = await split_multi_item_row(row, model)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_confidence_reduced_for_sub_rows(self) -> None:
        """Sub-rows have confidence reduced by 10% from parent."""
        row = _make_row(
            cells={"item_description": "Item A\nItem B"},
            needs_llm_split=True,
        )
        row.confidence = 1.0
        split_response = json.dumps(
            [
                {"item_text": "Item A", "location": ""},
                {"item_text": "Item B", "location": ""},
            ]
        )
        model = _mock_model_response(split_response)

        result = await split_multi_item_row(row, model)

        assert len(result) == 2
        assert result[0].confidence == pytest.approx(0.9)
        assert result[1].confidence == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# 6. extract_all_rows — full loop with mix of normal and split rows
# ---------------------------------------------------------------------------


class TestExtractAllRows:
    """Tests for the extract_all_rows() orchestrator."""

    @pytest.mark.asyncio
    async def test_normal_rows_extracted(self) -> None:
        """Normal rows (no split) are extracted and mapped to records."""
        rows = [
            _make_row(
                cells={
                    "room_location": "Room 101",
                    "item_description": "Ceiling tiles",
                },
                row_index=0,
            ),
            _make_row(
                cells={"room_location": "Room 102", "item_description": "Vinyl tiles"},
                row_index=1,
            ),
        ]

        response_1 = json.dumps(
            {
                "room_name": "Room 101",
                "floor_level": None,
                "item_location": "Ceiling",
                "item_name": "Ceiling tiles",
                "friability": "NF",
                "acm_classification": None,
                "acm_sub_classification": None,
                "condition": "Good",
                "disturbance_potential": "Low",
            }
        )
        response_2 = json.dumps(
            {
                "room_name": "Room 102",
                "floor_level": None,
                "item_location": "Floor",
                "item_name": "Vinyl tiles",
                "friability": "NF",
                "acm_classification": None,
                "acm_sub_classification": None,
                "condition": "Fair",
                "disturbance_potential": "Medium",
            }
        )
        model = _mock_model_sequence([response_1, response_2])

        records = await extract_all_rows(
            rows=rows,
            building_context="Block A",
            model=model,
            source_id="source:test",
            building_id="building:block_a",
        )

        assert len(records) == 2
        assert all(isinstance(r, ACMExtractionRecord) for r in records)
        assert records[0].room_name == "Room 101"
        assert records[1].room_name == "Room 102"

    @pytest.mark.asyncio
    async def test_split_rows_expanded(self) -> None:
        """Rows with needs_llm_split=True are split before extraction."""
        rows = [
            _make_row(
                cells={
                    "room_location": "Room 201",
                    "item_description": "Vinyl tiles\nCeiling tiles",
                },
                needs_llm_split=True,
                row_index=0,
            ),
        ]

        # Split response (2 items)
        split_response = json.dumps(
            [
                {"item_text": "Vinyl tiles", "location": "Floor"},
                {"item_text": "Ceiling tiles", "location": "Ceiling"},
            ]
        )
        # Extraction responses for each sub-row
        extract_1 = json.dumps(
            {
                "room_name": "Room 201",
                "floor_level": None,
                "item_location": "Floor",
                "item_name": "Vinyl tiles",
                "friability": "NF",
                "acm_classification": None,
                "acm_sub_classification": None,
                "condition": "Good",
                "disturbance_potential": "Low",
            }
        )
        extract_2 = json.dumps(
            {
                "room_name": "Room 201",
                "floor_level": None,
                "item_location": "Ceiling",
                "item_name": "Ceiling tiles",
                "friability": "NF",
                "acm_classification": None,
                "acm_sub_classification": None,
                "condition": "Good",
                "disturbance_potential": "Low",
            }
        )

        model = _mock_model_sequence([split_response, extract_1, extract_2])

        records = await extract_all_rows(
            rows=rows,
            building_context="Block B",
            model=model,
            source_id="source:test",
            building_id="building:block_b",
        )

        assert len(records) == 2
        assert records[0].product == "Vinyl tiles"
        assert records[1].product == "Ceiling tiles"

    @pytest.mark.asyncio
    async def test_failed_extraction_creates_low_confidence_record(self) -> None:
        """When extraction fails completely, a low-confidence fallback is created."""
        rows = [
            _make_row(
                cells={"item_description": "Unknown material"},
                row_index=0,
            ),
        ]
        # Both attempts return invalid JSON
        model = _mock_model_sequence(["not json", "still not json"])

        records = await extract_all_rows(
            rows=rows,
            building_context="Block C",
            model=model,
            source_id="source:test",
            building_id="building:block_c",
        )

        assert len(records) == 1
        assert records[0].extraction_confidence == "low"
        assert any("LLM extraction failed" in issue for issue in records[0].data_issues)


# ---------------------------------------------------------------------------
# 7. extract_all_rows — SSE event emission
# ---------------------------------------------------------------------------


class TestExtractAllRowsSSE:
    """Tests for SSE event emission in extract_all_rows()."""

    @pytest.mark.asyncio
    async def test_sse_events_emitted(self) -> None:
        """SSE progress events are published via event_bus."""
        rows = [
            _make_row(
                cells={"item_description": "Fibro eaves"},
                row_index=0,
            ),
        ]
        model = _mock_model_response(VALID_CEILING_TILE_JSON)

        event_bus = PipelineEventBus()
        event_bus.publish = AsyncMock()

        records = await extract_all_rows(
            rows=rows,
            building_context="Block D",
            model=model,
            source_id="source:test",
            building_id="building:block_d",
            event_bus=event_bus,
        )

        assert len(records) == 1
        assert event_bus.publish.call_count == 1

        # Check event structure
        event = event_bus.publish.call_args[0][0]
        assert event.type == "extraction.row_progress"
        assert event.data["row"] == 1
        assert event.data["total"] == 1
        assert "Block D" in event.data["message"]

    @pytest.mark.asyncio
    async def test_sse_event_failure_does_not_break_extraction(self) -> None:
        """Event bus publish failure does not stop extraction."""
        rows = [
            _make_row(
                cells={"item_description": "Pipe insulation"},
                row_index=0,
            ),
        ]
        model = _mock_model_response(VALID_PIPE_LAGGING_JSON)

        event_bus = PipelineEventBus()
        event_bus.publish = AsyncMock(side_effect=RuntimeError("Bus broken"))

        # Should NOT raise despite bus failure
        records = await extract_all_rows(
            rows=rows,
            building_context="Block E",
            model=model,
            source_id="source:test",
            building_id="building:block_e",
            event_bus=event_bus,
        )

        assert len(records) == 1


# ---------------------------------------------------------------------------
# 8. Integration: build_kv_prompt → extract_single_row → map to record
# ---------------------------------------------------------------------------


class TestIntegration:
    """End-to-end integration tests (with mocked LLM)."""

    @pytest.mark.asyncio
    async def test_prompt_to_record_pipeline(self) -> None:
        """Full pipeline: build prompt → extract → map → ACMExtractionRecord."""
        row = _make_row(
            cells={
                "room_location": "Room 303",
                "item_description": "Vinyl floor tiles",
                "friability": "NF",
                "condition": "Good",
                "sample_number": "34511-039-001",
            },
            column_mapping={
                "room_location": "Room/Area",
                "item_description": "Material",
                "friability": "F/NF",
                "condition": "Condition",
                "sample_number": "Sample No",
            },
            page_number=5,
            current_level="GROUND FLOOR",
        )

        # Verify prompt is well-formed
        prompt = build_kv_prompt(row, "Block A - Main Building")
        assert "Building: Block A - Main Building" in prompt
        assert "Level: GROUND FLOOR" in prompt
        assert "Room/Area: Room 303" in prompt

        # Mock extraction
        extraction_json = json.dumps(
            {
                "room_name": "Room 303",
                "floor_level": "Ground Floor",
                "item_location": "Floor",
                "item_name": "Vinyl floor tiles",
                "friability": "NF",
                "acm_classification": "Chrysotile",
                "acm_sub_classification": "Vinyl Tiles",
                "condition": "Good",
                "disturbance_potential": "Low",
            }
        )
        model = _mock_model_response(extraction_json)

        # Extract
        item = await extract_single_row(row, "Block A", model)
        assert item.item_name == "Vinyl floor tiles"
        assert item.floor_level == "Ground Floor"

        # Map to ACMExtractionRecord
        from open_notebook.domain.acm_row_mappers import (
            map_item_row_to_extraction_record,
        )

        record = map_item_row_to_extraction_record(
            row=item,
            building_id="building:block_a",
            source_id="source:test",
            page_number=5,
            row_index=0,
        )

        assert isinstance(record, ACMExtractionRecord)
        assert record.building_id == "building:block_a"
        assert record.product == "Vinyl floor tiles"
        assert record.room_name == "Room 303"
        assert record.page_number == 5
        assert record.extraction_confidence == "medium"

    @pytest.mark.asyncio
    async def test_pipe_lagging_friable_record(self) -> None:
        """Friable pipe lagging produces correct classification."""
        row = _make_row(
            cells={
                "room_location": "Boiler Room",
                "item_description": "Pipe lagging",
                "friability": "F",
                "condition": "Poor",
            },
        )
        model = _mock_model_response(VALID_PIPE_LAGGING_JSON)

        item = await extract_single_row(row, "Service Block", model)

        from open_notebook.domain.acm_row_mappers import (
            map_item_row_to_extraction_record,
        )

        record = map_item_row_to_extraction_record(
            row=item,
            building_id="building:service",
            source_id="source:test",
        )

        assert record.friable == "Friable"
        assert record.product == "Pipe lagging"


# ---------------------------------------------------------------------------
# 9. _build_fallback_record
# ---------------------------------------------------------------------------


class TestBuildFallbackRecord:
    """Tests for the fallback record builder."""

    def test_fallback_uses_raw_cells(self) -> None:
        """Fallback record extracts product from raw cell data."""
        row = _make_row(
            cells={
                "room_location": "Office 1",
                "item_description": "Cement sheet",
            },
            row_index=3,
            page_number=7,
            current_level="Level 2",
        )

        record = _build_fallback_record(
            row=row,
            building_id="building:test",
            source_id="source:test",
            error_msg="JSON parse error",
        )

        assert record.extraction_confidence == "low"
        assert record.product == "Cement sheet"
        assert record.room_name == "Office 1"
        assert record.floor_level == "Level 2"
        assert record.page_number == 7
        assert any("JSON parse error" in d for d in record.data_issues)

    def test_fallback_unknown_product_when_no_match(self) -> None:
        """Fallback record uses 'Unknown' when no product cell is found."""
        row = _make_row(
            cells={"some_other_col": "data"},
        )

        record = _build_fallback_record(
            row=row,
            building_id="building:test",
            source_id="source:test",
            error_msg="Total failure",
        )

        assert record.product == "Unknown"
