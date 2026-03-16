# Bug Fix 11 Phase 2: Extraction Quality — 16→31 Records

**Created**: 2026-03-11
**Source**: Clutch_Broadmeadows.pdf (source:rw12h46pyx00urdp545v)
**Baseline**: 16/31 records (52% recall) after Phase 1 fixes
**Target**: 31/31 records (100% recall) with >80% field accuracy
**Ground Truth**: `benchmarks/ground_truth/broadmeadows.json`

## Dependencies

| Issue | Priority | Blocks |
|-------|----------|--------|
| `bug-page-range-table-loss` | P0 | Record count (estimated +10-15 records) |
| `bug-per-row-schema-missing-fields` | P0 | Field accuracy + benchmark matching |
| `bug-row-segmenter-subheaders` | P1 | `internal_external` field accuracy |
| `bug-building-record-not-persisted` | P1 | Frontend building view |
| `bug-correction-stage-format-json` (existing) | P1 | Ollama correction quality |
| `bug-extraction-progress-stuck-running` (existing) | P1 | Benchmark automation reliability |

## Execution Plan

### Phase 1: Record Recovery (P0 — fixes record count) [estimated +15 records] ✅ DONE

#### Task 1.1: Fix `_merge_provider_tables` multi-table-per-page overwrite — ✅
#### Task 1.2: Fix building `page_end` for single-building documents — ✅
#### Task 1.3: Fix page filter silent fallback + page_number=0 handling — ✅
#### Task 1.4: Add page range exclusion warning in orchestrator — ✅

### Phase 2: Field Completeness (P0 — fixes field accuracy) ✅ DONE

#### Task 2.1: Add `sample_number`, `sample_result`, `acm_product` to ACMItemRow — ✅
#### Task 2.2: Update row extraction prompt for new fields — ✅
#### Task 2.3: Update mapper to use new fields — ✅
#### Task 2.4: Add `internal_external` to ACMItemRow + segmenter — ✅

### Phase 3: Building Persistence (P1 — fixes frontend) [enables building view]

> **Finding F1**: `extract_building_node` already has persistence code (lines 613-644)
> but skips entirely when LLM returns None (line 606-611). Need fallback.
> **Finding F2**: `_heuristic_fallback` lacks `document_metadata` param — can't use `site_name`.

#### Task 3.1: Fallback BuildingRecord when LLM extraction fails
- **File**: `open_notebook/graphs/acm_extraction.py:606-611`
- **Change**: When `result is None`, create minimal BuildingRecord from BuildingMeta fields (name, building_id, source_id) instead of returning None
- **Rationale**: LLM enrichment (address, type, category) is nice-to-have; the basic record is essential for FK linkage and frontend building view
- **Test**: Building with failed LLM still creates a BuildingRecord in DB
- **Status**: [x] Done (commit b05c91ab) — minimal BuildingRecord fallback created

#### Task 3.2: Pass `document_metadata` to `_heuristic_fallback` + use site_name
- **File**: `open_notebook/extractors/building_inventory.py:326, 463-471, 665-667`
- **Change**:
  1. Add `document_metadata: Optional[dict] = None` param to `_heuristic_fallback`
  2. In catch-all (line 463-471): use `document_metadata.get("site_name", "Main Building")` as name
  3. In `compile_building_inventory` (line 667): pass `document_metadata` to `_heuristic_fallback`
- **Test**: Catch-all building uses actual site name ("Broadmeadows Police Station")
- **Status**: [x] Done (commit b05c91ab) — document_metadata propagated, site_name used in catch-all

### Phase 4: Correction + Progress Fixes (P1 — existing issues)

> **Finding F3**: Correction model never gets `_apply_ollama_extraction_settings()` — line 1595.
> **Finding F4**: PipelineLogger has no `finalize()` method.
> **Finding F5**: `acm_commands.py` has no pipeline_logger reference — use direct DB write (Option B).

#### Task 4.1: Apply `format="json"` to correction stage
- **File**: `open_notebook/graphs/acm_extraction.py:1601` (after model provisioning)
- **Change**: Add `model = _apply_ollama_extraction_settings(model)` after line 1601
- **Import**: `_apply_ollama_extraction_settings` already in scope via `from .utils import ...`
- **Test**: Ollama correction model has `format="json"` set
- **Status**: [x] Done (commit b05c91ab) — format="json" applied to correction model
- **Ref**: `docs/issues/bug-correction-stage-format-json.md`

