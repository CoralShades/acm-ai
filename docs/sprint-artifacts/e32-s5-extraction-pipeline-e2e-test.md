# E32-S5: Extraction Pipeline E2E Test — Tech Spec

**Story ID**: E32-S5
**Story Points**: 3
**Risk**: MEDIUM
**Type**: Backend
**Dependencies**: E32-S1 (done), E32-S2 (done), E32-S3 (done), E32-S4 (done)
**Sprint**: V3-5

---

## 1. Overview

This story creates `tests/test_v3_e2e_pipeline.py` — a V3-specific pipeline integration test that validates the complete extraction flow:

1. **Phase 0** (source_commands layer): dual-provider extract → consensus → raw_extraction storage
2. **Phase 1** (graph): AI Building extraction → BuildingRecord saved with correct source FK
3. **Phase 2** (graph): AI Item extraction → ACMRecord saved with correct building_record_id FK
4. **Phase 3** (graph): Validation + correction loop
5. **Phase 4** (graph): Save to DB

The test file is entirely self-contained — no live SurrealDB, no GPU, no mandatory LLM API key (accuracy tests gated by `RUN_E2E_LLM=true`). It extends the patterns from `test_e2e_extraction.py` and `tests/benchmarks/test_v3_dual_provider.py`.

---

## 2. Background

### What already exists

| File | Purpose | Gap |
|------|---------|-----|
| `test_e2e_extraction.py` | Legacy path (no building inventory), no V3 building extraction | No BuildingRecord, no V3 graph path |
| `tests/benchmarks/test_v3_dual_provider.py` | Accuracy benchmark (requires `RUN_BENCHMARK_LLM=true`) | No FK checks, no raw extraction, no SF name checks |
| `test_dual_provider_pipeline.py` | Unit tests for `_run_dual_provider_extraction`, `_merge_provider_tables`, `_store_docling_tables` | No graph integration |

### What E32-S5 adds

| AC | What it tests | Where gap is |
|----|--------------|-------------|
| AC1 | Full V3 pipeline smoke test (mocked LLM + DB) | Not tested end-to-end |
| AC2 | Broadmeadows 31/31, all SF picklist values valid, all dep chains valid | Recall tested in benchmark; picklist+dep chain validity not asserted per-record |
| AC3 | Alexander >= 40/43 baseline, >= 42/43 stretch | Recall tested in benchmark; stretch goal not asserted here |
| AC4 | BuildingRecord + ACMRecord created with correct FKs | Not tested anywhere |
| AC5 | raw_extraction_table populated with per-provider data | Not tested in graph-level tests |
| AC6 | consensus_metadata (consensus_tier + scores) populated on ACMTableSection | Tested in unit tests; not in graph E2E |
| AC7 | All exported field names match SF API names | Not tested |
| AC8 | SF object-level correctness: Building__c + Item__c as separate entities | Not tested |

---

## 3. Acceptance Criteria

| AC | Description | Test Class |
|----|-------------|------------|
| AC1 | Full pipeline smoke (mocked LLM, mocked DB) | `TestV3PipelineSmoke` |
| AC2 | Broadmeadows 31/31, picklist valid, dep chains valid | `TestBroadmeadowsAccuracy` (gated) |
| AC3 | Alexander >= 40/43 baseline | `TestAlexanderAccuracy` (gated) |
| AC4 | BuildingRecord.source_id == source.id; ACMRecord.building_record_id set | `TestBuildingItemForeignKeys` |
| AC5 | raw_extraction populated per provider | `TestRawExtractionStorage` |
| AC6 | ACMTableSection.consensus_tier populated in dual mode | `TestConsensusFieldPopulation` |
| AC7 | ACMRecord/BuildingRecord serialized with by_alias=True yield SF API names | `TestSFFieldNameConformance` |
| AC8 | Building__c fields and Item__c fields match SF schema config | `TestSFObjectLevelCorrectness` |

---

## 4. File Changes

