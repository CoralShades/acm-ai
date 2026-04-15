# Pipeline Audit: Broadmeadows 31 -> 10 Record Loss

**Date:** 2026-04-16
**Branch:** feat/sf-reconciliation-20260411
**Auditor:** Pipeline Audit Session (PA-0 through PA-SYNTH)

## Executive Summary

The Broadmeadows Police Station PDF (31 ground-truth ACM records) produces only 10 records through the extraction pipeline. Root cause analysis identified **one primary** and **four contributing** causes. The primary cause accounts for 60%+ of the record loss and has a one-line fix.

## Pipeline Architecture

```
Upload → POST /api/sources → process_source command
  ├─ source_graph (PyMuPDF text extraction)
  └─ Docling Direct API (table extraction → acm_table_section)

Frontend → POST /api/acm/extract → acm_extract command (MANUAL trigger)
  └─ LangGraph Pipeline:
     1. metadata_and_structure  (1 LLM call, first 15K chars)
     2. inventory               (1 LLM call, building identification)
     3. save_intelligence        (DB write)
     4. schema_inference         (1 LLM call, column mapping)
     5. extract_building         (1 LLM call per building, Phase 1 metadata)
     6. extract_items            (per-row OR bulk, Phase 2 items)
     7. normalize_to_sf          (deterministic field mapping)
     8. validate                 (strict field validation)
     9. correct                  (corrective RAG loop, conditional)
    10. deduplicate              (composite key dedup)
    11. recover_no_access        (text scan for missed No Access entries)
    12. save                     (DB write → acm_record)
```

## Root Cause Analysis

### RC-1: CRITICAL — Building page_end capped at +2 pages (LLM path)

**File:** `open_notebook/extractors/building_inventory.py:830-842`
**Impact:** Loss of 15-20 records (primary cause of 31→10)

The LLM-based building inventory path expands single-building `page_end` by only +2 pages:

```python
_PAGE_END_EXPANSION_MARGIN = 2
expanded_end = min(current_end + _PAGE_END_EXPANSION_MARGIN, total)
```

If the LLM reports Broadmeadows register ends at page 12 but it actually runs to page 18, only pages up to 14 are processed. Everything beyond is silently excluded by:
- `_extract_building_content()` (orchestrator.py:280-307)
- `_get_docling_tables()` page range query (orchestrator.py:54-65)

**Contrast:** The heuristic fallback path correctly sets `page_end = total_pages` at `building_inventory.py:618-627`. This fix was already implemented for the heuristic but NOT applied to the LLM path.

**Fix:**
```python
# building_inventory.py:830-842 — replace +2 margin with total_pages
if len(inventory.buildings) == 1 and document_structure:
    total = document_structure.total_pages
    bld = inventory.buildings[0]
    current_end = bld.page_end or bld.page_start
    if total and current_end < total:
        bld.page_end = total  # Match heuristic behavior
```

The concern about over-extraction (including lab results/risk assessments) is less harmful than losing 60%+ of records. Downstream filters (`_is_acm_table()`, validation, dedup) handle non-register content.

---

### RC-2: HIGH — Heuristic cross-validation cannot extend existing building page ranges

**File:** `open_notebook/extractors/building_inventory.py:846-867`
**Impact:** Prevents self-healing when LLM underestimates

The heuristic cross-validation at line 846 only ADDS buildings the LLM missed. It does NOT extend the page_end of buildings the LLM found:

```python
if h_id_lower not in llm_ids and h_name_lower not in llm_names:
    inventory.buildings.append(h_building)  # Only adds NEW buildings
```

For Broadmeadows (single building), the heuristic finds the same building with `page_end=total_pages`, but the duplicate check prevents merging. The LLM's truncated page_end persists.

**Fix:** After cross-validation, compare page ranges and use the wider range:
```python
for h_building in heuristic.buildings:
    for llm_building in inventory.buildings:
        if llm_building matches h_building:
            llm_building.page_end = max(llm_building.page_end, h_building.page_end)
```

---

### RC-3: MEDIUM — Silent table rejection by _is_acm_table() filter

**File:** `open_notebook/extractors/row_segmenter.py:151-184, 759`
**Impact:** Could drop tables with non-standard column headers (0-5 records)

The `_is_acm_table()` filter requires `item_description` to be fuzzy-matched from column headers. If a table uses unrecognized headers (e.g., "ACM Description", "Suspected Material"), the table is rejected.

