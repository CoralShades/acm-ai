# Story E20-S2: REGEX_ONLY Yield Check + FULL_LLM Escalation

**Epic:** E20 — Extraction Completeness & 100% Record Capture
**Priority:** P0
**Status:** backlog
**Change Proposal:** SCP-20260224 (2026-02-24)
**Depends on:** E20-S1

---

## User Story

**As a** developer fixing extraction quality,
**I want to** automatically escalate REGEX_ONLY extractions to FULL_LLM when they return unexpectedly few records,
**So that** buildings with unusual formatting don't silently yield empty or partial results.

---

## Background

In `open_notebook/extractors/orchestrator.py`, SAMP buildings with `BuildingComplexity.SIMPLE` complexity are assigned `ExtractionStrategy.REGEX_ONLY`. REGEX_ONLY uses hardcoded room/row patterns that work for standard SAMP formatting but fail silently on non-standard documents (merged cells, missing separators, variant column orders).

Currently, if REGEX_ONLY returns 0 records for a building with known content, the pipeline continues without escalation. The building is effectively extracted as empty.

⚠️ **API COST: Every extraction triggers real OpenRouter spend.**
- Write and verify full implementation + unit tests FIRST
- Run ONE real extraction to validate (Broadmeadows ≈32 records)
- Only re-extract if this specific bug is confirmed fixed
- NEVER use mocked LLM responses to test extraction accuracy — real PDFs only from docs/samplePDF/

---

## Acceptance Criteria

### Code Change
- [x] After REGEX_ONLY extraction: compare `len(extracted_records)` against `building.acm_item_count_estimate`
- [x] If yield < 50% of estimate AND estimate > 0: log warning + escalate to FULL_LLM for that building
- [x] If `acm_item_count_estimate` is None: escalate if `len(extracted_records) == 0` and building has page content
- [x] Escalation is logged at WARNING level: `"Building {id}: REGEX_ONLY yield {n}/{estimate} < 50% — escalating to FULL_LLM"`
- [x] Stats updated to reflect escalation: `strategy_distribution["regex_escalated_to_llm"] += 1`

### Strategy Selection Audit
- [x] Review `_select_strategy()` for SAMP buildings: confirm that any building with > 3 pages of content is not mis-classified as SIMPLE
- [x] If needed: raise complexity threshold for SIMPLE classification

### Tests
- [x] Unit test: mock REGEX_ONLY returning 0 records for a building with estimate=5 → verify FULL_LLM is called
- [x] Unit test: mock REGEX_ONLY returning 3 records for estimate=4 (75% yield) → verify NO escalation
- [x] Unit test: building with `acm_item_count_estimate=None` and 0 REGEX records → verify escalation
- [x] `uv run ruff check .` passes
- [x] All existing tests pass

### Validation
- [x] ONE real extraction on Broadmeadows PDF after both E20-S1 and E20-S2 are implemented
- [x] Log shows escalation decisions per building
- [x] Record count improvement documented

---

## Technical Notes

### Where to Add the Yield Check
In `orchestrator.py`, after the REGEX_ONLY extraction call:
```python
# After calling regex extraction
regex_records = await _run_regex_extraction(building, markdown_content)

# Yield check
estimate = building.acm_item_count_estimate or 0
if len(regex_records) == 0 and (estimate > 0 or building_has_content):
    logger.warning(f"Building {building.building_id}: REGEX_ONLY yield 0/{estimate} — escalating to FULL_LLM")
    llm_records = await _run_llm_extraction(building, ...)
    return llm_records
elif estimate > 0 and len(regex_records) / estimate < 0.5:
    logger.warning(f"Building {building.building_id}: REGEX_ONLY yield {len(regex_records)}/{estimate} < 50% — escalating")
    llm_records = await _run_llm_extraction(building, ...)
    return llm_records
return regex_records
```

### `acm_item_count_estimate` Source
This field is populated by `building_inventory.py` during Stage -1 (document structure analysis). Ensure it's populated for SAMP documents. If the estimate is missing or 0, the escalation uses the "zero records" trigger.

---

## Key Files Modified

| File | Change |
|------|--------|
| `open_notebook/extractors/orchestrator.py` | Modified — add yield check + escalation after REGEX_ONLY |
| `tests/test_orchestrator*.py` | Modified or new — yield check + escalation tests |

---

## Estimated Effort

M (Medium) — Logic addition to orchestrator + unit tests. Validation requires one real extraction run.

---

**Story Status:** ⬜ BACKLOG