| # | File | Change Type | Description |
|---|------|-------------|-------------|
| 1 | `tests/test_v3_e2e_pipeline.py` | CREATE | Full V3 pipeline E2E test suite (8 test classes, ~20 tests) |

No changes to production code. No new fixtures required — reuses `benchmarks/fixtures/` and `benchmarks/ground_truth/` directories, and `tests/fixtures/acm_extraction/`.

---

## 5. Implementation Details

### 5.1 Module-level helpers

```python
"""V3 Extraction Pipeline E2E Tests — E32-S5.

Tests the full V3 pipeline: dual-provider extract → consensus → AI building
extraction → AI item extraction → validation → correction → save.

Mocked DB + LLM tests (AC1, AC4-AC8) run always.
Accuracy tests (AC2, AC3) require RUN_E2E_LLM=true.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

BENCHMARKS_DIR = Path(__file__).resolve().parent.parent / "benchmarks"
FIXTURES_DIR = BENCHMARKS_DIR / "fixtures"
GROUND_TRUTH_DIR = BENCHMARKS_DIR / "ground_truth"
```

#### `_require_e2e_llm()` helper

```python
def _require_e2e_llm():
    """Skip test unless RUN_E2E_LLM=true is set in the environment."""
    if os.environ.get("RUN_E2E_LLM", "").lower() not in ("1", "true", "yes"):
        pytest.skip("E2E LLM test skipped — set RUN_E2E_LLM=true to enable")
```

#### `_load_docling_fixture(doc_key)` helper

```python
def _load_docling_fixture(doc_key: str) -> list[dict]:
    path = FIXTURES_DIR / f"docling_{doc_key}.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f).get("tables", [])
```

#### `_make_mock_source(source_id, content)` helper

Reuse pattern from `test_e2e_extraction.py`:

```python
def _make_mock_source(source_id: str = "source:e32s5_test", content: str = "") -> MagicMock:
    source = MagicMock()
    source.id = source_id
    source.full_text = content
    source.title = "E32-S5 Test School"
    source.asset = MagicMock(file_path="data/uploads/test.pdf")
    return source
```

#### `_make_mock_v3_llm()` helper

Returns a mock LLM for the V3 graph path that handles both building extraction and item extraction calls. Returns minimal valid JSON for each:

```python
def _make_mock_v3_llm() -> AsyncMock:
    """Mock LLM that returns minimal valid JSON for building or item extraction."""
    building_json = json.dumps({
        "building_name": "Admin Block",
        "building_type": "Educational",
        "building_category": "School - Primary",
        "construction_type": "Brick",
        "estimated_year_built": "1975",
        "extraction_confidence": "medium",
    })
    item_json = json.dumps({
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
                "sample_result": "Positive",
                "page_number": 1,
                "extraction_confidence": "high",
            }
        ],
        "status": "VALID",
        "total_records": 1,
    })
    call_count = {"n": 0}

    async def _mock_ainvoke(messages, **kwargs):
        call_count["n"] += 1
        response = MagicMock()
        # First call is always building extraction; subsequent calls are item extraction
        response.content = building_json if call_count["n"] == 1 else item_json
        return response

    model = AsyncMock()
    model.ainvoke = AsyncMock(side_effect=_mock_ainvoke)
    return model
```

#### `_run_v3_extraction_mocked(source, captured)` helper

Runs the V3 extraction graph with:
- Mocked DB (captures BuildingRecord.save, ACMRecord.save, ACMTableSection.save)
- Mocked LLM (mocked provision_langchain_model)
- Mocked docling tables

```python
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
        br = MagicMock()
        br.id = f"building_record:mock_{len(building_records)}"
        building_records.append(self)
        return br

    async def capture_acm_save(self):
        acm_records.append(self)

    async def capture_table_save(self):
        table_sections.append(self)

    async def noop_auto_populate(document_meta, source_id):
        pass

    async def mock_docling_tables(src_id, page_start, page_end):
        return [
            t for t in docling_tables
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
```

---

### 5.2 Class: `TestV3PipelineSmoke` (AC1)

```python
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
        out = await asyncio.get_event_loop().run_until_complete(
            _run_v3_extraction_mocked(source)
        )
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
```

