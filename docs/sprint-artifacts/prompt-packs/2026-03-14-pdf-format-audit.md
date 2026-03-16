# Session: Audit PDF Processing Layer — PyMuPDF, Docling Outputs, and Format Detection Templates

## Skills to Load

/systematic-debugging — structured diagnosis before proposing fixes
/acm-observability — query traces, inspect graph state, debug extraction failures
/planning-with-files — persistent markdown plan for session continuity
/verification-before-completion — verify findings before claiming audit complete

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Branch: ACMV3
- Ground truth file exists: `D:/ailocal/acm-ai/benchmarks/ground_truth/broadmeadows.json`
- Sample PDF exists: `D:/ailocal/acm-ai/docs/samplePDF/Clutch_Broadmeadows.pdf`
- Docling installed: `uv run python -c "import docling; print(docling.__version__)"`
- PyMuPDF installed: `uv run python -c "import fitz; print(fitz.version)"`

---

## Project Glossary

Key terms for this session. Refer to these definitions when interpreting code or instructions.

| Term | Definition |
|------|-----------  |
| PyMuPDF (`fitz`) | PDF parser that extracts full text with `--- Page N ---` markers. First stage of PDF ingestion in `source_commands.py`. Output stored as `source.full_text`. |
| Docling | ML-based table extraction engine (TableFormer ACCURATE mode). Produces 3 output types: JSON (cell-level), HTML, and Markdown. Tables stored in `acm_table_section`. |
| `docling_document_json` | Lossless cell-level JSON from `table.data.model_dump(mode="json")`. Contains `text`, `row_span`, `col_span`, `start_row_offset_idx`, etc. Primary input for per-row extraction via `row_segmenter.py`. |
| SAMP | School Asbestos Management Plan — uses `## B00A - Name - Year - Construction` building headers with `#### B00A-R0001 - Room` room headers. Detected by `_BUILDING_HEADER` regex. |
| ARA | Asbestos Register Assessment — uses `Building Name:\n<name>` repeated header blocks. Used by Greencap, Prensa, etc. Detected by `_detect_ara_buildings()`. |
| BAR | Building Asbestos Register — **secondary format** that should NEVER impact pipeline flow or extraction outcome. Document type classification only. |
| BuildingRecord | Pydantic domain model for Salesforce Building__c object. One per building. Persisted to `building_record` table. |
| ACMRecord | Pydantic domain model for Salesforce Item__c object. One per ACM sample. Persisted to `acm_record` table. FK to `building_record`. |
| RawTableRow | Pydantic model in `row_segmenter.py` — one parsed row from a Docling JSON table. Contains `cells` dict (canonical_name → value), `column_mapping`, `raw_text`. |
| ACMItemRow | 9-field extraction schema in `acm_row_schemas.py`. Output of per-row LLM extraction. Mapped to `ACMExtractionRecord` by deterministic mapper. |
| `_BUILDING_HEADER` | Regex in `building_inventory.py` matching SAMP building headers: `^#+\s*(?:Building[:\s]*)?([A-Z]\d+[A-Z]?|D\d{2,3})\s+[-–]\s+...` |
| `_detect_ara_buildings` | Function in `building_inventory.py` that detects ARA-format buildings from `Building Name:\n<name>` header blocks. |
| DocumentStructure | Pydantic model carrying document_type, register_start_page, building_ids, total_pages. Extracted by `metadata_and_structure_node`. |
| Broadmeadows | Ground truth benchmark: 1 building ("Broadmeadows Police Station"), 31 ACM records, consultant "Prensa Pty Ltd". |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name`. |

---

## Current State

- Branch: ACMV3 (last commit: `feat(frontend): complete frontend audit`)
- Sprint: V3-8, 6 stories remaining (E35-S3..S8)
- Pipeline audit completed: 42 SurrealDB tables cataloged, 11 orphaned tables removed (migration 50)
- Per-row extraction (v3.5) is the current default path
- Docling Direct API extraction runs BEFORE the graph (in `source_commands.py`)
- `mode="json"` fix was applied in Bug Fix 11 (was `mode="python"` causing SurrealDB storage failures)
- MinerU 2.x in main venv, dual-provider optional (`MINERU_ENABLED`)

### Known Format Detection Concerns

1. SAMP regex `_BUILDING_HEADER` may not match all real PyMuPDF heading formats
2. ARA `_detect_ara_buildings` only looks for `Building Name:` — some consultants may use "Building:", "Property:", etc.
3. Generic fallback divides register evenly by building count — inaccurate when buildings have very different sizes
4. BAR document_type is detected but unclear if any code branches on it
5. Docling JSON cell keys must match exactly what `row_segmenter.py` expects — no schema validation exists

---

## Key Files

Files this session will read and audit. **This is a research/audit session — no code modifications unless explicitly approved by user.**

**Read (PyMuPDF audit):**
- `D:/ailocal/acm-ai/commands/source_commands.py` — `_extract_tables_with_docling()`, Docling config
- `D:/ailocal/acm-ai/open_notebook/graphs/acm_extraction.py` — `_extract_page_range_text()`, `_extract_building_content()`
- `D:/ailocal/acm-ai/open_notebook/extractors/document_structure.py` — `_PAGE_PATTERN`, page marker detection

**Read (Docling output audit — CRITICAL):**
- `D:/ailocal/acm-ai/commands/source_commands.py:81-178` — `_extract_tables_with_docling()` (all 3 output types)
- `D:/ailocal/acm-ai/open_notebook/extractors/row_segmenter.py` — Docling JSON parsing, `COLUMN_ALIASES`, cell expectations
- `D:/ailocal/acm-ai/open_notebook/extractors/providers/docling_adapter.py` — Docling provider adapter
- `D:/ailocal/acm-ai/open_notebook/extractors/orchestrator.py` — `_inject_docling_tables()` (markdown injection for LLM)

**Read (format detection audit):**
- `D:/ailocal/acm-ai/open_notebook/extractors/building_inventory.py` — `_BUILDING_HEADER`, `_detect_ara_buildings`, `_heuristic_fallback`
- `D:/ailocal/acm-ai/open_notebook/extractors/metadata_extractor.py` — cover page regex patterns
- `D:/ailocal/acm-ai/open_notebook/extractors/metadata_and_structure.py` — combined LLM extraction
- `D:/ailocal/acm-ai/open_notebook/extractors/document_structure.py` — DocumentType enum, structure detection

**Read (Salesforce model alignment):**
- `D:/ailocal/acm-ai/open_notebook/domain/acm.py` — BuildingRecord, ACMRecord field definitions
- `D:/ailocal/acm-ai/open_notebook/domain/acm_row_schemas.py` — ACMItemRow 9-field schema
- `D:/ailocal/acm-ai/open_notebook/domain/acm_row_mappers.py` — ACMItemRow → ACMExtractionRecord mapper

**Read (prompt templates):**
- `D:/ailocal/acm-ai/prompts/acm/metadata_and_structure.jinja` — metadata+structure prompt
- `D:/ailocal/acm-ai/prompts/acm/building_inventory.jinja` — building inventory prompt
- `D:/ailocal/acm-ai/prompts/acm/row_extraction.jinja` — per-row item extraction prompt
- `D:/ailocal/acm-ai/prompts/acm/v3_building_extraction.jinja` — building metadata prompt
- `D:/ailocal/acm-ai/prompts/acm/v3_item_extraction.jinja` — item extraction prompt

**Read (ground truth):**
- `D:/ailocal/acm-ai/benchmarks/ground_truth/broadmeadows.json` — expected output (1 building, 31 records)

**Write (output):**
- `D:/ailocal/acm-ai/docs/sprint-artifacts/pdf-format-audit/findings.md` — audit findings
- `D:/ailocal/acm-ai/docs/sprint-artifacts/pdf-format-audit/task_plan.md` — task plan
- `D:/ailocal/acm-ai/docs/sprint-artifacts/pdf-format-audit/progress.md` — progress tracker

---

## Plan

Read `docs/sprint-artifacts/pdf-format-audit/task_plan.md` before starting. Update it as you work.

### Task Plan Reference

- task_plan.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/pdf-format-audit/task_plan.md`
- findings.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/pdf-format-audit/findings.md`
- progress.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/pdf-format-audit/progress.md`

