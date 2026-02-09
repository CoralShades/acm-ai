"""Tests for Building Inventory Compilation (E1-S17).

Tests Pydantic models, building/room detection, page range extraction,
complexity classification, processing group generation, heuristic fallback,
and LangGraph pipeline integration.
"""

import pytest

from open_notebook.extractors.building_inventory import (
    BuildingComplexity,
    BuildingInventory,
    BuildingMeta,
    ProcessingGroup,
    RoomMeta,
)


class TestPydanticModels:
    """Task 1: Pydantic model creation tests."""

    def test_building_complexity_enum(self):
        assert BuildingComplexity.SIMPLE == "simple"
        assert BuildingComplexity.COMPLEX == "complex"

    def test_room_meta_creation(self):
        room = RoomMeta(room_id="B00A-R0001", name="External Movement")
        assert room.room_id == "B00A-R0001"
        assert room.name == "External Movement"
        assert room.area_m2 is None
        assert room.page is None

    def test_room_meta_with_area(self):
        room = RoomMeta(room_id="B00A-R0002", name="Office Area", area_m2=32.5, page=15)
        assert room.area_m2 == 32.5
        assert room.page == 15

    def test_building_meta_minimal(self):
        building = BuildingMeta(
            building_id="B00A",
            page_start=10,
            complexity=BuildingComplexity.SIMPLE,
        )
        assert building.building_id == "B00A"
        assert building.page_start == 10
        assert building.page_end is None
        assert building.name is None
        assert building.year is None
        assert building.construction is None
        assert building.purpose is None
        assert building.area_m2 is None
        assert building.levels is None
        assert building.rooms == []
        assert building.acm_item_count_estimate is None
        assert building.complexity == BuildingComplexity.SIMPLE

    def test_building_meta_full(self):
        rooms = [
            RoomMeta(room_id="B00A-R0001", name="Office"),
            RoomMeta(room_id="B00A-R0002", name="Hallway", area_m2=12.0),
        ]
        building = BuildingMeta(
            building_id="B00A",
            name="Admin Building",
            year=1924,
            construction="Brick",
            purpose="Administration",
            area_m2=450.0,
            levels=2,
            page_start=10,
            page_end=14,
            complexity=BuildingComplexity.COMPLEX,
            rooms=rooms,
            acm_item_count_estimate=15,
        )
        assert building.name == "Admin Building"
        assert building.year == 1924
        assert building.construction == "Brick"
        assert building.purpose == "Administration"
        assert building.area_m2 == 450.0
        assert building.levels == 2
        assert building.page_end == 14
        assert len(building.rooms) == 2
        assert building.acm_item_count_estimate == 15

    def test_processing_group_creation(self):
        group = ProcessingGroup(
            group_id=1,
            building_ids=["B00A", "B00B"],
            page_start=10,
            page_end=15,
            estimated_pages=6,
        )
        assert group.group_id == 1
        assert group.building_ids == ["B00A", "B00B"]
        assert group.page_start == 10
        assert group.page_end == 15
        assert group.estimated_pages == 6

    def test_building_inventory_creation(self):
        from open_notebook.extractors.document_structure import DocumentType

        buildings = [
            BuildingMeta(
                building_id="B00A",
                page_start=10,
                page_end=14,
                complexity=BuildingComplexity.COMPLEX,
            ),
            BuildingMeta(
                building_id="B00B",
                page_start=15,
                page_end=16,
                complexity=BuildingComplexity.SIMPLE,
            ),
        ]
        groups = [
            ProcessingGroup(
                group_id=1,
                building_ids=["B00A", "B00B"],
                page_start=10,
                page_end=16,
                estimated_pages=7,
            ),
        ]
        inventory = BuildingInventory(
            buildings=buildings,
            processing_groups=groups,
            total_buildings=2,
            document_type="SAMP",
        )
        assert inventory.total_buildings == 2
        assert len(inventory.buildings) == 2
        assert len(inventory.processing_groups) == 1
        assert inventory.document_type == "SAMP"

    def test_building_inventory_defaults(self):
        inventory = BuildingInventory(
            buildings=[],
            processing_groups=[],
            total_buildings=0,
        )
        assert inventory.buildings == []
        assert inventory.processing_groups == []
        assert inventory.total_buildings == 0
        assert inventory.document_type is None


