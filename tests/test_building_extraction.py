"""
Unit tests for extract_building_node (E32-S1).

All DB calls and LLM calls are mocked. Tests validate:
- Normal path: N buildings -> N BuildingRecord saves + N IDs in state
- Partial failure: middle building raises exception -> first/last still save
- Empty inventory: node returns empty list without error
- None LLM result: _v3_extract_building_meta returns None -> building skipped
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.extractors.acm_schemas_v3 import BuildingExtractionResult
from open_notebook.extractors.building_inventory import (
    BuildingInventory,
    BuildingMeta,
)
from open_notebook.graphs.acm_extraction import extract_building_node

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_state():
    """Minimal state dict for extract_building_node tests."""
    source = MagicMock()
    source.id = "source:test123"
    source.full_text = "<!-- Page 1 -->\nBuilding content for B001...\n<!-- Page 6 -->\nBuilding content for B002..."
    return {
        "source": source,
        "model_id": "openai:gpt-4o-mini",
        "building_inventory": BuildingInventory(
            buildings=[
                BuildingMeta(building_id="B001", name="Main", page_start=1, page_end=5),
                BuildingMeta(building_id="B002", name="Gym", page_start=6, page_end=10),
            ],
            processing_groups=[],
            total_buildings=2,
        ),
        "pipeline_logger": None,
        "agui_emitter": None,
    }


def _make_extraction_result(**kwargs) -> BuildingExtractionResult:
    """Helper: create a BuildingExtractionResult with defaults."""
    defaults = {
        "building_name": "Test Building",
        "extraction_confidence": "high",
    }
    defaults.update(kwargs)
    return BuildingExtractionResult(**defaults)


def _make_saved_record(record_id: str) -> MagicMock:
    """Helper: create a mock saved record with an id attribute."""
    saved = MagicMock()
    saved.id = record_id
    return saved


# ---------------------------------------------------------------------------
# Test: normal path — all buildings saved
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.save",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.generate_internal_id",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._extract_building_content",
)
async def test_normal_path_saves_all_buildings(
    mock_extract_content,
    mock_v3_extract,
    mock_gen_id,
    mock_save,
    mock_state,
):
    """3-building inventory -> 3 BuildingRecord saves + 3 IDs returned."""
    # Give state 3 buildings
    mock_state["building_inventory"] = BuildingInventory(
        buildings=[
            BuildingMeta(building_id="B001", name="Main", page_start=1, page_end=5),
            BuildingMeta(building_id="B002", name="Gym", page_start=6, page_end=10),
            BuildingMeta(building_id="B003", name="Hall", page_start=11, page_end=15),
        ],
        processing_groups=[],
        total_buildings=3,
    )
    mock_extract_content.return_value = "Some building content"
    mock_v3_extract.return_value = _make_extraction_result()
    mock_gen_id.side_effect = [
        "BLD#TEST1234_001",
        "BLD#TEST1234_002",
        "BLD#TEST1234_003",
    ]
    mock_save.side_effect = [
        _make_saved_record("building_record:001"),
        _make_saved_record("building_record:002"),
        _make_saved_record("building_record:003"),
    ]

    result = await extract_building_node(mock_state, config={})

    assert "building_records" in result
    assert len(result["building_records"]) == 3
    assert mock_save.call_count == 3
    assert mock_gen_id.call_count == 3
    assert mock_v3_extract.call_count == 3


# ---------------------------------------------------------------------------
# Test: partial failure — middle building raises, first and third still save
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.save",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.generate_internal_id",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._extract_building_content",
)
async def test_partial_failure_preserves_results(
    mock_extract_content,
    mock_v3_extract,
    mock_gen_id,
    mock_save,
    mock_state,
):
    """Second building raises RuntimeError -> first and third still produce records."""
    mock_state["building_inventory"] = BuildingInventory(
        buildings=[
            BuildingMeta(building_id="B001", name="Main", page_start=1, page_end=5),
            BuildingMeta(building_id="B002", name="Gym", page_start=6, page_end=10),
            BuildingMeta(building_id="B003", name="Hall", page_start=11, page_end=15),
        ],
        processing_groups=[],
        total_buildings=3,
    )
    mock_extract_content.return_value = "Some building content"
    # Second call raises an exception
    mock_v3_extract.side_effect = [
        _make_extraction_result(building_name="Main Building"),
        RuntimeError("LLM provider failure"),
        _make_extraction_result(building_name="Hall Building"),
    ]
    mock_gen_id.side_effect = ["BLD#TEST1234_001", "BLD#TEST1234_003"]
    mock_save.side_effect = [
        _make_saved_record("building_record:001"),
        _make_saved_record("building_record:003"),
    ]

    result = await extract_building_node(mock_state, config={})

    assert "building_records" in result
    assert len(result["building_records"]) == 2
    assert mock_save.call_count == 2


# ---------------------------------------------------------------------------
# Test: None building_inventory -> returns empty list without error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_inventory_returns_empty_list(mock_state):
    """state['building_inventory'] = None -> returns {'building_records': []}."""
    mock_state["building_inventory"] = None

    result = await extract_building_node(mock_state, config={})

    assert result == {"building_records": [], "building_meta_cache": {}}


# ---------------------------------------------------------------------------
# Test: BuildingInventory with empty buildings list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_none_inventory_buildings_returns_empty(mock_state):
    """BuildingInventory(buildings=[]) -> returns {'building_records': []}."""
    mock_state["building_inventory"] = BuildingInventory(
        buildings=[],
        processing_groups=[],
        total_buildings=0,
    )

    result = await extract_building_node(mock_state, config={})

    assert result == {"building_records": [], "building_meta_cache": {}}


# ---------------------------------------------------------------------------
# Test: LLM returns None -> minimal BuildingRecord created (Bug Fix 11 Phase 3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.save",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.generate_internal_id",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._extract_building_content",
)
async def test_llm_returns_none_creates_minimal_building(
    mock_extract_content,
    mock_v3_extract,
    mock_gen_id,
    mock_save,
    mock_state,
):
    """_v3_extract_building_meta returns None -> minimal BuildingRecord saved (not skipped).

    Bug Fix 11 Phase 3: Instead of silently skipping a building when Phase 1 LLM
    fails, a minimal BuildingRecord is created using building_meta_entry fields so
    that FK linkage and frontend display still work.
    """
    mock_state["building_inventory"] = BuildingInventory(
        buildings=[
            BuildingMeta(building_id="B001", name="Main", page_start=1, page_end=5),
        ],
        processing_groups=[],
        total_buildings=1,
    )
    mock_extract_content.return_value = "Some building content"
    mock_v3_extract.return_value = None
    mock_gen_id.return_value = "BLD#TEST1234_001"
    mock_save.return_value = _make_saved_record("building_record:001")

    result = await extract_building_node(mock_state, config={})

    # Minimal record must be saved and its ID included in the result
    assert len(result["building_records"]) == 1
    assert result["building_records"][0] == "building_record:001"
    mock_gen_id.assert_called_once()
    mock_save.assert_called_once()
    # meta_cache entry for this building_id should be None (no LLM result)
    assert result["building_meta_cache"].get("B001") is None


# ---------------------------------------------------------------------------
# Test: empty building content -> skipped, _v3_extract_building_meta not called
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._extract_building_content",
)
async def test_empty_building_content_skips(
    mock_extract_content,
    mock_v3_extract,
    mock_state,
):
    """_extract_building_content returns '' -> _v3_extract_building_meta not called."""
    mock_state["building_inventory"] = BuildingInventory(
        buildings=[
            BuildingMeta(building_id="B001", name="Main", page_start=1, page_end=5),
        ],
        processing_groups=[],
        total_buildings=1,
    )
    mock_extract_content.return_value = "   "  # whitespace only

    result = await extract_building_node(mock_state, config={})

    assert result["building_records"] == []
    mock_v3_extract.assert_not_called()


# ---------------------------------------------------------------------------
# Test: returned dict has correct keys
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.save",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction.BuildingRecord.generate_internal_id",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._v3_extract_building_meta",
    new_callable=AsyncMock,
)
@patch(
    "open_notebook.graphs.acm_extraction._extract_building_content",
)
async def test_state_dict_has_correct_keys(
    mock_extract_content,
    mock_v3_extract,
    mock_gen_id,
    mock_save,
    mock_state,
):
    """Returned dict always has key 'building_records' with a list value."""
    mock_extract_content.return_value = "Some building content"
    mock_v3_extract.return_value = _make_extraction_result()
    mock_gen_id.side_effect = ["BLD#TEST1234_001", "BLD#TEST1234_002"]
    mock_save.side_effect = [
        _make_saved_record("building_record:001"),
        _make_saved_record("building_record:002"),
    ]

    result = await extract_building_node(mock_state, config={})

    assert "building_records" in result
    assert isinstance(result["building_records"], list)
    assert len(result["building_records"]) == 2
