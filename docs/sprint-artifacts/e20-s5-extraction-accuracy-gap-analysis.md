# Story E20-S5: Extraction Accuracy Gap Analysis — Remaining 4 Records

**Epic:** E20 — Extraction Completeness & 100% Record Capture
**Priority:** P1
**Status:** backlog
**Depends on:** E20-S1, E20-S2, E20-S3, E20-S4
**Created:** 2026-02-24 — per E20-S4 AC: "If < 100%: create E20-S5 with gap analysis"

---

## User Story

**As a** developer validating the extraction pipeline,
**I want to** investigate and fix the 4 records still missing from the Broadmeadows extraction,
**So that** the pipeline achieves 100% record capture on the canonical test document.

---

## Background

E20-S4 ran the Broadmeadows E2E test after all E20 fixes and achieved 27/31 (87%).
Four records remain missing. Two distinct root causes identified:

**Root cause A — "Not Sampled" location extraction:**
The LLM assigns `location="?"` or wrong location for Not Sampled rows. These rows appear
in the PDF without a dedicated location column value, and the extraction prompt doesn't
guide the LLM to copy the location from context (room header or adjacent rows).

**Root cause B — East Ductwork / Roof page coverage:**
Sample 34511-039-015 (Flange joints, Roof / East Ductwork) is completely absent.
This record is on the Roof level — possibly not included in the text chunk or mislabeled
as a boundary page.

**Root cause C — E2E test uses old pipeline:**
The E2E test (`acm_extraction.py` graph) does NOT exercise the new orchestrator pipeline
where E20-S1 (boundary fix) and E20-S2 (yield check) live. A proper test against
the orchestrator should be created.

---

## Missing Records (from E20-S4 log)

| # | Level | Room | Location | Item | Sample |
|---|-------|------|----------|------|--------|
| 1 | Ground | Front Desk Area | Filing Cabinet | Filing Cabinet | Not Sampled |
| 2 | Level 1 | Switch Room | Automatic Battery Charger | Fuse cartridge | Not Sampled |
| 3 | Ground | Roof | East Ductwork | Flange joints | 34511-039-015 |
| 4 | Ground | Main Foyer | Room Adjacent Disabled Toilet | Unknown | Not Sampled |

---

## Acceptance Criteria

### Gap Analysis (Required)
- [ ] Read the raw Broadmeadows PDF page by page and locate each missing record
- [ ] Identify the exact page and table row for each missing record
- [ ] Identify WHY each was missed (prompt gap, location extraction, page coverage)

### Fix A — "Not Sampled" location extraction
- [ ] Update `prompts/acm/building_extraction.jinja` to guide location extraction for Not Sampled rows
- [ ] Instructions: "For Not Sampled/No Access rows, extract the location from the table column — do not use '?' if a value exists in the source"
- [ ] Unit test: verify extracted records for Not Sampled rows have correct location

### Fix B — East Ductwork page coverage
- [ ] Verify which page sample 34511-039-015 appears on in the PDF
- [ ] Check if that page is included in the extraction chunk
- [ ] If page is missing: trace to `register_start_page` calculation in `acm_extraction.py`

### Fix C — E2E test pipeline alignment (Recommended)
- [ ] Create or update `test_broadmeadows_e2e.py` to optionally test the orchestrator pipeline
- [ ] The orchestrator (new pipeline) should show higher accuracy due to E20-S1/S2 fixes
- [ ] Annotate the existing test to make clear it tests the legacy `acm_extraction.py` graph

### Validation
- [ ] After fixes: re-run `uv run pytest tests/test_broadmeadows_e2e.py -m integration -v -s`
- [ ] Target: 31/31 (100%)
- [ ] Log results to `docs/sprint-artifacts/e20-broadmeadows-validation-s5.log`
- [ ] If 31/31: mark E20 complete in sprint-status.yaml

---

## Technical Notes

### Finding records in the PDF
```python
import fitz
doc = fitz.open("docs/samplePDF/Clutch_Broadmeadows.pdf")
for i, page in enumerate(doc, 1):
    text = page.get_text()
    if "34511-039-015" in text or "East Ductwork" in text:
        print(f"Page {i}: {text[:200]}")
```

### Location extraction for Not Sampled rows
The prompt currently says:
> "For No Access entries: set no_access=true, sample_result='No Access'"

But doesn't say: "Extract the location field from the table — don't infer '?'"

Fix in `prompts/acm/building_extraction.jinja` in the Not Sampled / No Access section.

### Raw debug output
Previous extraction debug files saved to: `_debug/acm_prompts/`
These show exactly what the LLM received and responded with.

---

## Dev Agent Record

*(to be filled in upon implementation)*