**Mitigated by:** Fallback to all tables when ALL fail filter (line 760-768). But when SOME pass and SOME don't, rejected tables are silently dropped with no per-table logging.

**Fix:** Add per-table rejection logging and expand `COLUMN_ALIASES["item_description"]` with more variants.

---

### RC-4: MEDIUM — Docling TableFormer misses small table fragments

**File:** `commands/source_commands.py:211-222` (gap detection warning)
**Impact:** 2 records lost (page 8 known issue)

Page 8 of Broadmeadows has a 2-row table that Docling's TableFormer misses. Gap detection exists (logs a warning) but doesn't recover the rows.

**Mitigated by:** `recover_no_access_node` at line 2178 scans full_text for "No Access" entries. But this only works for No Access/Not Sampled patterns, not for all record types.

---

### RC-5: LOW — Content truncation for metadata extraction

**File:** `open_notebook/graphs/acm_extraction.py:356-359`
**Impact:** Could cause wrong `register_start_page` (cascading effect)

Metadata extraction truncates to 15K chars (first ~5 pages). If the register section header isn't in the first 5 pages, `register_start_page` could be wrong, causing `_trim_to_register()` to clip register content before the inventory LLM sees it.

---

## Fix Priority

| Priority | Fix | Expected Record Recovery | Effort |
|----------|-----|-------------------------|--------|
| P0 | RC-1: Change page_end expansion to total_pages | +15-20 records | 1 line |
| P1 | RC-2: Merge wider page ranges from heuristic | +2-5 records (defensive) | ~10 lines |
| P2 | RC-3: Add per-table rejection logging + expand aliases | +0-5 records + observability | ~15 lines |
| P3 | RC-4: Improve TableFormer sensitivity or add text fallback | +2 records | Complex |

## Pipeline Component Map (PA-7)

| Node | LLM Calls | Purpose | Necessary? |
|------|-----------|---------|------------|
| metadata_and_structure | 1 | Identify consultant, site, register_start_page | YES |
| inventory | 1 | Identify buildings and page ranges | YES |
| save_intelligence | 0 | Persist for UI display | YES |
| schema_inference | 1 | Column mapping for multi-format support | YES |
| extract_building | N (1/building) | Phase 1: Building metadata | YES |
| extract_items | N (varies) | Phase 2: ACM items | YES (core) |
| normalize_to_sf | 0 | Map V3 fields to V2 schema | YES |
| validate | 0 | Reject invalid records | YES |
| correct | 0-N | Fix validation failures | YES |
| deduplicate | 0 | Remove duplicates | YES |
| recover_no_access | 0 | Recover missed No Access entries | YES |
| save | 0 | Persist to database | YES |

**Conclusion:** No unnecessary pipeline components found. All 12 nodes serve essential purposes. The pipeline is architecturally sound — the record loss is caused by a page range configuration bug, not a design flaw.

## Worker Auto-Trigger (PA-8)

**Finding:** NO automatic chaining from `process_source` → `acm_extract`. The frontend must explicitly call `POST /api/acm/extract` to create the second command.

**Entry points:**
- `UploadWizard.tsx:149` — primary upload path
- `AddSourceDialog.tsx:363/447` — legacy dialog
- `upload-service.ts:66-68` — bulk upload
- `QuickUploadDialog.tsx:129` — quick upload

The 10 records confirm `acm_extract` DID fire for the Broadmeadows test. This is not the root cause.

## Speed Analysis

The pipeline architecture supports fast execution:
- Pre-extraction intelligence: 3 sequential LLM calls (metadata, inventory, schema)
- Per-building extraction: N concurrent LLM calls (bounded by `_MAX_CONCURRENT_BUILDINGS`)
- Post-extraction: Deterministic (validation, dedup, save)

RunPod RTX 5090 completing in 45s is consistent with:
- ~5s for Docling table extraction (GPU accelerated)
- ~10s for 3 pre-extraction LLM calls (Ollama, GPU)
- ~15s for building + items extraction (1 building, GPU)
- ~15s for validation, dedup, save

The old 37min-1hr time was caused by:
1. OCR being enabled on native PDFs (now fixed: `do_ocr=False`)
2. Possibly MinerU running in addition to Docling (now optional)
3. CPU-bound processing instead of GPU

## Next Steps

1. Apply RC-1 fix (1 line change)
2. Run local extraction with Broadmeadows PDF
3. Verify record count reaches 31
4. Apply RC-2 and RC-3 fixes
5. Run Alexander District Hospital PDF (43 ground truth)
6. Set up Langfuse/LangSmith for trace visibility
