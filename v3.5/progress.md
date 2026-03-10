# Progress: Per-Row ACM Extraction Pipeline

**Started:** 2026-03-07
**Status:** Phase 4 COMPLETE — offline verification passed, ready for live E2E test
**Primary Input:** DoclingDocument JSON | **Debug:** HTML export | **LLM Format:** Key-value pairs

---

## Schema Scope (User-Confirmed)

**Item__c: 9 fields from PDF** — room_name, floor_level, item_location, item_name, friability, acm_classification, acm_sub_classification, condition, disturbance_potential

**Building__c: 14 fields from PDF** — name, address, suburb, postcode, state, type, category, sub_category, construction, year_built, levels, owned/leased, frequency, risk_rating

**NOT extracted (user fills in SF):** sample_result, quantity, recommendations, labelled, no_access, internal_external

---

## Current Status by Phase

### Phase 0: Infrastructure Prerequisites — COMPLETE ✅
| Sub-Agent | Task | Status | Tests |
|-----------|------|--------|-------|
| 0A | Store DoclingDocument JSON | ✅ | 12/12 pass |
| 0B | Building schema + prompt gaps | ✅ | 19/19 pass |
| 0C | Truncation fallback + output budget | ✅ | 17/17 pass |

**Files modified (Phase 0):**
- `open_notebook/extractors/providers/base.py` — added `docling_json` to NormalizedTable
- `open_notebook/extractors/providers/docling_adapter.py` — call `export_to_dict()`
- `commands/source_commands.py` — store + propagate docling_document_json
- `open_notebook/domain/acm.py` — added building_sub_category, building_risk_rating
- `open_notebook/extractors/acm_schemas_v3.py` — 5 fields on BuildingExtractionResult + truncated status
- `open_notebook/graphs/acm_extraction.py` — 5 new kwargs to BuildingRecord + truncation retry
- `open_notebook/graphs/utils.py` — 30% output budget reserve + configurable model
- `open_notebook/extractors/orchestrator.py` — TruncationError catch
- `prompts/acm/v3_building_extraction.jinja` — 5 new fields in prompt
- `migrations/47.surrealql` — building_sub_category, building_risk_rating
- `migrations/48.surrealql` — docling_document_json on acm_table_section

**New test files:**
- `tests/test_docling_json_storage.py` (12 tests)
- `tests/test_building_schema_gaps.py` (19 tests)
- `tests/test_truncation_fallback.py` (17 tests)

### Phase 1: Parallel Independent Tasks — COMPLETE ✅
| Agent | Task | Status | Tests |
|-------|------|--------|-------|
| Agent 1 | Row Segmentation Engine | ✅ | 32/32 pass |
| Agent 2 | 9-Field Schema + Mapper | ✅ | 47/47 pass |
| Agent 5 | Edge Case Fixtures | ✅ | 14 files (11 JSON + 2 MD + 1 README) |

**Files created (Phase 1):**
- `open_notebook/extractors/row_segmenter.py` — RawTableRow model, COLUMN_ALIASES, segment_docling_table(), segment_multiple_tables(), scan_text_for_synthetics(), generate_debug_table()
- `open_notebook/domain/acm_row_schemas.py` — ACMItemRow (9 fields for LLM output)
- `open_notebook/domain/acm_row_mappers.py` — map_item_row_to_extraction_record(), normalize_friability(), is_friable_bool()
- `tests/test_row_segmenter.py` (32 tests)
- `tests/test_acm_row_mappers.py` (47 tests)
- `tests/fixtures/edge_case_tables/` — 14 fixture files (Types A-H)

### Phase 2: Per-Row Extractor — COMPLETE ✅
| Agent | Task | Status | Tests |
|-------|------|--------|-------|
| Agent 3 | Per-Row Extraction Orchestrator | ✅ | 27/27 pass |

**Files created (Phase 2):**
- `open_notebook/extractors/row_extractor.py` — build_kv_prompt(), extract_single_row(), split_multi_item_row(), extract_all_rows(), _build_fallback_record()
- `prompts/acm/row_extraction.jinja` — System prompt for per-row extraction (9-field JSON schema)
- `prompts/acm/row_split.jinja` — System prompt for multi-item cell splitting (Type E1)
- `tests/test_row_extractor.py` (27 tests)

### Phase 3: Pipeline Integration — COMPLETE ✅
| Agent | Task | Status | Tests |
|-------|------|--------|-------|
| Agent 4 | Pipeline Integration | ✅ | 9/9 pass |

