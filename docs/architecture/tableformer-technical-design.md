# Technical Design: TableFormer Integration into ACM-AI Extraction Pipeline

| Field        | Value                                          |
|--------------|------------------------------------------------|
| **ADR**      | ADR-001 (TableFormer Activation)               |
| **Date**     | 2026-02-27                                     |
| **Author**   | Winston (Architect)                            |
| **Status**   | Draft                                          |

---

## Table of Contents

1. [Overview](#1-overview)
2. [Source Processing Changes](#2-source-processing-changes)
3. [Pipeline Input Changes](#3-pipeline-input-changes)
4. [Schema and Storage](#4-schema-and-storage)
5. [Frontend Impact](#5-frontend-impact)
6. [Dead Code Removal Plan](#6-dead-code-removal-plan)
7. [Pipeline Stage Fallback Analysis](#7-pipeline-stage-fallback-analysis)
8. [Epic/Story Breakdown](#8-epicstory-breakdown)
9. [Testing Strategy](#9-testing-strategy)
10. [Rollout Plan](#10-rollout-plan)

---

## 1. Overview

### Goal

Activate Docling's built-in TableFormer model to improve table structure
recognition in ACM survey PDFs, increasing extraction accuracy from 90.3%
to 97–100% on the Broadmeadows benchmark.

### Architecture Principle

**Minimal blast radius.** TableFormer runs inside the existing Docling pipeline
during `process_source`. The output is *better markdown* stored in the same
`source.full_text` field. No changes to the LangGraph extraction graph, the
orchestrator, or the LLM prompt templates are required for Phase 1.

### Execution Flow (Phase 1)

```
                    BEFORE                                    AFTER
                    ======                                    =====

PDF                                           PDF
 │                                             │
 ▼                                             ▼
Docling (basic markdown)                      Docling + TableFormer (accurate mode)
 │                                             │
 ▼                                             ▼
source.full_text (raw markdown)               source.full_text (enhanced markdown)
 │                                             │  - Tables have correct cell alignment
 │                                             │  - Merged cells preserved
 │                                             │  - Multi-line values kept together
 ▼                                             ▼
LLM extraction (same prompts)                LLM extraction (same prompts, better input)
 │                                             │
 ▼                                             ▼
ACMRecord (28/31)                             ACMRecord (30–31/31 projected)
```

---

## 2. Source Processing Changes

### 2A. Configuration Update — `open_notebook/graphs/source.py`

**Current code** (lines 34–79):

```python
async def content_process(state: SourceState) -> dict:
    content_settings = ContentSettings(...)
    content_state: Dict[str, Any] = state["content_state"]

    content_state["url_engine"] = (
        content_settings.default_content_processing_engine_url or "auto"
    )
    content_state["document_engine"] = (
        content_settings.default_content_processing_engine_doc or "auto"
    )
    content_state["output_format"] = "markdown"
    ...
    processed_state = await extract_content(content_state)
    return {"content_state": processed_state}
```

**Required change:**

```python
import os

async def content_process(state: SourceState) -> dict:
    content_settings = ContentSettings(...)
    content_state: Dict[str, Any] = state["content_state"]

    content_state["url_engine"] = (
        content_settings.default_content_processing_engine_url or "auto"
    )

    # TableFormer activation (ADR-001)
    # When enabled, forces Docling engine and activates table structure recognition.
    # Controlled via environment variable for gradual rollout.
    table_structure_enabled = os.environ.get(
        "DOCLING_TABLE_STRUCTURE", "false"
    ).lower() == "true"

    if table_structure_enabled:
        content_state["document_engine"] = "docling"
        content_state["docling_table_structure"] = True
        content_state["docling_table_mode"] = os.environ.get(
            "DOCLING_TABLE_MODE", "accurate"
        )
        logger.info("TableFormer enabled: docling_table_structure=True, mode=accurate")
    else:
        content_state["document_engine"] = (
            content_settings.default_content_processing_engine_doc or "auto"
        )

    content_state["output_format"] = "markdown"
    ...
```

**Key design decisions:**

1. **Environment variable control** (`DOCLING_TABLE_STRUCTURE`): Allows
   enabling/disabling without code changes, supporting A/B testing.
2. **Explicit `document_engine = "docling"`**: Required when activating
   TableFormer — the "auto" engine may select a non-Docling path.
3. **Mode selection** (`accurate` vs `fast`): Default to `accurate` for
   maximum quality; `fast` option available for high-volume scenarios.

### 2B. Model Weight Download — First-Run Behavior

**How it works:** Docling auto-downloads TableFormer weights on first use.
Files are cached in `$HOME/.cache/docling/models/` (~500 MB).

**Handling strategies:**

| Environment | Strategy |
|-------------|----------|
| **Dev (local)** | Auto-download on first `process_source` with flag enabled |
| **Docker** | Add `RUN python -c "from docling.models import TableFormerModel; TableFormerModel()"` to Dockerfile |
| **CI** | Cache `$HOME/.cache/docling/` in CI artifact cache |
| **Air-gapped** | Pre-download and mount as volume |

**No code change required** — Docling handles caching internally.

### 2C. Timing Analysis — Does TableFormer Delay full_text?

**Critical constraint:** `acm_commands.py:120–147` polls for `source.full_text`
for up to **120 seconds**. The `process_source` command runs in parallel via
`source_graph` and writes `full_text` at the end.

**Timeline analysis:**

```
                           BEFORE           AFTER (TableFormer)
process_source total:      ~5–10s           ~20–35s
  ├─ Docling PDF→markdown: ~3–8s            ~15–30s (TableFormer adds ~15–25s)
  ├─ save_source:          ~1s              ~1s
  └─ vectorize (if embed): ~2–5s            ~2–5s

acm_extract polling:       polls at 120s    polls at 120s
                           margin: 110s+    margin: 85–100s
```

**Verdict: SAFE.** Even with TableFormer, `process_source` completes in
~20–35s, well within the 120s polling window. The `full_text` field is written
by `save_source()` (line 82–107 of `source.py`), which runs after
`content_process()` completes — including TableFormer.

**TableFormer does NOT delay full_text** — it runs as part of Docling's
internal pipeline and produces the enhanced markdown that becomes `full_text`.
There is no separate post-processing step.

---

## 3. Pipeline Input Changes

### 3A. How the Orchestrator Gets TableFormer Data

**No change required for Phase 1.**

The orchestrator (`orchestrator.py:870–974`) reads content from
`source.full_text` via `normalize_docling_text()`. With TableFormer active,
this text already contains better-structured tables. The orchestrator's
`_extract_building_content()` function (line 266) slices by page markers —
this works identically whether tables are basic or TableFormer-enhanced.

### 3B. Format — What Changes in the Markdown?

**Before (basic Docling):**

```markdown
| Building | Room | Product | Result |
|---|---|---|---|
| B009 | R0001 | Vinyl floor tiles | Positive |
B009 | R0001 | Fuse cartridge | Not Sampled
Switch Room | Automatic
Battery Charger |
```

Note: broken rows, missing pipes, split cell values across lines.

**After (TableFormer-enhanced Docling):**

```markdown
| Building | Room | Product | Result |
|---|---|---|---|
| B009 | R0001 - General Storeroom | Vinyl floor tiles | Positive |
| B009 | R0001 - Switch Room | Automatic Battery Charger / Fuse cartridge | Not Sampled |
```

TableFormer's deep learning model detects cell boundaries, merged cells, and
multi-line values, producing clean markdown tables that the LLM can parse
without ambiguity.

### 3C. Where in the Pipeline Does This Inject?

**No new injection point.** The improvement flows through the existing path:

```
source.full_text (enhanced by TableFormer)
        ↓
prepare_context() [acm_extraction.py:1022]
        ↓ calls normalize_docling_text()
        ↓ then _preprocess_acm_content()
        ↓ then _chunk_content()
        ↓
extract_records() or orchestrate_extraction()
        ↓
LLM receives better-structured markdown
```

### 3D. Fallback Chain

The existing content fallback in `prepare_context()` (lines 1028–1057)
currently checks for MinerU HTML table sections. With MinerU removed (see
Section 6), the fallback chain simplifies to:

**Phase 1 fallback chain:**

```
1. source.full_text (TableFormer-enhanced Docling markdown)
   └── if TableFormer fails internally → basic Docling markdown (automatic)
2. normalize_docling_text() cleanup
3. _preprocess_acm_content() structural markers
4. LLM extraction
```

**No MinerU HTML check needed** — the `prepare_context()` MinerU HTML path
(lines 1028–1057) becomes dead code and should be removed alongside the
MinerU cleanup (Section 6).

---

## 4. Schema and Storage

### 4A. Does `acm_table_section` Need Changes?

**Phase 1: No schema changes required.**

TableFormer output is consumed entirely through `source.full_text` (enhanced
markdown). The `acm_table_section` table is not used in Phase 1.

**Phase 2 (future): Optional schema additions for structured table storage.**

If we later want to store TableFormer's structured output (DataFrames, JSON)
alongside the markdown, we would add:

```surql
-- Migration XX: TableFormer structured table storage
DEFINE FIELD structured_json ON acm_table_section TYPE option<string>;
DEFINE FIELD extraction_method ON acm_table_section TYPE option<string>;
-- e.g., 'tableformer_accurate', 'tableformer_fast', 'docling_basic'
```

And store tables as:

```python
section = ACMTableSection(
    source_id=str(source.id),
    page_start=table.page_start,
    page_end=table.page_end,
    raw_html=table.to_html(),                    # HTML rendering
    raw_text=table.to_markdown(),                 # Markdown rendering
    structured_json=table.to_json(),              # DataFrame as JSON
    table_type="tableformer_structured",
    extraction_method="tableformer_accurate",
)
```

**Not needed for Phase 1** — the accuracy improvement comes from better
markdown in `full_text`, not from storing structured data.

### 4B. Existing Schema Compatibility

The `acm_table_section` schema (migration 18) already supports:

| Field | Type | Phase 1 Use | Phase 2 Use |
|-------|------|-------------|-------------|
| `source_id` | `record<source>` | N/A | Links to source |
| `page_start` | `int` | N/A | Table page range |
| `page_end` | `int` | N/A | Table page range |
| `raw_html` | `option<string>` | N/A | TableFormer HTML output |
| `raw_text` | `option<string>` | N/A | TableFormer markdown output |
| `building_name` | `option<string>` | N/A | Per-building table grouping |
| `table_type` | `option<string>` | N/A | `"tableformer_structured"` |

The existing indexes (`section_source`, `section_pages`) are sufficient for
per-building page range queries in Phase 2.

---

## 5. Frontend Impact

### 5A. Raw Tables Endpoint — `GET /api/acm/jobs/{source_id}/raw-tables`

**Current behavior** (acm.py:1401–1455):

1. Check `acm_table_section` for MinerU HTML sections → return if found
2. Check `acm_table_section` for text sections → return if found
3. Fall back to `_extract_docling_markdown_tables(source.full_text)`

**Phase 1 impact:** Step 3 (the fallback) automatically improves because
`source.full_text` now contains better-structured tables from TableFormer.
No code change needed — the Docling markdown table extraction function
(`_extract_docling_markdown_tables`) works on pipe-delimited tables,
which TableFormer produces with better quality.

**Phase 2 impact:** If structured TableFormer data is stored in
`acm_table_section`, steps 1–2 would return those sections. The
`table_type` filter would need updating from `"mineru_html"` checks
to `"tableformer_structured"` checks.

### 5B. RawTableViewer Component

**No changes needed for Phase 1.** The `RawTableViewer` displays markdown
tables from the endpoint. With TableFormer, these tables have:

- Consistent column alignment (better markdown pipe tables)
- Preserved merged cells
- No split values across lines

This makes the raw table view **more useful** with zero frontend changes.

**Phase 2 opportunity:** If we store TableFormer DataFrames as JSON, we could
render interactive AG Grid tables instead of raw markdown. This would be a
new component, not a modification to the existing viewer.

### 5C. No Breaking Frontend Changes

The frontend consumes:

- `GET /api/acm/records` → unchanged (records are still ACMRecord objects)
- `GET /api/acm/jobs/{id}/raw-tables` → improved quality, same shape
- `GET /api/acm/jobs/{id}/buildings` → unchanged

---

## 6. Dead Code Removal Plan

### 6A. Files to Remove

| # | File | Lines | Action | Reason |
|---|------|-------|--------|--------|
| 1 | `open_notebook/extractors/mineru_table_extractor.py` | 557 | **DELETE** | MinerU requires paddle; TableFormer replaces this |
| 2 | `tests/test_mineru_table_extractor.py` | ~37 tests | **DELETE** | Tests for deleted code |
| 3 | `tests/test_source_commands_mineru.py` | ~1 file | **DELETE** | Tests for `_store_mineru_tables()` |

### 6B. Code to Remove from Existing Files

| # | File | Lines/Function | Action |
|---|------|---------------|--------|
| 1 | `commands/source_commands.py` | `MINERU_TABLE_TYPE` constant (L32) | Remove |
| 2 | `commands/source_commands.py` | `_resolve_source_pdf_path()` (L35–43) | Remove |
| 3 | `commands/source_commands.py` | `_update_table_extraction_metadata()` (L46–69) | Remove |
| 4 | `commands/source_commands.py` | `_store_mineru_tables()` (L72–145) | Remove |
| 5 | `commands/source_commands.py` | `_store_mineru_tables()` call in `process_source_command()` (L232–238) | Remove |
| 6 | `commands/source_commands.py` | Import of `ACMTableSection` (L10) | Remove (if no other use) |
| 7 | `open_notebook/extractors/orchestrator.py` | `_format_html_tables_for_llm()` (L393–408) | Remove |
| 8 | `open_notebook/extractors/orchestrator.py` | `_get_mineru_tables_for_building()` (L411–439) | Remove |
| 9 | `open_notebook/extractors/orchestrator.py` | MinerU check in `extract_building()` (L633–651) | Remove — simplify to always use `building_content` |
| 10 | `open_notebook/graphs/acm_extraction.py` | MinerU HTML path in `prepare_context()` (L1028–1057) | Remove |
| 11 | `tests/test_orchestrator.py` | `test_get_mineru_tables_for_building_filters_and_caches` | Remove |
| 12 | `tests/test_acm_extractor.py` | 5 MinerU-related tests (L720–833) | Remove |

### 6C. Legacy Regex Parser — `acm_extractor.py`

| File | Lines | Tests | Decision |
|------|-------|-------|----------|
| `open_notebook/extractors/acm_extractor.py` | ~850 | `test_acm_extractor.py` (~40 tests), `test_e2e_extraction.py` (4 refs), `test_generic_parser.py` (3 refs), `test_consultant_parsers.py` (5 refs), `test_acm_extractor_integration.py` (1 ref) | **DEPRECATE with TODO, do NOT remove yet** |

**Rationale:** The legacy regex parser (`extract_acm_records()`) is not called
by the LangGraph pipeline, but it IS imported by multiple test files for
unit-testing regex patterns (BUILDING_PATTERN, ROOM_PATTERN, etc.) and for
the E2E extraction test. Removing it requires refactoring 13+ test imports.

**Action:** Add deprecation header to `acm_extractor.py`:

```python
"""
DEPRECATED: Legacy regex-based ACM extractor.

This module is NOT used by the LangGraph extraction pipeline (acm_extraction.py).
It is retained for backward-compatible test infrastructure. Scheduled for removal
in a future cleanup sprint.

See ADR-001: docs/architecture/adr-tableformer-integration.md
"""
```

### 6D. `_extract_with_mineru()` Stub in `acm_extractor.py`

**Remove** — this function (line 385) always returns `[]` with a TODO.
It has no callers outside of its own file and the MinerU tests.

---

## 7. Pipeline Stage Fallback Analysis

### E23-S4 Validation Findings

The E23-S4 validation revealed that three pre-extraction stages fall back to
heuristics because the LLM returns non-JSON responses:

1. **structure_extraction** → heuristic page counting
2. **building_inventory** → regex-based building detection
3. **page_tagging** → default section assignment

### Should This Be Addressed in the TableFormer Epic?

**No — treat as a separate concern.**

**Rationale:**

1. **Different root cause.** The stage fallbacks are caused by LLM response
   parsing failures (non-JSON output), not by table structure quality.
   TableFormer improves table quality but doesn't affect these stages, which
   operate on the full document text (headers, TOC, page markers).

2. **Different fix.** The fix for stage fallbacks is either:
   - Better prompt engineering for the structure/inventory/tagging LLM calls
   - Adding `response_format: json_object` to the model parameters
   - Implementing retry logic specific to these stages

3. **Different risk profile.** Stage fallbacks cause suboptimal but functional
   extraction (the orchestrator still works with heuristic page ranges).
   TableFormer addresses a much higher-impact gap (missing records).

4. **Scope containment.** Bundling stage fallback fixes into the TableFormer
   epic increases scope, risk, and testing surface. Ship TableFormer first,
   measure improvement, then address stage reliability as a follow-up epic.

**Recommended:** Create a separate epic "E-XX: Pre-Extraction Stage Reliability"
with stories for each failing stage.

---

## 8. Epic/Story Breakdown

### Epic: TableFormer Integration (E-XX)

#### Story 1: Activate TableFormer in Source Processing [S/M — 2 SP]

**Scope:** Minimum viable change — just activate TableFormer.

**File changes:**
- `open_notebook/graphs/source.py` — Add TableFormer configuration
- `.env.example` — Add `DOCLING_TABLE_STRUCTURE` and `DOCLING_TABLE_MODE`

**Acceptance criteria:**
1. When `DOCLING_TABLE_STRUCTURE=true`, Docling uses TableFormer for PDFs
2. When `DOCLING_TABLE_STRUCTURE=false` (default), behavior is unchanged
3. `source.full_text` contains enhanced markdown with better table structure
4. Processing completes within 60s for a typical SAMP PDF (~30 pages)
5. Automatic fallback: if TableFormer model fails to load, Docling uses basic mode

**Tests:**
- Unit test: `content_process()` sets correct `content_state` keys
- Integration test: Process Broadmeadows PDF with flag on, verify `full_text` quality

---

#### Story 2: Broadmeadows Accuracy Validation [S — 1 SP]

**Scope:** Validate the accuracy improvement before shipping.

**Acceptance criteria:**
1. Run extraction with TableFormer enabled on Broadmeadows benchmark PDF
2. Compare record count and field accuracy against ground truth (31 records)
3. Document results: record count, field accuracy, processing time, memory usage
4. Identify any regressions (records that were correct before, wrong after)
5. Decision gate: If accuracy >= 30/31, proceed. If < 28/31, investigate.

**Tests:**
- Update `test_e2e_extraction.py` with TableFormer-enabled test case
- Benchmark processing time: assert < 60s

---

#### Story 3: Remove MinerU Dead Code [S — 1 SP]

**Scope:** Clean up dead code per ADR-001 Section D2.

**File changes:** See Section 6 above (3 files deleted, 8 files edited).

**Acceptance criteria:**
1. All MinerU-related code removed per the plan in Section 6B
2. `_store_mineru_tables()` and related functions removed from source_commands.py
3. MinerU HTML path removed from `prepare_context()` and `extract_building()`
4. All existing tests pass (except deleted MinerU tests)
5. `npm run build` passes (frontend unaffected)
6. `acm_extractor.py` has deprecation header but is NOT deleted

**Tests:**
- `uv run pytest` — all non-MinerU tests pass
- `uv run ruff check .` — no lint errors from orphaned imports

---

#### Story 4: Model Weight Pre-Download in Docker [S — 1 SP]

**Scope:** Ensure TableFormer works in containerized deployments.

**File changes:**
- `Dockerfile` — Add model pre-download step
- `docker-compose.yml` — Add `DOCLING_TABLE_STRUCTURE=true` to API/worker env

**Acceptance criteria:**
1. Docker build downloads TableFormer weights during image build
2. Container startup does not require internet access for model download
3. Health check endpoint verifies model availability

---

### Full Integration Stories (Phase 2 — Future Epic)

#### Story 5: Store Structured Table Data in acm_table_section [M — 3 SP]

**Scope:** Phase 2 — store TableFormer DataFrames alongside enhanced markdown.

**File changes:**
- New migration: Add `structured_json`, `extraction_method` fields
- `commands/source_commands.py` — Post-process Docling output to store tables
- `open_notebook/domain/acm.py` — Update ACMTableSection model

**Prerequisites:** Stories 1–3 complete.

---

#### Story 6: Frontend Structured Table Viewer [M — 3 SP]

**Scope:** Render TableFormer-structured data in AG Grid instead of raw markdown.

**File changes:**
- `frontend/src/components/acm/StructuredTableViewer.tsx` — New component
- `api/routers/acm.py` — Update raw-tables endpoint for new table_type

**Prerequisites:** Story 5 complete.

---

### Stretch Goal Stories (Phase 3 — Future Epic)

#### Story 7: Direct Field Mapping for Standard SAMP Tables [L — 5 SP]

**Scope:** Bypass LLM for standard SAMP-format tables where TableFormer
produces DataFrames with known column headers.

**How it works:**
1. TableFormer produces DataFrame with headers: Building, Room, Product, etc.
2. Column name matching maps DataFrame columns to ACMExtractionRecord fields
3. If column match confidence > 90%, skip LLM — create records directly
4. If column match fails, fall back to normal LLM extraction

**Prerequisites:** Stories 1–5 complete, extensive validation.

**Risk:** High — requires handling column name variations across consultants.

---

### Effort Summary

| Story | Size | Est. Points | Phase | Dependency |
|-------|------|-------------|-------|------------|
| S1: Activate TableFormer | S/M | 2 | 1 (MVP) | None |
| S2: Broadmeadows Validation | S | 1 | 1 (MVP) | S1 |
| S3: Remove MinerU Dead Code | S | 1 | 1 (MVP) | None (parallel) |
| S4: Docker Model Pre-Download | S | 1 | 1 (MVP) | S1 |
| S5: Store Structured Tables | M | 3 | 2 (Full) | S1–S3 |
| S6: Frontend Table Viewer | M | 3 | 2 (Full) | S5 |
| S7: Direct Field Mapping | L | 5 | 3 (Stretch) | S5, extensive validation |
| **Total Phase 1 (MVP)** | | **5 SP** | | |
| **Total Phase 2 (Full)** | | **11 SP** | | |
| **Total Phase 3 (Stretch)** | | **16 SP** | | |

---

## 9. Testing Strategy

### Phase 1 Tests

| Test Type | What | How | File |
|-----------|------|-----|------|
| **Unit** | `content_process()` sets TableFormer keys | Mock env var, assert `content_state` keys | `tests/test_source_graph.py` (new or existing) |
| **Unit** | Feature flag off → no TableFormer keys | Mock env var `false`, assert keys absent | Same file |
| **Integration** | Broadmeadows extraction accuracy | Process PDF with flag on, count records | `tests/test_e2e_extraction.py` |
| **Integration** | Processing time < 60s | Time the full `process_source` flow | Same file |
| **Regression** | All existing tests pass | `uv run pytest` | CI |
| **Regression** | Frontend builds | `cd frontend && npm run build` | CI |

### Phase 1 Test Removal

| File | Tests Removed | Reason |
|------|--------------|--------|
| `tests/test_mineru_table_extractor.py` | All (~37) | File deleted |
| `tests/test_source_commands_mineru.py` | All | File deleted |
| `tests/test_orchestrator.py` | 1 test | MinerU cache test |
| `tests/test_acm_extractor.py` | 5 tests | MinerU integration tests |
| `tests/test_acm_api.py` | 1 test | `test_raw_table_prefers_mineru_sections` |

---

## 10. Rollout Plan

### Phase 1: Gradual Rollout

```
Week 1:  S1 (Activate) + S2 (Validate) + S3 (Cleanup)
         └── Ship with DOCLING_TABLE_STRUCTURE=false (default)
         └── Run Broadmeadows validation
         └── If accuracy >= 30/31 → proceed

Week 2:  S4 (Docker) + Promote flag to true
         └── Update .env.example default to true
         └── Monitor processing times and memory
         └── Watch for regressions on diverse PDF formats

Week 3:  Stabilize + assess Phase 2 need
         └── If structured table storage adds value → plan Phase 2
         └── If enhanced markdown sufficient → skip Phase 2
```

### Rollback Plan

1. Set `DOCLING_TABLE_STRUCTURE=false` in `.env`
2. Restart worker process
3. Reprocess affected sources

No data migration needed — `source.full_text` is overwritten on reprocess.

### Monitoring

| Metric | Threshold | Action |
|--------|-----------|--------|
| Processing time per PDF | > 90s | Investigate; switch to `DOCLING_TABLE_MODE=fast` |
| Memory usage (worker) | > 8 GB | Scale worker instance or add limits |
| Extraction accuracy (sample) | < 28/31 | Rollback; investigate regression |
| Model download failure | Any | Check network; use pre-cached model |

---

## Related Documents

- ADR: `docs/architecture/adr-tableformer-integration.md`
- Research: `docs/research/tableformer-research-spike-20260227.md`
- Pipeline Audit: `docs/PIPELINE-AUDIT-FEB-25/pipeline-analysis-20260225.md`
- Schema: `migrations/18.surrealql`
