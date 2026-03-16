"""Integration tests for per-row extraction wired into the LangGraph pipeline.

Tests the Phase 3 integration: ACM_ITEM_EXTRACTION_MODE env var,
per-row vs bulk path routing, fallback behavior, and recovery node gating.

All DB calls, LLM calls, and external dependencies are mocked.
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.extractors.acm_schemas import ACMExtractionRecord
from open_notebook.extractors.row_segmenter import RawTableRow

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_raw_table_row(
    building_id: str = "B1",
    source_id: str = "source:test",
    row_index: int = 0,
    page_number: int = 1,
) -> RawTableRow:
    """Create a minimal RawTableRow for testing."""
    return RawTableRow(
        source_id=source_id,
        building_id=building_id,
        table_index=0,
        row_index=row_index,
        page_number=page_number,
        cells={"room_location": "Room 1", "item_description": "Vinyl Tiles"},
        raw_text="Room 1 | Vinyl Tiles",
    )


def _make_extraction_record(
    building_id: str = "B1",
    product: str = "Vinyl Tiles",
) -> ACMExtractionRecord:
    """Create a minimal ACMExtractionRecord for testing."""
    return ACMExtractionRecord(
        building_id=building_id,
        product=product,
        result="Unknown",
    )


def _make_building_meta_entry(
    building_id: str = "B1",
    name: str = "Building A",
    page_start: int = 1,
    page_end: int = 5,
):
    """Create a mock building inventory entry."""
    entry = MagicMock()
    entry.building_id = building_id
    entry.name = name
    entry.page_start = page_start
    entry.page_end = page_end
    return entry


def _make_mock_source(source_id: str = "source:test123", full_text: str = "Page 1"):
    """Create a mock Source object."""
    source = MagicMock()
    source.id = source_id
    source.full_text = full_text
    return source


def _make_mock_inventory(buildings=None):
    """Create a mock BuildingInventory."""
    inv = MagicMock()
    inv.buildings = buildings or [_make_building_meta_entry()]
    return inv


def _make_base_state(source=None, inventory=None):
    """Build minimal state dict for extract_items_node."""
    return {
        "source": source or _make_mock_source(),
        "building_inventory": inventory or _make_mock_inventory(),
        "schema_bundle": None,
        "building_meta_cache": {},
        "model_id": None,
        "operation_id": None,
        "_langchain_config": None,
    }


# ---------------------------------------------------------------------------
# Test: Per-row mode calls segment_multiple_tables + extract_all_rows
# ---------------------------------------------------------------------------


class TestPerRowPath:
    """Tests that per_row mode invokes row segmenter + row extractor."""

    @pytest.mark.asyncio
    async def test_per_row_mode_uses_segmenter_and_extractor(self):
        """When docling_document_json is available, per-row path is taken."""
        mock_rows = [_make_raw_table_row()]
        mock_records = [_make_extraction_record()]

        with (
            patch.dict(os.environ, {"ACM_ITEM_EXTRACTION_MODE": "per_row"}),
            patch(
                "open_notebook.graphs.acm_extraction._extract_building_content",
                return_value="Page 1 content",
            ),
            patch(
                "open_notebook.graphs.acm_extraction._get_docling_tables",
                new_callable=AsyncMock,
                return_value=[
                    {"docling_document_json": {"table_cells": [], "num_rows": 3, "num_cols": 5}}
                ],
            ),
            patch(
                "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "open_notebook.extractors.row_segmenter.segment_multiple_tables",
                return_value=mock_rows,
            ) as mock_segment,
            patch(
                "open_notebook.extractors.row_segmenter.scan_text_for_synthetics",
                return_value=[],
            ) as mock_scan,
            patch(
                "open_notebook.extractors.row_extractor.extract_all_rows",
                new_callable=AsyncMock,
                return_value=mock_records,
            ) as mock_extract,
            patch(
                "open_notebook.graphs.acm_extraction.provision_langchain_model",
                new_callable=AsyncMock,
                return_value=MagicMock(),
            ),
            patch(
                "open_notebook.graphs.acm_extraction.get_langfuse_handler",
                return_value=None,
            ),
        ):
            from open_notebook.graphs.acm_extraction import extract_items_node

            state = _make_base_state()
            config = MagicMock()
            result = await extract_items_node(state, config)

            # Verify per-row path was taken
            mock_segment.assert_called_once()
            mock_scan.assert_called_once()
            mock_extract.assert_called_once()

            # Verify records returned
            assert result["items_extracted"] is True
            assert len(result["records"]) == 1

    @pytest.mark.asyncio
    async def test_per_row_mode_populates_building_record_id(self):
        """Per-row path sets building_record_id FK from code_to_id_map."""
        record = _make_extraction_record(building_id="B1")
        mock_building = MagicMock()
        mock_building.building_code = "B1"
        mock_building.id = "building_record:abc"
        mock_building.internal_id = "B1"

        with (
            patch.dict(os.environ, {"ACM_ITEM_EXTRACTION_MODE": "per_row"}),
            patch(
                "open_notebook.graphs.acm_extraction._extract_building_content",
                return_value="Page 1 content",
            ),
            patch(
                "open_notebook.graphs.acm_extraction._get_docling_tables",
                new_callable=AsyncMock,
                return_value=[
                    {"docling_document_json": {"table_cells": [], "num_rows": 1, "num_cols": 1}}
                ],
            ),
            patch(
                "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
                new_callable=AsyncMock,
                return_value=[mock_building],
            ),
            patch(
                "open_notebook.extractors.row_segmenter.segment_multiple_tables",
                return_value=[_make_raw_table_row()],
            ),
            patch(
                "open_notebook.extractors.row_segmenter.scan_text_for_synthetics",
                return_value=[],
            ),
            patch(
                "open_notebook.extractors.row_extractor.extract_all_rows",
                new_callable=AsyncMock,
                return_value=[record],
            ),
            patch(
                "open_notebook.graphs.acm_extraction.provision_langchain_model",
                new_callable=AsyncMock,
                return_value=MagicMock(),
            ),
            patch(
                "open_notebook.graphs.acm_extraction.get_langfuse_handler",
                return_value=None,
            ),
        ):
            from open_notebook.graphs.acm_extraction import extract_items_node

            state = _make_base_state()
            config = MagicMock()
            result = await extract_items_node(state, config)

            assert result["items_extracted"] is True
            assert result["records"][0].building_record_id == "building_record:abc"


# ---------------------------------------------------------------------------
# Test: Bulk mode calls _chunk_and_extract_items
# ---------------------------------------------------------------------------


class TestBulkPath:
    """Tests that bulk mode invokes the existing _chunk_and_extract_items."""

    @pytest.mark.asyncio
    async def test_bulk_mode_calls_chunk_and_extract(self):
        """When ACM_ITEM_EXTRACTION_MODE=bulk, per-row path is skipped."""
        mock_item_result = MagicMock()
        mock_item_result.records = []
        mock_item_result.status = "valid"

        with (
            patch.dict(os.environ, {"ACM_ITEM_EXTRACTION_MODE": "bulk"}),
            patch(
                "open_notebook.graphs.acm_extraction._extract_building_content",
                return_value="Page 1 content",
            ),
            patch(
                "open_notebook.graphs.acm_extraction._get_docling_tables",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "open_notebook.graphs.acm_extraction._chunk_and_extract_items",
                new_callable=AsyncMock,
                return_value=mock_item_result,
            ) as mock_chunk,
            patch(
                "open_notebook.graphs.acm_extraction._normalize_v3_records",
                return_value=[],
            ),
        ):
            from open_notebook.graphs.acm_extraction import extract_items_node

            state = _make_base_state()
            config = MagicMock()
            result = await extract_items_node(state, config)

            # Verify bulk path was taken
            mock_chunk.assert_called_once()
            assert result["items_extracted"] is False


# ---------------------------------------------------------------------------
# Test: Fallback from per-row to bulk when no docling JSON
# ---------------------------------------------------------------------------


class TestPerRowFallback:
    """Tests graceful fallback to bulk when per-row prerequisites are missing."""

    @pytest.mark.asyncio
    async def test_fallback_when_no_docling_document_json(self):
        """If tables exist but lack docling_document_json, fall through to bulk."""
        mock_item_result = MagicMock()
        mock_item_result.records = []
        mock_item_result.status = "valid"

        with (
            patch.dict(os.environ, {"ACM_ITEM_EXTRACTION_MODE": "per_row"}),
            patch(
                "open_notebook.graphs.acm_extraction._extract_building_content",
                return_value="Page 1 content",
            ),
            patch(
                "open_notebook.graphs.acm_extraction._get_docling_tables",
                new_callable=AsyncMock,
                # Tables exist but WITHOUT docling_document_json key
                return_value=[{"raw_text": "some table", "page_start": 1}],
            ),
            patch(
                "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "open_notebook.graphs.acm_extraction._chunk_and_extract_items",
                new_callable=AsyncMock,
                return_value=mock_item_result,
            ) as mock_chunk,
            patch(
                "open_notebook.graphs.acm_extraction._normalize_v3_records",
                return_value=[],
            ),
        ):
            from open_notebook.graphs.acm_extraction import extract_items_node

            state = _make_base_state()
            config = MagicMock()
            result = await extract_items_node(state, config)

            # Should have fallen through to bulk path
            mock_chunk.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_when_no_rows_segmented(self):
        """If segmenter returns empty list, fall through to bulk."""
        mock_item_result = MagicMock()
        mock_item_result.records = []
        mock_item_result.status = "valid"

        with (
            patch.dict(os.environ, {"ACM_ITEM_EXTRACTION_MODE": "per_row"}),
            patch(
                "open_notebook.graphs.acm_extraction._extract_building_content",
                return_value="Page 1 content",
            ),
            patch(
                "open_notebook.graphs.acm_extraction._get_docling_tables",
                new_callable=AsyncMock,
                return_value=[
                    {"docling_document_json": {"table_cells": [], "num_rows": 0, "num_cols": 0}}
                ],
            ),
            patch(
                "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "open_notebook.extractors.row_segmenter.segment_multiple_tables",
                return_value=[],
            ),
            patch(
                "open_notebook.extractors.row_segmenter.scan_text_for_synthetics",
                return_value=[],
            ),
            patch(
                "open_notebook.graphs.acm_extraction._chunk_and_extract_items",
                new_callable=AsyncMock,
                return_value=mock_item_result,
            ) as mock_chunk,
            patch(
                "open_notebook.graphs.acm_extraction._normalize_v3_records",
                return_value=[],
            ),
        ):
            from open_notebook.graphs.acm_extraction import extract_items_node

            state = _make_base_state()
            config = MagicMock()
            result = await extract_items_node(state, config)

            # Should have fallen through to bulk path
            mock_chunk.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_when_no_docling_tables_at_all(self):
        """If _get_docling_tables returns empty, fall through to bulk."""
        mock_item_result = MagicMock()
        mock_item_result.records = []
        mock_item_result.status = "valid"

        with (
            patch.dict(os.environ, {"ACM_ITEM_EXTRACTION_MODE": "per_row"}),
            patch(
                "open_notebook.graphs.acm_extraction._extract_building_content",
                return_value="Page 1 content",
            ),
            patch(
                "open_notebook.graphs.acm_extraction._get_docling_tables",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "open_notebook.graphs.acm_extraction._chunk_and_extract_items",
                new_callable=AsyncMock,
                return_value=mock_item_result,
            ) as mock_chunk,
            patch(
                "open_notebook.graphs.acm_extraction._normalize_v3_records",
                return_value=[],
            ),
        ):
            from open_notebook.graphs.acm_extraction import extract_items_node

            state = _make_base_state()
            config = MagicMock()
            result = await extract_items_node(state, config)

            mock_chunk.assert_called_once()


# ---------------------------------------------------------------------------
# Test: Recovery node gating
# ---------------------------------------------------------------------------


class TestRecoveryNodeGating:
    """Tests that recover_no_access_node is gated in per-row mode."""

    @pytest.mark.asyncio
    async def test_recovery_skipped_when_per_row_actually_ran(self):
        """recover_no_access_node returns state unchanged when per_row actually ran."""
        from open_notebook.graphs.acm_extraction import recover_no_access_node

        records = [_make_extraction_record()]
        state = {
            "records": records,
            "source": _make_mock_source(),
            "context": MagicMock(),
            "per_row_actually_ran": True,
        }
        config = MagicMock()
        result = await recover_no_access_node(state, config)

        # Should return state unchanged (no-op)
        assert result is state

    @pytest.mark.asyncio
    async def test_recovery_runs_in_bulk_mode(self):
        """recover_no_access_node runs normally in bulk mode."""
        with (
            patch.dict(os.environ, {"ACM_ITEM_EXTRACTION_MODE": "bulk"}),
            patch(
                "open_notebook.graphs.acm_extraction._get_pipeline_logger",
                return_value=None,
            ),
            patch(
                "open_notebook.graphs.acm_extraction._get_agui_emitter",
                return_value=None,
            ),
            patch(
                "open_notebook.graphs.acm_extraction._recover_no_access_records",
                return_value=[],
            ) as mock_recover,
        ):
            from open_notebook.graphs.acm_extraction import recover_no_access_node

            source = _make_mock_source(full_text="some text about No Access rooms")
            state = {
                "records": [_make_extraction_record()],
                "source": source,
                "context": MagicMock(building_id="B1", building_name="Building A"),
            }
            config = MagicMock()
            result = await recover_no_access_node(state, config)

            # Recovery should have been attempted
            mock_recover.assert_called_once()


# ---------------------------------------------------------------------------
# Test: Environment variable defaults
# ---------------------------------------------------------------------------


class TestEnvVarDefaults:
    """Tests that the default extraction mode is per_row."""

    @pytest.mark.asyncio
    async def test_default_mode_is_per_row(self):
        """Without ACM_ITEM_EXTRACTION_MODE set, default is per_row."""
        # Ensure the env var is not set
        env = os.environ.copy()
        env.pop("ACM_ITEM_EXTRACTION_MODE", None)

        with (
            patch.dict(os.environ, env, clear=True),
            patch(
                "open_notebook.graphs.acm_extraction._extract_building_content",
                return_value="Page 1 content",
            ),
            patch(
                "open_notebook.graphs.acm_extraction._get_docling_tables",
                new_callable=AsyncMock,
                return_value=[
                    {"docling_document_json": {"table_cells": [], "num_rows": 1, "num_cols": 1}}
                ],
            ),
            patch(
                "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "open_notebook.extractors.row_segmenter.segment_multiple_tables",
                return_value=[_make_raw_table_row()],
            ),
            patch(
                "open_notebook.extractors.row_segmenter.scan_text_for_synthetics",
                return_value=[],
            ),
            patch(
                "open_notebook.extractors.row_extractor.extract_all_rows",
                new_callable=AsyncMock,
                return_value=[_make_extraction_record()],
            ) as mock_extract,
            patch(
                "open_notebook.graphs.acm_extraction.provision_langchain_model",
                new_callable=AsyncMock,
                return_value=MagicMock(),
            ),
            patch(
                "open_notebook.graphs.acm_extraction.get_langfuse_handler",
                return_value=None,
            ),
        ):
            from open_notebook.graphs.acm_extraction import extract_items_node

            state = _make_base_state()
            config = MagicMock()
            result = await extract_items_node(state, config)

            # Per-row path should have been taken (default)
            mock_extract.assert_called_once()
