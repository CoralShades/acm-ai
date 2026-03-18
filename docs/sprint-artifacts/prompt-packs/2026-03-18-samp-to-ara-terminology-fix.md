# Session: SAMP→ARA Terminology Fix — Rename incorrect "SAMP" terminology across entire codebase

## Critical Context

**All documents processed by this pipeline are ARA (Asbestos Register Assessment) documents.** The term "SAMP" (School Asbestos Management Plan) was used loosely during early development and propagated everywhere. The real distinction is between **consultant table formats** (Clutha/Broadmeadows format vs Alexander format vs other consultants), NOT between document types.

### The Correct Mental Model
```
WRONG:  "SAMP document" vs "ARA document" (two document types)
RIGHT:  All documents are ARA reports. Different consultants format the same ARA data differently.
         - Clutha/Broadmeadows consultant → specific table layout, B-series building codes
         - Alexander consultant → different headers, D-series codes
         - Other consultants → unknown layouts (Area 3 addresses this)
```

## Skills to Load

/planning-with-files — persistent markdown plan
/find-bugs — systematic discovery of misnamed references
/systematic-debugging — structured approach to cross-cutting rename
/verification-before-completion — verify rename completeness

---

## Prerequisites

- Branch: `git checkout ACMV3`
- All services can be stopped during this rename (code-only changes)
- Run after: `npm run build` baseline to verify no pre-existing build errors
- Run after: `uv run pytest tests/ -x` baseline to verify no pre-existing test failures

---

## Project Glossary

| Term | Definition |
|------|-----------|
| ARA | Asbestos Register Assessment — the CORRECT term for ALL documents processed by this pipeline |
| SAMP | School Asbestos Management Plan — INCORRECT term, being removed. Was used loosely to mean "the source PDF" |
| Consultant format | The specific table layout, column naming, and header patterns used by a particular consulting firm |
| Clutha format | The table format used by the Clutha/Broadmeadows consultant (B-series building codes, specific room headers) |
| Alexander format | The table format used by the Alexander District Hospital consultant (D-series codes, different section headers) |
| `_SAMP_BUILDING_ID` | Regex in orchestrator.py that gates extraction strategy. Should be renamed to a format-neutral name |
| `SCHOOL_PATTERN` | Regex in acm_extractor.py matching school/site names. Name is misleading but regex itself is format-neutral |
| `DocumentType` | Enum with `SAMP`, `ARA`, `Division_5`, `Unknown`. The `SAMP` value should be removed or renamed |

---

## Rename Rules

### What to rename
1. **"SAMP" → "ARA"** in all UI labels, user-facing strings, and documentation
2. **"SAMP document" → "ARA document"** in descriptions and comments
3. **"School Asbestos Management Plan" → "Asbestos Register Assessment"** everywhere
4. **Variable/function names** containing "SAMP" (e.g., `uploadSAMP` → `uploadARA`, `SAMP_FIXTURES_DIR` → `ARA_FIXTURES_DIR`)
5. **`DocumentType.SAMP`** → remove or rename to represent the actual concept
6. **`_SAMP_BUILDING_ID`** → `_STANDARD_BUILDING_ID` or `_CLUTHA_BUILDING_ID`
7. **`SCHOOL_PATTERN`** → `SITE_NAME_PATTERN` (the regex itself is format-neutral)
8. **Directory names**: `tests/e2e/fixtures/samps/` → `tests/e2e/fixtures/ara-documents/`

