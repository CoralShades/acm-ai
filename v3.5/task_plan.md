# Task Plan: Per-Row ACM Extraction Pipeline (v2)

**Date:** 2026-03-10 (Updated)
**Goal:** Redesign Item__c extraction from bulk-per-building to per-row, with Ollama truncation fix.

---

## Pipeline (4 Steps)

```
Step 1: Metadata + Structure   →  What is this PDF? Where does the register start?
Step 2: Building Inventory     →  How many buildings? What page ranges?
Step 3: Building Extraction    →  Per building: one Building__c record (14 fields)
Step 4: Item Extraction (NEW)  →  Per building → per ROW: one Item__c record (9 fields)
         ├── 4a. Get DoclingDocument JSON tables for building's pages
         ├── 4b. Row Segmentation: JSON cells → list[RawTableRow] (NO LLM)
         ├── 4c. Per-row LLM: KV prompt → ACMItemRow (9 fields, num_ctx=2048)
         ├── 4d. Deterministic post-processing: classify, normalize, validate (NO LLM)
         ├── 4e. Map ACMItemRow → ACMExtractionRecord → existing validate/save pipeline
         └── 4f. Retry failed rows only (max 2 per row)
```

---

## Phase 0: Infrastructure Prerequisites (3 PARALLEL sub-agents) — COMPLETE

| # | Task | Status | Agent | Files |
|---|------|--------|-------|-------|
| 0A | Store DoclingDocument JSON | ✅ | Phase 0A | docling_adapter.py, source_commands.py, orchestrator.py, migration 48 |
| 0B | Building schema gaps + prompt | ✅ | Phase 0B | acm.py, acm_schemas_v3.py, v3_building_extraction.jinja, migration 47 |
| 0C | Truncation fallback + output budget | ✅ | Phase 0C | orchestrator.py, acm_extraction.py, utils.py, acm_schemas_v3.py |

### Phase 0C Details (from Root Cause Analysis)
- [x] 0C.1: Add TruncationError catch in _v3_extract_items() → return status="truncated"
- [x] 0C.2: Add retry-with-cloud-model in _chunk_and_extract_items() on truncation
- [x] 0C.3: Reserve 30% output budget in _ollama_split_by_budget()
- [x] 0C.4: Make Ollama extraction model configurable via ACM_EXTRACTION_MODEL env var
- [x] 0C.5: Add "truncated" to ACMItemExtractionResult.status

## Phase 1: Parallel Independent Tasks (3 PARALLEL agents, after Phase 0) — COMPLETE

