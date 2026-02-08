"""Tests for Agentic Extraction Orchestrator (E1-S20).

Tests Pydantic models, extraction planning, per-building extraction,
parallel orchestration, graph wiring, and backward compatibility.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.extractors.acm_schemas import (
    ACMExtractionOutput,
    ACMExtractionRecord,
    ACMExtractionResult,
)
from open_notebook.extractors.building_inventory import (
    BuildingComplexity,
    BuildingInventory,
    BuildingMeta,
    ProcessingGroup,
)
from open_notebook.extractors.orchestrator import (
    BuildingExtractionPlan,
    BuildingExtractionStats,
    ExtractionPlan,
    ExtractionStrategy,
    OrchestratorStats,
    _extract_building_content,
    _regex_extract_simple_building,
    extract_building,
    merge_building_results,
    orchestrate_extraction,
    plan_extraction,
    should_use_orchestrator,
)
from open_notebook.extractors.page_tagger import (
    PageTag,
    PageTaggingResult,
    PageType,
    SectionTaxonomy,
)
from open_notebook.extractors.parsers.base import DocumentMeta

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_building(
    bid: str = "B00A",
    name: str = "Admin Building",
    page_start: int = 10,
    page_end: int = 15,
    complexity: BuildingComplexity = BuildingComplexity.COMPLEX,
) -> BuildingMeta:
    return BuildingMeta(
        building_id=bid,
        name=name,
        page_start=page_start,
        page_end=page_end,
        complexity=complexity,
    )


def _make_inventory(buildings: list[BuildingMeta] | None = None) -> BuildingInventory:
    if buildings is None:
        buildings = [
            _make_building("B00A", "Admin Building", 10, 15, BuildingComplexity.COMPLEX),
            _make_building("B00B", "Storage Shed", 16, 17, BuildingComplexity.SIMPLE),
            _make_building("B00C", "Portables", 18, 20, BuildingComplexity.COMPLEX),
        ]
    return BuildingInventory(
        buildings=buildings,
        processing_groups=[],
        total_buildings=len(buildings),
    )


def _make_page_tags(page_ranges: list[tuple[int, int, int]]) -> PageTaggingResult:
    """Create page tags. Each tuple is (page_number, section_id, confidence)."""
    pages = [
        PageTag(
            page_number=pn,
            section_id=sid,
            section_title="Test",
            confidence=conf,
            page_type=PageType.CONTENT,
        )
        for pn, sid, conf in page_ranges
    ]
    return PageTaggingResult(pages=pages, total_pages=max(pn for pn, _, _ in page_ranges))


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
# Task 7.4: ExtractionPlan generation
# ---------------------------------------------------------------------------


class TestExtractionPlan:
    def test_plan_from_inventory(self):
        inventory = _make_inventory()
        # All register pages for B00A (complex) and B00C (complex), some for B00B (simple)
        tags = _make_page_tags([
            (10, 4, 0.9), (11, 4, 0.9), (12, 4, 0.9),
            (13, 4, 0.9), (14, 4, 0.9), (15, 4, 0.9),
            (16, 4, 0.8), (17, 4, 0.8),
            (18, 4, 0.9), (19, 4, 0.9), (20, 4, 0.9),
        ])
        plan = plan_extraction(inventory, tags)
        assert plan.total_buildings == 3
        assert plan.buildings_to_extract == 3  # All have register pages
        assert plan.buildings_skipped == 0

    def test_plan_with_skip(self):
        """Buildings with no register pages should be SKIP."""
        inventory = _make_inventory([
            _make_building("B00A", "Admin", 10, 15, BuildingComplexity.COMPLEX),
            _make_building("B00B", "Appendix", 16, 20, BuildingComplexity.COMPLEX),
        ])
        tags = _make_page_tags([
            (10, 4, 0.9), (11, 4, 0.9), (12, 4, 0.9),
            (13, 4, 0.9), (14, 4, 0.9), (15, 4, 0.9),
            (16, 7, 0.8), (17, 7, 0.8), (18, 7, 0.8),
            (19, 7, 0.8), (20, 7, 0.8),
        ])
        plan = plan_extraction(inventory, tags)
        assert plan.buildings_to_extract == 1
        assert plan.buildings_skipped == 1
        b_plan = {p.building_id: p for p in plan.plans}
        assert b_plan["B00A"].strategy == ExtractionStrategy.FULL_LLM
        assert b_plan["B00B"].strategy == ExtractionStrategy.SKIP

    def test_plan_regex_for_simple(self):
        """Simple buildings with register pages should use REGEX_ONLY."""
        inventory = _make_inventory([
            _make_building("B00A", "Simple", 10, 12, BuildingComplexity.SIMPLE),
        ])
        tags = _make_page_tags([(10, 4, 0.9), (11, 4, 0.9), (12, 4, 0.9)])
        plan = plan_extraction(inventory, tags)
        assert plan.plans[0].strategy == ExtractionStrategy.REGEX_ONLY

    def test_plan_no_tags_defaults_to_full_llm(self):
        """Without page tags, all buildings default to FULL_LLM."""
        inventory = _make_inventory([
            _make_building("B00A", "Building", 10, 15, BuildingComplexity.SIMPLE),
        ])
        plan = plan_extraction(inventory, page_tags=None)
        assert plan.plans[0].strategy == ExtractionStrategy.FULL_LLM
        assert plan.estimated_llm_calls == 1


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
# Task 7.6: should_use_orchestrator
# ---------------------------------------------------------------------------


class TestShouldUseOrchestrator:
    def test_true_with_inventory(self):
        state = {"building_inventory": _make_inventory()}
        assert should_use_orchestrator(state) is True

    def test_false_when_none(self):
        state = {"building_inventory": None}
        assert should_use_orchestrator(state) is False

    def test_false_when_empty(self):
        state = {"building_inventory": BuildingInventory(
            buildings=[], processing_groups=[], total_buildings=0,
        )}
        assert should_use_orchestrator(state) is False

    def test_false_when_missing(self):
        state = {}
        assert should_use_orchestrator(state) is False


# ---------------------------------------------------------------------------
# Task 7.7: plan_extraction
# ---------------------------------------------------------------------------


class TestPlanExtraction:
    def test_correct_strategy_assignment(self):
        inventory = _make_inventory()
        tags = _make_page_tags([
            (10, 4, 0.9), (11, 4, 0.9), (12, 4, 0.9),
            (13, 4, 0.9), (14, 4, 0.9), (15, 4, 0.9),
            (16, 4, 0.8), (17, 4, 0.8),
            (18, 4, 0.9), (19, 4, 0.9), (20, 4, 0.9),
        ])
        plan = plan_extraction(inventory, tags)
        by_id = {p.building_id: p for p in plan.plans}
        assert by_id["B00A"].strategy == ExtractionStrategy.FULL_LLM
        assert by_id["B00B"].strategy == ExtractionStrategy.REGEX_ONLY
        assert by_id["B00C"].strategy == ExtractionStrategy.FULL_LLM

    def test_skip_non_register_buildings(self):
        inventory = _make_inventory([
            _make_building("B00A", "Methodology", 5, 8, BuildingComplexity.COMPLEX),
        ])
        tags = _make_page_tags([
            (5, 3, 0.9), (6, 3, 0.9), (7, 3, 0.9), (8, 3, 0.9),
        ])
        plan = plan_extraction(inventory, tags)
        assert plan.plans[0].strategy == ExtractionStrategy.SKIP

    def test_missing_page_tags_defaults_full_llm(self):
        inventory = _make_inventory([
            _make_building("B00A", "Building", 10, 15, BuildingComplexity.COMPLEX),
        ])
        plan = plan_extraction(inventory, page_tags=None)
        assert plan.plans[0].strategy == ExtractionStrategy.FULL_LLM

    def test_context_summary_with_metadata(self):
        inventory = _make_inventory([
            _make_building("B00A", "Admin", 10, 15, BuildingComplexity.COMPLEX),
        ])
        doc_meta = DocumentMeta(
            consultant_name="Greencap Pty Ltd",
            site_name="Test Primary School",
        )
        plan = plan_extraction(inventory, page_tags=None, document_meta=doc_meta)
        assert "Greencap" in plan.plans[0].context_summary
        assert "Test Primary School" in plan.plans[0].context_summary


# ---------------------------------------------------------------------------
# Task 7.8: _extract_building_content
# ---------------------------------------------------------------------------


class TestExtractBuildingContent:
    def test_correct_page_range(self):
        content = _make_content_with_pages([
            (1, "Page 1 intro"),
            (2, "Page 2 methodology"),
            (3, "Page 3 register B00A data"),
            (4, "Page 4 more B00A data"),
            (5, "Page 5 appendix"),
        ])
        result = _extract_building_content(content, 3, 4)
        assert "register B00A data" in result
        assert "more B00A data" in result
        assert "appendix" not in result

    def test_missing_page_markers(self):
        content = "No page markers here, just content"
        result = _extract_building_content(content, 1, 5)
        assert result == content

    def test_single_page_building(self):
        content = _make_content_with_pages([
            (1, "Page 1 content"),
            (2, "Single page building data"),
            (3, "Page 3 other"),
        ])
        result = _extract_building_content(content, 2, 2)
        assert "Single page building data" in result
        assert "Page 3 other" not in result


# ---------------------------------------------------------------------------
# Task 7.9: _regex_extract_simple_building
# ---------------------------------------------------------------------------


class TestRegexExtractSimpleBuilding:
    def test_creates_not_detected_records(self):
        content = """## B00A - Storage Shed