### What NOT to rename
- `sample_no`, `sample_result`, `nata_sample_number` — these are asbestos SAMPLE fields, not "SAMP"
- Historical commit messages and sprint-status.yaml entries — these are historical record
- V3/output/*.md files — these are historical research artifacts (mark as outdated instead)
- `DocumentType.SAMP` enum VALUE in `document_structure.py` — **KEEP the enum value as `"SAMP"`** for now. Renaming it requires a DB migration (the string is stored in `source_intelligence.document_type`). The enum can stay; just expand the description in prompts to "Site/School Asbestos Management Plan". A future migration can rename the DB values if desired.
- `prompts/acm/building_inventory.jinja` line 25 "NSW DoE SAMP Format" — this is correctly scoped to a specific format variant

### Rename with care
- `acm_extractor.py:SCHOOL_PATTERN` — the regex matches `ACM|SAMP` in headers. Update the regex to also match `ARA` and rename to `SITE_NAME_PATTERN`
- `document-detection.ts:ACM_PATTERNS` — the regex `/\bsamp\b/i` should become `/\bara\b/i` BUT keep `samp` as a secondary pattern since some uploaded files may still be named with "SAMP"
- `DocumentType` enum — if backend and frontend must stay in sync, change both simultaneously

---

## Files to Modify (by priority)

### P0: LLM Prompts (affects extraction quality — HIGHEST PRIORITY)

**CRITICAL FINDING:** `structure_extraction.jinja` line 16 has a classification heuristic that ONLY matches "School Asbestos Management Plan" — any SAMP from a hospital/police station/council without the word "School" gets classified as `Unknown`, which breaks `register_start_page` detection and degrades extraction.

- `prompts/acm/structure_extraction.jinja` — **CRITICAL**: 8 SAMP refs. Line 16 heuristic too narrow ("School Asbestos"). Line 85 page 13+ assumption school-specific. Broaden to "Site/School Asbestos Management Plan"
- `prompts/acm/metadata_extraction.jinja` — 3 refs. Line 50 "Generic SAMP Format" → "Generic / Other Format". Line 3 system prompt OK but expand "School" to "Site/School"
- `prompts/acm/metadata_and_structure.jinja` — 2 refs. Line 24 schema instruction says "school asbestos" — broaden
- `prompts/acm/page_tagging.jinja` — 1 ref. Line 3 system prompt — expand "School" to "Site/School"
- `prompts/acm/building_inventory.jinja` — 1 ref. Line 25 "NSW DoE SAMP Format" — this one is OK (correctly scoped to a specific format)
- `prompts/acm/v3_building_extraction.jinja` — 2 refs. Lines 103-107 worked example labeled "SAMP Format" with school example. Add non-school example
- `prompts/acm/legacy/extraction.jinja` — 8 refs. "FORMAT A: SAMP Format (School Asbestos Management Plans)" → "FORMAT A: DET Format (coded building IDs)"
- `prompts/acm/legacy/building_extraction.jinja` — 2 refs. Same FORMAT A rename
- `prompts/source_chat.jinja` — 5 refs. Chat told to "reference SAMP sections" for ALL docs → hallucinated references for ARA docs. Replace with generic "the site's management plan"
- `prompts/acm_analyst.jinja` — 1 ref. Line 4 user-facing system prompt says "SAMP" only

### P0: Pipeline Logic (affects extraction strategy)

**NEW FINDINGS:** `samp_detector.py` is an entire module named after SAMP. `llm_detector.py` line 55 tells the LLM to output `"samp"` as a format label.

- `open_notebook/extractors/format_detectors/samp_detector.py` — **ENTIRE FILE**: class `SAMPDetector`, `name="samp"` (registry key). Rename to `standard_detector.py` / `StandardFormatDetector`
- `open_notebook/extractors/format_detectors/__init__.py` — import + registration of SAMPDetector
- `open_notebook/extractors/format_detectors/llm_detector.py` — line 55: LLM prompt outputs `"samp"` as format label → must match new detector name
- `open_notebook/extractors/orchestrator.py` — rename `_SAMP_BUILDING_ID` → `_STANDARD_BUILDING_ID`
- `open_notebook/extractors/acm_extractor.py` — rename `SCHOOL_PATTERN` → `SITE_NAME_PATTERN`, add `ARA` to regex alternation
- `open_notebook/extractors/document_structure.py` — `DocumentType.SAMP` enum value (DB migration needed if renaming)
- `open_notebook/extractors/building_inventory.py` — 4 SAMP comments in extraction logic
- `open_notebook/graphs/acm_extraction.py` — comments about "SAMP-specific" logic
- `open_notebook/extractors/row_segmenter.py` — 2 "NSW DoE SAMP" column alias comments
- `open_notebook/domain/acm.py` — docstrings on ACMRecord and BuildingRecord
- `open_notebook/domain/acm_row_mappers.py` — docstring says "SAMP documents"
- `open_notebook/extractors/metadata_extractor.py` — module docstring
- `open_notebook/graphs/utils.py` — 4 comments about "SAMP docs"

### P1: Frontend UI (user-visible)
- `frontend/src/app/landing/page.tsx` — hero text + quick-start
- `frontend/src/components/upload/ProcessingOptionsStep.tsx` — card description
- `frontend/src/components/sources/steps/ProcessingStep.tsx` — 2 strings
- `frontend/src/components/documents/DocumentLibrary.tsx` — empty state + onboarding
- `frontend/src/components/acm/ExtractionProgress.tsx` — progress text
- `frontend/src/app/(dashboard)/settings/extraction/page.tsx` — settings description
- `frontend/src/components/settings/ExtractionSettingsForm.tsx` — radio description
- `frontend/src/lib/utils/document-detection.ts` — label + regex + comments
- `frontend/src/lib/types/intelligence.ts` — `DocumentType` union type
- `frontend/src/components/acm/SourceIntelligencePanel.tsx` — color map
- `frontend/src/config/branding.ts` — SEO keywords

### P2: E2E Tests + Helpers (many files)
- `tests/e2e/helpers/acm-helpers.ts` — rename `uploadSAMP` → `uploadARA`
- `tests/e2e/helpers/index.ts` — re-export
- `tests/e2e/acm-extraction.spec.ts` — ~40 SAMP references
- `tests/e2e/user-journeys.spec.ts` — ~30 SAMP references
- `tests/e2e/smart-chat.spec.ts` — ~10 SAMP references
- `tests/e2e/specs/jobs-pipeline.spec.ts` — test fixture name
- `tests/e2e/fixtures/samps/` → rename directory to `ara-documents/`
- `tests/e2e/fixtures/samps/README.md` — complete rewrite
- `tests/e2e/fixtures/samps/broadmeadows-expected-results.json` — source field

### P2: Python Tests
- `tests/test_acm_chat_context.py` — 4 "Test SAMP Document" fixtures
- `tests/test_acm_extractor_integration.py` — "SAMP Register" test fixture
- `scripts/benchmark_ollama.py` — `fixtures/samps` path reference

### P3: Agent Definitions + CLAUDE.md
- `CLAUDE.md` — project overview says "SAMP documents", glossary entry
- `.claude/agents/acm-e2e-tester.md` — line 25 "SAMP, Risk Assessment"
- `.claude/agents/acm-extraction-pre.md` — lines 23, 25, 67 "SAMPs", "SAMP"
- `.claude/rules/langgraph-ai.md` — if any SAMP references
- `README.md` — 4 "SAMP" references

### P4: Documentation (LOW — historical)
- `docs/` — various SAMP references in sprint artifacts and reviews
- `V3/output/*.md` — historical research (add "NOTE: SAMP terminology deprecated" header)

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH (3 parallel agents)

### Agent 1: prompt-and-pipeline-rename (P0)
Rename SAMP in all LLM prompts and pipeline Python code. This is the highest priority because it directly affects extraction quality.

Files: prompts/acm/*.jinja, orchestrator.py, acm_extractor.py, acm_extraction.py, building_inventory.py, domain models
Constraints: Do NOT change regex behavior, only rename variables and update string literals. The `SCHOOL_PATTERN` regex should ALSO match `ARA` in addition to `ACM|SAMP`.

### Agent 2: frontend-rename (P1)
Rename SAMP in all frontend TypeScript/React code. User-visible changes.

Files: All 11 HIGH severity frontend files + types + branding
Constraints: Keep `samp` as a secondary detection regex in document-detection.ts for backward compatibility.

### Agent 3: test-and-docs-rename (P2-P4)
Rename SAMP in E2E tests, Python tests, agent definitions, CLAUDE.md, README.
This is the bulk rename — many files but low risk (tests and docs).

Files: tests/e2e/*.ts, tests/*.py, .claude/agents/*.md, CLAUDE.md, README.md
Constraints: Rename `tests/e2e/fixtures/samps/` directory to `tests/e2e/fixtures/ara-documents/`. Update all path references.

### Execution Order
All 3 agents can run in parallel — they touch non-overlapping files.
After all complete, run verification.

---

## Context7 Directives

No library documentation needed for this rename session.

---

## Verification Checklist

Run these in order after ALL rename agents complete:

- [ ] `grep -ri "SAMP" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.jinja" open_notebook/ api/ commands/ prompts/ frontend/src/ | grep -v sample | grep -v "sample_" | grep -v "nata_sample" | wc -l` — should be 0 (no remaining SAMP references except "sample" field names)
- [ ] `uv run ruff check .` — Python lint (0 errors)
- [ ] `uv run pytest tests/ -x` — Backend tests (all pass, with renamed fixtures)
- [ ] `cd frontend && npm run build` — Frontend build (0 errors)
- [ ] `cd frontend && npm run lint` — Frontend lint (0 errors)
- [ ] Verify `tests/e2e/fixtures/ara-documents/` exists and `tests/e2e/fixtures/samps/` is removed
- [ ] Verify `DocumentType` enum no longer contains `SAMP` (or contains both for migration period)
- [ ] Verify LLM prompts reference "ARA document" not "SAMP document"
- [ ] Verify landing page says "ARA documents" not "SAMP documents"
- [ ] `git diff --stat` — review total files changed, ensure no unexpected modifications

---

## Commit Template

```
refactor: rename SAMP→ARA terminology across entire codebase

All documents are ARA (Asbestos Register Assessment) reports. The term
"SAMP" (School Asbestos Management Plan) was incorrectly used as a
document type when the real distinction is between consultant table
formats (Clutha vs Alexander vs others).

- Rename SAMP→ARA in LLM prompts (affects extraction quality)
- Rename _SAMP_BUILDING_ID→_STANDARD_BUILDING_ID in orchestrator
- Rename SCHOOL_PATTERN→SITE_NAME_PATTERN, add ARA to regex
- Fix 11 user-visible UI strings (landing, upload, settings, progress)
- Update DocumentType enum (SAMP→ARA in both frontend and backend)
- Rename tests/e2e/fixtures/samps/ → ara-documents/
- Rename uploadSAMP()→uploadARA() in E2E helpers
- Update CLAUDE.md, README.md, agent definitions

Co-Authored-By: Claude <noreply@anthropic.com>
```