### Execution Strategy

**Phase 1 — PyMuPDF Output Audit**

Step 1: Read `source_commands.py` to understand how PyMuPDF extracts text and inserts page markers.
Step 2: Read `_extract_page_range_text()` and `_extract_building_content()` in `acm_extraction.py` — verify the page marker regex matches what PyMuPDF produces.
Step 3: Read `_PAGE_PATTERN` in `document_structure.py` — does it handle all page marker variants?
Step 4: Test with Broadmeadows PDF — does PyMuPDF produce reliable markers for all pages?

**Phase 2 — Docling Output Audit (CRITICAL)**

Step 5: Read `_extract_tables_with_docling()` — trace how each output type (JSON, HTML, Markdown) is produced.
Step 6: Read `row_segmenter.py` lines 1-100 — document the EXACT cell keys it expects from Docling JSON.
Step 7: Verify `table.data.model_dump(mode="json")` produces keys matching row_segmenter expectations.
Step 8: Check `mode="json"` vs `mode="python"` — grep ALL call sites in the codebase.
Step 9: Read `docling_adapter.py` — how does the provider adapter produce its output?
Step 10: Read `_inject_docling_tables()` in `orchestrator.py` — is the markdown injection correct for LLM consumption?
Step 11: Cross-check: load a real Docling output and verify JSON/HTML/Markdown agree on row and column counts.