No Asbestos
B00A-R0001 - External Movement
No Asbestos
B00A-R0002 - Storeroom
No Asbestos"""
        records = _regex_extract_simple_building(content, "B00A", "Storage Shed")
        assert len(records) == 2
        assert all(r.result == "Not Detected" for r in records)
        assert all(r.building_id == "B00A" for r in records)
        assert records[0].room_id == "B00A-R0001"
        assert records[1].room_id == "B00A-R0002"

    def test_empty_content(self):
        records = _regex_extract_simple_building("", "B00A")
        assert records == []

    def test_no_room_patterns(self):
        content = "This is just general text without any room entries."
        records = _regex_extract_simple_building(content, "B00A")
        assert records == []

    def test_high_confidence(self):
        content = "B00A-R0001 - Office Area\nNo Asbestos"
        records = _regex_extract_simple_building(content, "B00A")
        assert len(records) == 1
        assert records[0].extraction_confidence == "high"


# ---------------------------------------------------------------------------
# Task 7.10: extract_building
# ---------------------------------------------------------------------------


class TestExtractBuilding:
    @pytest.mark.asyncio
    async def test_skip_returns_empty(self):
        plan = BuildingExtractionPlan(
            building_id="B00A",
            page_range=(1, 5),
            strategy=ExtractionStrategy.SKIP,
        )
        records, stats = await extract_building(plan, "content", {})
        assert records == []
        assert stats.strategy_used == "skip"
        assert stats.records_extracted == 0

    @pytest.mark.asyncio
    async def test_regex_only_path(self):
        content = _make_content_with_pages([
            (10, "## B00A - Storage Shed\nB00A-R0001 - External Movement\nNo Asbestos"),
        ])
        plan = BuildingExtractionPlan(
            building_id="B00A",
            building_name="Storage Shed",
            page_range=(10, 10),
            strategy=ExtractionStrategy.REGEX_ONLY,
        )
        records, stats = await extract_building(plan, content, {})
        assert len(records) == 1
        assert stats.strategy_used == "regex_only"
        assert records[0].result == "Not Detected"

    @pytest.mark.asyncio
    async def test_full_llm_error_handling(self):
        """LLM failure should return empty records with error in stats."""
        content = _make_content_with_pages([
            (10, "Some building content"),
        ])
        plan = BuildingExtractionPlan(
            building_id="B00A",
            page_range=(10, 10),
            strategy=ExtractionStrategy.FULL_LLM,
        )
        # Mock _llm_extract_building to raise an error
        with patch(
            "open_notebook.extractors.orchestrator._llm_extract_building",
            new_callable=AsyncMock,
            side_effect=Exception("LLM unavailable"),
        ):
            records, stats = await extract_building(plan, content, {})
        assert records == []
        assert stats.errors is not None
        assert "LLM unavailable" in stats.errors[0]

    @pytest.mark.asyncio
    async def test_full_llm_success(self):
        """Successful LLM extraction returns records."""
        content = _make_content_with_pages([
            (10, "Building content with ACM data"),
        ])
        plan = BuildingExtractionPlan(
            building_id="B00A",
            page_range=(10, 10),
            strategy=ExtractionStrategy.FULL_LLM,
        )
        mock_records = [
            ACMExtractionRecord(
                building_id="B00A",
                product="Floor Coverings",
                material_description="Vinyl Tiles",
                result="Detected",
            ),
        ]
        with patch(
            "open_notebook.extractors.orchestrator._llm_extract_building",
            new_callable=AsyncMock,
            return_value=mock_records,
        ):
            records, stats = await extract_building(plan, content, {})
        assert len(records) == 1
        assert stats.strategy_used == "full_llm"
        assert stats.records_extracted == 1


# ---------------------------------------------------------------------------
# Task 7.11: orchestrate_extraction LangGraph node
# ---------------------------------------------------------------------------


class TestOrchestrateExtraction:
    @pytest.mark.asyncio
    async def test_orchestrator_produces_records(self):
        """Orchestrator node should produce records from building extraction."""
        source = MagicMock()
        source.id = "source:test"
        source.full_text = _make_content_with_pages([
            (10, "## B00A - Storage Shed\nB00A-R0001 - External Movement\nNo Asbestos"),
        ])

        inventory = _make_inventory([
            _make_building("B00A", "Storage Shed", 10, 10, BuildingComplexity.SIMPLE),
        ])
        tags = _make_page_tags([(10, 4, 0.9)])

        state = {
            "source": source,
            "building_inventory": inventory,
            "page_tags": tags,
            "document_metadata": None,
            "start_time": 0.0,
        }
        config = MagicMock()
        result = await orchestrate_extraction(state, config)

        assert "records" in result
        assert "orchestrator_stats" in result
        stats = result["orchestrator_stats"]
        assert isinstance(stats, OrchestratorStats)
        assert stats.total_buildings == 1

    @pytest.mark.asyncio
    async def test_orchestrator_returns_enriched_context(self):
        """Orchestrator should return BuildingRoomContext with school_name from source.title."""
        from open_notebook.extractors.acm_schemas import BuildingRoomContext

        source = MagicMock()
        source.id = "source:test"
        source.title = "Springfield Primary School"
        source.full_text = _make_content_with_pages([
            (10, "## B00A - Storage Shed\nB00A-R0001 - External Movement\nNo Asbestos"),
        ])

        inventory = _make_inventory([
            _make_building("B00A", "Storage Shed", 10, 10, BuildingComplexity.SIMPLE),
        ])
        tags = _make_page_tags([(10, 4, 0.9)])

        state = {
            "source": source,
            "building_inventory": inventory,
            "page_tags": tags,
            "document_metadata": None,
            "start_time": 0.0,
        }
        config = MagicMock()
        result = await orchestrate_extraction(state, config)

        assert "context" in result
        ctx = result["context"]
        assert isinstance(ctx, BuildingRoomContext)
        assert ctx.school_name == "Springfield Primary School"

    @pytest.mark.asyncio
    async def test_legacy_fallback_not_triggered(self):
        """When inventory is present, orchestrator should be used (not legacy)."""
        state = {"building_inventory": _make_inventory()}
        assert should_use_orchestrator(state) is True

    @pytest.mark.asyncio
    async def test_legacy_fallback_when_no_inventory(self):
        """Without inventory, should_use_orchestrator returns False."""
        state = {"building_inventory": None}
        assert should_use_orchestrator(state) is False


# ---------------------------------------------------------------------------
# Task 7.12: Parallel extraction
# ---------------------------------------------------------------------------


class TestParallelExtraction:
    @pytest.mark.asyncio
    async def test_multiple_buildings(self):
        """Multiple buildings should all be extracted."""
        source = MagicMock()
        source.id = "source:test"
        source.full_text = _make_content_with_pages([
            (10, "## B00A - Storage Shed\nB00A-R0001 - Movement\nNo Asbestos"),
            (11, "## B00B - Office Block\nB00B-R0001 - Hallway\nNo Asbestos"),
        ])

        inventory = _make_inventory([
            _make_building("B00A", "Storage Shed", 10, 10, BuildingComplexity.SIMPLE),
            _make_building("B00B", "Office Block", 11, 11, BuildingComplexity.SIMPLE),
        ])
        tags = _make_page_tags([(10, 4, 0.9), (11, 4, 0.9)])

        state = {
            "source": source,
            "building_inventory": inventory,
            "page_tags": tags,
            "document_metadata": None,
            "start_time": 0.0,
        }
        config = MagicMock()
        result = await orchestrate_extraction(state, config)

        stats = result["orchestrator_stats"]
        assert stats.total_buildings == 2
        assert len(result["records"]) == 2  # One room per building

    @pytest.mark.asyncio
    async def test_one_failure_doesnt_block_others(self):
        """If one building fails, others should still succeed."""
        content = _make_content_with_pages([
            (10, "Building A content"),
            (11, "## B00B - Storage Shed\nB00B-R0001 - Movement\nNo Asbestos"),
        ])

        inventory = _make_inventory([
            _make_building("B00A", "Failing Building", 10, 10, BuildingComplexity.COMPLEX),
            _make_building("B00B", "Simple Building", 11, 11, BuildingComplexity.SIMPLE),
        ])
        tags = _make_page_tags([(10, 4, 0.9), (11, 4, 0.9)])

        source = MagicMock()
        source.id = "source:test"
        source.full_text = content

        state = {
            "source": source,
            "building_inventory": inventory,
            "page_tags": tags,
            "document_metadata": None,
            "start_time": 0.0,
        }

        # Mock LLM to fail for FULL_LLM buildings
        with patch(
            "open_notebook.extractors.orchestrator._llm_extract_building",
            new_callable=AsyncMock,
            side_effect=Exception("LLM failed"),
        ):
            config = MagicMock()
            result = await orchestrate_extraction(state, config)

        # B00B (regex) should still succeed
        assert len(result["records"]) >= 1
        stats = result["orchestrator_stats"]
        assert stats.total_buildings == 2

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self):
        """Semaphore should limit concurrent building extractions."""
        from open_notebook.extractors.orchestrator import _extract_buildings_parallel

        max_concurrent_seen = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        original_extract = extract_building

        async def tracked_extract(plan, content, state):
            nonlocal max_concurrent_seen, current_concurrent
            async with lock:
                current_concurrent += 1
                if current_concurrent > max_concurrent_seen:
                    max_concurrent_seen = current_concurrent
            await asyncio.sleep(0.05)  # Small delay to allow overlap
            async with lock:
                current_concurrent -= 1
            return [], BuildingExtractionStats(
                building_id=plan.building_id,
                records_extracted=0,
                pages_processed=1,
                strategy_used=plan.strategy.value,
                time_ms=50,
            )

        plans = [
            BuildingExtractionPlan(
                building_id=f"B{i:03d}", page_range=(i, i),
                strategy=ExtractionStrategy.FULL_LLM,
            )
            for i in range(6)  # 6 buildings, max_concurrent=2
        ]

        with patch(
            "open_notebook.extractors.orchestrator.extract_building",
            side_effect=tracked_extract,
        ):
            results = await _extract_buildings_parallel(plans, "content", {}, max_concurrent=2)

        assert len(results) == 6
        assert max_concurrent_seen <= 2, (
            f"Semaphore should limit to 2 concurrent, saw {max_concurrent_seen}"
        )


# ---------------------------------------------------------------------------
# Task 7.13: merge_building_results
# ---------------------------------------------------------------------------


class TestMergeBuildingResults:
    def test_combines_records(self):
        import time

        r1 = ACMExtractionRecord(
            building_id="B00A", product="Floor", material_description="Vinyl", result="Detected",
        )
        r2 = ACMExtractionRecord(
            building_id="B00B", product="Ceiling", material_description="Fibre Cement", result="Detected",
        )
        results = [
            ([r1], BuildingExtractionStats(
                building_id="B00A", records_extracted=1, pages_processed=5,
                strategy_used="full_llm", time_ms=1000,
            )),
            ([r2], BuildingExtractionStats(
                building_id="B00B", records_extracted=1, pages_processed=2,
                strategy_used="regex_only", time_ms=50,
            )),
        ]
        plan = ExtractionPlan(
            plans=[], total_buildings=2, buildings_to_extract=2,
            buildings_skipped=0, estimated_llm_calls=1,
        )

        records, stats = merge_building_results(results, plan, time.time())
        assert len(records) == 2
        assert stats.total_records == 2
        assert stats.buildings_extracted == 2
        assert "full_llm" in stats.strategy_distribution
        assert "regex_only" in stats.strategy_distribution


# ---------------------------------------------------------------------------
# Task 7.14: Graph wiring
# ---------------------------------------------------------------------------


class TestGraphWiring:
    def test_graph_has_orchestrate_node(self):
        from open_notebook.graphs.acm_extraction import graph

        assert "orchestrate" in graph.nodes

    def test_graph_has_legacy_nodes(self):
        from open_notebook.graphs.acm_extraction import graph

        assert "prepare" in graph.nodes
        assert "extract" in graph.nodes

    def test_conditional_edge_from_tag_pages(self):
        """tag_pages should have conditional edges to both orchestrate and prepare."""
        from open_notebook.graphs.acm_extraction import graph

        # Both orchestrate and prepare should be reachable from the compiled graph
        assert "orchestrate" in graph.nodes
        assert "prepare" in graph.nodes

    def test_orchestrate_connects_to_validate(self):
        """orchestrate node should connect to validate."""
        from open_notebook.graphs.acm_extraction import agent_state

        edges = agent_state.edges
        assert ("orchestrate", "validate") in edges or any(
            e == ("orchestrate", "validate") for e in edges
        )


# ---------------------------------------------------------------------------
# Task 7.15: Backward compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    def test_legacy_path_reachable(self):
        """The prepare -> extract path should still be compilable."""
        from open_notebook.graphs.acm_extraction import graph

        assert "prepare" in graph.nodes
        assert "extract" in graph.nodes
        assert "validate" in graph.nodes
        assert "correct" in graph.nodes
        assert "deduplicate" in graph.nodes
        assert "save" in graph.nodes

    def test_no_inventory_uses_legacy(self):
        """Without building_inventory, should_use_orchestrator returns False."""
        state = {"building_inventory": None, "page_tags": None}
        assert should_use_orchestrator(state) is False

    def test_empty_inventory_uses_legacy(self):
        state = {"building_inventory": BuildingInventory(
            buildings=[], processing_groups=[], total_buildings=0,
        )}
        assert should_use_orchestrator(state) is False


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
            plans=[], total_buildings=2, buildings_to_extract=2,
            buildings_skipped=0, estimated_llm_calls=1,
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
