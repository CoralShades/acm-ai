# Progress: Per-Row ACM Extraction Pipeline

**Started:** 2026-03-07
**Status:** NOT STARTED
**Primary Input:** DoclingDocument JSON | **Debug:** HTML export | **LLM Format:** Key-value pairs

---

## Phase 1: Parallel Independent Tasks

| Agent | Task | Status | Notes |
|-------|------|--------|-------|
| **Agent 1** | **Row Segmentation Engine** | ⬜ | |
| | Parse standard JSON tables (Type A) | ⬜ | |
| | Multi-page table merge (Type B) | ⬜ | |
| | Overlap row dedup (Type B) | ⬜ | |
| | Span registry for merged cells (Type C) | ⬜ | |
| | Hierarchical text fallback (Type D) | ⬜ | |
| | Multi-item cell detection (Type E1) | ⬜ | |
| | Note row skip (Type E2) | ⬜ | |
| | Sub-header context (Type E3) | ⬜ | |
| | Not Sampled text scan (Type F) | ⬜ | |
| | Fuzzy column mapping (Type G) | ⬜ | |
| | Split table JOIN (Type H) | ⬜ | |
| | HTML debug export per row + per building | ⬜ | |
| **Agent 2** | **Schemas + Mappers** | ⬜ | |
| | ACMItemRowSimple (12 fields) | ⬜ | |
| | map_row_simple_to_acm_record() | ⬜ | |
| | fuzzy_match_picklist() (rapidfuzz) | ⬜ | |
| | classify_product_from_description() | ⬜ | |
| | Dependency chain enforcement | ⬜ | |
| | Business rule: Negative→N/A | ⬜ | |
| **Agent 5** | **Edge Case Fixtures** | ⬜ | |
| | JSON fixtures for Type A-H | ⬜ | |
| | HTML debug fixtures for visual comparison | ⬜ | |
| | Markdown fixtures for Type D, F | ⬜ | |
| | Parameterized test scaffolds | ⬜ | |

## Phase 2: Sequential (depends on Phase 1)

| Agent | Task | Status | Notes |
|-------|------|--------|-------|
| **Agent 3** | **Per-Row Extractor** | ⬜ | |
| | row_extraction.jinja (KV format) | ⬜ | |
| | row_split.jinja (Type E1) | ⬜ | |
| | build_kv_prompt() | ⬜ | |
| | extract_single_row() + parse | ⬜ | |
| | split_multi_item_row() | ⬜ | |
| | extract_all_rows() loop | ⬜ | |
| | Retry logic (max 2 per row) | ⬜ | |
| | Langfuse child span per row | ⬜ | |
| | SSE event per row | ⬜ | |

## Phase 3: Integration (depends on Phase 2)

| Agent | Task | Status | Notes |
|-------|------|--------|-------|
| **Agent 4** | **Pipeline Integration** | ⬜ | |
| | ACM_EXTRACTION_STRATEGY env var | ⬜ | |
| | extract_items_node per-row path | ⬜ | |
| | Bulk path unchanged | ⬜ | |
| | SSE progress wiring | ⬜ | |
| | building_id FK on acm_record | ⬜ | |
| | Debug HTML storage | ⬜ | |

## Phase 4: Verification

| Check | Status | Result |
|-------|--------|--------|
| All edge cases pass | ⬜ | |
| ACMItemRowSimple→ACMRecord valid | ⬜ | |
| Picklist chain enforced | ⬜ | |
| qwen2.5:14b num_ctx=4096 works | ⬜ | |
| Row retry isolation | ⬜ | |
| Building↔Item FK correct | ⬜ | |
| Bulk path still works | ⬜ | |
| Langfuse traces clean | ⬜ | |
| HTML debug tables readable | ⬜ | |
| pytest passes | ⬜ | |
| Broadmeadows ≥31/31 | ⬜ | |
| Alexander ≥36/43 | ⬜ | |

---

## Decisions Log

| # | Decision | Date |
|---|----------|------|
| 1 | Primary input: DoclingDocument JSON (not HTML) | 2026-03-07 |
| 2 | LLM prompt format: Key-value pairs | 2026-03-07 |
| 3 | HTML debug export: Yes, secondary alongside JSON | 2026-03-07 |
| 4 | TableFormer: ACCURATE mode, do_cell_matching=True | 2026-03-07 |
| 5 | Confidence threshold | PENDING |
| 6 | MinerU fallback priority | PENDING |
| 7 | Column mapping cache strategy | PENDING |