**Phase 3 — Format Detection Template Audit**

Step 12: Read `_BUILDING_HEADER` regex in `building_inventory.py` — list all capture groups and test against sample headers.
Step 13: Read `_detect_ara_buildings()` — does it catch all Greencap/Prensa header variants?
Step 14: Read `_heuristic_fallback()` — trace the full fallback chain (SAMP → ARA → generic → single-building).
Step 15: Read `DocumentType` enum in `document_structure.py` — is BAR defined? Where is it referenced?
Step 16: Grep for all `DocumentType.BAR` or `"BAR"` or `"bar"` references in Python code and Jinja templates.
Step 17: Verify BAR never gates extraction logic — it should only affect display/classification, not data flow.

**Phase 4 — Salesforce Model Alignment**

Step 18: Read `BuildingRecord` and `ACMRecord` in `domain/acm.py` — list all fields.
Step 19: Read `ACMItemRow` in `acm_row_schemas.py` — list all 9 fields.
Step 20: Verify format detection output (building_id, building_name, page_range) maps correctly to BuildingRecord fields.
Step 21: Verify row extraction output maps correctly to ACMRecord fields via `acm_row_mappers.py`.

**Phase 5 — Ground Truth Comparison**

Step 22: Read `benchmarks/ground_truth/broadmeadows.json` — document expected output.
Step 23: Check if Broadmeadows PDF is ARA format (Prensa consultant) — does `_detect_ara_buildings` match it?
Step 24: Verify the pipeline would produce exactly 1 building and 31 records for Broadmeadows.

**Phase 6 — Synthesis**

Step 25: Compile all findings into `findings.md` with specific `file:line` references.
Step 26: Prioritize recommendations: CRITICAL (data loss), HIGH (incorrect output), MEDIUM (robustness), LOW (cosmetic).
Step 27: Present findings to user before any code changes.

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH
Use the Task tool to dispatch independent audit streams in parallel.
**All subagents should use `model: "sonnet"` for team-based work.**

### Phase 1+2 Subagents (launch in parallel)

**Subagent 1: pymupdf-auditor**
- Model: sonnet
- Task: Read `source_commands.py`, `acm_extraction.py` (`_extract_page_range_text`, `_extract_building_content`), and `document_structure.py` (`_PAGE_PATTERN`). Audit PyMuPDF page marker format, verify regex patterns match, identify edge cases. Return structured findings.
- Skills: /systematic-debugging

