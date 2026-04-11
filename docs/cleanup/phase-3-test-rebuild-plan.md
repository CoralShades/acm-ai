# Phase 3 — Test Scorched Earth + Rebuild Plan

> **Sub-skills consulted:** `writing-plans`, `api-testing`, `find-skills`
> **Authority:** DEC-015 (user authorized scorched earth, overriding `tests/` PROTECTED flag)
> **Branch:** `feat/sf-reconciliation-20260411`

## Goal

Delete the existing 110 test files (106 Python + 4 frontend) in one scorched-earth commit, then rebuild a **minimum viable test surface** that directly validates the Phase 2a/2b SF reconciliation work. Full coverage rebuild is tracked as **E38-S3** in a future session.

## Why scoped

Rebuilding all 110 tests from scratch in a single session is not feasible:
- Each test file averages ~100-400 lines and has non-trivial fixtures
- Many depend on a running SurrealDB + API stack
- Many are benchmark/integration tests that cost LLM time to re-run
- An agent team writing 110 test files unattended would produce drift from actual module signatures

This plan ships the **~6 highest-value test files** that directly assert the invariants Phase 2a/2b introduced. Everything else is tracked as follow-up work.

## Scope decisions

### In scope (Phase 3A — this session)

| # | Test file | What it asserts | Signal strength |
|---|---|---|---|
| 1 | `tests/test_sf_schema_snapshot.py` | `config/sf-schema-snapshot.json` parses, required keys present, each extractable field name exists in the raw describe JSON under `docs/sprint-artifacts/full-audit-2026-04-11/sf-describe/` | Catches any drift between the snapshot and the source of truth |
| 2 | `tests/test_sf_export_contract.py` | Every SF field name in `BUILDING_SF_MAPPING` and `ITEM_SF_MAPPING` (from `sf_export.py`) exists in the corresponding raw SF describe dump. Every Python field name on the right side exists on `BuildingRecord` / `ACMRecord` | **This is the test that would have caught the Phase 2b bug** |
| 3 | `tests/test_bar_to_sf_mapping.py` | `config/bar_to_sf_mapping.yaml` parses; documented mappings (Good→Stable, Medium→Moderate, YES→Yes) are present; every left-side value is a known BAR term; every non-null right-side value appears in the corresponding SF picklist from the snapshot | Invariant check on the deterministic mapping table |
| 4 | `tests/test_external_id_determinism.py` | `generate_external_id()` produces identical output for identical input; different inputs produce different output; hash format matches `ACM_[0-9a-f]{16}`; output length ≤ 255 (SF field limit) | Guarantees the re-extraction stability property |
| 5 | `tests/test_domain_models_smoke.py` | `BuildingRecord` and `ACMRecord` instantiate with minimal fields; Pydantic validation works; required fields enforced; no import errors | Catches domain-model regressions |
| 6 | `tests/conftest.py` | Shared fixtures: `sf_describe_json`, `sf_schema_snapshot`, `bar_mapping`, `sample_building`, `sample_acm_record`. All pure-Python, no DB, no network | Foundation for all other test files |

**Expected runtime:** all 6 tests should complete in < 5 seconds, no network, no DB, no LLM calls.

### Out of scope (deferred to E38-S3)

- API router tests (need DB fixtures + TestClient setup)
- Consensus engine tests (complex state)
- Benchmark tests (expensive LLM runs)
- LangGraph integration tests (complex fixtures)
- Frontend tests (separate toolchain)
- Migration tests (need DB)
- E2E browser tests (need full stack)
- All the existing `test_broadmeadows_*`, `test_alexander_*`, `test_v3_*` benchmark files

## Plan

### Task 1 — Scorched earth commit

**Step 1.1 — Inventory the deletion**
```bash
find tests -type f | wc -l          # should be ~110
find tests -type f -name "*.py"
```

**Step 1.2 — Execute deletion**
```bash
git rm -rf tests/
git rm -rf frontend/tests/ 2>/dev/null || true
git rm frontend/src/components/acm/__tests__/UploadWizard.test.tsx
git rm frontend/src/hooks/__tests__/useDependentPicklist.test.ts
git rm frontend/src/__tests__/RecordWizard.test.tsx
git rm frontend/src/__tests__/ValidationBadge.test.tsx
```

**Step 1.3 — Commit the deletion alone**
One commit for the deletion so it's cleanly revertable:
```bash
git commit -m "test: scorched earth delete before Phase 3 rebuild"
```

**Step 1.4 — Verify**
```bash
find tests 2>/dev/null | head    # should be empty or absent
uv run ruff check .              # should still pass — tests aren't imported
```

### Task 2 — Create tests/ scaffolding

**Step 2.1 — Create directory + empty conftest**
```bash
mkdir -p tests
touch tests/__init__.py
```

**Step 2.2 — Write `tests/conftest.py` with the shared fixtures**
Fixtures needed:
- `sf_describe_building` — loads `docs/sprint-artifacts/full-audit-2026-04-11/sf-describe/Building__c.json`
- `sf_describe_item` — loads `.../Item__c.json`
- `sf_schema_snapshot` — loads `config/sf-schema-snapshot.json`
- `bar_mapping` — loads `config/bar_to_sf_mapping.yaml`
- `sample_building_dict` — minimal valid BuildingRecord kwargs
- `sample_acm_dict` — minimal valid ACMRecord kwargs

