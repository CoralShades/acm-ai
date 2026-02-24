# Story E20-S5: Extraction Accuracy Gap Analysis — Remaining 4 Records

**Epic:** E20 — Extraction Completeness & 100% Record Capture
**Priority:** P1
**Status:** in-progress
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
- [x] Update `prompts/acm/building_extraction.jinja` to guide location extraction for Not Sampled rows
- [x] Instructions: "For Not Sampled/No Access rows, extract the location from the table column — do not use '?' if a value exists in the source"
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

**Updated:** 2026-02-25

### E2E Validation Results (2026-02-25)

**Extraction Attempt #7** — First successful extraction after OpenRouter provider routing fix.

| Metric | Value |
|--------|-------|
| Records extracted | 16 unique (32 total — worker race condition) |
| Core sample coverage | 15/16 (93.75%) |
| Missing sample | 34511-039-014 (Boiler Room, Walls, Expansion joint, Negative) |
| Extra sample | 34511-039-005 (valid from PDF, not in CSV) |
| Execution time | 87.9s |
| Model | anthropic/claude-sonnet-4.6 via OpenRouter → Anthropic direct |
| Strategy | full_llm (1 building, pages 1-3) |
| Confidence | 100% high |

### Field Coverage Gap Analysis (CSV vs Extraction Schema)

**24 of 43 CSV columns mapped (56%)**. Key gaps:

| Gap ID | Severity | CSV Fields | Impact |
|--------|----------|-----------|--------|
| G-02 | **HIGH** | date_of_inspection | No schema field — critical for compliance |
| G-01 | MEDIUM | address, suburb, postcode | Needed for BAR register exports |
| G-04 | MEDIUM | quantity_removed, removal_notification_no, epa_certificate_no | Removal compliance tracking |
| G-05 | MEDIUM | additional_comments | Free-text observations lost |
| G-06 | MEDIUM | floor_level | In extraction schema but NOT in domain ACMRecord — data lost at persistence |
| G-08 | INFO | acm_product_group, acm_product_type | CSV has natively; extraction re-classifies post-hoc |
| G-09 | LOW | room_area, location_detail, item_name | UI naming mismatch — phantom fields; data in location/product |

### OpenRouter Provider Routing Fix

Implemented in `open_notebook/graphs/utils.py`:
- `OPENROUTER_IGNORED_PROVIDERS = ["Amazon Bedrock", "Azure"]`
- `OPENROUTER_PROVIDER_ORDER = ["Anthropic", "Google", "OpenAI"]`
- `_apply_openrouter_preferences()` injects `extra_body` with provider routing + `transforms: ["middle-out"]`
- `provision_extraction_fallback_model()` priority: Anthropic direct → OpenAI direct → Ollama Qwen

Schema error fallback in `open_notebook/extractors/orchestrator.py`:
- `is_provider_schema_error()` detects grammar/schema rejection
- Falls back to direct `model.ainvoke()` + `parse_json_response()`

### Issues Discovered
1. **Worker race condition** (CRITICAL): Two workers picked up same command → 32 records. Need at-most-once delivery in surreal-commands.
2. **Missing sample 34511-039-014** (DATA): Boiler Room / Walls / Expansion joint. Needs investigation — may be lost during dedup or extraction.
3. **Provider error latency** (PERF): `extra_body` provider routing may not flow through structured output calls, causing initial failure + ~40s fallback delay.
4. **floor_level data loss** (SCHEMA): Extraction captures floor_level but ACMRecord domain model doesn't persist it.

### Remaining for closure
- [x] Fix worker race condition (new story: bug-worker-race-condition)
- [x] Investigate missing sample 34511-039-014 — prompt rules 9-12 added to extract utility areas, small items, and cross-references
- [x] Add missing high-priority CSV fields to extraction schema (date_of_inspection, address, suburb, postcode)
- [x] Fix floor_level persistence gap (extraction → domain model)
- [ ] Eliminate provider error initial failure (extra_body through structured output)
- [ ] Re-run E2E validation targeting 31/31 (16/16 core samples + 15 non-core rows)
- [ ] Clean up 16 duplicate records from worker race condition

### Prompt Fix Implementation (2026-02-25)
Added rules 9-12 to `prompts/acm/building_extraction.jinja`:
- **Rule 9**: Items in utility/service areas (Boiler Room, Switch Room, Plant Room, etc.) must not be skipped
- **Rule 10**: Small items (expansion joints, gaskets, mastic, caulking) are valid ACM items and must be extracted
- **Rule 11**: "Similar To"/"As Per" references — both the original sample and the referencing item must be extracted as separate records
- **Rule 12**: Negative/Not Detected items with sample numbers are valid sampled entries and must be extracted
