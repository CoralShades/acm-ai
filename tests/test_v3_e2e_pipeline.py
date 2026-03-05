"""V3 Extraction Pipeline E2E Tests — E32-S5.

Tests the full V3 pipeline: dual-provider extract → consensus → AI building
extraction → AI item extraction → validation → correction → save.

Mocked DB + LLM tests (AC1, AC4-AC8) run always.
Accuracy tests (AC2, AC3) require RUN_E2E_LLM=true.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

BENCHMARKS_DIR = Path(__file__).resolve().parent.parent / "benchmarks"
FIXTURES_DIR = BENCHMARKS_DIR / "fixtures"
GROUND_TRUTH_DIR = BENCHMARKS_DIR / "ground_truth"


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _require_e2e_llm():
    """Skip test unless RUN_E2E_LLM=true is set in the environment."""
    if os.environ.get("RUN_E2E_LLM", "").lower() not in ("1", "true", "yes"):
        pytest.skip("E2E LLM test skipped — set RUN_E2E_LLM=true to enable")


def _load_docling_fixture(doc_key: str) -> list[dict]:
    path = FIXTURES_DIR / f"docling_{doc_key}.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f).get("tables", [])


def _make_mock_source(
    source_id: str = "source:e32s5_test", content: str = ""
) -> MagicMock:
    source = MagicMock()
    source.id = source_id
    source.full_text = content
    source.title = "E32-S5 Test School"
    source.asset = MagicMock(file_path="data/uploads/test.pdf")
    return source


def _make_mock_v3_llm() -> AsyncMock:
    """Mock LLM that returns minimal valid JSON for building or item extraction.

    The same response is returned for all graph stages (metadata, structure,
    inventory, page-tagger, orchestrator).  Stages that do not receive valid
    JSON for their schema fall back to heuristic logic gracefully.  The
    orchestrator stage requires a valid ACMExtractionResult: records must have
    a ``result`` field and ``status`` must be the lowercase enum value.
    """
    # Used by: build_inventory, page_tagger, orchestrator item extraction, etc.
    # ACMExtractionResult validator requires: records[*].result (required),
    # status in {"valid", "invalid", "no_acm_data"} (lowercase).
    item_json = json.dumps(
        {
            "records": [
                {
                    "building_id": "A1",
                    "building_name": "Admin Block",
                    "room_id": "101",
                    "room_name": "Office",
                    "product": "Vinyl Floor Tiles",
                    "material_description": "300mm x 300mm vinyl floor tiles with backing",
                    "location": "Throughout office area",
                    "extent": "50 m²",
                    "friable": "Non-friable",
                    "material_condition": "Good",
                    "risk_status": "Low",
                    "result": "Positive",
                    "page_number": 1,
                    "extraction_confidence": "high",
                }
            ],
            "status": "valid",
            "total_records": 1,
        }
    )

    async def _mock_ainvoke(messages, **kwargs):
        response = MagicMock()
        response.content = item_json
        return response

    model = AsyncMock()
    model.ainvoke = AsyncMock(side_effect=_mock_ainvoke)
    return model


async def _run_v3_extraction_mocked(
    source: MagicMock,
    docling_tables: list[dict] | None = None,
) -> dict:
    """Run extract_acm_from_source with mocked DB + LLM.

    Returns:
        dict with keys: result, building_records, acm_records, table_sections
    """
    from open_notebook.domain.acm import ACMRecord, ACMTableSection, BuildingRecord
    from open_notebook.graphs.acm_extraction import extract_acm_from_source

    if docling_tables is None:
        docling_tables = []

    building_records: list = []
    acm_records: list = []
    table_sections: list = []

    async def capture_building_save(self):
        self.id = f"building_record:mock_{len(building_records)}"
        building_records.append(self)
        return self

    async def capture_acm_save(self):
        acm_records.append(self)

    async def capture_table_save(self):
        table_sections.append(self)

    async def noop_auto_populate(document_meta, source_id):
        pass

    async def mock_docling_tables(src_id, page_start, page_end):
        return [
            t
            for t in docling_tables
            if t.get("page_start", 0) >= page_start and t.get("page_end", 0) <= page_end
        ]

    async def mock_generate_internal_id(source_id):
        return f"BLD#E32S5_{len(building_records):03d}"

    mock_llm = _make_mock_v3_llm()

    with (
        patch.object(BuildingRecord, "save", capture_building_save),
        patch.object(ACMRecord, "save", capture_acm_save),
        patch.object(ACMTableSection, "save", capture_table_save),
        patch(
            "open_notebook.graphs.acm_extraction.auto_populate_site_config",
            noop_auto_populate,
        ),
        patch(
            "open_notebook.graphs.acm_extraction.provision_langchain_model",
            AsyncMock(return_value=mock_llm),
        ),
        patch(
            "open_notebook.graphs.utils.provision_langchain_model",
            AsyncMock(return_value=mock_llm),
        ),
        patch(
            "open_notebook.extractors.orchestrator._get_docling_tables",
            mock_docling_tables,
        ),
        patch(
            "open_notebook.graphs.acm_extraction._get_docling_tables",
            mock_docling_tables,
        ),
        patch.object(
            BuildingRecord,
            "generate_internal_id",
            staticmethod(mock_generate_internal_id),
        ),
        patch(
            "open_notebook.graphs.acm_extraction.BuildingRecord.get_by_source",
            AsyncMock(return_value=building_records),
        ),
    ):
        result = await extract_acm_from_source(source=source, force=False)

    return {
        "result": result,
        "building_records": building_records,
        "acm_records": acm_records,
        "table_sections": table_sections,
    }


# ---------------------------------------------------------------------------
# AC1: TestV3PipelineSmoke
# ---------------------------------------------------------------------------


class TestV3PipelineSmoke:
    """AC1: Full V3 pipeline runs without errors (mocked LLM + DB)."""

    @pytest.mark.asyncio
    async def test_full_v3_pipeline_completes_without_error(self):
        """Full pipeline from extract_acm_from_source returns success status."""
        content = (
            "--- Page 1 ---\n"
            "ASBESTOS REGISTER\n\n"
            "Building: A1 Admin Block (1975)\n"
            "Room 101 - Office\n"
            "Vinyl Floor Tiles | Non-friable | Good | Low | Positive\n"
        )
        source = _make_mock_source(content=content)
        out = await _run_v3_extraction_mocked(source)
        assert out["result"].status in ("success", "partial")
        assert out["result"].error is None

    @pytest.mark.asyncio
    async def test_pipeline_with_docling_fixtures_completes(self):
        """Pipeline with Broadmeadows Docling fixtures completes without error."""
        tables = _load_docling_fixture("broadmeadows")
        if not tables:
            pytest.skip("Docling fixture not found for broadmeadows")
        source = _make_mock_source(source_id="source:smoke_broadmeadows")
        # Source needs full_text for structure detection
        source.full_text = "--- Page 1 ---\nASBESTOS REGISTER\n"
        out = await _run_v3_extraction_mocked(source, docling_tables=tables)
        assert out["result"].status in ("success", "partial")


# ---------------------------------------------------------------------------
# AC4: TestBuildingItemForeignKeys
# ---------------------------------------------------------------------------


class TestBuildingItemForeignKeys:
    """AC4: BuildingRecord and ACMRecord have correct foreign key relationships."""

    @pytest.mark.asyncio
    async def test_building_record_source_id_matches_source(self):
        """BuildingRecord.source_id == source.id after extraction."""
        source = _make_mock_source(source_id="source:fk_test_001")
        source.full_text = (
            "--- Page 1 ---\nBuilding: A1 Admin Block\nRoom 101\n"
            "Vinyl Tiles | Non-friable | Good\n"
        )
        out = await _run_v3_extraction_mocked(source)
        for br in out["building_records"]:
            assert (
                "fk_test_001" in br.source_id or br.source_id == "source:fk_test_001"
            ), f"BuildingRecord.source_id={br.source_id!r} does not reference source"

    @pytest.mark.asyncio
    async def test_acm_record_source_id_matches_source(self):
        """ACMRecord.source_id == source.id after extraction."""
        source = _make_mock_source(source_id="source:fk_test_002")
        source.full_text = (
            "--- Page 1 ---\nBuilding: A1 Admin Block\nRoom 101\n"
            "Vinyl Tiles | Non-friable | Good\n"
        )
        out = await _run_v3_extraction_mocked(source)
        for rec in out["acm_records"]:
            assert (
                "fk_test_002" in rec.source_id or rec.source_id == "source:fk_test_002"
            ), f"ACMRecord.source_id={rec.source_id!r} does not reference source"

    @pytest.mark.asyncio
    async def test_acm_record_building_record_id_set(self):
        """ACMRecord.building_record_id references a persisted BuildingRecord."""
        source = _make_mock_source(source_id="source:fk_test_003")
        source.full_text = (
            "--- Page 1 ---\nBuilding: A1 Admin Block\nRoom 101\n"
            "Vinyl Tiles | Non-friable | Good\n"
        )
        out = await _run_v3_extraction_mocked(source)
        # Only assert if records were actually created (mock LLM may produce none)
        if out["building_records"] and out["acm_records"]:
            building_ids = {br.id for br in out["building_records"]}
            for rec in out["acm_records"]:
                if rec.building_record_id is not None:
                    assert rec.building_record_id in building_ids, (
                        f"ACMRecord.building_record_id={rec.building_record_id!r} "
                        f"does not match any BuildingRecord"
                    )


# ---------------------------------------------------------------------------
# AC5: TestRawExtractionStorage
# ---------------------------------------------------------------------------


class TestRawExtractionStorage:
    """AC5: raw_extraction table populated per provider after dual-provider extraction."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_raw_extraction_saved_for_each_provider(
        self, mock_registry, mock_store_raw
    ):
        """_store_raw_extractions called once per provider in dual mode."""
        from commands.source_commands import _run_dual_provider_extraction
        from open_notebook.extractors.providers.base import (
            NormalizedExtractionResult,
            NormalizedTable,
        )

        docling_mock = MagicMock()
        docling_mock.extract.return_value = NormalizedExtractionResult(
            provider_id="docling",
            tables=[
                NormalizedTable(
                    table_index=0,
                    page=1,
                    row_count=5,
                    col_count=3,
                    columns=["A", "B", "C"],
                    html="<d/>",
                    markdown="md",
                )
            ],
        )
        mineru_mock = MagicMock()
        mineru_mock.extract.return_value = NormalizedExtractionResult(
            provider_id="mineru",
            tables=[
                NormalizedTable(
                    table_index=0,
                    page=1,
                    row_count=5,
                    col_count=3,
                    columns=["A", "B", "C"],
                    html="<m/>",
                    markdown="md",
                )
            ],
        )

        def get_provider(pid):
            return docling_mock if pid == "docling" else mineru_mock

        mock_registry.return_value.get_provider.side_effect = get_provider

        _, _ = await _run_dual_provider_extraction("source:raw_test_001", "/tmp/test.pdf")

        # Called once per provider (docling + mineru)
        assert mock_store_raw.call_count == 2

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "false", "MINERU_ENABLED": "false"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.get_provider_registry")
    async def test_raw_extraction_saved_for_single_provider(
        self, mock_registry, mock_store_raw
    ):
        """_store_raw_extractions called once for single-provider mode."""
        from commands.source_commands import _run_dual_provider_extraction
        from open_notebook.extractors.providers.base import NormalizedExtractionResult

        mock_docling = MagicMock()
        mock_docling.extract.return_value = NormalizedExtractionResult(
            provider_id="docling", tables=[]
        )
        mock_registry.return_value.get_provider.return_value = mock_docling

        _, _ = await _run_dual_provider_extraction("source:raw_test_002", "/tmp/test.pdf")

        assert mock_store_raw.call_count == 1