**Files modified (Phase 3):**
- `open_notebook/graphs/acm_extraction.py` — per-row path in `_extract_items_for_building()`, recovery node gating
- `.env.example` — ACM_ITEM_EXTRACTION_MODE, ACM_ROW_EXTRACTION_NUM_CTX

**New test files:**
- `tests/test_pipeline_integration.py` (9 tests)

### Phase 4: Verification — COMPLETE ✅ (offline)
| Check | Status | Result |
|-------|--------|--------|
| `uv run ruff check .` | ✅ | Clean |
| Phase 0-3 tests (163 total) | ✅ | 163/163 pass |
| Full test suite | ✅ | 2154 passed, 0 failed (6 pre-existing excluded) |
| Frontend `npm run build` | ✅ | All pages compile |
| All new files exist | ✅ | All 31 files verified via Glob |
| Classification chain SF validation | ⬜ | Requires live Ollama |
| Per-row with Ollama num_ctx=2048 | ⬜ | Requires live Ollama |

---

## Session Log

### Session 8: 2026-03-10 — Phase 4 Verification (Offline)
**What was done:**
1. Ruff lint: clean (all checks passed)
2. Phase 0-3 specific tests: 163/163 pass (12+19+17+32+47+27+9)
3. Full test suite: 2154 passed, 14 skipped, 2 xfailed, 0 failed (excl. 6 pre-existing)
4. Frontend build: all pages compile successfully
5. File existence: all 31 new/modified files verified via Glob
6. Pre-existing failures confirmed (not caused by our changes):
   - `test_broadmeadows_e2e.py` — OpenRouter 402 (insufficient credits)
   - `test_building_inventory.py::test_prompt_template_renders` — prompt template changed
   - `test_document_structure.py::test_prompt_renders` — same pattern
   - `test_metadata_extractor.py::test_extract_cover_pages` — cover page count mismatch
   - `test_v3_e2e_pipeline.py::TestV3PipelineSmoke` (2 tests) — pre-existing, confirmed via stash+test
7. Updated task_plan.md and progress.md with Phase 4 results
8. Two checks deferred to live E2E: SF classification chain, Ollama num_ctx=2048

### Session 7: 2026-03-10 — Phase 3 Pipeline Integration
**What was done:**
1. Wired per-row extraction into `extract_items_node` in `acm_extraction.py`:
   - Added `ACM_ITEM_EXTRACTION_MODE` env var (default: `per_row`)
   - Per-row path: fetches `docling_document_json` from Docling tables, calls `segment_multiple_tables()` + `scan_text_for_synthetics()` + `extract_all_rows()`
   - Graceful fallback to bulk path when no DoclingDocument JSON or no rows segmented
   - Bulk path (`_chunk_and_extract_items` + `_normalize_v3_records`) unchanged
2. Gated `recover_no_access_node` — returns state unchanged in per-row mode (segmenter handles Type D/F)
3. Updated `.env.example` with `ACM_ITEM_EXTRACTION_MODE` and `ACM_ROW_EXTRACTION_NUM_CTX`
4. Verified `_get_docling_tables()` already returns `docling_document_json` via `SELECT *` (Phase 0A migration 48)
5. Created `tests/test_pipeline_integration.py` — 9 tests covering:
   - Per-row mode calls segmenter + extractor
   - Per-row mode populates building_record_id FK
   - Bulk mode calls `_chunk_and_extract_items`
   - Fallback: no docling_document_json -> bulk
   - Fallback: no rows segmented -> bulk
   - Fallback: no docling tables at all -> bulk
   - Recovery node skipped in per-row mode
   - Recovery node runs in bulk mode
   - Default mode is per_row
6. Ruff lint: clean
7. Integration tests: 9/9 pass
8. Full test suite: 2154 passed, 14 skipped, 2 xfailed (excl. pre-existing failures)
9. Updated task_plan.md and progress.md

### Session 6: 2026-03-10 — Phase 2 Implementation
**What was done:**
1. Dispatched Agent 3 (Per-Row Extraction Orchestrator) — sequential, depends on Agent 1+2 output
2. Agent 3 created 4 files:
   - `prompts/acm/row_extraction.jinja` — minimal system prompt with 9-field JSON schema
   - `prompts/acm/row_split.jinja` — multi-item cell splitting prompt
   - `open_notebook/extractors/row_extractor.py` — full orchestrator: build_kv_prompt(), extract_single_row() with retry, split_multi_item_row() for Type E1, extract_all_rows() main loop with SSE events and Langfuse spans, _build_fallback_record() for failures
   - `tests/test_row_extractor.py` — 27 tests across 9 test classes
