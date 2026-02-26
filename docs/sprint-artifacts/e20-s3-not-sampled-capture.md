# Story E20-S3: "Not Sampled" / "No Access" Explicit Record Capture

**Epic:** E20 — Extraction Completeness & 100% Record Capture
**Priority:** P0
**Status:** backlog
**Change Proposal:** SCP-20260224 (2026-02-24)
**Depends on:** E20-S2

---

## User Story

**As a** developer fixing extraction quality,
**I want to** update the extraction prompt to explicitly instruct the LLM to capture "Not Sampled" and "No Access" records as individual ACM rows,
**So that** every item in the SAMP document is captured even when no physical sample was taken.

---

## Background

SAMP documents include rows for rooms/areas where the assessor was unable to sample:
- **"Not Sampled"** — item was observed but not sampled (inaccessible material, safety restriction)
- **"No Access"** — entire room was inaccessible; no assessment performed

Current extraction behaviour: the LLM may omit these rows because they lack sample numbers or analysis results. The existing preprocessing normalisation in `preprocess_samp.py` handles some cases, but the LLM extraction prompt does not explicitly instruct that zero-sample rows are valid ACM records.

The `no_access` field (bool, migration 032) and existing `sample_result` enum values `"Not Sampled"` / `"No Access"` already exist in the schema. This story updates the extraction prompt only — no schema changes required.

⚠️ **API COST: Every extraction triggers real OpenRouter spend.**
- Write and verify full implementation + unit tests FIRST
- Run ONE real extraction to validate (Broadmeadows ≈32 records)
- Only re-extract if this specific bug is confirmed fixed
- NEVER use mocked LLM responses to test extraction accuracy — real PDFs only from docs/samplePDF/

---

## Acceptance Criteria

### Prompt Change
- [x] `prompts/acm_extraction.j2` (or equivalent) updated to include explicit instruction:
  > "Include rows where the sample_result is 'Not Sampled' or 'No Access'. These are valid ACM records even if no sample number exists. Set `sample_result = 'Not Sampled'` or `sample_result = 'No Access'` accordingly."
- [x] Instruction placed in the **output requirements** section of the prompt (not buried in examples)
- [x] If a room has "No Access" noted: set `no_access = true` on the record
- [x] Prompt instructs: do NOT skip rows just because `nata_sample_number` is empty

### Schema Alignment
- [x] Confirm `sample_result` enum in `register_enums.json` includes `"Not Sampled"` and `"No Access"` values
- [x] Confirm `ACMRecord` Pydantic model in `acm_schemas.py` allows `nata_sample_number` to be `None` / empty string

### Tests
- [x] Unit test: mock LLM response containing a "Not Sampled" row → verify record is included in output with correct `sample_result`
- [x] Unit test: mock LLM response containing a "No Access" room → verify record has `no_access = true`
- [x] Unit test: verify existing records with sample numbers are unaffected
- [x] `uv run ruff check .` passes
- [x] All existing tests pass

### Validation
- [x] ONE real extraction on Broadmeadows PDF after E20-S1, S2, and S3 are implemented
- [x] "Not Sampled" and "No Access" records appear in extraction output
- [x] Record count improvement documented in `docs/sprint-artifacts/party-mode-20260224/progress.md`

---

## Technical Notes

### Prompt Location
The ACM extraction prompt lives in `prompts/` as a Jinja2 template (`.j2` extension). The exact filename should be confirmed before editing.

Key prompt sections to update:
1. **Output field instructions** — add `no_access` field description
2. **Row inclusion rules** — explicitly state "include Not Sampled and No Access rows"
3. **Sample number** — mark as optional, not required for record inclusion

### Existing Preprocessing Support
`open_notebook/extractors/preprocess_samp.py` normalises "No Access" text markers. Confirm that normalisation output is correctly forwarded to the LLM context — if the LLM never sees the "No Access" text because the preprocessor strips it, the prompt update will have no effect.

### `no_access` Field
Added in Migration 032 (E19-S1):
```surql
DEFINE FIELD no_access ON acm_record TYPE option<bool> DEFAULT false;
```
The extraction schema (`acm_schemas.py`) needs a corresponding optional field:
```python
no_access: bool = Field(default=False)
```

---

## Key Files Modified

| File | Change |
|------|--------|
| `prompts/acm_extraction.j2` (or equivalent) | Modified — add Not Sampled / No Access extraction instruction |
| `open_notebook/extractors/acm_schemas.py` | Confirm `no_access` field exists; add if missing |
| `tests/test_acm_extraction*.py` | Modified or new — Not Sampled / No Access test cases |

---

## Estimated Effort

S (Small) — Prompt wording update + schema field confirmation + unit tests.

---

**Story Status:** ⬜ BACKLOG