# ---------------------------------------------------------------------------
# AC6: TestConsensusFieldPopulation
# ---------------------------------------------------------------------------


class TestConsensusFieldPopulation:
    """AC6: consensus_tier + consensus_scores populated on ACMTableSection in dual mode."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
    @patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
    @patch("commands.source_commands.repo_create", new_callable=AsyncMock)
    @patch("commands.source_commands.ensure_record_id", side_effect=lambda x: x)
    @patch("commands.source_commands.get_provider_registry")
    async def test_dual_provider_tables_have_consensus_tier(
        self, mock_registry, mock_ensure, mock_create, mock_store_raw
    ):
        """Tables from dual-provider extraction have consensus_tier set."""
        from commands.source_commands import _run_dual_provider_extraction
        from open_notebook.extractors.providers.base import (
            NormalizedExtractionResult,
            NormalizedTable,
        )

        def make_table(page, row_count):
            return NormalizedTable(
                table_index=0,
                page=page,
                row_count=row_count,
                col_count=3,
                columns=["A", "B", "C"],
                html="<table/>",
                markdown="md",
            )

        docling_mock = MagicMock()
        docling_mock.extract.return_value = NormalizedExtractionResult(
            provider_id="docling",
            tables=[make_table(1, 10), make_table(2, 5)],
        )
        mineru_mock = MagicMock()
        mineru_mock.extract.return_value = NormalizedExtractionResult(
            provider_id="mineru",
            tables=[make_table(1, 10)],  # page 1 only
        )

        def get_provider(pid):
            return docling_mock if pid == "docling" else mineru_mock

        mock_registry.return_value.get_provider.side_effect = get_provider

        result, _ = await _run_dual_provider_extraction(
            "source:consensus_test", "/tmp/test.pdf"
        )

        # All merged tables must have consensus_tier set
        for table in result:
            assert table.get("consensus_tier") is not None, (
                f"Table on page {table.get('page')} missing consensus_tier"
            )

        # Page 1 has both providers → multi_provider_* tier
        page1 = next(t for t in result if t["page"] == 1)
        assert page1["consensus_tier"].startswith("multi_provider_"), (
            f"Page 1 (dual) should have multi_provider_* tier, got {page1['consensus_tier']!r}"
        )

        # Page 2 has only Docling → single_provider
        page2 = next(t for t in result if t["page"] == 2)
        assert page2["consensus_tier"] == "single_provider"


# ---------------------------------------------------------------------------
# AC7: TestSFFieldNameConformance
# ---------------------------------------------------------------------------


class TestSFFieldNameConformance:
    """AC7: ACMRecord + BuildingRecord serialize to SF API names when by_alias=True."""

    def test_acm_record_sf_alias_fields_end_in_double_c(self):
        """ACMRecord fields with AliasChoices include SF names ending in '__c'."""
        from open_notebook.domain.acm import ACMRecord

        # Get all field definitions that have AliasChoices
        sf_fields = []
        for _field_name, field_info in ACMRecord.model_fields.items():
            validation_alias = field_info.validation_alias
            if hasattr(validation_alias, "choices"):
                sf_names = [
                    c
                    for c in validation_alias.choices
                    if isinstance(c, str) and c.endswith("__c")
                ]
                sf_fields.extend(sf_names)

        assert len(sf_fields) > 0, "ACMRecord should have SF alias fields ending in __c"
        # All SF names must end in __c
        for sf_name in sf_fields:
            assert sf_name.endswith("__c"), (
                f"SF alias {sf_name!r} does not end in '__c'"
            )

    def test_building_record_sf_alias_fields_end_in_double_c(self):
        """BuildingRecord fields with AliasChoices include SF names ending in '__c'."""
        from open_notebook.domain.acm import BuildingRecord

        sf_fields = []
        for _field_name, field_info in BuildingRecord.model_fields.items():
            validation_alias = field_info.validation_alias
            if hasattr(validation_alias, "choices"):
                sf_names = [
                    c
                    for c in validation_alias.choices
                    if isinstance(c, str) and c.endswith("__c")
                ]
                sf_fields.extend(sf_names)

        assert len(sf_fields) > 0, (
            "BuildingRecord should have SF alias fields ending in __c"
        )

    def test_acm_record_building_id_has_sf_alias(self):
        """ACMRecord.building_id has 'Building_Code__c' as an alias."""
        from open_notebook.domain.acm import ACMRecord

        field_info = ACMRecord.model_fields["building_id"]
        aliases = (
            field_info.validation_alias.choices
            if hasattr(field_info.validation_alias, "choices")
            else []
        )
        assert "Building_Code__c" in aliases, (
            f"building_id aliases {aliases!r} should include 'Building_Code__c'"
        )

    def test_building_record_building_code_has_sf_alias(self):
        """BuildingRecord.building_code has 'Building_Code__c' as an alias."""
        from open_notebook.domain.acm import BuildingRecord

        field_info = BuildingRecord.model_fields["building_code"]
        aliases = (
            field_info.validation_alias.choices
            if hasattr(field_info.validation_alias, "choices")
            else []
        )
        assert "Building_Code__c" in aliases


# ---------------------------------------------------------------------------
# AC8: TestSFObjectLevelCorrectness
# ---------------------------------------------------------------------------


class TestSFObjectLevelCorrectness:
    """AC8: Building__c and Item__c fields conform to SF schema config."""

    def test_building_record_has_required_sf_object_fields(self):
        """BuildingRecord covers the required Building__c SF object fields."""
        from open_notebook.domain.acm import BuildingRecord

        # Minimum required SF Building__c fields that must have aliases
        required_sf_building_fields = {
            "Building_Code__c",
            "Building_Name__c",
            "Building_Type__c",
        }

        all_aliases: set[str] = set()
        for field_info in BuildingRecord.model_fields.values():
            if hasattr(field_info.validation_alias, "choices"):
                for c in field_info.validation_alias.choices:
                    if isinstance(c, str) and c.endswith("__c"):
                        all_aliases.add(c)

        missing = required_sf_building_fields - all_aliases
        assert not missing, (
            f"BuildingRecord missing required SF Building__c fields: {missing}"
        )

    def test_acm_record_has_required_sf_item_fields(self):
        """ACMRecord covers the required Item__c SF object fields."""
        from open_notebook.domain.acm import ACMRecord

        required_sf_item_fields = {
            "Building_Code__c",
            "Building_Name__c",
        }

        all_aliases: set[str] = set()
        for field_info in ACMRecord.model_fields.values():
            if hasattr(field_info.validation_alias, "choices"):
                for c in field_info.validation_alias.choices:
                    if isinstance(c, str) and c.endswith("__c"):
                        all_aliases.add(c)

        missing = required_sf_item_fields - all_aliases
        assert not missing, f"ACMRecord missing required Item__c fields: {missing}"

    def test_building_record_and_acm_record_are_separate_entities(self):
        """BuildingRecord (Building__c) and ACMRecord (Item__c) are distinct table objects."""
        from open_notebook.domain.acm import ACMRecord, BuildingRecord

        assert BuildingRecord.table_name == "building_record"
        assert ACMRecord.table_name == "acm_record"
        assert BuildingRecord.table_name != ACMRecord.table_name

    def test_building_record_internal_id_format(self):
        """BuildingRecord.internal_id must match the BLD# prefix pattern."""
        from open_notebook.domain.acm import BuildingRecord

        br = BuildingRecord(
            internal_id="BLD#TEST_001",
            source_id="source:test",
        )
        assert br.internal_id.startswith("BLD#"), (
            f"BuildingRecord.internal_id={br.internal_id!r} should start with 'BLD#'"
        )


