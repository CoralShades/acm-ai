# Epic 20: Extraction Completeness & 100% Record Capture

**Status:** backlog
**Priority:** P0
**Change Proposal:** SCP-20260224 (2026-02-24)
**Trigger:** Post-demo stakeholder feedback — Issue 4 (missing records)

---

## Summary

Fix the extraction pipeline to achieve 100% record capture on the Broadmeadows Police Station test case (32/32 records, including all "Not Sampled", "No Access", and edge-case items). Three root causes identified: page boundary truncation, REGEX_ONLY silent failures, and insufficient LLM prompting for edge-case records.

---

## Current State

- **Broadmeadows E2E test:** 28/31 matched records (90%), threshold at 80%
- **Missing records:** 2 "Not Sampled" edge cases + 1 sampled item (roof ductwork)
- **Root causes:** Identified in PR #55 post-review and party-mode session 2026-02-24

## Target State

- **100% record capture:** 32/32 records on Broadmeadows (all 32 in the source, 31 testable + 1 unlisted)
- **E2E test threshold raised to 97%** (30/31+ matched records in test assertions)
- **No silent failures:** REGEX_ONLY escalates to FULL_LLM when yield is below expected

---

## Epic Stories

| Story | Title | Priority | Size | Status |
|-------|-------|----------|------|--------|
| E20-S1 | Fix Page Boundary Truncation | P0 | M | backlog |
| E20-S2 | REGEX_ONLY Yield Check + FULL_LLM Escalation | P0 | M | backlog |
| E20-S3 | "Not Sampled" / No Access Record Capture | P0 | M | backlog |
| E20-S4 | E2E Accuracy Validation — 100% Broadmeadows | P0 | S | backlog |

---

## Root Cause Analysis

### Root Cause 1: Page Boundary Truncation (→ E20-S1)

In `open_notebook/extractors/building_inventory.py`:
- `page_end` for building N is set to the `page_start` of building N+1
- If a building's last records appear on the same page as the next building's header, those records fall outside the extraction window
- Fix: extend `page_end` to include one additional overlap page; the extraction prompt naturally ignores irrelevant rows from the next building

### Root Cause 2: REGEX_ONLY Silent Failures (→ E20-S2)

In `open_notebook/extractors/orchestrator.py`:
- SAMP buildings with `BuildingComplexity.SIMPLE` (few rooms, few items) are routed to `ExtractionStrategy.REGEX_ONLY`
- REGEX_ONLY uses fixed room/row patterns that fail silently on non-standard formatting
- No yield check: if REGEX_ONLY returns 0 records for a building with known content, extraction ends without escalation
- Fix: after REGEX_ONLY extraction, compare yield to `acm_item_count_estimate`; if yield < 50% of estimate, escalate to FULL_LLM

### Root Cause 3: Missing "Not Sampled" Capture (→ E20-S3)

Current LLM extraction prompt treats "Not Sampled", "Not Accessible", "No Access" as informational notes rather than distinct ACM records:
- Battery charger fuse cartridge (Not Sampled) — missed
- Unknown toilet room item (Not Sampled) — missed
- These should be extracted as records with `sample_result = 'Not Sampled'` and `no_access = true`
- Fix: explicit extraction prompt instructions for these variants; add to system instructions

---

## Implementation Sequence

```
E20-S1 → E20-S2 → E20-S3 → E20-S4
```

E20-S1 and E20-S2 can be implemented in the same story if combined scope fits. E20-S3 depends on E20-S1 (correct pages must be passed to LLM before prompt can be tested).

---

## Cost Awareness

⚠️ **API COST: Every extraction triggers real OpenRouter spend.**
- Write and verify full implementation + unit tests FIRST
- Run ONE real extraction to validate (Broadmeadows ≈32 records, Alexandra ≈533 records)
- Only re-extract if a specific confirmed bug was fixed
- NEVER use mocked LLM responses to test extraction accuracy — real PDFs only from docs/samplePDF/

---

## Key Files Modified

| File | Change |
|------|--------|
| `open_notebook/extractors/building_inventory.py` | Extend `page_end` with overlap (E20-S1) |
| `open_notebook/extractors/orchestrator.py` | Add yield check + FULL_LLM escalation (E20-S2) |
| `prompts/acm_extraction.j2` (or equivalent) | Not Sampled / No Access capture (E20-S3) |
| `tests/test_broadmeadows_e2e.py` | Raise threshold to 97% (E20-S4) |