| Agent | Task | Status | Files |
|-------|------|--------|-------|
| **Agent 1** | **Row Segmentation Engine** | ✅ | row_segmenter.py, test_row_segmenter.py |
| | RawTableRow model | ✅ | |
| | COLUMN_ALIASES (12 canonical, Jaro-Winkler) | ✅ | |
| | segment_docling_table() — Types A, C, E1-E3 | ✅ | |
| | segment_multiple_tables() — Types B, H | ✅ | |
| | scan_text_for_synthetics() — Types D, F | ✅ | |
| | generate_debug_table() | ✅ | |
| **Agent 2** | **9-Field Schema + Mapper** | ✅ | acm_row_schemas.py, acm_row_mappers.py, test_acm_row_mappers.py |
| | ACMItemRow (9 fields) | ✅ | |
| | map_item_row_to_extraction_record() | ✅ | Target: ACMExtractionRecord |
| **Agent 5** | **Edge Case Fixtures** | ✅ | tests/fixtures/edge_case_tables/*.json |
| | JSON fixtures for Type A-H (11 files) | ✅ | |
| | Markdown fixtures (Type D, F) | ✅ | |

## Phase 2: Sequential (after Phase 1) — COMPLETE

| Agent | Task | Status | Files |
|-------|------|--------|-------|
| **Agent 3** | **Per-Row Extractor** | ✅ | row_extractor.py, row_extraction.jinja, row_split.jinja, test_row_extractor.py |
| | row_extraction.jinja (9-field KV) | ✅ | num_ctx=2048 |
| | build_kv_prompt() | ✅ | |
| | extract_single_row() | ✅ | |
| | split_multi_item_row() | ✅ | Type E1 |
| | extract_all_rows() loop | ✅ | |
| | _build_fallback_record() | ✅ | Low-confidence fallback on extraction failure |
| | SSE event emission | ✅ | Via PipelineEventBus |

## Phase 3: Integration (after Phase 2) — COMPLETE

| Agent | Task | Status | Files |
|-------|------|--------|-------|
| **Agent 4** | **Pipeline Integration** | ✅ | acm_extraction.py, .env.example, test_pipeline_integration.py |
| | ACM_ITEM_EXTRACTION_MODE env var | ✅ | per_row \| bulk |
| | extract_items_node per-row path | ✅ | |
| | Gate recovery functions in per-row mode | ✅ | |
| | Bulk path unchanged | ✅ | |

## Phase 4: Verification

| Check | Status | Result |
|-------|--------|--------|
| All edge cases pass | ✅ | 32 segmenter tests pass |
| 9-field → ACMExtractionRecord valid | ✅ | 47 mapper tests pass |
| Classification chain passes SF validation | ⬜ | Requires live Ollama E2E test |
| Building has all 14 fields | ✅ | 5 new fields added, 19 tests pass |
| Per-row works with Ollama num_ctx=2048 | ⬜ | Requires live Ollama E2E test |
| TruncationError triggers cloud fallback | ✅ | 17 tests pass |
| Output budget reserves 30% | ✅ | Verified in test |
| Bulk path still works | ✅ | 9 integration tests confirm bulk fallback |
| Building↔Item FK correct | ✅ | Integration test verifies building_record_id population |
| DoclingDocument JSON stored | ✅ | 12 tests pass |
| `uv run pytest` passes | ✅ | 2154 passed, 0 failed (excl. 6 pre-existing) |
| `uv run ruff check .` passes | ✅ | Clean |
| Frontend `npm run build` passes | ✅ | All pages compile |
| All new files exist | ✅ | 14 fixtures + 7 source + 3 migrations + 7 tests verified |

---

## Execution Order

```
Phase 0 (parallel — no dependencies between sub-agents):  ✅ COMPLETE
  0A: Store DoclingDocument JSON                           ✅
  0B: Building schema gaps + prompt                        ✅
  0C: Truncation fallback + output budget fix              ✅

Phase 1 (parallel — no dependencies, after Phase 0):  ✅ COMPLETE
  Agent 1: Row Segmentation Engine                     ✅ 32 tests
  Agent 2: 9-Field Schema + Mapper                     ✅ 47 tests
  Agent 5: Edge Case Fixtures                          ✅ 14 files

Phase 2 (sequential — depends on Agent 1 + Agent 2):  ✅ COMPLETE
  Agent 3: Per-Row Extraction Orchestrator              ✅ 27 tests

Phase 3 (sequential — depends on Agent 3):  ✅ COMPLETE
  Agent 4: Pipeline Integration              ✅ 9 tests

Phase 4 (verification):  ✅ COMPLETE (offline checks)
  Full test suite + ruff + frontend build
  2 remaining checks require live Ollama E2E test
```

---

## Ollama Model Config

```bash
# Per-row extraction (tiny context, 9 fields)
ACM_ROW_EXTRACTION_NUM_CTX=2048

# Configurable extraction model (was hardcoded qwen2.5:7b)
ACM_EXTRACTION_MODEL=llama3.1:8b

# Extraction mode toggle
ACM_ITEM_EXTRACTION_MODE=per_row

# Pre-extraction (building meta, large context)
ACM_PRE_EXTRACTION_MODEL=qwen2.5:14b-instruct-q4_K_M
ACM_PRE_EXTRACTION_NUM_CTX=32768

# Context window for bulk extraction (if using bulk mode)
OLLAMA_NUM_CTX=32768
```

---

## Decisions Log

| # | Decision | Date |
|---|----------|------|
| 1 | Primary input: DoclingDocument JSON (not HTML) | 2026-03-07 |
| 2 | LLM prompt format: Key-value pairs | 2026-03-07 |
| 3 | Item__c: 9 fields only (user confirmed) | 2026-03-07 |
| 4 | Building__c: 14 fields (user confirmed) | 2026-03-07 |
| 5 | No rapidfuzz — reuse Jaro-Winkler from consensus/matcher.py | 2026-03-07 |
| 6 | Mapper targets ACMExtractionRecord (not ACMRecord) | 2026-03-07 |
| 7 | num_ctx=2048 for per-row (9 fields fits easily) | 2026-03-07 |
| 8 | Drop: sample_result, quantity, recommendations, no_access from extraction | 2026-03-07 |
| 9 | Drop: normalize_recommendation(), Negative→N/A rule | 2026-03-07 |
| 10 | Gate recovery functions in per-row mode | 2026-03-07 |
| 11 | TruncationError fallback with cloud model retry | 2026-03-10 |
| 12 | Reserve 30% output budget in _ollama_split_by_budget | 2026-03-10 |
| 13 | Make Ollama extraction model configurable (ACM_EXTRACTION_MODEL env var) | 2026-03-10 |
| 14 | Default extraction model: llama3.1:8b (not qwen2.5:7b) | 2026-03-10 |
