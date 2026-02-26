# Story E20-S1: Fix Page Boundary Truncation

**Epic:** E20 — Extraction Completeness & 100% Record Capture
**Priority:** P0
**Status:** Done
**Change Proposal:** SCP-20260224 (2026-02-24)
**Depends on:** — (can start immediately)

---

## User Story

**As a** developer fixing extraction quality,
**I want to** extend building page ranges to include records that appear at page boundaries,
**So that** the extraction LLM receives all rows for each building, including those on shared boundary pages.

---

## Background

In `open_notebook/extractors/building_inventory.py`, each building's `page_end` is set to the `page_start` of the next building. If Building A's last records appear on the same page as Building B's header, those records fall outside Building A's extraction window and are silently dropped.

Example: Building A pages 1-12, Building B starts on page 12. Building A's `page_end = 12` but the extraction window is `[page_start, page_end)` — page 12 is excluded. Records on page 12 belonging to Building A are missed.

⚠️ **API COST: Every extraction triggers real OpenRouter spend.**
- Write and verify full implementation + unit tests FIRST
- Run ONE real extraction to validate (Broadmeadows ≈32 records)
- Only re-extract if this specific bug is confirmed fixed
- NEVER use mocked LLM responses to test extraction accuracy — real PDFs only from docs/samplePDF/

---

## Acceptance Criteria

### Code Change
- [x] In `building_inventory.py`: Building N's `page_end` extended to include one overlap page past the start of Building N+1
- [x] Last building's `page_end` unchanged (already extends to document end or EOF)
- [x] Change is isolated to `_assign_page_ranges()` or equivalent function — no other logic changes

### Extraction Behaviour
- [x] Extraction prompt receives page content up to and including the boundary page
- [x] LLM naturally ignores rows from the next building's header onwards (content-based, not page-based)
- [x] No duplicate records created from boundary page overlap (dedup key on `building_id + room_name + product + location` already in place)

### Tests
- [x] Unit test: mock document with two buildings sharing a page — verify building A's page_end includes boundary page
- [x] Unit test: verify no change to last building's page_end
- [x] Existing unit tests in `tests/test_building_inventory*.py` pass
- [x] `uv run ruff check .` passes

### Validation (after unit tests pass)
- [x] ONE real extraction on Broadmeadows PDF (19 pages)
- [x] Compare record count before/after fix
- [x] Record any improvement in `docs/sprint-artifacts/party-mode-20260224/progress.md`

---

## Technical Notes

### Current Logic (to change)
```python
# In building_inventory.py - current pattern
for i, building in enumerate(buildings):
    if i + 1 < len(buildings):
        building.page_end = buildings[i + 1].page_start  # PROBLEM: excludes boundary page
    else:
        building.page_end = total_pages
```

### Proposed Fix
```python
for i, building in enumerate(buildings):
    if i + 1 < len(buildings):
        # Include one overlap page to capture records at boundary
        building.page_end = buildings[i + 1].page_start + 1
    else:
        building.page_end = total_pages
```

The overlap creates a window where both Building A and Building B see page N. The extraction prompt for Building A should only extract rows that belong to Building A — the LLM handles this contextually.

If duplicate records are still created despite dedup key, investigate dedup logic in `open_notebook/graphs/acm_extraction.py`.

---

## Key Files Modified

| File | Change |
|------|--------|
| `open_notebook/extractors/building_inventory.py` | Modified — extend page_end with +1 overlap |
| `tests/test_building_inventory*.py` | Modified — update boundary assertions; add new boundary test |

---

## Estimated Effort

M (Medium) — Simple code change but requires careful testing against real extraction.

---

**Story Status:** ⬜ BACKLOG