class TestPromptTemplate:
    """Task 2: Prompt template tests."""

    def test_prompt_template_renders(self):
        from ai_prompter import Prompter

        prompter = Prompter(prompt_template="acm/building_inventory")
        result = prompter.render(data={"content": "Sample document content"})
        assert "Building Inventory Compilation" in result
        assert "Sample document content" in result

    def test_prompt_contains_building_detection_instructions(self):
        from ai_prompter import Prompter

        prompter = Prompter(prompt_template="acm/building_inventory")
        result = prompter.render(data={"content": ""})
        assert "B000-series" in result
        assert "D-series" in result

    def test_prompt_contains_room_detection_instructions(self):
        from ai_prompter import Prompter

        prompter = Prompter(prompt_template="acm/building_inventory")
        result = prompter.render(data={"content": ""})
        assert "R000-series" in result
        assert "R####" in result or "R0001" in result

    def test_prompt_contains_complexity_classification(self):
        from ai_prompter import Prompter

        prompter = Prompter(prompt_template="acm/building_inventory")
        result = prompter.render(data={"content": ""})
        assert "simple" in result
        assert "complex" in result
        assert "No Asbestos" in result

    def test_prompt_contains_page_range_instructions(self):
        from ai_prompter import Prompter

        prompter = Prompter(prompt_template="acm/building_inventory")
        result = prompter.render(data={"content": ""})
        assert "page_start" in result
        assert "page_end" in result
        assert "Page N" in result or "page marker" in result.lower()


# Sample document content for heuristic testing
SAMPLE_REGISTER_CONTENT = """
--- Page 10 ---

## B00A - Admin Building - 1924 - Brick

### Interior

#### B00A-R0001 - External Movement

| Product | Material Description | Result |
|---------|---------------------|--------|
| Eaves Lining | Fibre cement sheet | Detected |
| Wall Lining | Plasterboard | Not Detected |

--- Page 11 ---

#### B00A-R0002 - Office Area - 32.5 m²

| Product | Material Description | Result |
|---------|---------------------|--------|
| Floor Tiles | Vinyl floor tiles | Detected |
| Ceiling | Fibre cement | Detected |

--- Page 12 ---

## B00B - Gymnasium - 1950 - Steel

No Asbestos Containing Materials Found

--- Page 13 ---

## D01 - Demountable 1

### Interior

#### D01-R0001 - Classroom

| Product | Material Description | Result |
|---------|---------------------|--------|
| Wall Lining | Fibre cement sheet | Detected |

--- Page 14 ---

## B009 - Special Purpose - 1960

### Interior

#### B009-R0001 - Storeroom - 6.61 m²

| Product | Material Description | Result |
|---------|---------------------|--------|
| Roof Material | Corrugated cement | Detected |

#### B009-R0005 - General Storeroom

| Product | Material Description | Result |
|---------|---------------------|--------|
| Eaves | Fibre cement | Not Detected |

--- Page 15 ---
"""


class TestHeuristicFallback:
    """Task 3: Heuristic fallback tests."""

    def test_building_id_detection_b_series(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT)
        building_ids = [b.building_id for b in result.buildings]
        assert "B00A" in building_ids
        assert "B00B" in building_ids
        assert "B009" in building_ids

    def test_building_id_detection_d_series(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT)
        building_ids = [b.building_id for b in result.buildings]
        assert "D01" in building_ids

    def test_building_name_extraction(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT)
        b00a = next(b for b in result.buildings if b.building_id == "B00A")
        assert b00a.name == "Admin Building"

    def test_building_year_extraction(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT)
        b00a = next(b for b in result.buildings if b.building_id == "B00A")
        assert b00a.year == 1924

    def test_building_construction_extraction(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT)
        b00a = next(b for b in result.buildings if b.building_id == "B00A")
        assert b00a.construction == "Brick"

    def test_page_range_mapping(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT)
        b00a = next(b for b in result.buildings if b.building_id == "B00A")
        assert b00a.page_start == 10
        assert b00a.page_end == 11

    def test_page_range_single_page_building(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT)
        b00b = next(b for b in result.buildings if b.building_id == "B00B")
        assert b00b.page_start == 12
        assert b00b.page_end == 12

    def test_complexity_simple_no_asbestos(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT)
        b00b = next(b for b in result.buildings if b.building_id == "B00B")
        assert b00b.complexity == BuildingComplexity.SIMPLE

    def test_complexity_complex_building(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT)
        b00a = next(b for b in result.buildings if b.building_id == "B00A")
        assert b00a.complexity == BuildingComplexity.COMPLEX

    def test_room_code_detection(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT)
        b00a = next(b for b in result.buildings if b.building_id == "B00A")
        room_ids = [r.room_id for r in b00a.rooms]
        assert "B00A-R0001" in room_ids
        assert "B00A-R0002" in room_ids

    def test_room_area_extraction(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT)
        b00a = next(b for b in result.buildings if b.building_id == "B00A")
        r0002 = next(r for r in b00a.rooms if r.room_id == "B00A-R0002")
        assert r0002.area_m2 == 32.5

    def test_acm_item_count_estimate_populated(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT)
        b00a = next(b for b in result.buildings if b.building_id == "B00A")
        # B00A has "Detected" entries, so estimate should be non-None
        assert b00a.acm_item_count_estimate is not None
        assert b00a.acm_item_count_estimate > 0
        # B00B has "No Asbestos" marker, so estimate should be None (0 items)
        b00b = next(b for b in result.buildings if b.building_id == "B00B")
        assert b00b.acm_item_count_estimate is None

    def test_total_buildings_count(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT)
        assert result.total_buildings == 4

    def test_empty_content(self):
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback("")
        assert result.total_buildings == 0
        assert result.buildings == []

    def test_no_document_structure(self):
        """compile_building_inventory works without DocumentStructure."""
        from open_notebook.extractors.building_inventory import _heuristic_fallback

        result = _heuristic_fallback(SAMPLE_REGISTER_CONTENT, document_structure=None)
        assert result.total_buildings > 0