**Subagent 2: docling-output-auditor**
- Model: sonnet
- Task: Read `source_commands.py:81-178` (`_extract_tables_with_docling`), `row_segmenter.py` (cell key expectations), `docling_adapter.py`, and `orchestrator.py` (`_inject_docling_tables`). Audit ALL three output types (JSON, HTML, Markdown). Verify `mode="json"` usage everywhere. Grep for all `model_dump` calls on Docling objects. Cross-check output consistency. Return structured findings.
- Skills: /systematic-debugging

**Subagent 3: format-detection-auditor**
- Model: sonnet
- Task: Read `building_inventory.py` (`_BUILDING_HEADER`, `_detect_ara_buildings`, `_heuristic_fallback`), `document_structure.py` (`DocumentType`), and all Jinja templates in `prompts/acm/`. Audit format detection patterns, trace BAR references, verify alignment with BuildingRecord/ACMRecord models. Read `broadmeadows.json` ground truth. Return structured findings.
- Skills: /systematic-debugging

### Phase 3 (after all subagents complete)

Synthesize all 3 subagent outputs. Compile into `findings.md`. Present prioritized recommendations to user.

**CRITICAL RULE: This is a research/audit session. DO NOT modify any code files. Only write to `docs/sprint-artifacts/pdf-format-audit/`.**

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "docling" → query-docs for "DocumentConverter TableFormerMode export_to_dataframe model_dump"
2. resolve-library-id for "pymupdf" → query-docs for "page text extraction markdown output"
3. resolve-library-id for "pydantic" → query-docs for "model_dump mode json python"

---

## Verification Checklist

Run these checks before marking the audit complete. All must pass.