#### Task 4.2: Add terminal status write for extraction progress
- **File**: `commands/acm_commands.py:220-253` (after `extract_acm_from_source` returns)
- **Approach**: Option B — direct SurrealDB write (no PipelineLogger reference needed)
- **Change**: After line 220, write `status="completed"` to `extraction_progress` table using `repo_query` + the command_id
- **Also**: Write `status="failed"` in the error path (line 226)
- **Test**: `extraction_progress` shows "completed" after extraction finishes
- **Status**: [x] Done (commit b05c91ab) — terminal status writes for completed/failed/no_data paths
- **Ref**: `docs/issues/bug-extraction-progress-stuck-running.md`

### Phase 5: Verification

#### Task 5.1: Run benchmark harness against ground truth
- **Command**: `uv run python scripts/research/e29_benchmark_harness.py`
- **Target**: Broadmeadows ≥28/31 records (90% recall), ≥70% field accuracy
- **Status**: [x] Partial — 3/3 buildings persist. Per-row path was blocked by docling_document_json NULL (now fixed). Full benchmark pending.

#### Task 5.2: Live extraction with agent-browser screenshots
- **Steps**: Upload Broadmeadows PDF → extract → verify records in UI → screenshots
- **Target**: All 31 records visible, building name correct, fields populated
- **Status**: [x] Partial — buildings verified via API. Full E2E with agent-browser pending.

## Subagent Routing

| Task | Agent Type | Model |
|------|-----------|-------|
| 1.1-1.4 | `backend-specialist` | sonnet |
| 2.1-2.4 | `backend-specialist` | sonnet |
| 3.1-3.2 | `backend-specialist` | sonnet |
| 4.1-4.2 | `backend-specialist` | sonnet |
| 5.1 | `qa-specialist` | sonnet |
| 5.2 | `acm-e2e-tester` | sonnet |

## Success Criteria

- [ ] Broadmeadows: ≥28/31 records (90% recall)
- [ ] Broadmeadows: ≥70% field accuracy (sample_no, sample_result, product, room_name)
- [x] `building_record` table populated (3/3 buildings saved)
- [ ] Source register view shows building(s) with record counts
- [x] Extraction progress reaches "completed" status
- [x] All existing tests pass (2123 passed)
- [x] Ruff lint clean

## Phase 6-7 Addendum (2026-03-11)

Additional fixes discovered during live verification:

| Fix | File | Issue |
|-----|------|-------|
| Docling export_to_dict | `docling_adapter.py:151` | `TableItem` has no `export_to_dict()` — use `table.data.model_dump(mode="python")` |
| Table re-extraction on force | `acm_commands.py` | `force=true` now re-extracts tables when `docling_document_json` IS NULL |
| Truncation retry guard | `acm_extraction.py` | Checks cloud API keys before retrying (prevents infinite loop in Ollama-only mode) |
| Field schema query | `acm.py:2350` | Query now targets `field_schema:default` directly (avoids sf_v1 NULL config_json error) |

## Phase 8: Post-Restart Fixes (2026-03-12)

4 bugs found after restarting services with Phase 1-7 fixes:

| # | Severity | File | Fix | Status |
|---|----------|------|-----|--------|
| 8.1 | PRIMARY | `utils.py:860-897` | `_get_db_extraction_model()` resolves SurrealDB record IDs (`model:xxx`) to model names via DB lookup | [x] Done |
| 8.2 | CRITICAL | `docling_adapter.py:151` | `model_dump(mode="python")` → `mode="json"` (non-serializable enums/Pydantic objects) | [x] Done |
| 8.3 | CRITICAL | `utils.py:281-285` | `_apply_ollama_extraction_settings` respects caller's explicit `num_ctx` (per-row: 2048, was overwritten to 32768) | [x] Done |
| 8.4 | HIGH | `row_extractor.py:149` | loguru `{max}` → `{max_retries}` (Python builtin shadow) | [x] Done |

### Phase 8 Root Cause
`default_extraction_model` in SurrealDB stores a record ID (`model:znay2wr8u9q39lxj2q37`) from `find_or_create_model()`, not a model name. `_get_db_extraction_model()` returned it as-is → Ollama 404 → all LLM calls fail → 0 buildings → 0 records.