class TestProcessingGroups:
    """Task 3.6: Processing group generation tests."""

    def test_create_groups_from_buildings(self):
        from open_notebook.extractors.building_inventory import (
            _create_processing_groups,
        )

        buildings = [
            BuildingMeta(
                building_id="B00A",
                page_start=10,
                page_end=11,
                complexity=BuildingComplexity.COMPLEX,
            ),
            BuildingMeta(
                building_id="B00B",
                page_start=12,
                page_end=12,
                complexity=BuildingComplexity.SIMPLE,
            ),
            BuildingMeta(
                building_id="D01",
                page_start=13,
                page_end=13,
                complexity=BuildingComplexity.COMPLEX,
            ),
            BuildingMeta(
                building_id="B009",
                page_start=14,
                page_end=15,
                complexity=BuildingComplexity.COMPLEX,
            ),
        ]
        groups = _create_processing_groups(buildings)
        assert len(groups) > 0
        # All buildings should be covered
        all_bids = []
        for g in groups:
            all_bids.extend(g.building_ids)
        assert set(all_bids) == {"B00A", "B00B", "D01", "B009"}

    def test_groups_target_3_to_5_pages(self):
        from open_notebook.extractors.building_inventory import (
            _create_processing_groups,
        )

        buildings = [
            BuildingMeta(
                building_id="B00A",
                page_start=10,
                page_end=12,
                complexity=BuildingComplexity.COMPLEX,
            ),
            BuildingMeta(
                building_id="B00B",
                page_start=13,
                page_end=13,
                complexity=BuildingComplexity.SIMPLE,
            ),
            BuildingMeta(
                building_id="D01",
                page_start=14,
                page_end=14,
                complexity=BuildingComplexity.COMPLEX,
            ),
            BuildingMeta(
                building_id="B009",
                page_start=15,
                page_end=19,
                complexity=BuildingComplexity.COMPLEX,
            ),
        ]
        groups = _create_processing_groups(buildings)
        assert len(groups) >= 2  # Should split into multiple groups
        # First group: B00A(10-12)+B00B(13)+D01(14) = 5 pages, within target
        assert groups[0].estimated_pages <= 5
        # B009(15-19) must be in a separate group since adding it would exceed 5 pages
        assert "B009" in groups[-1].building_ids
        for group in groups:
            assert group.estimated_pages >= 1

    def test_groups_have_sequential_ids(self):
        from open_notebook.extractors.building_inventory import (
            _create_processing_groups,
        )

        buildings = [
            BuildingMeta(
                building_id="B00A",
                page_start=10,
                page_end=12,
                complexity=BuildingComplexity.COMPLEX,
            ),
            BuildingMeta(
                building_id="B00B",
                page_start=15,
                page_end=20,
                complexity=BuildingComplexity.COMPLEX,
            ),
        ]
        groups = _create_processing_groups(buildings)
        for i, group in enumerate(groups):
            assert group.group_id == i + 1

    def test_empty_buildings_no_groups(self):
        from open_notebook.extractors.building_inventory import (
            _create_processing_groups,
        )

        groups = _create_processing_groups([])
        assert groups == []

    def test_single_building_one_group(self):
        from open_notebook.extractors.building_inventory import (
            _create_processing_groups,
        )

        buildings = [
            BuildingMeta(
                building_id="B00A",
                page_start=10,
                page_end=12,
                complexity=BuildingComplexity.COMPLEX,
            ),
        ]
        groups = _create_processing_groups(buildings)
        assert len(groups) == 1
        assert groups[0].building_ids == ["B00A"]