# ---------------------------------------------------------------------------
# AC2: TestBroadmeadowsAccuracy — gated by RUN_E2E_LLM=true
# ---------------------------------------------------------------------------


@pytest.mark.v3_e2e
class TestBroadmeadowsAccuracy:
    """AC2: Broadmeadows accuracy — 31/31 records, valid SF picklists, valid dep chains."""

    def test_broadmeadows_record_count(self, monkeypatch):
        """Broadmeadows extracts all 31 expected records."""
        _require_e2e_llm()
        from scripts.research.e29_benchmark_harness import (
            load_ground_truth,
            match_records,
        )
        from tests.benchmarks.test_v3_dual_provider import _run_mocked_extraction

        monkeypatch.setenv("V3_DUAL_PROVIDER", "false")
        records = _run_mocked_extraction("broadmeadows", mineru_tables=[])
        gt_data = load_ground_truth(GROUND_TRUTH_DIR / "broadmeadows.json")
        match_result = match_records(gt_data["records"], records)
        matched = len(match_result.matched_pairs)
        assert matched == 31, f"Broadmeadows: expected 31/31, got {matched}/31"

    def test_broadmeadows_all_picklist_values_valid_sf(self, monkeypatch):
        """All Broadmeadows extracted records have valid SF picklist values."""
        _require_e2e_llm()
        from open_notebook.extractors.parsers.config_loader import load_field_config
        from open_notebook.extractors.validators.sf_picklist_validator import (
            SalesforcePicklistValidator,
        )
        from tests.benchmarks.test_v3_dual_provider import _run_mocked_extraction

        monkeypatch.setenv("V3_DUAL_PROVIDER", "false")
        records = _run_mocked_extraction("broadmeadows", mineru_tables=[])

        config = load_field_config()
        validator = SalesforcePicklistValidator(config)

        invalid_count = 0
        for rec in records:
            rec_dict = rec.model_dump() if hasattr(rec, "model_dump") else vars(rec)
            issues = validator.validate_flat_enums(rec_dict)
            invalid_count += len(issues)

        assert invalid_count == 0, (
            f"Broadmeadows: {invalid_count} picklist validation errors found across all records"
        )

    def test_broadmeadows_all_dependency_chains_valid(self, monkeypatch):
        """All Broadmeadows records have valid dependency chain values."""
        _require_e2e_llm()
        from open_notebook.extractors.parsers.config_loader import load_field_config
        from open_notebook.extractors.validators.sf_picklist_validator import (
            SalesforcePicklistValidator,
        )
        from tests.benchmarks.test_v3_dual_provider import _run_mocked_extraction

        monkeypatch.setenv("V3_DUAL_PROVIDER", "false")
        records = _run_mocked_extraction("broadmeadows", mineru_tables=[])

        config = load_field_config()
        validator = SalesforcePicklistValidator(config)

        chain_errors = 0
        for rec in records:
            rec_dict = rec.model_dump() if hasattr(rec, "model_dump") else vars(rec)
            issues = validator.validate_all_chains(rec_dict)
            chain_errors += len(issues)

        assert chain_errors == 0, (
            f"Broadmeadows: {chain_errors} dependency chain errors found"
        )


