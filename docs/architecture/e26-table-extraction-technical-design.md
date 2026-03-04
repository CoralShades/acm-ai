# E26 Technical Design: Docling Direct API Integration

| Field | Value |
|-------|-------|
| **ADR** | ADR-001 (D5: Docling Direct API) |
| **Date** | 2026-02-27 |
| **Author** | Winston (Architect) |
| **Status** | Draft |
| **Depends On** | E25 spike results (`docs/reviews/e25-table-extraction-comparison.md`) |
| **Target** | Broadmeadows >= 30/31 (96.8%), Alexander maintains 54/54 |

---

## Table of Contents

1. [Overview](#1-overview)
2. [Source Processing Changes](#2-source-processing-changes)
3. [Pipeline Integration](#3-pipeline-integration)
4. [Schema Changes](#4-schema-changes)
5. [Frontend Impact](#5-frontend-impact)
6. [Testing Strategy](#6-testing-strategy)
7. [Rollout Plan](#7-rollout-plan)
8. [Story Breakdown](#8-story-breakdown)

---

## 1. Overview

### Problem

content-core's markdown serializer destroys TableFormer's table structure
(E24: 17/31 regression). The serializer reads cells in column-major order,
producing fragmented text where "Same as" references lose their room/product
context and sample numbers split across lines.

### Solution

Run Docling `DocumentConverter` in parallel with PyMuPDF during source
processing. Store DataFrames in `acm_table_section`. Inject structured
table data into the orchestrator's per-building LLM context.

### Key Difference from E24

| Aspect | E24 (content-core path) | E26 (Direct API path) |
|--------|------------------------|----------------------|
| Entry point | `content-core.extract_content()` | `docling.DocumentConverter.convert()` |
| Table model | TableFormer (same) | TableFormer (same) |
| Output format | Markdown via content-core serializer | `table.export_to_dataframe(doc=doc)` |
| Row coherence | **BROKEN** (column-major) | **PRESERVED** (row-major DataFrames) |
| Replaces full_text? | Yes (overwrites) | **No** (parallel — PyMuPDF full_text unchanged) |
| Feature flag | `DOCLING_TABLE_STRUCTURE` | `DOCLING_DIRECT_TABLE_EXTRACTION` (new) |
| E25 accuracy | 17/31 (54.8%) | 29/31 (93.5%) DataFrames alone |

### Architecture — Hybrid Approach A

```
PDF Upload
├── PyMuPDF (via content-core)
│   └── source.full_text  (unchanged — proven 28/31 path)
│       └── Page markers: --- Page N ---
│       └── Reading-order text (includes page 8 content)
│
└── Docling Direct API  (NEW — parallel extraction)
    └── DocumentConverter(TableFormerMode.ACCURATE)
        └── doc.tables[N].export_to_dataframe(doc=doc)
            ├── df.to_markdown()  → acm_table_section.raw_text
            ├── table.export_to_html(doc=doc) → acm_table_section.raw_html
            ├── df.to_csv()  → acm_table_section.structured_json
            └── table.prov[0].page_no → acm_table_section.page_start

Orchestrator (per-building)
├── building_content = _extract_building_content(source.full_text, pages)
├── docling_tables = get_docling_tables(source_id, page_start, page_end)
├── IF docling_tables exist:
│   └── Append DataFrame markdown to LLM context
│   └── Add supplementary prompt instruction
└── LLM extraction → ACMRecord (target: 30-31/31)
```

---

## 2. Source Processing Changes

### 2A. New Function: `_extract_tables_with_docling()`

**Location**: `commands/source_commands.py` (called from `process_source_command()`)

```python
import os
import re
from typing import Any, Dict, List

from loguru import logger


DOCLING_DIRECT_TABLE_EXTRACTION = os.environ.get(
    "DOCLING_DIRECT_TABLE_EXTRACTION", "false"
).lower() == "true"


async def _extract_tables_with_docling(source_id: str, pdf_path: str) -> List[Dict[str, Any]]:
    """
    Run Docling Direct API on PDF, return list of table dicts.
    Runs AFTER PyMuPDF text extraction (does not replace it).

    Uses DocumentConverter directly, bypassing content-core's serialization
    layer that caused E24's row-fragmentation regression.
    """
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

    pipeline_options = PdfPipelineOptions(do_table_structure=True)
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    pipeline_options.table_structure_options.do_cell_matching = True

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )

    result = converter.convert(pdf_path)
    doc = result.document

    tables: List[Dict[str, Any]] = []
    for idx, table in enumerate(doc.tables):
        try:
            df = table.export_to_dataframe(doc=doc)

            # --- Normalization pipeline (patterns validated in E25-S1) ---

            # 1. Fix split sample numbers: "34511-039- 001" → "34511-039-001"
            df = df.map(
                lambda v: re.sub(r"(\d+)-\s+(\d+)", r"\1-\2", str(v))
                if isinstance(v, str) else v
            )

            # 2. Strip "Asbestos " prefix from hazard status
            for col in df.columns:
                if "hazard" in col.lower() or "status" in col.lower():
                    df[col] = df[col].apply(
                        lambda v: re.sub(r"^Asbestos\s+", "", str(v))
                        if isinstance(v, str) else v
                    )

            page_no = table.prov[0].page_no if table.prov else -1

            tables.append({
                "table_index": idx,
                "page": page_no,
                "rows": len(df),
                "columns": list(df.columns),
                "csv": df.to_csv(index=False),
                "markdown": df.to_markdown(index=False),
                "html": table.export_to_html(doc=doc),
            })

            logger.info(
                f"Docling table {idx}: page={page_no}, rows={len(df)}, "
                f"cols={len(df.columns)}"
            )
        except Exception as e:
            logger.warning(f"Docling table {idx} export failed: {e}")
            continue

    logger.info(
        f"Docling Direct API: {len(tables)} tables extracted from {pdf_path}"
    )
    return tables
```

**Design notes**:

1. **Imports are inside the function** — Docling is a heavy import (~2s). Only
   load when the feature flag is on and we have a PDF to process.

2. **Normalization is minimal** — Only fix known data quality issues from E25-S1:
   split sample numbers and "Asbestos " prefix. More aggressive normalization
   (column mapping, "Same as" → "As Per") is deferred to the orchestrator layer.

3. **Error handling per-table** — If one table fails to export, continue with
   the rest. Log the failure for debugging.

### 2B. Integration into `process_source_command()`

After `source_graph.ainvoke()` completes (which saves `source.full_text` via
PyMuPDF), run Docling extraction if:
- `DOCLING_DIRECT_TABLE_EXTRACTION` is `true`
- Source has a file_path pointing to a PDF

```python
# In process_source_command(), after source_graph result:

if DOCLING_DIRECT_TABLE_EXTRACTION:
    source = result["source"]
    pdf_path = _resolve_source_pdf_path(source)
    if pdf_path and pdf_path.lower().endswith(".pdf"):
        try:
            tables = await _extract_tables_with_docling(
                str(source.id), pdf_path
            )
            if tables:
                await _store_docling_tables(str(source.id), tables)
                logger.info(
                    f"Stored {len(tables)} Docling tables for source {source.id}"
                )
        except Exception as e:
            logger.error(f"Docling table extraction failed: {e}")
            # Non-fatal — PyMuPDF text is already saved
```

**Critical design choice**: Docling runs AFTER `source_graph` completes.
This means `source.full_text` is already saved before Docling starts.
If Docling fails, the pipeline continues with PyMuPDF text only — zero
regression risk.

### 2C. Storage Function: `_store_docling_tables()`

```python
async def _store_docling_tables(source_id: str, tables: List[Dict[str, Any]]) -> None:
    """Store Docling DataFrame tables in acm_table_section."""
    from open_notebook.database.repository import repo

    for table in tables:
        await repo.create("acm_table_section", {
            "source_id": source_id,
            "page_start": table["page"],
            "page_end": table["page"],
            "raw_html": table.get("html"),
            "raw_text": table.get("markdown"),
            "structured_json": table.get("csv"),
            "table_type": "docling_direct_api",
            "building_name": None,  # Populated later by orchestrator if needed
        })
```

### 2D. PDF Path Resolution

The source's file_path is set by content-core during `content_process()`.
For uploaded PDFs, this is a local path like `uploads/source_abc123.pdf`.

```python
def _resolve_source_pdf_path(source) -> str | None:
    """Resolve the PDF path from a processed source."""
    if source.asset and source.asset.file_path:
        return str(source.asset.file_path)
    return None
```

### 2E. Feature Flag

```python
DOCLING_DIRECT_TABLE_EXTRACTION = os.environ.get(
    "DOCLING_DIRECT_TABLE_EXTRACTION", "false"
).lower() == "true"
```

**Separate from E24's `DOCLING_TABLE_STRUCTURE` flag.** This controls the
new parallel path. E24's flag controls content-core's internal serialization.
Both can be independently enabled/disabled:

| Flag Combination | Behavior |
|-----------------|----------|
| Both OFF (default) | PyMuPDF text only — current production path |
| `DOCLING_TABLE_STRUCTURE=true` only | E24 path — DO NOT USE (17/31 regression) |
| `DOCLING_DIRECT_TABLE_EXTRACTION=true` only | **E26 path** — PyMuPDF text + Docling DataFrames |
| Both ON | Not recommended — redundant Docling processing |

---

## 3. Pipeline Integration

### 3A. Orchestrator Changes

In `open_notebook/extractors/orchestrator.py`, modify `extract_building()` to
load and inject Docling tables into the LLM context.

**Current flow** (orchestrator.py:568-714):
```
extract_building(plan, content, state)
  → building_content = _extract_building_content(content, pages)
  → _llm_extract_building(building_content, plan, state, "markdown")
```

**New flow**:
```
extract_building(plan, content, state)
  → building_content = _extract_building_content(content, pages)
  → docling_tables = await _get_docling_tables(source_id, page_start, page_end)
  → IF docling_tables:
      → enriched_content = _inject_docling_tables(building_content, docling_tables)
      → _llm_extract_building(enriched_content, plan, state, "markdown")
    ELSE:
      → _llm_extract_building(building_content, plan, state, "markdown")
```

### 3B. Table Loading Function

```python
async def _get_docling_tables(
    source_id: str,
    page_start: int,
    page_end: int,
) -> List[Dict[str, Any]]:
    """Load Docling Direct API tables from acm_table_section for a page range."""
    from open_notebook.database.repository import repo

    query = """
        SELECT * FROM acm_table_section
        WHERE source_id = $source_id
        AND table_type = 'docling_direct_api'
        AND page_start >= $page_start
        AND page_end <= $page_end
        ORDER BY page_start ASC
    """
    results = await repo.query(query, {
        "source_id": source_id,
        "page_start": page_start,
        "page_end": page_end,
    })
    return results or []
```

### 3C. Context Injection Strategy

```python
def _inject_docling_tables(
    building_content: str,
    docling_tables: List[Dict[str, Any]],
) -> str:
    """Inject Docling DataFrame markdown into building content for LLM context."""
    if not docling_tables:
        return building_content

    context_parts = [building_content]
    context_parts.append(
        "\n\n## Structured Table Data (from PDF table extraction)\n"
        "The following tables were extracted directly from the PDF with "
        "preserved row structure. Each row is a complete ACM register entry.\n"
    )

    for table in docling_tables:
        page = table.get("page_start", "?")
        raw_text = table.get("raw_text", "")
        if raw_text:
            context_parts.append(f"### Table (Page {page})\n{raw_text}\n")

    context_parts.append(
        "\n**IMPORTANT**: The structured table data above preserves exact row "
        "structure from the PDF. Each row represents one ACM record. Rows with "
        "'Same as', 'As Per', 'Not Sampled', or 'No Access' entries are separate "
        "records that must EACH be extracted as individual ACM records.\n"
    )

    return "\n".join(context_parts)
```

### 3D. Prompt Changes

The extraction prompt (`prompts/acm/building_extraction.j2`) needs a small
addition to guide the LLM when structured table data is available:

```jinja2
{% if input_format == "markdown" %}
{# Existing prompt content unchanged #}

When structured table data is provided (under "## Structured Table Data"),
prioritize it over the document text for extracting ACM records. Each row
in the structured table represents one ACM record, including rows with:
- "Same as [sample number]" — these are valid "As Per" records
- "Not Sampled" — these are valid assumed-positive records
- "No Access" — these are valid records with unknown status
- "Assumed positive" — these are valid untested positive records

Extract EVERY row as a separate record. Do not merge or skip any rows.
{% endif %}
```

### 3E. Integration Point in extract_building()

The change to `extract_building()` is minimal — add the table loading and
injection before the existing LLM call:

```python
async def extract_building(
    plan: BuildingExtractionPlan,
    content: str,
    state: dict,
) -> Tuple[List[ACMExtractionRecord], BuildingExtractionStats]:
    # ... existing code up to llm_input_content assignment ...

    llm_input_content = building_content
    llm_input_format = "markdown"

    # NEW: Inject Docling tables if available (D5)
    source_id = str(state.get("source", {}).id) if state.get("source") else None
    if source_id:
        docling_tables = await _get_docling_tables(
            source_id, plan.page_range[0], plan.page_range[1]
        )
        if docling_tables:
            llm_input_content = _inject_docling_tables(
                building_content, docling_tables
            )
            logger.info(
                f"Building {plan.building_id}: injected {len(docling_tables)} "
                f"Docling tables into LLM context"
            )

    # ... rest of existing code uses llm_input_content ...
```

---

## 4. Schema Changes

### 4A. Migration Assessment

The existing `acm_table_section` schema (migration 18) has most fields needed.
One new field is required for DataFrame storage:

| Field | Type | Status | Purpose |
|-------|------|--------|---------|
| `source_id` | `record<source>` | EXISTS | Link to source |
| `page_start` | `int` | EXISTS | From `table.prov[0].page_no` |
| `page_end` | `int` | EXISTS | Same as page_start (single-page tables) |
| `raw_html` | `option<string>` | EXISTS | From `table.export_to_html(doc=doc)` |
| `raw_text` | `option<string>` | EXISTS | From `df.to_markdown(index=False)` |
| `building_name` | `option<string>` | EXISTS | Optional building inference |
| `table_type` | `option<string>` | EXISTS | `"docling_direct_api"` (new value) |
| **`structured_json`** | **`option<string>`** | **NEW** | DataFrame as CSV for programmatic access |

### 4B. New Migration

Create migration file (next available number):

```surql
-- Migration N: Docling Direct API table storage (E26, ADR-001 D5)
-- Adds structured_json field for DataFrame storage

DEFINE FIELD structured_json ON acm_table_section TYPE option<string>;
```

The existing indexes (`section_source`, `section_pages`) are sufficient for
the queries in Section 3B.

### 4C. table_type Values

| Value | Source | Description |
|-------|--------|-------------|
| `"docling_direct_api"` | E26 | DataFrames from Docling DocumentConverter |
| `"tableformer_structured"` | Future | Reserved for D4 Phase 2 (content-core path) |
| `NULL` or absent | Legacy | Old MinerU entries (if any remain) |

---

## 5. Frontend Impact

### 5A. Raw Tables Tab — Automatic Improvement

The existing Raw Tables tab (`GET /api/acm/jobs/{source_id}/raw-tables`)
already checks `acm_table_section` first. With Docling Direct API tables
stored there (with `raw_html` and `raw_text` populated), the tab will
automatically show better-quality tables. **No frontend code change needed.**

Flow:
1. API checks `acm_table_section` for this source → finds Docling tables
2. Returns `raw_html` (rich table) and `raw_text` (markdown fallback)
3. `RawTableViewer` renders the HTML tables

### 5B. Future: AG Grid Direct Rendering

If DataFrames are stored as `structured_json` (CSV format), a future story
could parse them into AG Grid column/row definitions — giving interactive
table exploration with sorting, filtering, and column resize. This is a
Phase 2 enhancement, not part of E26.

### 5C. No Breaking Changes

| Endpoint | Impact |
|----------|--------|
| `GET /api/acm/records` | Unchanged (records are still ACMRecord objects) |
| `GET /api/acm/jobs/{id}/raw-tables` | Improved quality (Docling tables), same shape |
| `GET /api/acm/jobs/{id}/buildings` | Unchanged |

---

## 6. Testing Strategy

### Unit Tests

| Test | What | How | File |
|------|------|-----|------|
| `_extract_tables_with_docling()` returns tables | Mock `DocumentConverter`, assert structure | `tests/test_source_commands_docling.py` |
| Sample number normalization | `"34511-039- 001"` → `"34511-039-001"` | Same file |
| Hazard status normalization | `"Asbestos Negative"` → `"Negative"` | Same file |
| `_store_docling_tables()` persists correctly | Mock repo, assert CREATE calls | Same file |
| `_inject_docling_tables()` format | Assert markdown injection format | `tests/test_orchestrator_docling.py` |
| `_get_docling_tables()` filters by page range | Mock query, assert WHERE clause | Same file |
| Feature flag OFF → no Docling extraction | Env var `false`, assert not called | `tests/test_source_commands_docling.py` |

### Integration Tests

| Test | What | How |
|------|------|-----|
| Broadmeadows full pipeline | Process PDF with flag ON, verify 30+ register rows in `acm_table_section` | `tests/test_docling_integration.py` |
| Alexander no-regression | Process PDF with flag ON, verify 54/54 maintained | Same file |
| Orchestrator with Docling tables | Full extraction with tables injected, count records | Same file |

### E2E Tests

| Test | What | How |
|------|------|-----|
| Upload → Extract → Review | Full workflow with Docling tables in context | `tests/test_broadmeadows_e2e.py` (updated) |

### Performance Tests

| Test | What | Threshold |
|------|------|-----------|
| Docling extraction time | `_extract_tables_with_docling()` alone | < 60s |
| Full pipeline time | Upload → records | < 300s |

---

## 7. Rollout Plan

### Phase 1: Parallel Extraction (E26-S1 + S2)

- Add `_extract_tables_with_docling()` to `process_source_command`
- Store tables in `acm_table_section` with `table_type="docling_direct_api"`
- Feature flag OFF by default
- Validate on Broadmeadows: count tables (expect 8), verify DataFrame rows (expect 30 register rows)
- Validate on Alexander: count tables, verify no interference with existing extraction

### Phase 2: Context Injection (E26-S3)

- Modify orchestrator to inject Docling tables into LLM context
- Add supplementary prompt instruction for structured table handling
- Validate extraction accuracy: target >= 30/31 on Broadmeadows
- Compare with/without Docling tables on same PDF

### Phase 3: Validation + Promotion (E26-S4)

- Run full validation on both benchmark PDFs
- Decision gate:
  - Broadmeadows >= 30/31 AND Alexander 54/54 → promote flag to `true`
  - Broadmeadows < 28/31 → rollback, investigate
  - Broadmeadows 28-29/31 → investigate, do not promote yet
- Update `.env.example` default if promoted
- Document results in `docs/reviews/e26-validation-results.md`

### Rollback

1. Set `DOCLING_DIRECT_TABLE_EXTRACTION=false` in `.env`
2. Restart worker
3. No data migration needed — `acm_table_section` rows are supplementary
4. Existing `source.full_text` (PyMuPDF) is unaffected

---

## 8. Story Breakdown

### E26-S1: Add Docling Direct API Extraction to Source Processing [M — 3 SP]

**Scope**: Implement the parallel Docling extraction path in source processing.

**File changes**:
| File | Change |
|------|--------|
| `commands/source_commands.py` | Add `_extract_tables_with_docling()`, `_store_docling_tables()`, `_resolve_source_pdf_path()` |
| `commands/source_commands.py` | Add Docling call after `source_graph` in `process_source_command()` |
| `migrations/N.surrealql` | Add `structured_json` field to `acm_table_section` |
| `.env.example` | Add `DOCLING_DIRECT_TABLE_EXTRACTION=false` |
| `tests/test_source_commands_docling.py` | Unit tests for extraction, normalization, storage |

**Acceptance criteria**:
1. When `DOCLING_DIRECT_TABLE_EXTRACTION=true`, Docling Direct API runs after PyMuPDF
2. When flag is `false` (default), behavior is unchanged — zero regression risk
3. DataFrames stored in `acm_table_section` with `table_type="docling_direct_api"`
4. Sample number normalization applied (`34511-039- 001` → `34511-039-001`)
5. Hazard status normalization applied (strip "Asbestos " prefix)
6. Per-table error handling — one table failure doesn't block others
7. `source.full_text` remains the PyMuPDF output (unchanged)

**Known patterns from E25 to handle**:
- Split sample numbers: `re.sub(r'(\d+)-\s+(\d+)', r'\1-\2', value)`
- Compound column headers varying across tables
- Merged cell artifacts (Table 2, Row 3)

---

### E26-S2: Broadmeadows DataFrame Validation [S — 1 SP]

**Scope**: Validate that Docling extraction produces correct DataFrames.

**Acceptance criteria**:
1. Run Docling extraction on Broadmeadows with flag ON
2. Verify 8 tables stored in `acm_table_section` (3 register, 5 other)
3. Verify 30 register rows across tables 2, 3, 4 (10 per page on pp.5-7)
4. Verify 9/9 "Same as" rows present in DataFrames
5. Verify 4/6 "Not Sampled" rows present (matching E25 spike results)
6. Verify DataFrame column structure matches E25 report
7. Document any discrepancies vs spike in validation report

**Output**: `docs/reviews/e26-s2-validation-results.md`

---

### E26-S3: Inject Docling Tables into Orchestrator Context [M — 3 SP]

**Scope**: Modify orchestrator to load and inject Docling tables into LLM context.

**File changes**:
| File | Change |
|------|--------|
| `open_notebook/extractors/orchestrator.py` | Add `_get_docling_tables()`, `_inject_docling_tables()` |
| `open_notebook/extractors/orchestrator.py` | Modify `extract_building()` to inject tables |
| `prompts/acm/building_extraction.j2` | Add structured table handling instruction |
| `tests/test_orchestrator_docling.py` | Unit tests for loading, injection, prompt changes |

**Acceptance criteria**:
1. Orchestrator loads `acm_table_section` records filtered by building page range
2. If Docling tables exist: DataFrame markdown appended to LLM context after full_text
3. If no Docling tables: existing behavior unchanged (full_text only)
4. Supplementary prompt instruction guides LLM to prioritize structured table data
5. "Same as", "Not Sampled", "No Access" rows explicitly mentioned in prompt
6. Integration test: full extraction with Docling tables produces >= 29 records

---

### E26-S4: Accuracy Validation — Target 30+/31 [S — 1 SP]

**Scope**: Full pipeline validation with decision gate.

**Acceptance criteria**:
1. Run full extraction pipeline on Broadmeadows with Docling tables ON
2. Cross-reference against ground truth CSV (31 records)
3. Decision gate:
   - >= 30/31 (96.8%) → **PROMOTE** flag to default `true`
   - 28-29/31 → investigate, document issues, keep flag `false`
   - < 28/31 → **ROLLBACK**, flag remains `false`
4. Alexander regression check: must maintain 54/54 (or explain variance)
5. Generate validation report: `docs/reviews/e26-s4-validation-results.md`
6. Record #9 (Switch Room / Battery Charger) must be captured (was missing in E23)

**Output**: `docs/reviews/e26-s4-validation-results.md`

---

### E26-S5: Frontend — Enhanced Raw Tables Display [S — 1 SP]

**Scope**: Verify and enhance Raw Tables tab with Docling data.

**Acceptance criteria**:
1. Raw Tables tab automatically displays Docling tables (from `acm_table_section`)
2. Verify HTML rendering quality (DataFrames produce clean `<table>` elements)
3. Verify markdown fallback works (for non-HTML consumers)
4. Optional: Add "Source" indicator showing `docling_direct_api` vs legacy
5. No regression in existing Raw Tables behavior for non-Docling sources

**Can run in parallel with S3-S4.**

---

### Effort Summary

| Story | Size | SP | Phase | Dependency |
|-------|------|----|-------|------------|
| E26-S1: Docling Direct API Extraction | M | 3 | 1 | None |
| E26-S2: DataFrame Validation | S | 1 | 1 | S1 |
| E26-S3: Orchestrator Context Injection | M | 3 | 2 | S1 |
| E26-S4: Accuracy Validation | S | 1 | 2 | S3 |
| E26-S5: Frontend Raw Tables | S | 1 | Parallel | S1 |
| **Total E26** | | **9 SP** | | |

### Critical Path

```
E26-S1 (Extraction) ──→ E26-S2 (DataFrame Validation) ──→ E26-S3 (Context Injection) ──→ E26-S4 (Accuracy Validation)
                    └──→ E26-S5 (Frontend) [parallel with S3-S4]
```

---

## Related Documents

- ADR: `docs/architecture/adr-tableformer-integration.md` (D5)
- E25 Spike Results: `docs/reviews/e25-table-extraction-comparison.md`
- E25 Raw Data: `research-output/e25/comparison_summary.json`
- E24 Validation (regression): `docs/reviews/e24-validation-results.md`
- E23 Baseline: `docs/reviews/e23-validation-results.md`
- D1-D4 Technical Design: `docs/architecture/tableformer-technical-design.md`
- Schema: `migrations/18.surrealql` (acm_table_section)
- Orchestrator: `open_notebook/extractors/orchestrator.py`
- Source Processing: `commands/source_commands.py`