All session-scoped where possible. Pure file reads, no DB.

### Task 3 — Write `tests/test_sf_schema_snapshot.py`

**What it tests:**
1. Snapshot JSON parses
2. Required top-level keys (`version`, `objects`, `dependent_picklist_chains`)
3. `Building__c` section has `required_custom_fields` and `extractable_fields`
4. `Item__c` section has `parent_relationship` and `upsert_key.blocker` (documents the known issue)
5. Every field name in `extractable_fields` for each object exists in the corresponding raw describe JSON's `fields` array
6. Dependent picklist controllers (`Friability_of_Material__c`, `Building_Type__c`) are marked as controllers on the right fields

### Task 4 — Write `tests/test_sf_export_contract.py`

**THE critical test** — the one that would have caught the Phase 2b bug.

```python
def test_building_sf_mapping_fields_exist_in_describe(sf_describe_building):
    """Every SF field name in BUILDING_SF_MAPPING must exist in the live describe."""
    from open_notebook.extractors.exporters.sf_export import BUILDING_SF_MAPPING

    describe_field_names = {f["name"] for f in sf_describe_building["fields"]}
    # External_ID__c is real; Building__r.External_ID__c is a relationship lookup, skip
    for sf_name, _python_field in BUILDING_SF_MAPPING:
        if "." in sf_name:
            continue
        assert sf_name in describe_field_names, (
            f"{sf_name} in BUILDING_SF_MAPPING does not exist in Building__c describe"
        )

def test_item_sf_mapping_fields_exist_in_describe(sf_describe_item):
    # same pattern for ITEM_SF_MAPPING
    ...

def test_building_mapping_python_fields_exist_on_model():
    """Every Python field name must exist on the BuildingRecord model."""
    from open_notebook.domain.acm import BuildingRecord
    from open_notebook.extractors.exporters.sf_export import BUILDING_SF_MAPPING

    model_fields = set(BuildingRecord.model_fields.keys())
    for sf_name, python_field in BUILDING_SF_MAPPING:
        assert python_field in model_fields, (
            f"Python field '{python_field}' (mapped to SF '{sf_name}') "
            f"does not exist on BuildingRecord"
        )

# same for ACMRecord / ITEM_SF_MAPPING
```

### Task 5 — Write `tests/test_bar_to_sf_mapping.py`

```python
def test_mapping_yaml_parses(bar_mapping):
    assert "Item__c" in bar_mapping
    assert "Building__c" in bar_mapping

def test_condition_good_maps_to_stable(bar_mapping):
    """PRD FR-1405 contract."""
    assert bar_mapping["Item__c"]["Condition__c"]["Good"] == "Stable"

def test_disturbance_medium_maps_to_moderate(bar_mapping):
    assert bar_mapping["Item__c"]["Disturbance_Potential_of_Material__c"]["Medium"] == "Moderate"

def test_yes_no_case_normalized(bar_mapping):
    assert bar_mapping["Item__c"]["Labelled__c"]["YES"] == "Yes"
    assert bar_mapping["Building__c"]["Public_Access__c"]["YES"] == "Yes"

def test_all_non_null_targets_are_valid_sf_picklist_values(bar_mapping, sf_schema_snapshot):
    """Every right-side value (that's not null) must appear in the SF picklist
    for the target field. Catches drift between mapping table and SF schema."""
    for obj_name in ("Item__c", "Building__c"):
        obj_mapping = bar_mapping.get(obj_name, {})
        obj_schema = sf_schema_snapshot["objects"][obj_name]["extractable_fields"]
        for field_name, translations in obj_mapping.items():
            if not isinstance(translations, dict):
                continue
            field_schema = obj_schema.get(field_name, {})
            valid_values = set(field_schema.get("values", []))
            if not valid_values:
                continue  # field is not a restricted picklist or has too many values
            for _bar, sf_value in translations.items():
                if sf_value is None:
                    continue
                assert sf_value in valid_values, (
                    f"{obj_name}.{field_name} mapping produces '{sf_value}' "
                    f"which is not in the SF picklist {valid_values}"
                )
```

### Task 6 — Write `tests/test_external_id_determinism.py`

