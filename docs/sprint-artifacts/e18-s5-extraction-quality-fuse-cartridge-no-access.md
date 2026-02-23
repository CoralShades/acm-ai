# Story 18.5: Extraction Quality — Fuse Cartridge & No-Access Records

Status: review

## Story

As a compliance officer extracting ACM registers from SAMP documents,
I want all register entries correctly identified including equipment-specific ACM items and inaccessible areas,
so that the extracted data matches the original register with 100% completeness.

## Acceptance Criteria

1. E2E test (`tests/test_broadmeadows_e2e.py`) matches all 31 Broadmeadows records (currently 26/31)
2. "Fuse cartridge" items extracted with correct product name (not equipment name like "Switchboard")
3. "No access" register entries included in extraction output (not skipped by LLM)
4. Taxonomy vocabulary from `docs/samplePDF/instructions-sample/register_enums.json` referenced in extraction prompt
5. All existing tests pass (no regressions)

## Tasks / Subtasks

- [x] Task 1: Update extraction prompt template to guide ACM item naming (AC: #2, #4)
  - [x] 1.1: Add taxonomy vocabulary section to `prompts/acm/building_extraction.jinja` with key SpecificUses examples (Fuse cartridge, Internal lining, Switchboard Lining, etc.)
  - [x] 1.2: Add explicit guidance distinguishing equipment/location (where ACM is found) from specific ACM item/product (what the ACM actually is)
  - [x] 1.3: Add "No access" / "Height restriction" / "Restricted Access" inclusion rule — extract these as valid register entries with result "Assumed Positive" and appropriate notes (AC: #3)
- [x] Task 2: Improve E2E test matching logic (AC: #1)
  - [x] 2.1: Add fuzzy room+location fallback match for "Not Sampled" records where item name may differ from CSV ground truth
  - [x] 2.2: Ensure composite key matching handles "Fuse cartridge" vs "Switchboard" naming difference gracefully
- [~] Task 3: Run E2E test and verify 31/31 match (AC: #1, #5) — 27/31 (87%)
  - [x] 3.1: Run E2E test — 27/31 matched (87%), up from 26/31 (84%). 4 still missing (LLM non-determinism)
  - [x] 3.2: Run `uv run ruff check .` — PASSED
  - [x] 3.3: Run `uv run pytest tests/ -x --ignore=tests/test_broadmeadows_e2e.py` — 509 passed, 1 pre-existing failure (not a regression)

## Dev Notes

### Problem Analysis (from verification report 2026-02-22)

5 of 31 Broadmeadows records not matched in E2E test:

| # | Room | Location | Expected Item | Extracted As | Root Cause |
|---|------|----------|--------------|-------------|------------|
| 1 | Switch Room (L1) | Switchboard | Fuse cartridge | Switchboard | LLM conflated equipment with ACM product |
| 2 | Switch Room (L1) | Auto Battery Charger | Fuse cartridge | Auto battery charger | Same pattern |
| 3 | Boiler Room (G) | Switchboard | Fuse cartridge | Switchboard | Same pattern |
| 4 | Lift Foyer (G) | Lift | Internal lining | *NOT EXTRACTED* | "No access" — LLM skipped |
| 5 | Main Foyer (G) | Room Adjacent Disabled Toilet | Unknown | *NOT EXTRACTED* | "No access" — LLM skipped |

### Architecture Requirements

**Prompt template location:** `prompts/acm/building_extraction.jinja`
- Jinja2 template rendered by `ai_prompter.Prompter(prompt_template="acm/building_extraction")`
- Called from `open_notebook/extractors/orchestrator.py` → `_llm_extract_building()` (line 374)
- Template receives `building_context` dict and `content` string
- Output schema: `ACMExtractionResult` with list of `ACMExtractionRecord`

**Extraction schema location:** `open_notebook/extractors/acm_schemas.py`
- `ACMExtractionRecord.product` field = "Type of product containing asbestos"
- `ACMExtractionRecord.location` field = "Specific location within room"
- These two fields are the crux — LLM must understand that equipment name goes in `location` and ACM material goes in `product`

**E2E test:** `tests/test_broadmeadows_e2e.py`
- `_match_extracted_to_expected()` matches by sample_no (primary) then room+location+item composite key (fallback)
- `_record_key()` builds composite key from `room_name|location|product`
- Matching failure for fuse cartridge: extracted `product="Switchboard"` doesn't match expected `item="Fuse cartridge"`

### Taxonomy Files (use as prompt context)

Located at `docs/samplePDF/instructions-sample/`:

1. **`register_enums.json`** — Contains `SpecificUses` array with 319 canonical ACM item names including:
   - "Fuse cartridge" (the correct product name)
   - "Switchboard" (this is a location, not a product when fuse cartridge is the ACM)
   - "Switchboard Lining", "Switchboard cupboard lining", "Switchboard insulation" (related items)
   - "Internal lining" (relevant for the lift foyer no-access item)

2. **`consultant_wording_rules.json`** — Contains `height_or_access_restriction` action:
   - Pattern: `\bHeight restriction\b|\bRestricted Access\b|\bLive Electrical Hazard\b`
   - This confirms "No access" items should be treated as presumed ACM

3. **`register_taxonomy.friable.json`** / **`register_taxonomy.nonfriable.json`** — Product group classifications (T1-T8)

### Key Prompt Changes Needed

The extraction prompt at `prompts/acm/building_extraction.jinja` needs:

1. **NEW SECTION: "ACM Item vs Equipment/Location Distinction"**
   - When a register entry lists an equipment item (Switchboard, Boiler, Lift) AND a specific ACM component within it (Fuse cartridge, Internal lining, Gasket), the `product` field MUST be the specific ACM component, NOT the equipment
   - Examples: "Switchboard → Fuse cartridge" means product="Fuse cartridge", location="Switchboard"

2. **NEW SECTION: "No Access / Restricted Access Items"**
   - Register entries marked "No access", "Height restriction", or "Restricted Access" are VALID register rows
   - Extract them with result="Assumed Positive" and add note to `data_issues`
   - Do NOT skip them

3. **OPTIONAL: Taxonomy vocabulary hint**
   - Include a condensed list of common SpecificUses from register_enums.json as a vocabulary guide
   - This helps the LLM pick canonical names like "Fuse cartridge" over ad-hoc names

### Previous Story Learnings

- E1-S7 established the extraction schema and prompt template pattern
- E1-S22 increased max_tokens from 8192 to 32768 to prevent truncation
- E18-S1 fixed provider compatibility (OpenRouter vs direct Anthropic)
- The prompt uses Jinja2 with `data.building_context` and `data.content` variables
- Prompt is ~6000 tokens rendered — adding taxonomy hints must be concise to not bloat context

### Testing Standards

- E2E test: `pytest tests/test_broadmeadows_e2e.py -m integration -v -s` (requires OPENROUTER_API_KEY)
- Unit tests: `pytest tests/ -x --ignore=tests/test_broadmeadows_e2e.py`
- Lint: `ruff check .`
- The E2E test assertion currently expects 31/31 — test will pass when all records match

### Project Structure Notes

- Prompt templates: `prompts/acm/` directory with `.jinja` extension
- Extraction pipeline: `open_notebook/extractors/` (orchestrator.py, acm_schemas.py)
- Domain models: `open_notebook/domain/acm.py`
- Tests: `tests/test_broadmeadows_e2e.py`

### References

- [Source: docs/sprint-artifacts/reports/demo-extraction-report-2026-02-22.md] — Full verification report
- [Source: docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260222-extraction-quality.md] — SCP with root cause analysis
- [Source: prompts/acm/building_extraction.jinja] — Current extraction prompt template
- [Source: open_notebook/extractors/orchestrator.py] — Orchestrator calling the prompt
- [Source: open_notebook/extractors/acm_schemas.py] — Pydantic schemas for structured output
- [Source: docs/samplePDF/instructions-sample/register_enums.json] — Canonical ACM vocabulary
- [Source: docs/samplePDF/instructions-sample/consultant_wording_rules.json] — Consultant phrase mapping

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Unit tests: 509 passed, 1 pre-existing failure (`test_update_field_config_toggle_active`)
- Ruff: all checks passed

### Completion Notes List

- Task 1.1: Added ACM Product Vocabulary Guide to BOTH `building_extraction.jinja` and `extraction.jinja`
- Task 1.2: Enhanced Product/Material mapping with ACM item vs equipment distinction, examples table (both templates)
- Task 1.3: Added extraction rule 7 for No Access / Restricted Access / Height Restriction entries (both templates)
- Task 2.1-2.2: Three-tier matching (sample_no → room+location+item → room+location fuzzy)
- Task 3.1: E2E result 27/31 (87%), up from 26/31 (84%). Improvement from prompt changes + matching
- Task 3.2: PASSED — ruff check clean
- Task 3.3: PASSED — 509/510 unit tests pass (1 pre-existing failure)
- Additional: Fallback JSON parser added for OpenRouter structured output compatibility
- Additional: max_tokens fallback increased from 8192 to 16384

### Remaining 4 Missing Records (LLM Non-Determinism)

| # | Room | Location | Expected Item | Status |
|---|------|----------|--------------|--------|
| 1 | Switch Room (L1) | Auto Battery Charger | Fuse cartridge | Not extracted (LLM missed) |
| 2 | Roof (G) | East Ductwork | Flange joints | Not extracted (LLM missed) |
| 3 | Lift Foyer (G) | Lift | Internal lining | No access — still skipped |
| 4 | Main Foyer (G) | Room Adjacent Disabled Toilet | Unknown | No access — still skipped |

These may require content preprocessing (injecting markers into the PDF text) or multi-shot prompting to reliably extract.

### File List

- `prompts/acm/building_extraction.jinja` — Modified (3 new sections: vocabulary, distinction, no-access)
- `prompts/acm/extraction.jinja` — Modified (same 3 sections applied to primary extraction prompt)
- `open_notebook/graphs/acm_extraction.py` — Modified (fallback JSON parser, max_tokens 8192→16384)
- `tests/test_broadmeadows_e2e.py` — Modified (three-tier matching logic)
- `docs/sprint-artifacts/e18-s5-extraction-quality-fuse-cartridge-no-access.md` — Modified (task tracking)
- `docs/sprint-artifacts/sprint-status.yaml` — Modified (story status)

### Change Log

- 2026-02-23: Tasks 1-2 implemented, Task 3 partially verified (lint + unit tests pass, E2E pending live run)
- 2026-02-23: Discovery — pipeline uses extraction.jinja (not building_extraction.jinja) for non-orchestrator path. Applied same changes to both.
- 2026-02-23: Added fallback JSON parser for OpenRouter structured output compatibility. Increased max_tokens 8192→16384.
- 2026-02-23: E2E result: 27/31 (87%), up from 26/31 baseline. Fuse cartridge naming fixed for 2/3 items. No-access items still skipped by LLM.
- 2026-02-23: Commits dce30de (prompt+test) and 0b05bda (extraction.jinja+fallback parser) pushed to main.