class TestCompileBuildingInventory:
    """Task 3: Full compile_building_inventory function tests."""

    @pytest.mark.asyncio
    async def test_compile_with_heuristic_fallback(self):
        """LLM unavailable - should fall back to heuristic."""
        from open_notebook.extractors.building_inventory import (
            compile_building_inventory,
        )

        result = await compile_building_inventory(
            content=SAMPLE_REGISTER_CONTENT,
            document_structure=None,
            model_id=None,
        )
        assert result is not None
        assert result.total_buildings == 4
        assert len(result.processing_groups) > 0

    @pytest.mark.asyncio
    async def test_compile_with_document_structure(self):
        """Uses DocumentStructure to focus on register content."""
        from open_notebook.extractors.building_inventory import (
            compile_building_inventory,
        )
        from open_notebook.extractors.document_structure import DocumentStructure

        doc_structure = DocumentStructure(
            register_start_page=10,
            building_ids=["B00A", "B00B", "D01", "B009"],
            total_pages=15,
        )
        result = await compile_building_inventory(
            content=SAMPLE_REGISTER_CONTENT,
            document_structure=doc_structure,
            model_id=None,
        )
        assert result is not None
        assert result.total_buildings >= 4

    @pytest.mark.asyncio
    async def test_compile_empty_content(self):
        from open_notebook.extractors.building_inventory import (
            compile_building_inventory,
        )

        result = await compile_building_inventory(
            content="",
            document_structure=None,
            model_id=None,
        )
        assert result is not None
        assert result.total_buildings == 0

    @pytest.mark.asyncio
    async def test_compile_with_mock_llm(self):
        """Test LLM path with mock structured output."""
        from unittest.mock import AsyncMock, patch

        from open_notebook.extractors.building_inventory import (
            compile_building_inventory,
        )

        mock_inventory = BuildingInventory(
            buildings=[
                BuildingMeta(
                    building_id="B00A",
                    name="Admin",
                    page_start=10,
                    page_end=12,
                    complexity=BuildingComplexity.COMPLEX,
                ),
            ],
            processing_groups=[],
            total_buildings=1,
            document_type="SAMP",
        )

        with patch(
            "open_notebook.extractors.building_inventory._llm_compile_inventory",
            new_callable=AsyncMock,
            return_value=mock_inventory,
        ):
            result = await compile_building_inventory(
                content=SAMPLE_REGISTER_CONTENT,
                document_structure=None,
                model_id="test-model",
            )

        assert result is not None
        assert result.total_buildings == 1
        assert result.buildings[0].building_id == "B00A"
        # Processing groups should be generated even from LLM path
        assert len(result.processing_groups) >= 1  # Generated from buildings


class TestLangGraphIntegration:
    """Task 4: LangGraph pipeline integration tests."""

    def test_extraction_state_has_building_inventory(self):
        """building_inventory field exists in ExtractionState."""
        from open_notebook.graphs.acm_extraction import ExtractionState

        # Verify the TypedDict has the field
        annotations = ExtractionState.__annotations__
        assert "building_inventory" in annotations

    def test_graph_has_inventory_node(self):
        """Graph includes the compile_inventory node."""
        from open_notebook.graphs.acm_extraction import graph

        node_names = list(graph.nodes.keys())
        assert "inventory" in node_names

    def test_graph_structure_to_inventory_edge(self):
        """Graph wires structure -> inventory edge."""
        from open_notebook.graphs.acm_extraction import agent_state

        edges = agent_state.edges
        assert ("structure", "inventory") in edges or any(
            e == ("structure", "inventory") for e in edges
        ), "Missing edge: structure -> inventory"

    @pytest.mark.asyncio
    async def test_compile_inventory_node_with_content(self):
        """compile_inventory node returns BuildingInventory in state."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from open_notebook.graphs.acm_extraction import compile_inventory

        mock_source = MagicMock()
        mock_source.id = "source:test"
        mock_source.full_text = SAMPLE_REGISTER_CONTENT

        state = {
            "source": mock_source,
            "model_id": None,
            "document_structure": None,
        }

        # Patch LLM to force heuristic fallback
        with patch(
            "open_notebook.extractors.building_inventory._llm_compile_inventory",
            new_callable=AsyncMock,
            side_effect=Exception("No LLM"),
        ):
            result = await compile_inventory(state, MagicMock())

        assert "building_inventory" in result
        inventory = result["building_inventory"]
        assert inventory is not None
        assert inventory.total_buildings == 4

    @pytest.mark.asyncio
    async def test_compile_inventory_node_empty_content(self):
        """compile_inventory returns None for empty content."""
        from unittest.mock import MagicMock

        from open_notebook.graphs.acm_extraction import compile_inventory

        mock_source = MagicMock()
        mock_source.id = "source:test"
        mock_source.full_text = ""

        state = {
            "source": mock_source,
            "model_id": None,
            "document_structure": None,
        }

        result = await compile_inventory(state, MagicMock())
        assert result["building_inventory"] is None

    def test_initial_state_has_building_inventory_none(self):
        """Initial state initializes building_inventory to None."""
        # Verify the initial state dict pattern in extract_acm_from_source
        import inspect

        from open_notebook.graphs import acm_extraction

        source_code = inspect.getsource(acm_extraction.extract_acm_from_source)
        assert (
            '"building_inventory": None' in source_code
            or "'building_inventory': None" in source_code
        )