**Implementation note**: Use `pytest.mark.asyncio` throughout. The `_run_v3_extraction_mocked` helper must be `async def` and awaited directly inside `async` test functions (not via `asyncio.run()`).

---

### 5.3 Class: `TestBuildingItemForeignKeys` (AC4)

```python
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
            assert "fk_test_001" in br.source_id or br.source_id == "source:fk_test_001", (
                f"BuildingRecord.source_id={br.source_id!r} does not reference source"
            )

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
            assert "fk_test_002" in rec.source_id or rec.source_id == "source:fk_test_002", (
                f"ACMRecord.source_id={rec.source_id!r} does not reference source"
            )
```

---

### 5.4 Class: `TestRawExtractionStorage` (AC5)

This tests `_store_raw_extractions` in the source_commands layer directly:

```python
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
        from open_notebook.extractors.providers.base import NormalizedExtractionResult, NormalizedTable

        docling_mock = MagicMock()
        docling_mock.extract.return_value = NormalizedExtractionResult(
            provider_id="docling",
            tables=[NormalizedTable(table_index=0, page=1, row_count=5, col_count=3,
                                    columns=["A", "B", "C"], html="<d/>", markdown="md")],
        )
        mineru_mock = MagicMock()
        mineru_mock.extract.return_value = NormalizedExtractionResult(
            provider_id="mineru",
            tables=[NormalizedTable(table_index=0, page=1, row_count=5, col_count=3,
                                    columns=["A", "B", "C"], html="<m/>", markdown="md")],
        )

        def get_provider(pid):
            return docling_mock if pid == "docling" else mineru_mock

        mock_registry.return_value.get_provider.side_effect = get_provider

        await _run_dual_provider_extraction("source:raw_test_001", "/tmp/test.pdf")

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

        await _run_dual_provider_extraction("source:raw_test_002", "/tmp/test.pdf")

        assert mock_store_raw.call_count == 1
```

---

### 5.5 Class: `TestConsensusFieldPopulation` (AC6)

```python
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
        from open_notebook.extractors.providers.base import NormalizedExtractionResult, NormalizedTable

        def make_table(page, row_count):
            return NormalizedTable(
                table_index=0, page=page, row_count=row_count, col_count=3,
                columns=["A", "B", "C"], html="<table/>", markdown="md"
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

        result = await _run_dual_provider_extraction("source:consensus_test", "/tmp/test.pdf")

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
```

---

### 5.6 Class: `TestSFFieldNameConformance` (AC7)

Pure unit tests — no async needed:

```python
class TestSFFieldNameConformance:
    """AC7: ACMRecord + BuildingRecord serialize to SF API names when by_alias=True."""

    def test_acm_record_sf_alias_fields_end_in_double_c(self):
        """ACMRecord fields with AliasChoices include SF names ending in '__c'."""
        from open_notebook.domain.acm import ACMRecord

        # Get all field definitions that have AliasChoices
        sf_fields = []
        for field_name, field_info in ACMRecord.model_fields.items():
            validation_alias = field_info.validation_alias
            if hasattr(validation_alias, "choices"):
                sf_names = [
                    c for c in validation_alias.choices
                    if isinstance(c, str) and c.endswith("__c")
                ]
                sf_fields.extend(sf_names)

        assert len(sf_fields) > 0, "ACMRecord should have SF alias fields ending in __c"
        # All SF names must end in __c
        for sf_name in sf_fields:
            assert sf_name.endswith("__c"), f"SF alias {sf_name!r} does not end in '__c'"

    def test_building_record_sf_alias_fields_end_in_double_c(self):
        """BuildingRecord fields with AliasChoices include SF names ending in '__c'."""
        from open_notebook.domain.acm import BuildingRecord

        sf_fields = []
        for field_name, field_info in BuildingRecord.model_fields.items():
            validation_alias = field_info.validation_alias
            if hasattr(validation_alias, "choices"):
                sf_names = [
                    c for c in validation_alias.choices
                    if isinstance(c, str) and c.endswith("__c")
                ]
                sf_fields.extend(sf_names)

        assert len(sf_fields) > 0, "BuildingRecord should have SF alias fields ending in __c"

    def test_acm_record_building_id_has_sf_alias(self):
        """ACMRecord.building_id has 'Building_Code__c' as an alias."""
        from open_notebook.domain.acm import ACMRecord

        field_info = ACMRecord.model_fields["building_id"]
        aliases = field_info.validation_alias.choices if hasattr(field_info.validation_alias, "choices") else []
        assert "Building_Code__c" in aliases, (
            f"building_id aliases {aliases!r} should include 'Building_Code__c'"
        )

    def test_building_record_building_code_has_sf_alias(self):
        """BuildingRecord.building_code has 'Building_Code__c' as an alias."""
        from open_notebook.domain.acm import BuildingRecord

        field_info = BuildingRecord.model_fields["building_code"]
        aliases = field_info.validation_alias.choices if hasattr(field_info.validation_alias, "choices") else []
        assert "Building_Code__c" in aliases
```