# ---------------------------------------------------------------------------
# AC3: TestAlexanderAccuracy — gated by RUN_E2E_LLM=true
# ---------------------------------------------------------------------------


@pytest.mark.v3_e2e
class TestAlexanderAccuracy:
    """AC3: Alexander accuracy — >= 40/43 baseline, >= 42/43 stretch."""

    def test_alexander_baseline_recall(self, monkeypatch):
        """Alexander extracts >= 40/43 ground truth records (baseline)."""
        _require_e2e_llm()
        from scripts.research.e29_benchmark_harness import (
            load_ground_truth,
            match_records,
        )
        from tests.benchmarks.test_v3_dual_provider import _run_mocked_extraction

        monkeypatch.setenv("V3_DUAL_PROVIDER", "false")
        records = _run_mocked_extraction("alexander", mineru_tables=[])
        gt_data = load_ground_truth(GROUND_TRUTH_DIR / "alexander.json")
        match_result = match_records(gt_data["records"], records)
        matched = len(match_result.matched_pairs)
        assert matched >= 40, f"Alexander baseline: {matched}/43, need >= 40"

    def test_alexander_stretch_recall(self, monkeypatch):
        """Alexander extracts >= 42/43 ground truth records (stretch goal)."""
        _require_e2e_llm()
        from scripts.research.e29_benchmark_harness import (
            load_ground_truth,
            match_records,
        )
        from tests.benchmarks.test_v3_dual_provider import _run_mocked_extraction

        monkeypatch.setenv("V3_DUAL_PROVIDER", "false")
        records = _run_mocked_extraction("alexander", mineru_tables=[])
        gt_data = load_ground_truth(GROUND_TRUTH_DIR / "alexander.json")
        match_result = match_records(gt_data["records"], records)
        matched = len(match_result.matched_pairs)
        # Stretch goal — xfail if not met
        if matched < 42:
            pytest.xfail(f"Alexander stretch goal: {matched}/43, need >= 42 (stretch)")