3. Ruff lint: clean
4. Phase 2 tests: 27/27 pass
5. Full test suite: 434 passed, 1 failed (pre-existing test_broadmeadows_e2e.py — requires SurrealDB)
6. Updated task_plan.md and progress.md

### Session 5: 2026-03-10 — Phase 1 Implementation
**What was done:**
1. Dispatched 3 parallel agents for Phase 1 (Agent 1, Agent 2, Agent 5)
2. Agent 1 (Row Segmenter): created row_segmenter.py with RawTableRow model, 12 COLUMN_ALIASES with Jaro-Winkler matching, segment_docling_table(), segment_multiple_tables(), scan_text_for_synthetics(), generate_debug_table(). 32 tests.
3. Agent 2 (Schema+Mapper): created acm_row_schemas.py (ACMItemRow, 9 fields), acm_row_mappers.py (map_item_row_to_extraction_record targeting ACMExtractionRecord, normalize_friability, is_friable_bool). 47 tests.
4. Agent 5 (Fixtures): created 14 fixture files in tests/fixtures/edge_case_tables/ — 11 JSON (Types A, B×2, C×2, E1, E2, E3, G×2, H), 2 MD (Types D, F), 1 README.
5. Ruff lint: clean (all Phase 1 files)
6. Phase 1 tests: 79/79 pass (32 segmenter + 47 mapper)
7. Full test suite: 434 passed, 1 failed (pre-existing test_broadmeadows_e2e.py — requires SurrealDB)
8. Updated task_plan.md and progress.md

### Session 4: 2026-03-10 — Phase 0 Implementation
**What was done:**
1. Dispatched 3 parallel sub-agents for Phase 0 (0A, 0B, 0C)
2. All 3 completed successfully with 48 total tests passing
3. Accidentally lost changes via `git stash` (checking pre-existing test failure)
4. Re-dispatched all 3 agents to re-apply source changes
5. All re-applied successfully, 48/48 Phase 0 tests pass
6. Ruff lint: clean
7. Full test suite: 1957 passed, 3 pre-existing failures (unrelated)
8. Updated task_plan.md and progress.md

**Pre-existing test failures (not caused by Phase 0):**
- `test_broadmeadows_e2e.py` — requires running SurrealDB
- `test_building_inventory.py::TestPromptTemplate::test_prompt_template_renders` — prompt template rendering mismatch
- `test_document_structure.py::TestPromptTemplate::test_prompt_renders` — same pattern
- `test_metadata_extractor.py::TestCoverPageExtraction::test_extract_cover_pages` — expects 5 pages, gets 3
- `test_v3_e2e_pipeline.py::TestV3PipelineSmoke` (2 tests) — MetadataAndStructureLLM validation errors

### Session 3: 2026-03-10 — Session Prompt v2
**What was done:**
1. Incorporated root cause analysis findings (truncation fallback, output budget, model default)
2. Rewrote CLAUDE_CODE_SESSION_PROMPT.md as v2 with Phase 0 expanded to 3 sub-agents
3. Updated all planning files

### Session 2: 2026-03-07 — Gap Analysis v2
**What was done:**
1. Gap Analysis v1: 4 agents audited codebase vs planning files
2. User clarified exact SF schema → only 9 Item + 14 Building fields
3. Gap Analysis v2: rewrote with user's actual schema

### Session 1: 2026-03-07 — Initial Planning
- Created v3.5/CLAUDE_CODE_SESSION_PROMPT.md, findings.md, task_plan.md, progress.md

---

## Reboot Check (5 Questions)

1. **Last milestone:** Phase 4 complete (offline) — all tests pass, ruff clean, frontend builds
2. **Active task:** Live E2E test with Ollama + SurrealDB
3. **Blockers:** None — 2 checks need running Ollama
4. **Last modified:** task_plan.md, progress.md (Phase 4 checkboxes)
5. **Next action:** Start services, upload a PDF, verify per-row extraction with Ollama (num_ctx=2048)

## Pending Tasks (Carry Forward)
1. Observability stack validation
2. Frontend SSE/AG-UI verification