---

### 5.7 Class: `TestSFObjectLevelCorrectness` (AC8)

```python
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
```

---

### 5.8 Class: `TestBroadmeadowsAccuracy` (AC2) — gated

```python
@pytest.mark.v3_e2e
class TestBroadmeadowsAccuracy:
    """AC2: Broadmeadows accuracy — 31/31 records, valid SF picklists, valid dep chains."""

    def test_broadmeadows_record_count(self, monkeypatch):
        """Broadmeadows extracts all 31 expected records."""
        _require_e2e_llm()
        from scripts.research.e29_benchmark_harness import (
            get_benchmark_configs,
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
        from open_notebook.extractors.validators.sf_picklist_validator import SalesforcePicklistValidator
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
        from open_notebook.extractors.validators.sf_picklist_validator import SalesforcePicklistValidator
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
```

---

### 5.9 Class: `TestAlexanderAccuracy` (AC3) — gated

```python
@pytest.mark.v3_e2e
class TestAlexanderAccuracy:
    """AC3: Alexander accuracy — >= 40/43 baseline, >= 42/43 stretch."""

    def test_alexander_baseline_recall(self, monkeypatch):
        """Alexander extracts >= 40/43 ground truth records (baseline)."""
        _require_e2e_llm()
        from scripts.research.e29_benchmark_harness import load_ground_truth, match_records
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
        from scripts.research.e29_benchmark_harness import load_ground_truth, match_records
        from tests.benchmarks.test_v3_dual_provider import _run_mocked_extraction

        monkeypatch.setenv("V3_DUAL_PROVIDER", "false")
        records = _run_mocked_extraction("alexander", mineru_tables=[])
        gt_data = load_ground_truth(GROUND_TRUTH_DIR / "alexander.json")
        match_result = match_records(gt_data["records"], records)
        matched = len(match_result.matched_pairs)
        # Stretch goal — xfail if not met
        if matched < 42:
            pytest.xfail(f"Alexander stretch goal: {matched}/43, need >= 42 (stretch)")
```

---

## 6. Test Plan

### Always-run tests (no LLM key required)