```python
import re
from types import SimpleNamespace

from open_notebook.extractors.exporters.sf_export import generate_external_id

HASH_PATTERN = re.compile(r"^ACM_[0-9a-f]{16}$")

def test_same_input_produces_same_id():
    b1 = SimpleNamespace(building_name="Broadmeadows", external_id=None, building_unique_id=None)
    b2 = SimpleNamespace(building_name="Broadmeadows", external_id=None, building_unique_id=None)
    assert generate_external_id(b1, "source:abc") == generate_external_id(b2, "source:abc")

def test_different_source_produces_different_id():
    b = SimpleNamespace(building_name="Broadmeadows", external_id=None, building_unique_id=None)
    assert generate_external_id(b, "source:abc") != generate_external_id(b, "source:xyz")

def test_different_building_name_produces_different_id():
    b1 = SimpleNamespace(building_name="Broadmeadows", external_id=None, building_unique_id=None)
    b2 = SimpleNamespace(building_name="Alexander",    external_id=None, building_unique_id=None)
    assert generate_external_id(b1, "source:abc") != generate_external_id(b2, "source:abc")

def test_generated_id_matches_hash_format():
    b = SimpleNamespace(building_name="Broadmeadows", external_id=None, building_unique_id=None)
    assert HASH_PATTERN.match(generate_external_id(b, "source:abc"))

def test_stored_external_id_is_honoured():
    b = SimpleNamespace(building_name="anything", external_id="PRE_SET_ID", building_unique_id=None)
    assert generate_external_id(b, "source:abc") == "PRE_SET_ID"

def test_stored_building_unique_id_takes_precedence_over_hash():
    b = SimpleNamespace(building_name="anything", external_id=None, building_unique_id="USER_ID_42")
    assert generate_external_id(b, "source:abc") == "USER_ID_42"

def test_id_length_within_sf_limit():
    """External_ID__c is Text(255) in Building__c describe."""
    b = SimpleNamespace(
        building_name="A" * 1000,  # pathologically long
        external_id=None,
        building_unique_id=None,
    )
    assert len(generate_external_id(b, "source:" + "B" * 1000)) <= 255
```

### Task 7 — Write `tests/test_domain_models_smoke.py`

```python
def test_building_record_instantiates():
    from open_notebook.domain.acm import BuildingRecord
    b = BuildingRecord(internal_id="bld_1", source_id="source:abc")
    assert b.internal_id == "bld_1"

def test_acm_record_instantiates():
    from open_notebook.domain.acm import ACMRecord
    r = ACMRecord(
        source_id="source:abc",
        building_id="bld_1",
        product="Floor covering",
        material_description="Vinyl sheet",
        result="Negative",
    )
    assert r.product == "Floor covering"

def test_building_record_missing_required_field_raises():
    import pytest
    from pydantic import ValidationError
    from open_notebook.domain.acm import BuildingRecord
    with pytest.raises(ValidationError):
        BuildingRecord()  # missing internal_id, source_id

def test_domain_module_imports_clean():
    """Catch import-time errors from dead code / bad references."""
    import open_notebook.domain.acm  # noqa: F401
    import open_notebook.extractors.exporters.sf_export  # noqa: F401
    import open_notebook.graphs.acm_extraction  # noqa: F401
```

### Task 8 — Verify + Commit

**Step 8.1 — Run the test suite**
```bash
uv run pytest tests/ -v
```
Expected: 25+ passing tests in < 5 seconds.

**Step 8.2 — Ruff check**
```bash
uv run ruff check tests/
```
Expected: all checks passed.

**Step 8.3 — Commit**
```bash
git add tests/
git commit -m "test: rebuild minimum viable test surface for SF reconciliation (Phase 3A)"
```

**Step 8.4 — Update sprint-status.yaml**
Mark `sf-reconciliation-phase-3a-test-rebuild: done` with note that E38-S3 covers the incremental rebuild.

## Execution strategy

Given the test files are straightforward (pure-Python, no DB, no LLM, clear assertions), I'll write them directly in the main session rather than dispatching a subagent team. The complexity that would warrant subagents (parallel independent investigation) isn't present here — these 6 files share fixtures and need to be consistent with each other.

## Risks

| Risk | Mitigation |
|---|---|
| Deleting `tests/conftest.py` removes fixtures that some imported module expects at import time | Verify with `uv run ruff check .` after deletion; nothing in `open_notebook/` or `api/` should import from `tests/` |
| `ACMRecord` / `BuildingRecord` required-field set has drifted from what my test assumes | Task 7 uses the actual model_fields at runtime; safer than hardcoded assumptions |
| `BUILDING_SF_MAPPING` entries like `Building__r.External_ID__c` aren't in the describe field list | Handled in Task 4 — skip entries containing `.` |
| SF picklist values in the snapshot are case-sensitive; BAR mapping values must match exactly | Task 5 asserts this; failure indicates either the snapshot is wrong or the mapping is wrong |
| `generate_external_id` length test with 1000-char building name may exceed 255 if the function doesn't truncate | If test fails, it's a real bug — the function needs a length check added |
| Some tests in Phase 3A might need adjustments based on actual code behavior | I'll iterate after first pytest run |

## What this does NOT cover (tracked as E38-S3)

- FastAPI router tests (`test_acm_api.py`, `test_bulk_operations.py`, etc.)
- Command layer tests (`test_acm_commands.py`)
- Extraction pipeline tests (`test_acm_extractor.py`, `test_e2e_extraction.py`)
- Schema inference tests (`test_schema_inference.py`)
- Consensus engine tests (`test_consensus_engine.py`)
- Row segmenter tests (`test_adaptive_segmenter.py`)
- Benchmark tests (`test_broadmeadows_e2e.py`, `test_e28_ara_recovery.py`)
- Frontend component tests (4 files)
- Playwright E2E tests

These stay deleted and will be rebuilt incrementally as E38-S3 progresses.
