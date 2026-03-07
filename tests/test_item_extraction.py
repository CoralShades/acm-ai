"""
Unit tests for E32-S2: Item__c AI Extraction Node.

Tests extract_items_node and _chunk_and_extract_items
using mocked LLM calls — no live SurrealDB required.

Story: E32-S2 Item__c AI Extraction Node
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.extractors.acm_schemas import ACMExtractionRecord
from open_notebook.extractors.acm_schemas_v3 import (
    ACMItemExtractionResult,
    ACMItemRecord,
    BuildingExtractionResult,
)
from open_notebook.extractors.building_inventory import (
    BuildingInventory,
    BuildingMeta,
)
from open_notebook.graphs.acm_extraction import (
    _ITEM_EXTRACTION_CHUNK_CHARS,
    _chunk_and_extract_items,
    extract_items_node,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_inventory(building_ids=("B01",)):
    """Build a minimal BuildingInventory for the given building IDs."""
    buildings = [
        BuildingMeta(
            building_id=bid,
            name=f"Building {bid}",
            page_start=1,
            page_end=5,
        )
        for bid in building_ids
    ]
    return BuildingInventory(
        buildings=buildings,
        processing_groups=[],
        total_buildings=len(buildings),
    )


def _make_state(inventory=None, building_records=None):
    """Construct a minimal graph state dict."""
    source = MagicMock()
    source.id = "source:001"
    source.full_text = "--- Page 1 ---\nContent line one\n--- Page 5 ---\nMore content"
    return {
        "source": source,
        "building_inventory": inventory,
        "building_records": building_records or [],
        "schema_bundle": None,
        "model_id": None,
        "_langchain_config": None,
        "pipeline_logger": None,
        "agui_emitter": None,
        "document_metadata": None,
    }


def _make_extraction_record(building_id: str = "B01") -> ACMExtractionRecord:
    """Create a minimal ACMExtractionRecord."""
    return ACMExtractionRecord(
        building_id=building_id,
        product="Ceiling Tile",
        result="Positive",
    )


def _make_item_result(n: int = 1) -> ACMItemExtractionResult:
    """Create an ACMItemExtractionResult with n ACMItemRecord objects."""
    items = [
        ACMItemRecord(
            room_or_area=f"Room {i}",
            item_name="Ceiling Tile",
            sample_result="Positive",
        )
        for i in range(n)
    ]
    return ACMItemExtractionResult(records=items, status="valid")


# ---------------------------------------------------------------------------
# Tests: extract_items_node
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_extract_items_node_happy_path():
    """Happy path: one building, 3 items extracted and normalised."""
    inventory = _make_inventory(("B01",))
    state = _make_state(inventory=inventory)

    records = [_make_extraction_record("B01") for _ in range(3)]
    building_meta_result = BuildingExtractionResult(building_name="Building B01")

    with (
        patch(
            "open_notebook.graphs.acm_extraction._get_docling_tables",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
            new=AsyncMock(return_value=building_meta_result),
        ),
        patch(
            "open_notebook.graphs.acm_extraction._v3_extract_items",
            new=AsyncMock(return_value=_make_item_result(3)),
        ),
        patch(
            "open_notebook.graphs.acm_extraction._normalize_v3_records",
            return_value=records,
        ),
        patch(
            "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
            new=AsyncMock(return_value=[]),
        ),
    ):
        result = await extract_items_node(state, config=None)

    assert result["items_extracted"] is True
    assert len(result["records"]) == 3


@pytest.mark.asyncio
async def test_extract_items_node_no_inventory():
    """When building_inventory is None, node returns empty records without LLM calls."""
    state = _make_state(inventory=None)

    with patch(
        "open_notebook.graphs.acm_extraction._v3_extract_items",
        new=AsyncMock(),
    ) as mock_extract:
        result = await extract_items_node(state, config=None)
        mock_extract.assert_not_called()

    assert result == {"records": [], "items_extracted": False}


@pytest.mark.asyncio
async def test_extract_items_node_empty_buildings():
    """When inventory has no buildings, node returns empty records without LLM calls."""
    inventory = BuildingInventory(buildings=[], processing_groups=[], total_buildings=0)
    state = _make_state(inventory=inventory)

    with patch(
        "open_notebook.graphs.acm_extraction._v3_extract_items",
        new=AsyncMock(),
    ) as mock_extract:
        result = await extract_items_node(state, config=None)
        mock_extract.assert_not_called()

    assert result == {"records": [], "items_extracted": False}


@pytest.mark.asyncio
async def test_extract_items_node_multiple_buildings():
    """Two buildings, 2 records each → 4 total records, items_extracted=True."""
    inventory = _make_inventory(("B01", "B02"))
    state = _make_state(inventory=inventory)

    building_meta_result = BuildingExtractionResult(building_name="Building")

    def make_two_records(building_id: str):
        return [_make_extraction_record(building_id) for _ in range(2)]

    call_count = {"n": 0}

    def normalize_side_effect(bm, ir, plan):
        bid = plan.building_id
        return make_two_records(bid)

    with (
        patch(
            "open_notebook.graphs.acm_extraction._get_docling_tables",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
            new=AsyncMock(return_value=building_meta_result),
        ),
        patch(
            "open_notebook.graphs.acm_extraction._v3_extract_items",
            new=AsyncMock(return_value=_make_item_result(2)),
        ),
        patch(
            "open_notebook.graphs.acm_extraction._normalize_v3_records",
            side_effect=normalize_side_effect,
        ),
        patch(
            "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
            new=AsyncMock(return_value=[]),
        ),
    ):
        result = await extract_items_node(state, config=None)

    assert result["items_extracted"] is True
    assert len(result["records"]) == 4


@pytest.mark.asyncio
async def test_extract_items_node_building_failure():
    """First building raises exception; second building still processed."""
    inventory = _make_inventory(("B01", "B02"))
    state = _make_state(inventory=inventory)

    call_count = {"n": 0}
    building_meta_result = BuildingExtractionResult(building_name="Building")

    async def flaky_extract(content, plan, bm, st, sb, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("LLM timeout")
        return _make_item_result(2)

    records_b02 = [_make_extraction_record("B02") for _ in range(2)]

    def normalize_side_effect(bm, ir, plan):
        return records_b02

    with (
        patch(
            "open_notebook.graphs.acm_extraction._get_docling_tables",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
            new=AsyncMock(return_value=building_meta_result),
        ),
        patch(
            "open_notebook.graphs.acm_extraction._v3_extract_items",
            side_effect=flaky_extract,
        ),
        patch(
            "open_notebook.graphs.acm_extraction._normalize_v3_records",
            side_effect=normalize_side_effect,
        ),
        patch(
            "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
            new=AsyncMock(return_value=[]),
        ),
    ):
        result = await extract_items_node(state, config=None)

    # B01 failed, B02 succeeded → 2 records, items_extracted=True
    assert result["items_extracted"] is True
    assert len(result["records"]) == 2


@pytest.mark.asyncio
async def test_extract_items_node_zero_records():
    """When _v3_extract_items returns zero items, items_extracted is False."""
    inventory = _make_inventory(("B01",))
    state = _make_state(inventory=inventory)

    building_meta_result = BuildingExtractionResult(building_name="Building B01")

    with (
        patch(
            "open_notebook.graphs.acm_extraction._get_docling_tables",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
            new=AsyncMock(return_value=building_meta_result),
        ),
        patch(
            "open_notebook.graphs.acm_extraction._v3_extract_items",
            new=AsyncMock(
                return_value=ACMItemExtractionResult(records=[], status="valid")
            ),
        ),
        patch(
            "open_notebook.graphs.acm_extraction._normalize_v3_records",
            return_value=[],
        ),
        patch(
            "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
            new=AsyncMock(return_value=[]),
        ),
    ):
        result = await extract_items_node(state, config=None)

    assert result["items_extracted"] is False
    assert result["records"] == []


# ---------------------------------------------------------------------------
# Tests: _chunk_and_extract_items
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chunk_and_extract_items_small():
    """Content smaller than chunk threshold → _v3_extract_items called exactly once."""
    content = "x" * (_ITEM_EXTRACTION_CHUNK_CHARS - 100)
    plan = MagicMock()
    building_meta = None
    state: dict = {}
    schema_bundle = None

    with patch(
        "open_notebook.graphs.acm_extraction._v3_extract_items",
        new=AsyncMock(return_value=_make_item_result(2)),
    ) as mock_extract:
        result = await _chunk_and_extract_items(
            content, plan, building_meta, state, schema_bundle
        )
        mock_extract.assert_called_once()

    assert len(result.records) == 2


@pytest.mark.asyncio
async def test_chunk_and_extract_items_large():
    """Content = 3x chunk threshold → _v3_extract_items called 3 times, records merged."""
    content = "x" * (3 * _ITEM_EXTRACTION_CHUNK_CHARS)
    plan = MagicMock()
    building_meta = None
    state: dict = {}
    schema_bundle = None

    with patch(
        "open_notebook.graphs.acm_extraction._v3_extract_items",
        new=AsyncMock(return_value=_make_item_result(2)),
    ) as mock_extract:
        result = await _chunk_and_extract_items(
            content, plan, building_meta, state, schema_bundle
        )
        assert mock_extract.call_count == 3

    # 3 calls × 2 records each = 6 merged records
    assert len(result.records) == 6
    assert result.status == "valid"


# ---------------------------------------------------------------------------
# Test: building_record_id population
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_building_record_id_populated():
    """BuildingRecord.get_by_source returns a record → building_record_id set on ACMExtractionRecord."""
    inventory = _make_inventory(("B01",))
    state = _make_state(inventory=inventory)

    # Simulate a persisted BuildingRecord with matching building_code
    saved_building = MagicMock()
    saved_building.building_code = "B01"
    saved_building.id = "building_record:abc123"

    extraction_record = _make_extraction_record("B01")
    building_meta_result = BuildingExtractionResult(building_name="Building B01")

    with (
        patch(
            "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
            new=AsyncMock(return_value=building_meta_result),
        ),
        patch(
            "open_notebook.graphs.acm_extraction._v3_extract_items",
            new=AsyncMock(return_value=_make_item_result(1)),
        ),
        patch(
            "open_notebook.graphs.acm_extraction._normalize_v3_records",
            return_value=[extraction_record],
        ),
        patch(
            "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
            new=AsyncMock(return_value=[saved_building]),
        ),
    ):
        result = await extract_items_node(state, config=None)

    assert len(result["records"]) == 1
    assert result["records"][0].building_record_id == "building_record:abc123"