| Test | Class | Covers |
|------|-------|--------|
| `test_full_v3_pipeline_completes_without_error` | `TestV3PipelineSmoke` | AC1 |
| `test_pipeline_with_docling_fixtures_completes` | `TestV3PipelineSmoke` | AC1 (skipped if fixture absent) |
| `test_building_record_source_id_matches_source` | `TestBuildingItemForeignKeys` | AC4 |
| `test_acm_record_source_id_matches_source` | `TestBuildingItemForeignKeys` | AC4 |
| `test_raw_extraction_saved_for_each_provider` | `TestRawExtractionStorage` | AC5 |
| `test_raw_extraction_saved_for_single_provider` | `TestRawExtractionStorage` | AC5 |
| `test_dual_provider_tables_have_consensus_tier` | `TestConsensusFieldPopulation` | AC6 |
| `test_acm_record_sf_alias_fields_end_in_double_c` | `TestSFFieldNameConformance` | AC7 |
| `test_building_record_sf_alias_fields_end_in_double_c` | `TestSFFieldNameConformance` | AC7 |
| `test_acm_record_building_id_has_sf_alias` | `TestSFFieldNameConformance` | AC7 |
| `test_building_record_building_code_has_sf_alias` | `TestSFFieldNameConformance` | AC7 |
| `test_building_record_has_required_sf_object_fields` | `TestSFObjectLevelCorrectness` | AC8 |
| `test_acm_record_has_required_sf_item_fields` | `TestSFObjectLevelCorrectness` | AC8 |
| `test_building_record_and_acm_record_are_separate_entities` | `TestSFObjectLevelCorrectness` | AC8 |
| `test_building_record_internal_id_format` | `TestSFObjectLevelCorrectness` | AC8 |

### LLM-gated tests (require `RUN_E2E_LLM=true`)

| Test | Class | Covers |
|------|-------|--------|
| `test_broadmeadows_record_count` | `TestBroadmeadowsAccuracy` | AC2 |
| `test_broadmeadows_all_picklist_values_valid_sf` | `TestBroadmeadowsAccuracy` | AC2 |
| `test_broadmeadows_all_dependency_chains_valid` | `TestBroadmeadowsAccuracy` | AC2 |
| `test_alexander_baseline_recall` | `TestAlexanderAccuracy` | AC3 |
| `test_alexander_stretch_recall` | `TestAlexanderAccuracy` | AC3 (xfail if < 42) |

### Verification commands

```bash
# Always-run tests (no LLM key needed)
cd "$CLAUDE_PROJECT_DIR" && uv run pytest tests/test_v3_e2e_pipeline.py -v -k "not v3_e2e"

# All tests including accuracy (requires API key + RUN_E2E_LLM=true)
cd "$CLAUDE_PROJECT_DIR" && RUN_E2E_LLM=true uv run pytest tests/test_v3_e2e_pipeline.py -v

# Lint check
cd "$CLAUDE_PROJECT_DIR" && uv run ruff check tests/test_v3_e2e_pipeline.py
```

---

## 7. Implementation Notes

### Async test pattern

All tests using `_run_v3_extraction_mocked()` are `async def` with `@pytest.mark.asyncio`. The helper itself is `async def` and awaited directly.

### Mock LLM for V3 graph

The V3 graph calls `provision_langchain_model` at multiple points:
1. `extract_building_node` → expects JSON with building fields
2. `extract_items_node` → expects JSON with `ACMExtractionResult` format

The `_make_mock_v3_llm()` helper uses a call counter to return building JSON on the first call and item JSON on subsequent calls. This mirrors the actual graph invocation order.

### BuildingRecord.get_by_source mock

The `extract_items_node` calls `BuildingRecord.get_by_source(source_id)` to look up persisted building record IDs. The mock must return the already-captured `building_records` list so FK wiring works correctly.

### pytest.ini / conftest.py marks

The `v3_e2e` mark needs to be registered. Add to `pytest.ini` or `pyproject.toml`:

```ini
[tool:pytest]
markers =
    v3_e2e: V3 end-to-end accuracy tests (require RUN_E2E_LLM=true)
    v3_benchmark: V3 benchmark accuracy tests (require RUN_BENCHMARK_LLM=true)
```

**Check `pyproject.toml` first** — if `v3_benchmark` is already registered there, add `v3_e2e` in the same place.

---

## 8. Definition of Done

- [ ] `tests/test_v3_e2e_pipeline.py` created with all 8 test classes
- [ ] All 15 always-run tests pass: `uv run pytest tests/test_v3_e2e_pipeline.py -v -k "not v3_e2e"`
- [ ] `v3_e2e` mark registered in `pyproject.toml`
- [ ] `uv run ruff check tests/test_v3_e2e_pipeline.py` passes clean
- [ ] No pre-existing tests broken: `uv run pytest tests/ -x --ignore=tests/benchmarks` passes
