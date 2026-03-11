# Bug Fix 11 — Progress

## Date: 2026-03-11

## Session Summary

### Problem
After v3.5 per-row extraction implementation, live extraction of `Clutch_Broadmeadows.pdf` (source:rw12h46pyx00urdp545v) produced **0 records, 0 buildings**.

### Root Cause Chain
1. LLM returned `room_code` instead of `room_id`/`name` -> Pydantic validation failed (26 errors)
2. Heuristic fallback only knew SAMP/ARA formats -> Division_5 doc matched neither -> 0 buildings
3. 0 buildings -> `extract_building_node` and `extract_items_node` both skipped -> 0 records
4. Additional: `page_number` missing from docling JSON, SF UPSERT error, prompt terminology issues

### Fixes Applied (6 total)

| Fix | Status | Result |
|-----|--------|--------|
| 1. Room key remapping in `_coerce_rooms_in_inventory` | Done | `room_code`/`room_name` etc. now remapped to `room_id`/`name` |
| 2. Generic heuristic fallback for all doc types | Done | Uses `document_structure.building_ids` or catch-all building |
| 3. SF Schema UPSERT inline record ID | Done | No more startup error |
| 4. Prompt terminology (generic, doc-agnostic) | Done | Removed SAMP/ARA/school references |
| 5. Building ID generation + metadata injection | Done | Sequential B001/B002 IDs, metadata context in prompt |
| 6. Inject `page_number` into docling JSON | Done | Segmenter gets correct page numbers |

### Live Extraction Results
- **Before:** 0 records, 0 buildings
- **After:** 16 records, 1 building (B001)
- Extraction completed in ~8.4s
- 4 records LLM-corrected, 0 failed
- Building `B001` correctly generated (not hallucinated SAMP-style)

### Remaining Issues Found During Live Test
1. **`building_record` table empty** — `extract_building_node` creates buildings in state but building name = building ID ("B001" instead of actual building name). May need prompt refinement or building extraction path fix.
2. **`acm_product` field null** — Per-row extraction prompt may not be mapping ACM product correctly
3. **`room_area` field null** — Per-row extraction missing room/area extraction
4. **Source register view (`/source/:id`) shows 0 buildings** — Queries `building_record` table which is empty

### Pre-Existing Test Failures (Analyzed)
All 4 were already fixed in commit `034fdb9d`:
- Tests 3 & 4 were real pipeline bugs (missing `building_records`, `items_extracted`, `building_meta_cache` in initial_state)
- Tests 1 & 2 were alignment/environment issues

### Verification
- 2119 tests passed, ruff clean
- Live extraction: 16 records confirmed in SurrealDB
- Screenshots saved in `docs/sprint-artifacts/bug-fix-11/screenshots/`

---

## Phase 2: Gap Analysis (2026-03-11)

### Problem
16 records extracted but ground truth expects 31. Where are the other 15?

### Root Causes Identified (6 bugs)

| # | Bug | Impact | Issue File |
|---|-----|--------|-----------|
| 1 | Building `page_end` underestimation → tables on later pages excluded | HIGH (~10-15 records) | `bug-page-range-table-loss.md` |
| 2 | `_merge_provider_tables` overwrites multiple tables per page | MEDIUM (~3-5 records) | `bug-page-range-table-loss.md` |
| 3 | Silent fallback in page filter masks page_number=0 | MEDIUM | `bug-page-range-table-loss.md` |
| 4 | `_LEVEL_REGEX` missing `INTERNAL` keyword | LOW (wrong fields) | `bug-row-segmenter-subheaders.md` |
| 5 | `ACMItemRow` missing sample_no, sample_result, acm_product | HIGH (benchmark fails) | `bug-per-row-schema-missing-fields.md` |
| 6 | Buildings not persisted to `building_record` table | P1 (frontend broken) | `bug-building-record-not-persisted.md` |

### Deliverables Created
- 4 issue files in `docs/issues/`
- Task plan: `docs/sprint-artifacts/bug-fix-11/task_plan.md` (5 phases, 13 tasks)
- Sprint status updated with 5 new story entries
- Workflow status changelog updated

### Phase 2 Status: PLANNED — Ready for execution

---

### Screenshots
| # | Description | File |
|---|-------------|------|
| 01 | Jobs page before (0 records, 0 buildings) | `01-jobs-page-before.png` |
| 02 | Extraction triggered (16 records) | `02-extraction-triggered.png` |
| 03 | Records table scroll | `03-extraction-records-scroll.png` |
| 04 | Jobs overview after (16 records, 1 building) | `04-jobs-overview-after.png` |
| 05 | Buildings tab (B001) | `05-buildings-tab.png` |
| 06 | Raw Tables tab (8 docling tables) | `06-raw-tables-tab.png` |
| 09 | ACM Records tab (16 records) | `09-acm-records-tab.png` |
| 10 | Source register view (0 buildings - known issue) | `10-source-register-view.png` |
| 11 | Extraction log (complete, 4 corrected) | `11-extraction-log.png` |