- [ ] PyMuPDF page markers analyzed — all variants documented, regex compatibility verified
- [ ] Docling JSON cell keys documented — exact key names vs row_segmenter expectations mapped
- [ ] Docling HTML output quality assessed — merged cell handling verified
- [ ] Docling Markdown output accuracy assessed — column alignment verified
- [ ] All `model_dump()` call sites found — mode="json" confirmed everywhere (no mode="python")
- [ ] `_BUILDING_HEADER` regex tested against ≥3 sample headers — match/miss documented
- [ ] `_detect_ara_buildings` tested against Broadmeadows PDF format — match confirmed
- [ ] Generic fallback page range logic audited — single-building handling verified
- [ ] BAR format impact traced — confirmed no pipeline branching on BAR document_type
- [ ] BuildingRecord fields aligned with format detection output
- [ ] ACMRecord fields aligned with extraction output via mapper
- [ ] Ground truth comparison: Broadmeadows = 1 building, 31 records expected
- [ ] All findings documented in `findings.md` with `file:line` references
- [ ] No code files modified (research-only session)

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| READ | ~20 | source_commands.py, acm_extraction.py, document_structure.py, row_segmenter.py, docling_adapter.py, orchestrator.py, building_inventory.py, metadata_extractor.py, metadata_and_structure.py, acm.py, acm_row_schemas.py, acm_row_mappers.py, prompts/acm/*.jinja, broadmeadows.json |
| MODIFY | 0 | — (research-only session) |
| NEW | 3 | pdf-format-audit/task_plan.md, findings.md, progress.md |
| DELETE | 0 | — |

---

## Commit Template

When audit is complete, use this commit message structure:

```
docs(audit): PDF processing layer & format detection audit — PyMuPDF, Docling, SAMP/ARA/BAR

Audit all three Docling output types (JSON/HTML/Markdown), PyMuPDF page markers,
and format detection templates. Verify BAR format is secondary with no pipeline
impact. Validated against Broadmeadows ground truth (1 building, 31 records).

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## Critical Rules

1. **RESEARCH ONLY** — do NOT modify any code files. All output goes to `docs/sprint-artifacts/pdf-format-audit/`
2. **Diagnose BEFORE recommending** — follow /systematic-debugging strictly. No guessing.
3. **BAR must be secondary** — verify it NEVER gates extraction logic, NEVER changes pipeline flow, NEVER impacts output
4. **Docling JSON is CRITICAL** — this is the primary data source for per-row extraction. Cell key mismatches = silent data loss
5. **`mode="json"` everywhere** — `mode="python"` returns non-serializable enums. Any remaining `mode="python"` call is a bug.
6. **Ground truth comparison** — every finding must be contextualized against Broadmeadows expected output (1 building, 31 records)
7. **File:line references** — all findings must cite specific `file_path:line_number` locations
8. **Present before acting** — all recommendations must be presented to user before any code changes are proposed

---

## Pipeline Debug Session Findings (2026-03-14)

### Session Summary

Commit: `476c285e`
Branch: ACMV3
Model used during session: phi4:14b-q4_K_M (misconfigured — see RC9 below)
Result: 0 → 29 records (93.5% of 31 ground truth)
Building detected: 1 ("Broadmeadows Police Station") — correct
Mode: Bulk extraction (per-row never triggered — see RC8 below)

---

### Fixes Applied in This Session (8 total)

| # | File | Change | Status |
|---|------|--------|--------|
| F1 | `open_notebook/extractors/metadata_and_structure.py` | Added `format="json"` to ChatOllama instantiation — Ollama was returning prose instead of JSON | Applied |
| F2 | `open_notebook/extractors/building_inventory.py` | Added `format="json"` to ChatOllama instantiation — same root cause as F1 | Applied |
| F3 | `prompts/acm/metadata_and_structure.jinja` | Rewrote prompt: 141 → 56 lines — too long for Ollama 8b context window | Applied |
| F4 | `prompts/acm/building_inventory.jinja` | Rewrote prompt: 130 → 58 lines — too long for Ollama 8b context window | Applied |
| F5 | `prompts/acm/row_split.jinja` | Extended prompt: 3 → 15 lines — added explicit JSON schema examples | Applied |
| F6 | `commands/acm_commands.py` | Stale `docling_document_json` detection: `IS NULL` → `IS NULL OR = {}` in SurrealQL stale-table check | Applied |
| F7 | `open_notebook/graphs/acm_extraction.py` | Same stale detection fix (`IS NULL OR = {}`) in graph node that checks for stale tables | Applied |
| F8 | `open_notebook/extractors/orchestrator.py` | Added `ensure_record_id()` for SurrealDB param binding in stale table check + WebSocket retry for `_get_docling_tables()` timeout | Applied |

---

### Remaining Issues (FOCUS for Next Session)

#### RC8 (MEDIUM-HIGH): `docling_document_json` Stored as Empty Dict `{}`

**Symptom:**
- 8 `acm_table_section` rows in SurrealDB have `raw_text` populated (895–17,519 chars each) but `docling_document_json = {}`
- This is NOT the old `mode="python"` bug — that was fixed in Bug Fix 11
- The stale detection fix (F6/F7) now correctly identifies empty dicts and triggers re-extraction, but newly created tables ALSO have empty `docling_document_json`

**Impact:**
- Per-row extraction is completely blocked — `extract_items_node` at `acm_extraction.py:1034` checks `if dj:` and empty dict `{}` is falsy
- Forces bulk fallback → fewer records extracted (29 vs 31)
- Re-extraction loop runs endlessly: detects stale → re-runs Docling → stores empty dict again → detects stale again

**Root Cause Hypotheses (in order of likelihood):**
1. `docling_adapter.py:151` — `table.data.model_dump(mode="json")` may return valid data, but `repo_create` in the database layer drops/truncates it silently
2. Docling `TableData` object has an empty `data` attribute despite the DataFrame being populated (upstream Docling parsing issue)
3. The SurrealDB `CONTENT` clause in the INSERT for `acm_table_section` does not include `docling_document_json` correctly

**Investigation Steps (next session):**
```python
# Step 1: Add debug logging to docling_adapter.py BEFORE the repo_create call
# File: open_notebook/extractors/providers/docling_adapter.py ~line 151
dump = table.data.model_dump(mode="json")
logger.debug("docling_adapter model_dump result: keys=%s, cells_count=%d",
             list(dump.keys()), len(dump.get("grid", [])))
# Expected: keys=['grid', 'num_rows', 'num_cols', ...], cells_count > 0
# If cells_count == 0 → Docling TableData is empty → upstream parse failure
# If keys is empty → model_dump() itself is returning {} → Pydantic schema mismatch
```

```python
# Step 2: Verify repo_create stores the field
# File: open_notebook/database/repositories/acm_table_section_repository.py
# Grep for the INSERT / CREATE query — check if docling_document_json is in the CONTENT dict
# Run: uv run python -c "
# from open_notebook.database.repositories.acm_table_section_repository import ACMTableSectionRepository
# import asyncio; r = ACMTableSectionRepository()
# # inspect the create() method signature and SQL template
# import inspect; print(inspect.getsource(r.create))
# "
```

```surql
-- Step 3: Query SurrealDB directly to compare raw_text vs docling_document_json presence
SELECT id, string::len(raw_text) AS raw_len, docling_document_json, table_index
FROM acm_table_section
WHERE source_id = 'source:<YOUR_ID>'
ORDER BY table_index;
-- If raw_len > 0 but docling_document_json = {} → data is lost at storage layer
-- If raw_len > 0 and docling_document_json is populated → truthy check issue
```

```python
# Step 4: Test model_dump() on a real Docling table in isolation
# Run: uv run python scripts/debug_docling_dump.py  (create this script)
# Script should: load Broadmeadows PDF, run Docling, inspect table.data.model_dump(mode="json")
# Expected fields per CLAUDE.md: text, row_span, col_span, start_row_offset_idx,
#   end_row_offset_idx, start_col_offset_idx, end_col_offset_idx, column_header, row_header
```

**Files to Read:**
- `open_notebook/extractors/providers/docling_adapter.py` (lines 140–165)
- `open_notebook/database/repositories/acm_table_section_repository.py` (CREATE/INSERT logic)
- `open_notebook/graphs/acm_extraction.py` (line 1034 — the `if dj:` truthy check)
- `commands/acm_commands.py` — re-extraction trigger logic

---

#### RC9 (MEDIUM): Model Selection Mismatch

**Symptom:**
- `.env` sets `DEFAULT_EXTRACTION_MODEL=ollama/qwen2.5:7b`
- Worker logs show phi4:14b-q4_K_M being used instead
- `phi4` produces unreliable structured JSON for metadata stage (see RC10)

**Root Cause (confirmed from CLAUDE.md memory):**
- `open_notebook:default_models` in SurrealDB stores a SurrealDB record ID (`model:t58qz9neoqg8x35hoyqs`) as the default, NOT a model name string
- `_get_db_extraction_model()` in `open_notebook/graphs/utils.py` resolves `model:xxx` IDs via direct record reference — it correctly resolves the ID, but it points to phi4, not qwen2.5
- The SurrealDB default was set at some earlier point to phi4 and persists across restarts
- `update_defaults_if_needed()` in `api/model_provisioning.py` only fills **empty** fields — it does not overwrite an existing phi4 default with the env var value

**Impact:**
- Metadata extraction fails with phi4 (fields return None)
- JSON format enforcement (`format="json"`) may not be sufficient for phi4's structured output
- Operator intent (qwen2.5:7b) is silently ignored

**Investigation Steps (next session):**
```surql
-- Step 1: Find what model is currently stored as the default
SELECT default_extraction_model FROM open_notebook:default_models;
-- Result will be a record ID like model:t58qz9neoqg8x35hoyqs

-- Step 2: Resolve that ID to a name
SELECT id, name, provider FROM model WHERE id = model:t58qz9neoqg8x35hoyqs;
-- Expected: { name: "phi4:14b-q4_K_M", provider: "ollama" }

-- Step 3: Find which model corresponds to qwen2.5:7b
SELECT id, name FROM model WHERE name ~ "qwen2.5" OR name ~ "qwen";
```

```python
# Step 4: Audit update_defaults_if_needed() logic
# File: api/model_provisioning.py ~line 213
# Is there a way to FORCE overwrite the default from env var?
# Consider: if ACM_EXTRACTION_MODEL env var is set, always overwrite (not just fill empty)
```

**Proposed Fix (for next session to implement after user approval):**
- Add logic to `update_defaults_if_needed()`: if `ACM_EXTRACTION_MODEL` or `DEFAULT_EXTRACTION_MODEL` env var is set, overwrite the DB default (not just fill-if-empty)
- Alternative: Add a `/api/models/reset-defaults` endpoint or admin command to clear the SurrealDB default

**Files to Read:**
- `api/model_provisioning.py` (`update_defaults_if_needed()`, `find_or_create_model()`)
- `open_notebook/graphs/utils.py` (`_get_db_extraction_model()`)
- `migrations/` — check if any migration seeds the default_models record

---

#### RC10 (MEDIUM): phi4 Metadata Extraction Failure

**Symptom (from worker logs):**
```
[14:18:25.680] MetadataAndStructureLLM validation errors: total_pages=None, page_start=None
[14:18:25.697] Using heuristic fallback: consultant=Unknown, type=UNKNOWN, buildings=0
```

**Root Cause:**
- phi4:14b cannot reliably populate all fields in `DocumentStructure` even with shorter prompts (F3/F4 applied)
- `total_pages=None` and `page_start=None` suggest phi4 skips optional-looking fields
- Prompt shortening (141→56 lines) helped but didn't fully solve phi4's structured output weakness

**Impact:**
- `consultant=Unknown` means Prensa is not identified — the document type (ARA) may not be correctly classified
- `buildings=0` from metadata stage means the building inventory phase must work from scratch
- Despite this, building inventory compiled correctly (1 building found via LLM)

**Investigation Steps (next session):**
- Compare phi4 vs llama3.1:8b vs qwen2.5:7b on the metadata prompt with `format="json"`
- Check if `total_pages` and `page_start` are marked `Optional` in the Pydantic schema — phi4 may be omitting them because they appear optional
- Consider making fields non-optional or adding sentinel defaults

**Files to Read:**
- `open_notebook/extractors/metadata_and_structure.py` — Pydantic schema for LLM output
- `prompts/acm/metadata_and_structure.jinja` — current shorter prompt (post-F3)

---

#### RC11 (LOW): Missing 2 Records from Ground Truth (29/31)

**Symptom:**
- Ground truth: 31 records
- Extracted: 29 records (bulk mode)
- Worker log shows 24 records before dedup, 2 exact deduped → 22 unique from bulk extraction

**Root Cause Hypotheses:**
1. Chunk boundary splitting — long register content split at row boundaries, losing rows that straddle chunks
2. "As Per" cross-reference rows — records like "As per room above" may be skipped by LLM
3. Near-duplicate room names (e.g., "Fan Room" vs "Level 1, fan room") — dedup misses near-duplicates
4. Records only accessible in per-row mode (Docling JSON with merged cells) — lost because per-row never triggers

**Worker Log Reference:**
```
[14:20:12.278] V3 Phase 2 [B001]: 12 records (first chunk)
[14:21:28.871] V3 Phase 2 [B001]: 12 records (second chunk) → 24 total, 2 deduped → 22
```
Note: The jump from 22 to 29 in the final count suggests later processing added 7 more records. Verify if a third chunk ran or if the correction pass added records.

**Investigation Steps (next session):**
- Fix RC8 first (restore per-row extraction) — this alone may recover the 2 missing records
- Add chunk boundary logging to identify which records are lost at which chunk edge
- Review near-duplicate detection threshold in `open_notebook/extractors/consensus/matcher.py`

---

### Worker Log Reference (Full Relevant Excerpt)

Copy this into `docs/sprint-artifacts/pdf-format-audit/findings.md` when starting next session:

```
[14:18:25.680] MetadataAndStructureLLM validation errors: total_pages=None, page_start=None
[14:18:25.697] Using heuristic fallback: consultant=Unknown, type=UNKNOWN, buildings=0
[14:18:44.758] Building inventory compiled: 1 buildings, 1 groups (via LLM, not heuristic)
[14:18:55.202] 11 acm_table_section rows have NULL docling_document_json — per-row falls back to bulk
[14:20:12.278] V3 Phase 2 [B001]: 12 records (first chunk)
[14:21:28.871] V3 Phase 2 [B001]: 12 records (second chunk) → 24 total, 2 deduped → 22
```

---

### Updated: Known Format Detection Concerns

(Appending to the list in the "Current State" section above)

6. **phi4 cannot reliably emit all required fields** — even with `format="json"` and a 56-line prompt. Fields marked `Optional` in the Pydantic schema are silently omitted. Consider making `total_pages` and all page range fields non-optional with explicit sentinel defaults (e.g., `-1` or `0`).
7. **`docling_document_json = {}` is now indistinguishable from a fresh empty row** — the stale detection fix (F6/F7) treats `= {}` the same as `IS NULL`. But if the re-extraction ALSO produces `{}`, the pipeline loops indefinitely. Add a re-extraction attempt counter or a `docling_extraction_attempted` boolean flag to `acm_table_section`.
8. **Model selection env var is silently ignored when a DB default exists** — `DEFAULT_EXTRACTION_MODEL` in `.env` has no effect if `open_notebook:default_models` already has a non-null `default_extraction_model` field pointing to a different model. This is a configuration observability gap.
9. **Bulk extraction produces duplicate room names with case/prefix variation** — "Fan Room" and "Level 1, fan room" are treated as distinct records. The dedup pass uses exact string matching; fuzzy matching is not applied at the bulk extraction level.

---

### Updated: Verification Checklist (Additions for Next Session)

Add these items to the checklist above before marking the next session complete:

- [ ] **RC8 resolved**: `docling_document_json` populated with valid cell data (not `{}`) after Docling extraction
- [ ] **RC8 verified**: `extract_items_node` enters per-row path (`if dj:` is truthy) for at least one table
- [ ] **RC9 resolved**: Model actually used matches `DEFAULT_EXTRACTION_MODEL` or `ACM_EXTRACTION_MODEL` env var
- [ ] **RC9 verified**: SurrealDB `open_notebook:default_models.default_extraction_model` resolves to correct model name
- [ ] **RC10 assessed**: phi4 metadata failure documented — either model swapped (RC9 fix) or Pydantic schema hardened
- [ ] **RC11 assessed**: Missing 2 records root-caused — chunk boundary vs per-row gap vs near-duplicate
- [ ] **Re-extraction loop check**: Confirm no infinite re-extraction loop (stale detection does not re-trigger after one successful re-extraction)
- [ ] **Per-row extraction confirmed triggered**: Worker log shows `per_row` path, not `bulk fallback`, for at least one run
- [ ] **Ground truth**: 31/31 records extracted OR gap documented with specific root cause per missing record

---

### Actionable Starting Point for Next Session

Run these commands in order at session start to establish ground state:

```bash
# 1. Confirm services are running
curl http://localhost:5055/health
docker ps | grep acm-ai-db

# 2. Check current model default in SurrealDB
# (Run via SurrealDB REST or ws client)
# SELECT default_extraction_model FROM open_notebook:default_models;
# Then: SELECT name FROM model WHERE id = <result>;

# 3. Check acm_table_section state for the last run
# SELECT id, string::len(raw_text) AS raw_len, docling_document_json, table_index
# FROM acm_table_section ORDER BY table_index LIMIT 20;

# 4. Read the 4 key files for RC8 investigation
# docling_adapter.py, acm_table_section_repository.py, acm_extraction.py:1034, acm_commands.py

# 5. Add debug logging to docling_adapter.py:151, re-run extraction, observe logs
```

**Fix priority for next session:**
1. RC8 (docling_document_json empty) — blocks per-row extraction entirely
2. RC9 (model mismatch) — using wrong model silently
3. RC10 (phi4 metadata failure) — will self-resolve if RC9 is fixed and correct model used
4. RC11 (missing 2 records) — likely resolves after RC8 fix restores per-row extraction
