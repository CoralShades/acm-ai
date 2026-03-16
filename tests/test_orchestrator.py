"""Tests for Agentic Extraction Orchestrator (E1-S20).

Tests Pydantic models, per-building content extraction, and ACMExtractionOutput stats.
"""

import pytest

from open_notebook.extractors.acm_schemas import ACMExtractionOutput
from open_notebook.extractors.building_inventory import BuildingInventory
from open_notebook.extractors.orchestrator import (
    BuildingExtractionPlan,
    ExtractionPlan,
    ExtractionStrategy,
    OrchestratorStats,
    _extract_building_content,
)


def _make_content_with_pages(page_ranges: list[tuple[int, str]]) -> str:
    """Create content with page markers."""
    parts = []
    for page_num, text in page_ranges:
        parts.append(f"--- Page {page_num} ---\n{text}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Task 7.2: ExtractionStrategy enum
# ---------------------------------------------------------------------------


class TestExtractionStrategy:
    def test_enum_values(self):
        assert ExtractionStrategy.FULL_LLM == "full_llm"
        assert ExtractionStrategy.REGEX_ONLY == "regex_only"
        assert ExtractionStrategy.SKIP == "skip"

    def test_enum_from_value(self):
        assert ExtractionStrategy("full_llm") == ExtractionStrategy.FULL_LLM
        assert ExtractionStrategy("regex_only") == ExtractionStrategy.REGEX_ONLY
        assert ExtractionStrategy("skip") == ExtractionStrategy.SKIP


# ---------------------------------------------------------------------------
# Task 7.3: BuildingExtractionPlan
# ---------------------------------------------------------------------------


class TestBuildingExtractionPlan:
    def test_creation(self):
        plan = BuildingExtractionPlan(
            building_id="B00A",
            building_name="Admin",
            page_range=(10, 15),
            strategy=ExtractionStrategy.FULL_LLM,
            complexity="complex",
        )
        assert plan.building_id == "B00A"
        assert plan.page_range == (10, 15)
        assert plan.strategy == ExtractionStrategy.FULL_LLM

    def test_defaults(self):
        plan = BuildingExtractionPlan(
            building_id="B00A",
            page_range=(1, 5),
            strategy=ExtractionStrategy.SKIP,
        )
        assert plan.building_name is None
        assert plan.complexity == "complex"
        assert plan.context_summary is None


# ---------------------------------------------------------------------------
# Task 7.5: OrchestratorStats
# ---------------------------------------------------------------------------


class TestOrchestratorStats:
    def test_default_values(self):
        stats = OrchestratorStats()
        assert stats.total_buildings == 0
        assert stats.buildings_extracted == 0
        assert stats.buildings_skipped == 0
        assert stats.total_records == 0
        assert stats.strategy_distribution == {}
        assert stats.total_time_ms == 0
        assert stats.plan is None

    def test_aggregation(self):
        stats = OrchestratorStats(
            total_buildings=3,
            buildings_extracted=2,
            buildings_skipped=1,
            total_records=15,
            strategy_distribution={"full_llm": 1, "regex_only": 1, "skip": 1},
            total_time_ms=5000,
        )
        assert stats.total_buildings == 3
        assert stats.total_records == 15


# ---------------------------------------------------------------------------
# Task 7.8: _extract_building_content
# ---------------------------------------------------------------------------


class TestExtractBuildingContent:
    def test_correct_page_range(self):
        content = _make_content_with_pages(
            [
                (1, "Page 1 intro"),
                (2, "Page 2 methodology"),
                (3, "Page 3 register B00A data"),
                (4, "Page 4 more B00A data"),
                (5, "Page 5 appendix"),
            ]
        )
        result = _extract_building_content(content, 3, 4)
        assert "register B00A data" in result
        assert "more B00A data" in result
        assert "appendix" not in result

    def test_missing_page_markers(self):
        content = "No page markers here, just content"
        result = _extract_building_content(content, 1, 5)
        assert result == content

    def test_single_page_building(self):
        content = _make_content_with_pages(
            [
                (1, "Page 1 content"),
                (2, "Single page building data"),
                (3, "Page 3 other"),
            ]
        )
        result = _extract_building_content(content, 2, 2)
        assert "Single page building data" in result
        assert "Page 3 other" not in result


# ---------------------------------------------------------------------------
# Task 7.16: ACMExtractionOutput includes orchestrator_stats
# ---------------------------------------------------------------------------


class TestACMExtractionOutputOrchestratorStats:
    def test_output_has_orchestrator_stats_field(self):
        output = ACMExtractionOutput(
            source_id="source:test",
            status="success",
            total_records=5,
            orchestrator_stats={"total_buildings": 3, "total_records": 5},
        )
        assert output.orchestrator_stats is not None
        assert output.orchestrator_stats["total_buildings"] == 3

    def test_output_orchestrator_stats_default_none(self):
        output = ACMExtractionOutput(
            source_id="source:test",
            status="success",
        )
        assert output.orchestrator_stats is None

    def test_model_dump_serialization_roundtrip(self):
        """Verify OrchestratorStats.model_dump() produces valid dict for ACMExtractionOutput."""
        plan = ExtractionPlan(
            plans=[],
            total_buildings=2,
            buildings_to_extract=2,
            buildings_skipped=0,
            estimated_llm_calls=1,
        )
        stats = OrchestratorStats(
            total_buildings=2,
            buildings_extracted=2,
            buildings_skipped=0,
            total_records=10,
            strategy_distribution={"full_llm": 1, "regex_only": 1},
            total_time_ms=3000,
            plan=plan,
        )
        stats_dict = stats.model_dump()
        output = ACMExtractionOutput(
            source_id="source:test",
            status="success",
            total_records=10,
            orchestrator_stats=stats_dict,
        )
        assert output.orchestrator_stats["total_buildings"] == 2
        assert output.orchestrator_stats["strategy_distribution"]["full_llm"] == 1
        assert output.orchestrator_stats["plan"]["total_buildings"] == 2


# ---------------------------------------------------------------------------
# R2: RoomMeta Typing Coercion Tests (R2-AC1)
# ---------------------------------------------------------------------------


class TestRoomMetaCoercion:
    """Tests for _coerce_rooms_in_inventory (R2-T1)."""

    def test_coerces_string_rooms_to_roommeta(self):
        """String rooms are converted to {room_id, name} dicts."""
        from open_notebook.extractors.building_inventory import (
            _coerce_rooms_in_inventory,
        )

        parsed = {
            "buildings": [
                {
                    "building_id": "B00A",
                    "name": "Admin",
                    "page_start": 1,
                    "rooms": ["Room A", "Room B"],
                }
            ],
            "processing_groups": [],
            "total_buildings": 1,
        }
        _coerce_rooms_in_inventory(parsed)
        rooms = parsed["buildings"][0]["rooms"]
        assert len(rooms) == 2
        assert rooms[0] == {"room_id": "Room A", "name": "Room A"}
        assert rooms[1] == {"room_id": "Room B", "name": "Room B"}

    def test_preserves_dict_rooms(self):
        """Dict rooms pass through unchanged."""
        from open_notebook.extractors.building_inventory import (
            _coerce_rooms_in_inventory,
        )

        parsed = {
            "buildings": [
                {
                    "building_id": "B00A",
                    "name": "Admin",
                    "page_start": 1,
                    "rooms": [{"room_id": "R001", "name": "Office", "area_m2": 20.0}],
                }
            ],
            "processing_groups": [],
            "total_buildings": 1,
        }
        _coerce_rooms_in_inventory(parsed)
        rooms = parsed["buildings"][0]["rooms"]
        assert len(rooms) == 1
        assert rooms[0]["room_id"] == "R001"
        assert rooms[0]["area_m2"] == 20.0

    def test_handles_mixed_rooms(self):
        """Mix of strings and dicts are both handled correctly."""
        from open_notebook.extractors.building_inventory import (
            _coerce_rooms_in_inventory,
        )

        parsed = {
            "buildings": [
                {
                    "building_id": "B00A",
                    "name": "Admin",
                    "page_start": 1,
                    "rooms": [
                        "Hallway",
                        {"room_id": "R002", "name": "Lab"},
                    ],
                }
            ],
            "processing_groups": [],
            "total_buildings": 1,
        }
        _coerce_rooms_in_inventory(parsed)
        rooms = parsed["buildings"][0]["rooms"]
        assert len(rooms) == 2
        assert rooms[0] == {"room_id": "Hallway", "name": "Hallway"}
        assert rooms[1]["room_id"] == "R002"

    def test_handles_none_rooms(self):
        """None rooms default to empty list."""
        from open_notebook.extractors.building_inventory import (
            _coerce_rooms_in_inventory,
        )

        parsed = {
            "buildings": [
                {
                    "building_id": "B00A",
                    "name": "Admin",
                    "page_start": 1,
                    "rooms": None,
                }
            ],
            "processing_groups": [],
            "total_buildings": 1,
        }
        _coerce_rooms_in_inventory(parsed)
        assert parsed["buildings"][0]["rooms"] == []

    def test_handles_missing_rooms_key(self):
        """Missing rooms key gets defaulted to empty list."""
        from open_notebook.extractors.building_inventory import (
            _coerce_rooms_in_inventory,
        )

        parsed = {
            "buildings": [
                {
                    "building_id": "B00A",
                    "name": "Admin",
                    "page_start": 1,
                }
            ],
            "processing_groups": [],
            "total_buildings": 1,
        }
        _coerce_rooms_in_inventory(parsed)
        assert parsed["buildings"][0]["rooms"] == []

    def test_coerced_rooms_validate_as_building_inventory(self):
        """Coerced string rooms pass BuildingInventory.model_validate()."""
        from open_notebook.extractors.building_inventory import (
            _coerce_rooms_in_inventory,
        )

        parsed = {
            "buildings": [
                {
                    "building_id": "B00A",
                    "name": "Admin",
                    "page_start": 1,
                    "rooms": ["External", "Roof Space"],
                    "complexity": "complex",
                }
            ],
            "processing_groups": [],
            "total_buildings": 1,
        }
        _coerce_rooms_in_inventory(parsed)
        inv = BuildingInventory.model_validate(parsed)
        assert len(inv.buildings[0].rooms) == 2
        assert inv.buildings[0].rooms[0].name == "External"
        assert inv.buildings[0].rooms[0].room_id == "External"
