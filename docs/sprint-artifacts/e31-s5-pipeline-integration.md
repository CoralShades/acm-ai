# Tech Spec: E31-S5 — Pipeline Integration

**Sprint:** V3-4
**Story Points:** 3
**Risk:** HIGH
**Type:** Backend
**Status:** ready-for-dev
**Depends on:** E31-S3 (Consensus Layer Core — DONE), E31-S4 (Raw Extraction Table — DONE)

---

## 1. Problem Statement

E31-S3 and E31-S4 established the data structures needed for dual-provider extraction: the
`raw_extraction` table stores per-provider outputs, and `acm_table_section` now has
`consensus_tier` / `consensus_scores` columns. However, the pipeline in `commands/source_commands.py`
still runs only a single provider (Docling via `get_provider_registry().get_default()`) and
discards the MinerU provider entirely.

This story wires the two providers into a sequential execution pipeline with a page-level
consensus merge, so that:

1. Docling always runs first (lower VRAM, ~4 GB).
2. MinerU runs second when `V3_DUAL_PROVIDER=true` and `MINERU_ENABLED=true` (higher VRAM,
   ~10 GB), ensuring the GPU is not contended.
3. A pure merge function reconciles the two providers' table outputs page by page and assigns
   a `consensus_tier` to each merged table.
4. The merged tables are stored in `acm_table_section` with full consensus metadata.
5. Two new fallback contracts (F9 and F10) are added to the strategy registry to give the
   consensus merge formal telemetry tags.
6. A feature flag (`V3_DUAL_PROVIDER`) allows operators to revert to Docling-only mode
   without a code change.

---

## 2. Solution Design

### 2.1 Sequential GPU Execution Model

The providers **must not** run concurrently because both rely on GPU VRAM:

```
Docling extract (~4 GB VRAM)
     |
     v (complete)
_store_raw_extractions(source_id, docling_result)
     |
     v
[V3_DUAL_PROVIDER=true AND MINERU_ENABLED=true?]
     |  yes
     v
MinerU extract (~10 GB VRAM)
     |
     v (complete or ProviderError fallback)
_store_raw_extractions(source_id, mineru_result)
     |
     v
_merge_provider_tables(docling_result, mineru_result)
     |
     v
_store_docling_tables(source_id, merged_tables)
          (writes consensus_tier + consensus_scores)
```

When `V3_DUAL_PROVIDER=false` or `MINERU_ENABLED=false`, only Docling runs and all merged
tables receive `consensus_tier="single_provider"`.

### 2.2 Feature Flag: `V3_DUAL_PROVIDER`

Read dynamically from the environment at call time (not at module import time) so tests can
monkeypatch `os.environ` without reloading the module.

```python
# Module-level constant: documents the env var name only.
V3_DUAL_PROVIDER_ENV_VAR = "V3_DUAL_PROVIDER"
```

Effective value computed inside `_run_dual_provider_extraction()`:

```python
dual_enabled = (
    os.environ.get("V3_DUAL_PROVIDER_ENV_VAR", "true").lower() == "true"
    and os.environ.get("MINERU_ENABLED", "false").lower() == "true"
)
```

Default is `"true"` so existing deployments that already have `MINERU_ENABLED=true` will
automatically use dual-provider. Deployments with `MINERU_ENABLED=false` (default) are
unaffected — the flag has no effect when MinerU is disabled.

### 2.3 `_run_dual_provider_extraction()` — New Async Function

```python
async def _run_dual_provider_extraction(
    source_id: str,
    pdf_path: str,
    pipeline_logger: Optional[PipelineLogger] = None,
) -> List[Dict[str, Any]]:
    """
    Run Docling (always) then MinerU (if dual-provider enabled) sequentially.

    Returns a list of merged table dicts ready to pass to _store_docling_tables().
    Each dict contains: table_index, page, rows, columns, csv, markdown, html,
    consensus_tier, consensus_scores.
    """
    registry = get_provider_registry()

    # --- Step 1: Always run Docling first ---
    docling_provider = registry.get_provider("docling")
    docling_result = docling_provider.extract(
        pdf_path, pipeline_logger=pipeline_logger
    )
    await _store_raw_extractions(source_id, docling_result)

    # --- Step 2: Dual-provider gate ---
    dual_enabled = (
        os.environ.get("V3_DUAL_PROVIDER", "true").lower() == "true"
        and os.environ.get("MINERU_ENABLED", "false").lower() == "true"
    )

    if not dual_enabled:
        logger.info(
            "Dual-provider disabled (V3_DUAL_PROVIDER or MINERU_ENABLED off); "
            "using Docling-only tables."
        )
        return [
            {
                "table_index": t.table_index,
                "page": t.page,
                "rows": t.row_count,
                "columns": t.columns,
                "csv": t.csv,
                "markdown": t.markdown,
                "html": t.html,
                "consensus_tier": "single_provider",
                "consensus_scores": None,
            }
            for t in docling_result.tables
        ]

    # --- Step 3: Run MinerU second (GPU released by Docling by now) ---
    try:
        mineru_provider = registry.get_provider("mineru")
        mineru_result = mineru_provider.extract(pdf_path)
        await _store_raw_extractions(source_id, mineru_result)
    except ProviderError as e:
        logger.warning(
            f"MinerU extraction failed — falling back to Docling-only: {e}"
        )
        return [
            {
                "table_index": t.table_index,
                "page": t.page,
                "rows": t.row_count,
                "columns": t.columns,
                "csv": t.csv,
                "markdown": t.markdown,
                "html": t.html,
                "consensus_tier": "single_provider",
                "consensus_scores": None,
            }
            for t in docling_result.tables
        ]

    # --- Step 4: Merge and return ---
    return _merge_provider_tables(docling_result, mineru_result)
```

### 2.4 `_merge_provider_tables()` — New Pure Function

Pure function (no I/O, no async). Receives two `NormalizedExtractionResult` objects and
returns a list of merged table dicts.

**Grouping strategy:** tables are grouped by `page` number (integer). For each page:

- If only one provider has a table for this page: `consensus_tier = "single_provider"`.
- If both providers have a table for the same page: compute `row_divergence` and assign
  either `"multi_provider_agreement"` (F10) or `"multi_provider_conflict"` (F9).

**Row-divergence formula:**

```python
row_divergence = abs(d_rows - m_rows) / max(d_rows, m_rows)
# where d_rows = Docling table row_count, m_rows = MinerU table row_count
# Guard: if max(d_rows, m_rows) == 0, row_divergence = 0.0
```

**Threshold:** `row_divergence > 0.40` → conflict; `<= 0.40` → agreement.

**Field preference when both providers have data:**
- `html` field: prefer MinerU (richer merged-cell handling).
- `markdown` field: prefer Docling (normalization pipeline validated in E25-S1).
- `csv`: prefer Docling (DataFrame-generated, higher fidelity).
- `columns`: prefer Docling (same reason).
- `rows`: use Docling `row_count` for `rows` field (stored in `acm_table_section.raw_text`
  metadata; MinerU count goes into `consensus_scores`).

**Tables with `page <= 0` (unknown page number):** always `consensus_tier = "single_provider"`,
included as-is using whichever provider produced them. Unknown-page tables from Docling are
processed first, then unknown-page tables from MinerU that have no Docling counterpart are
appended.

**`consensus_scores` dict shape:**

```python
{
    "docling": d_rows / (d_rows + m_rows),   # Docling weight
    "mineru": m_rows / (d_rows + m_rows),    # MinerU weight
    "row_divergence": row_divergence,
    "agreement": 1.0 - row_divergence,
}
# Guard: if d_rows + m_rows == 0, all values set to 0.0
```

**Telemetry:** emit `FallbackId.F9_PROVIDER_CONFLICT` or `FallbackId.F10_CONSENSUS_ARBITRATION`
via `emit_fallback_telemetry()` for every page where both providers contributed.

**Function signature:**

```python
def _merge_provider_tables(
    docling_result: "NormalizedExtractionResult",
    mineru_result: "NormalizedExtractionResult",
) -> List[Dict[str, Any]]:
    ...
```

### 2.5 `_store_docling_tables()` — Extended to Write Consensus Fields

Currently stores `raw_html`, `raw_text`, `structured_json`, `table_type`, `building_name`.
After this story it also writes `consensus_tier` and `consensus_scores`:

```python
async def _store_docling_tables(source_id: str, tables: List[Dict[str, Any]]) -> None:
    """Store merged tables in acm_table_section with consensus metadata."""
    for table in tables:
        await repo_create(
            "acm_table_section",
            {
                "source_id": ensure_record_id(source_id),
                "page_start": table["page"],
                "page_end": table["page"],
                "raw_html": table.get("html"),
                "raw_text": table.get("markdown"),
                "structured_json": table.get("csv"),
                "table_type": "docling_direct_api",
                "building_name": None,
                "consensus_tier": table.get("consensus_tier"),
                "consensus_scores": table.get("consensus_scores"),
            },
        )
```

The `consensus_tier` and `consensus_scores` columns already exist in the database schema
(migration 42, E31-S4). No new migration is required.

### 2.6 `process_source_command()` — Replace Provider Call-Site

In the main command handler, replace the current single-provider block (lines ~353-379) with
a call to `_run_dual_provider_extraction()`:

**Before (current):**
```python
provider = get_provider_registry().get_default()
extraction_result = provider.extract(
    pdf_path, pipeline_logger=docling_pl
)
await _store_raw_extractions(str(processed_source.id), extraction_result)
docling_tables = [
    {
        "table_index": t.table_index,
        "page": t.page,
        "rows": t.row_count,
        "columns": t.columns,
        "csv": t.csv,
        "markdown": t.markdown,
        "html": t.html,
    }
    for t in extraction_result.tables
]
if docling_tables:
    await _store_docling_tables(
        str(processed_source.id), docling_tables
    )
```

**After (E31-S5):**
```python
# E31-S5: Dual-provider sequential extraction with consensus merge
merged_tables = await _run_dual_provider_extraction(
    source_id=str(processed_source.id),
    pdf_path=pdf_path,
    pipeline_logger=docling_pl,
)
if merged_tables:
    await _store_docling_tables(
        str(processed_source.id), merged_tables
    )
    logger.info(
        f"Stored {len(merged_tables)} consensus tables "
        f"for source {processed_source.id}"
    )
```

### 2.7 Strategy Registry — Add F9 and F10

Extend `FallbackId` enum with two new members, and add corresponding `FallbackContract`
entries to `FALLBACK_MATRIX`.

**New enum members:**

```python
F9_PROVIDER_CONFLICT = "fallback.provider_conflict"
F10_CONSENSUS_ARBITRATION = "fallback.consensus_arbitration"
```

**New FALLBACK_MATRIX entries:**

```python
FallbackId.F9_PROVIDER_CONFLICT: FallbackContract(
    id=FallbackId.F9_PROVIDER_CONFLICT,
    detection="Two providers return tables for same page with row_divergence > 0.40",
    behavior="Set consensus_tier='multi_provider_conflict'; prefer MinerU HTML + Docling markdown",
    severity="non-fatal (degraded confidence)",
    telemetry_tag="fallback.provider_conflict",
    retry_eligible=False,
),
FallbackId.F10_CONSENSUS_ARBITRATION: FallbackContract(
    id=FallbackId.F10_CONSENSUS_ARBITRATION,
    detection="MinerU result used to arbitrate table on page where both providers returned tables",
    behavior="MinerU HTML chosen as primary raw_html; consensus_tier='multi_provider_agreement'",
    severity="informational",
    telemetry_tag="fallback.consensus_arbitration",
    retry_eligible=False,
),
```

---

## 3. File Changes Table

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/extractors/strategy_registry.py` | MODIFY | Add `F9_PROVIDER_CONFLICT` and `F10_CONSENSUS_ARBITRATION` to `FallbackId` enum and `FALLBACK_MATRIX` dict |
| `commands/source_commands.py` | MODIFY | Add `V3_DUAL_PROVIDER_ENV_VAR` constant; add `_run_dual_provider_extraction()` async function; add `_merge_provider_tables()` pure function; update `_store_docling_tables()` to write `consensus_tier`/`consensus_scores`; replace provider call-site in `process_source_command()` |
| `tests/test_dual_provider_pipeline.py` | CREATE | New test file covering feature flag, dual extraction, merge logic, storage, and registry |
| `tests/test_strategy_registry.py` | MODIFY | Update count assertion from 8 to 10 in `test_fallback_matrix_has_all_eight_entries`; add two new test classes for F9/F10 |

---

## 4. Implementation Steps

### Step 1 — Extend `strategy_registry.py` with F9 and F10

**1a. Add enum members.** In `open_notebook/extractors/strategy_registry.py`, append to
the `FallbackId` enum body immediately after `F8_DOCLING_FAILURE`:

```python
    F9_PROVIDER_CONFLICT = "fallback.provider_conflict"
    F10_CONSENSUS_ARBITRATION = "fallback.consensus_arbitration"
```

**1b. Add FALLBACK_MATRIX entries.** Append to the `FALLBACK_MATRIX` dict immediately after
the `F8_DOCLING_FAILURE` entry (before the closing `}`):

```python
    FallbackId.F9_PROVIDER_CONFLICT: FallbackContract(
        id=FallbackId.F9_PROVIDER_CONFLICT,
        detection="Two providers return tables for same page with row_divergence > 0.40",
        behavior="Set consensus_tier='multi_provider_conflict'; prefer MinerU HTML + Docling markdown",
        severity="non-fatal (degraded confidence)",
        telemetry_tag="fallback.provider_conflict",
        retry_eligible=False,
    ),
    FallbackId.F10_CONSENSUS_ARBITRATION: FallbackContract(
        id=FallbackId.F10_CONSENSUS_ARBITRATION,
        detection="MinerU result used to arbitrate table on page where both providers returned tables",
        behavior="MinerU HTML chosen as primary raw_html; consensus_tier='multi_provider_agreement'",
        severity="informational",
        telemetry_tag="fallback.consensus_arbitration",
        retry_eligible=False,
    ),
```

### Step 2 — Add `_merge_provider_tables()` to `source_commands.py`

Insert the following pure function immediately **after** `_store_raw_extractions()` (currently
ending around line 237) and **before** the `@command` decorator for `process_source_command`:

```python
def _merge_provider_tables(
    docling_result: "NormalizedExtractionResult",
    mineru_result: "NormalizedExtractionResult",
) -> List[Dict[str, Any]]:
    """
    Merge per-provider table outputs into a unified list for acm_table_section storage.

    Pure function — no I/O, no async. Groups tables by page number and computes
    row_divergence to assign a consensus_tier to each merged table.

    Args:
        docling_result: NormalizedExtractionResult from DoclingAdapter.extract().
        mineru_result: NormalizedExtractionResult from MinerUAdapter.extract().

    Returns:
        List of table dicts with keys: table_index, page, rows, columns, csv,
        markdown, html, consensus_tier, consensus_scores.
    """
    from open_notebook.extractors.strategy_registry import (
        FallbackId,
        emit_fallback_telemetry,
    )

    # Index by page number; page <= 0 means unknown — handle separately
    docling_by_page: Dict[int, Any] = {}
    mineru_by_page: Dict[int, Any] = {}

    unknown_docling = []
    unknown_mineru = []

    for t in docling_result.tables:
        if t.page > 0:
            docling_by_page[t.page] = t
        else:
            unknown_docling.append(t)

    for t in mineru_result.tables:
        if t.page > 0:
            mineru_by_page[t.page] = t
        else:
            unknown_mineru.append(t)

    merged: List[Dict[str, Any]] = []
    all_pages = sorted(set(docling_by_page.keys()) | set(mineru_by_page.keys()))

    for page in all_pages:
        d_table = docling_by_page.get(page)
        m_table = mineru_by_page.get(page)

        if d_table and not m_table:
            # Only Docling has this page
            merged.append({
                "table_index": d_table.table_index,
                "page": page,
                "rows": d_table.row_count,
                "columns": d_table.columns,
                "csv": d_table.csv,
                "markdown": d_table.markdown,
                "html": d_table.html,
                "consensus_tier": "single_provider",
                "consensus_scores": None,
            })

        elif m_table and not d_table:
            # Only MinerU has this page
            merged.append({
                "table_index": m_table.table_index,
                "page": page,
                "rows": m_table.row_count,
                "columns": m_table.columns,
                "csv": m_table.csv,
                "markdown": m_table.markdown,
                "html": m_table.html,
                "consensus_tier": "single_provider",
                "consensus_scores": None,
            })

        else:
            # Both providers have this page — compute consensus
            d_rows = d_table.row_count  # type: ignore[union-attr]
            m_rows = m_table.row_count  # type: ignore[union-attr]

            denom = max(d_rows, m_rows)
            row_divergence = abs(d_rows - m_rows) / denom if denom > 0 else 0.0
            total_rows = d_rows + m_rows
            scores = {
                "docling": d_rows / total_rows if total_rows > 0 else 0.0,
                "mineru": m_rows / total_rows if total_rows > 0 else 0.0,
                "row_divergence": row_divergence,
                "agreement": 1.0 - row_divergence,
            }

            if row_divergence > 0.40:
                consensus_tier = "multi_provider_conflict"
                emit_fallback_telemetry(
                    FallbackId.F9_PROVIDER_CONFLICT,
                    building_name=f"page={page}",
                    reason=f"row_divergence={row_divergence:.3f} (docling={d_rows}, mineru={m_rows})",
                )
            else:
                consensus_tier = "multi_provider_agreement"
                emit_fallback_telemetry(
                    FallbackId.F10_CONSENSUS_ARBITRATION,
                    building_name=f"page={page}",
                    reason=f"row_divergence={row_divergence:.3f} — MinerU HTML preferred",
                )

            merged.append({
                "table_index": d_table.table_index,  # type: ignore[union-attr]
                "page": page,
                "rows": d_rows,
                "columns": d_table.columns,  # type: ignore[union-attr]
                "csv": d_table.csv,  # type: ignore[union-attr]
                "markdown": d_table.markdown,  # type: ignore[union-attr]
                "html": m_table.html or d_table.html,  # Prefer MinerU HTML  # type: ignore[union-attr]
                "consensus_tier": consensus_tier,
                "consensus_scores": scores,
            })

    # Append unknown-page tables (page <= 0), Docling first, then MinerU
    _table_counter = len(merged)
    for t in unknown_docling:
        merged.append({
            "table_index": _table_counter,
            "page": t.page,
            "rows": t.row_count,
            "columns": t.columns,
            "csv": t.csv,
            "markdown": t.markdown,
            "html": t.html,
            "consensus_tier": "single_provider",
            "consensus_scores": None,
        })
        _table_counter += 1

    for t in unknown_mineru:
        merged.append({
            "table_index": _table_counter,
            "page": t.page,
            "rows": t.row_count,
            "columns": t.columns,
            "csv": t.csv,
            "markdown": t.markdown,
            "html": t.html,
            "consensus_tier": "single_provider",
            "consensus_scores": None,
        })
        _table_counter += 1

    logger.info(
        f"_merge_provider_tables: {len(merged)} merged tables "
        f"(docling={len(docling_result.tables)}, mineru={len(mineru_result.tables)})"
    )
    return merged
```

### Step 3 — Add `_run_dual_provider_extraction()` to `source_commands.py`

Insert immediately after `_merge_provider_tables()` (before `@command`):

```python
async def _run_dual_provider_extraction(
    source_id: str,
    pdf_path: str,
    pipeline_logger: Optional[PipelineLogger] = None,
) -> List[Dict[str, Any]]:
    """
    Run Docling then (optionally) MinerU sequentially to prevent VRAM contention.

    Returns merged table dicts ready for _store_docling_tables().
    When dual-provider is disabled, returns Docling-only tables with
    consensus_tier='single_provider'.

    Args:
        source_id: Fully qualified source record ID (e.g. 'source:abc123').
        pdf_path: Absolute path to the PDF file on disk.
        pipeline_logger: Optional PipelineLogger for stage observability.

    Returns:
        List of merged table dicts (see _merge_provider_tables for shape).
    """
    registry = get_provider_registry()

    # Step 1: Always run Docling first
    docling_provider = registry.get_provider("docling")
    docling_result = docling_provider.extract(
        pdf_path, pipeline_logger=pipeline_logger
    )
    await _store_raw_extractions(source_id, docling_result)
    logger.info(
        f"Docling extracted {len(docling_result.tables)} tables "
        f"from {pdf_path}"
    )

    # Step 2: Check dual-provider gate
    dual_enabled = (
        os.environ.get("V3_DUAL_PROVIDER", "true").lower() == "true"
        and os.environ.get("MINERU_ENABLED", "false").lower() == "true"
    )

    if not dual_enabled:
        logger.info(
            "Dual-provider disabled (V3_DUAL_PROVIDER or MINERU_ENABLED not set); "
            "returning Docling-only results."
        )
        return [
            {
                "table_index": t.table_index,
                "page": t.page,
                "rows": t.row_count,
                "columns": t.columns,
                "csv": t.csv,
                "markdown": t.markdown,
                "html": t.html,
                "consensus_tier": "single_provider",
                "consensus_scores": None,
            }
            for t in docling_result.tables
        ]

    # Step 3: Run MinerU second (GPU released by Docling at this point)
    try:
        mineru_provider = registry.get_provider("mineru")
        mineru_result = mineru_provider.extract(pdf_path)
        await _store_raw_extractions(source_id, mineru_result)
        logger.info(
            f"MinerU extracted {len(mineru_result.tables)} tables "
            f"from {pdf_path}"
        )
    except ProviderError as e:
        logger.warning(
            f"MinerU extraction failed — falling back to Docling-only: {e}"
        )
        return [
            {
                "table_index": t.table_index,
                "page": t.page,
                "rows": t.row_count,
                "columns": t.columns,
                "csv": t.csv,
                "markdown": t.markdown,
                "html": t.html,
                "consensus_tier": "single_provider",
                "consensus_scores": None,
            }
            for t in docling_result.tables
        ]

    # Step 4: Merge results
    return _merge_provider_tables(docling_result, mineru_result)
```

### Step 4 — Update `_store_docling_tables()` in `source_commands.py`

Replace the existing function body (lines 163-178) to add `consensus_tier` and
`consensus_scores` to the `repo_create` call:

```python
async def _store_docling_tables(source_id: str, tables: List[Dict[str, Any]]) -> None:
    """Store merged provider tables in acm_table_section with consensus metadata."""
    for table in tables:
        await repo_create(
            "acm_table_section",
            {
                "source_id": ensure_record_id(source_id),
                "page_start": table["page"],
                "page_end": table["page"],
                "raw_html": table.get("html"),
                "raw_text": table.get("markdown"),
                "structured_json": table.get("csv"),
                "table_type": "docling_direct_api",
                "building_name": None,
                "consensus_tier": table.get("consensus_tier"),
                "consensus_scores": table.get("consensus_scores"),
            },
        )
```

### Step 5 — Replace provider call-site in `process_source_command()`

In the `process_source_command` function, locate the block inside the
`if DOCLING_DIRECT_TABLE_EXTRACTION:` branch (currently lines ~353-393). Replace the inner
`try` block contents with the `_run_dual_provider_extraction()` call:

```python
if DOCLING_DIRECT_TABLE_EXTRACTION:
    pdf_path = _resolve_source_pdf_path(processed_source)
    if pdf_path and pdf_path.lower().endswith(".pdf"):
        docling_command_id = (
            str(input_data.execution_context.command_id)
            if input_data.execution_context
            else None
        )
        docling_pl = PipelineLogger(
            source_id=str(processed_source.id),
            command_id=docling_command_id,
        )
        try:
            # E31-S5: Dual-provider sequential extraction with consensus merge
            merged_tables = await _run_dual_provider_extraction(
                source_id=str(processed_source.id),
                pdf_path=pdf_path,
                pipeline_logger=docling_pl,
            )
            if merged_tables:
                await _store_docling_tables(
                    str(processed_source.id), merged_tables
                )
                logger.info(
                    f"Stored {len(merged_tables)} consensus tables "
                    f"for source {processed_source.id}"
                )
        except ProviderError as e:
            docling_pl.stage_fail(
                StageId.DOCLING_EXTRACTION,
                error=str(e),
            )
            logger.error(f"Docling table extraction failed: {e}")
            # Non-fatal — PyMuPDF text is already saved
        except Exception as e:
            docling_pl.stage_fail(
                StageId.DOCLING_EXTRACTION,
                error=str(e),
            )
            logger.error(f"Unexpected error during table extraction: {e}")
            # Non-fatal — PyMuPDF text is already saved
```

### Step 6 — Update `tests/test_strategy_registry.py`

**6a.** Rename the existing count-assertion test to reflect the new total, and update the
count from 8 to 10:

```python
def test_fallback_matrix_has_all_ten_entries(self):
    """All 10 fallback scenarios (F1-F10) are present in the matrix."""
    assert len(FALLBACK_MATRIX) == 10
```

**6b.** Add two new test classes after `TestDoclingFailureFallback`:

```python
class TestProviderConflictFallback:
    def test_provider_conflict_fallback_exists(self):
        """F9 contract exists — conflict tier, MinerU HTML preferred."""
        contract = FALLBACK_MATRIX[FallbackId.F9_PROVIDER_CONFLICT]
        assert "conflict" in contract.behavior.lower()
        assert contract.severity == "non-fatal (degraded confidence)"
        assert contract.retry_eligible is False

    def test_provider_conflict_telemetry_tag(self):
        contract = FALLBACK_MATRIX[FallbackId.F9_PROVIDER_CONFLICT]
        assert contract.telemetry_tag == "fallback.provider_conflict"


class TestConsensusArbitrationFallback:
    def test_consensus_arbitration_fallback_exists(self):
        """F10 contract exists — informational, MinerU HTML chosen."""
        contract = FALLBACK_MATRIX[FallbackId.F10_CONSENSUS_ARBITRATION]
        assert "mineru" in contract.behavior.lower()
        assert contract.severity == "informational"
        assert contract.retry_eligible is False

    def test_consensus_arbitration_telemetry_tag(self):
        contract = FALLBACK_MATRIX[FallbackId.F10_CONSENSUS_ARBITRATION]
        assert contract.telemetry_tag == "fallback.consensus_arbitration"
```

### Step 7 — Create `tests/test_dual_provider_pipeline.py`

Create this file from scratch. See Section 6 (Test Plan) for the full test content.

---

## 5. Acceptance Criteria Mapping

| AC | Requirement | Satisfied By |
|----|-------------|--------------|
| AC1 | Orchestrator runs providers sequentially: Docling first, then MinerU hybrid | `_run_dual_provider_extraction()` — Docling completes before MinerU starts |
| AC2 | Sequential GPU execution to prevent VRAM contention | No concurrent `await` across provider calls; Docling `extract()` is synchronous, MinerU starts only after `_store_raw_extractions()` returns |
| AC3 | Raw results stored in `raw_extraction` per provider (already done in E31-S4) | `_store_raw_extractions()` called after each provider run in `_run_dual_provider_extraction()` |
| AC4 | Consensus engine merges results into unified `acm_table_section` | `_merge_provider_tables()` + updated `_store_docling_tables()` writing `consensus_tier`/`consensus_scores` |
| AC5 | Consensus telemetry emitted via PipelineLogger / emit_fallback_telemetry | `emit_fallback_telemetry(F9 or F10, ...)` called inside `_merge_provider_tables()` for every dual-provider page |
| AC6 | Strategy registry extended with F9 and F10 | Step 1: `FallbackId` enum + `FALLBACK_MATRIX` entries in `strategy_registry.py` |
| AC7 | Feature flag `V3_DUAL_PROVIDER=true` (default) — can disable MinerU to fall back to Docling-only | `dual_enabled` gate in `_run_dual_provider_extraction()`; default `"true"` safely combined with `MINERU_ENABLED` default `"false"` |
| AC8 | Integration test: upload PDF -> dual extraction -> consensus -> merged table sections | `TestRunDualProviderExtraction.test_dual_extraction_produces_merged_tables` (mocked end-to-end) |

---

## 6. Test Plan

File: `tests/test_dual_provider_pipeline.py`

All tests use `unittest.mock` patches. No live SurrealDB or GPU required.

### 6.1 `TestDualProviderFeatureFlag`

Tests for the `V3_DUAL_PROVIDER` + `MINERU_ENABLED` interaction.

**`test_dual_disabled_when_v3_flag_false`**
```python
@pytest.mark.asyncio
@patch.dict(os.environ, {"V3_DUAL_PROVIDER": "false", "MINERU_ENABLED": "true"})
@patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
@patch("commands.source_commands.get_provider_registry")
async def test_dual_disabled_when_v3_flag_false(mock_registry, mock_store):
    """When V3_DUAL_PROVIDER=false, only Docling runs."""
    from commands.source_commands import _run_dual_provider_extraction
    from open_notebook.extractors.providers.base import NormalizedExtractionResult, NormalizedTable

    mock_docling = MagicMock()
    mock_docling.extract.return_value = NormalizedExtractionResult(
        provider_id="docling",
        tables=[NormalizedTable(table_index=0, page=1, row_count=5, col_count=3,
                                columns=["A","B","C"], html="<table/>", markdown="")],
    )
    mock_registry.return_value.get_provider.return_value = mock_docling

    result = await _run_dual_provider_extraction("source:abc", "/tmp/test.pdf")

    assert len(result) == 1
    assert result[0]["consensus_tier"] == "single_provider"
    # MinerU should NOT have been called
    assert mock_docling.extract.call_count == 1
```

**`test_dual_disabled_when_mineru_disabled`**
- Same pattern but `V3_DUAL_PROVIDER=true`, `MINERU_ENABLED=false`
- Assert only one extract call and all tables have `consensus_tier="single_provider"`

**`test_dual_enabled_when_both_flags_true`**
- `V3_DUAL_PROVIDER=true`, `MINERU_ENABLED=true`
- Two providers registered; both return one table each on different pages
- Assert `get_provider` called twice (once for "docling", once for "mineru")

**`test_v3_flag_defaults_to_true`**
- Unset `V3_DUAL_PROVIDER` from environment
- Verify that with `MINERU_ENABLED=true`, MinerU provider IS requested

### 6.2 `TestRunDualProviderExtraction`

**`test_docling_runs_first_then_mineru`**
```python
@pytest.mark.asyncio
@patch.dict(os.environ, {"V3_DUAL_PROVIDER": "true", "MINERU_ENABLED": "true"})
@patch("commands.source_commands._store_raw_extractions", new_callable=AsyncMock)
@patch("commands.source_commands.get_provider_registry")
async def test_docling_runs_first_then_mineru(mock_registry, mock_store):
    """Docling extract is called before MinerU extract (sequential execution)."""
    from commands.source_commands import _run_dual_provider_extraction
    from open_notebook.extractors.providers.base import NormalizedExtractionResult

    call_order = []
    docling_mock = MagicMock()
    mineru_mock = MagicMock()

    def docling_extract(*args, **kwargs):
        call_order.append("docling")
        return NormalizedExtractionResult(provider_id="docling", tables=[])

    def mineru_extract(*args, **kwargs):
        call_order.append("mineru")
        return NormalizedExtractionResult(provider_id="mineru", tables=[])

    docling_mock.extract.side_effect = docling_extract
    mineru_mock.extract.side_effect = mineru_extract

    def get_provider(pid):
        if pid == "docling":
            return docling_mock
        return mineru_mock

    mock_registry.return_value.get_provider.side_effect = get_provider

    await _run_dual_provider_extraction("source:abc", "/tmp/test.pdf")

    assert call_order == ["docling", "mineru"]
```

**`test_mineru_failure_falls_back_to_docling_only`**
- MinerU raises `ProviderError`
- Assert result contains only Docling tables with `consensus_tier="single_provider"`
- Assert `_store_raw_extractions` called once (Docling), not twice

**`test_raw_extractions_stored_for_each_provider`**
- Both providers succeed, each with one table
- Assert `_store_raw_extractions` called twice (once per provider)

**`test_dual_extraction_produces_merged_tables`** (AC8 integration test proxy)
- Docling returns 2 tables (pages 1, 2); MinerU returns 2 tables (pages 1, 3)
- Page 1: both providers — should be merged (agreement or conflict)
- Page 2: Docling only — `consensus_tier="single_provider"`
- Page 3: MinerU only — `consensus_tier="single_provider"`
- Assert `len(result) == 3`

### 6.3 `TestMergeProviderTables`

Pure function tests — no async, no mocks needed.

**`test_agreement_tier_when_row_divergence_low`**
```python
def test_agreement_tier_when_row_divergence_low():
    """row_divergence <= 0.40 → multi_provider_agreement."""
    from commands.source_commands import _merge_provider_tables
    from open_notebook.extractors.providers.base import NormalizedExtractionResult, NormalizedTable

    docling = NormalizedExtractionResult(
        provider_id="docling",
        tables=[NormalizedTable(table_index=0, page=2, row_count=10, col_count=3,
                                columns=["A","B","C"], html="<d/>", markdown="d")],
    )
    mineru = NormalizedExtractionResult(
        provider_id="mineru",
        tables=[NormalizedTable(table_index=0, page=2, row_count=9, col_count=3,
                                columns=["A","B","C"], html="<m/>", markdown="m")],
    )
    result = _merge_provider_tables(docling, mineru)
    assert len(result) == 1
    assert result[0]["consensus_tier"] == "multi_provider_agreement"
    assert result[0]["html"] == "<m/>"   # MinerU HTML preferred
    assert result[0]["markdown"] == "d"  # Docling markdown preferred
```

**`test_conflict_tier_when_row_divergence_high`**
```python
def test_conflict_tier_when_row_divergence_high():
    """row_divergence > 0.40 → multi_provider_conflict."""
    from commands.source_commands import _merge_provider_tables
    from open_notebook.extractors.providers.base import NormalizedExtractionResult, NormalizedTable

    docling = NormalizedExtractionResult(
        provider_id="docling",
        tables=[NormalizedTable(table_index=0, page=1, row_count=20, col_count=2,
                                columns=["A","B"], html="<d/>", markdown="d")],
    )
    mineru = NormalizedExtractionResult(
        provider_id="mineru",
        tables=[NormalizedTable(table_index=0, page=1, row_count=5, col_count=2,
                                columns=["A","B"], html="<m/>", markdown="m")],
    )
    result = _merge_provider_tables(docling, mineru)
    assert len(result) == 1
    assert result[0]["consensus_tier"] == "multi_provider_conflict"
    # row_divergence = |20-5| / 20 = 0.75 > 0.40
```

**`test_single_provider_for_page_with_only_docling`**
```python
def test_single_provider_for_page_with_only_docling():
    """Page with only Docling table gets consensus_tier='single_provider'."""
    from commands.source_commands import _merge_provider_tables
    from open_notebook.extractors.providers.base import NormalizedExtractionResult, NormalizedTable

    docling = NormalizedExtractionResult(
        provider_id="docling",
        tables=[NormalizedTable(table_index=0, page=5, row_count=3, col_count=2,
                                columns=["A","B"], html="<d/>", markdown="d")],
    )
    mineru = NormalizedExtractionResult(provider_id="mineru", tables=[])
    result = _merge_provider_tables(docling, mineru)
    assert len(result) == 1
    assert result[0]["consensus_tier"] == "single_provider"
    assert result[0]["consensus_scores"] is None
```

**`test_single_provider_for_page_with_only_mineru`**
- MinerU-only page → `consensus_tier="single_provider"`

**`test_unknown_page_tables_always_single_provider`**
```python
def test_unknown_page_tables_always_single_provider():
    """Tables with page=-1 receive consensus_tier='single_provider'."""
    from commands.source_commands import _merge_provider_tables
    from open_notebook.extractors.providers.base import NormalizedExtractionResult, NormalizedTable

    docling = NormalizedExtractionResult(
        provider_id="docling",
        tables=[NormalizedTable(table_index=0, page=-1, row_count=2, col_count=2,
                                columns=["A","B"], html="<d/>", markdown="d")],
    )
    mineru = NormalizedExtractionResult(
        provider_id="mineru",
        tables=[NormalizedTable(table_index=0, page=-1, row_count=2, col_count=2,
                                columns=["A","B"], html="<m/>", markdown="m")],
    )
    result = _merge_provider_tables(docling, mineru)
    # Both unknown-page tables appended as single_provider (no page-based grouping)
    assert all(r["consensus_tier"] == "single_provider" for r in result)
```

**`test_consensus_scores_values_correct`**
- Docling: 10 rows, MinerU: 10 rows (same)
- `row_divergence = 0.0`, `agreement = 1.0`
- `docling = 0.5`, `mineru = 0.5`

**`test_consensus_scores_zero_rows_guard`**
- Both providers return 0 rows
- Assert no ZeroDivisionError; all score values = 0.0

**`test_mineru_html_preferred_over_docling_html`**
- Docling html="docling-html", MinerU html="mineru-html"
- Assert merged table's `html == "mineru-html"`

**`test_docling_markdown_preferred_over_mineru_markdown`**
- Docling markdown="docling-md", MinerU markdown="mineru-md"
- Assert merged table's `markdown == "docling-md"`

**`test_fallback_to_docling_html_when_mineru_html_empty`**
- MinerU html="" (empty string) → merged table's `html` falls back to Docling's html

**`test_multiple_pages_merged_correctly`**
- Docling: pages [1, 2, 3]; MinerU: pages [1, 3, 4]
- Page 1: merged; Page 2: docling-only; Page 3: merged; Page 4: mineru-only
- Assert `len(result) == 4`

### 6.4 `TestStorageWithConsensus`

**`test_store_docling_tables_writes_consensus_tier`**
```python
@pytest.mark.asyncio
@patch("commands.source_commands.repo_create", new_callable=AsyncMock)
async def test_store_docling_tables_writes_consensus_tier(mock_create):
    """_store_docling_tables passes consensus_tier to repo_create."""
    from commands.source_commands import _store_docling_tables

    tables = [{
        "page": 3,
        "html": "<table/>",
        "markdown": "md",
        "csv": "a,b",
        "consensus_tier": "multi_provider_agreement",
        "consensus_scores": {"docling": 0.5, "mineru": 0.5, "agreement": 1.0, "row_divergence": 0.0},
    }]
    await _store_docling_tables("source:abc", tables)

    mock_create.assert_called_once()
    call_kwargs = mock_create.call_args[0][1]
    assert call_kwargs["consensus_tier"] == "multi_provider_agreement"
    assert call_kwargs["consensus_scores"]["agreement"] == 1.0
```

**`test_store_docling_tables_writes_none_consensus_for_single_provider`**
```python
@pytest.mark.asyncio
@patch("commands.source_commands.repo_create", new_callable=AsyncMock)
async def test_store_docling_tables_none_consensus(mock_create):
    """Single-provider tables store consensus_tier='single_provider' and scores=None."""
    from commands.source_commands import _store_docling_tables

    tables = [{
        "page": 1,
        "html": "<table/>",
        "markdown": "md",
        "csv": None,
        "consensus_tier": "single_provider",
        "consensus_scores": None,
    }]
    await _store_docling_tables("source:abc", tables)

    call_kwargs = mock_create.call_args[0][1]
    assert call_kwargs["consensus_tier"] == "single_provider"
    assert call_kwargs["consensus_scores"] is None
```

### 6.5 `TestStrategyRegistryF9F10`

**`test_f9_and_f10_exist_in_matrix`**
```python
def test_f9_and_f10_exist_in_matrix():
    from open_notebook.extractors.strategy_registry import FALLBACK_MATRIX, FallbackId
    assert FallbackId.F9_PROVIDER_CONFLICT in FALLBACK_MATRIX
    assert FallbackId.F10_CONSENSUS_ARBITRATION in FALLBACK_MATRIX
```

**`test_fallback_matrix_now_has_ten_entries`**
```python
def test_fallback_matrix_now_has_ten_entries():
    from open_notebook.extractors.strategy_registry import FALLBACK_MATRIX
    assert len(FALLBACK_MATRIX) == 10
```

**`test_f9_is_non_fatal_non_retry`**
```python
def test_f9_is_non_fatal_non_retry():
    from open_notebook.extractors.strategy_registry import FALLBACK_MATRIX, FallbackId
    contract = FALLBACK_MATRIX[FallbackId.F9_PROVIDER_CONFLICT]
    assert contract.retry_eligible is False
    assert "non-fatal" in contract.severity
```

**`test_f10_is_informational_non_retry`**
```python
def test_f10_is_informational_non_retry():
    from open_notebook.extractors.strategy_registry import FALLBACK_MATRIX, FallbackId
    contract = FALLBACK_MATRIX[FallbackId.F10_CONSENSUS_ARBITRATION]
    assert contract.retry_eligible is False
    assert contract.severity == "informational"
```

**`test_all_ten_fallback_ids_in_matrix`**
```python
def test_all_ten_fallback_ids_in_matrix():
    from open_notebook.extractors.strategy_registry import FALLBACK_MATRIX, FallbackId
    for fid in FallbackId:
        assert fid in FALLBACK_MATRIX, f"{fid} missing from FALLBACK_MATRIX"
```

---

## 7. Verification Protocol

Before marking this story complete, the implementing agent MUST run:

```bash
cd "D:/ailocal/acm-ai"
uv run ruff check . --fix
uv run ruff format .
uv run pytest tests/test_dual_provider_pipeline.py -v
uv run pytest tests/test_strategy_registry.py -v
```

All tests must pass (green). Ruff must report zero errors.

Additionally verify file state:

```
open_notebook/extractors/strategy_registry.py  -- FallbackId has F9 and F10; FALLBACK_MATRIX has 10 entries
commands/source_commands.py                    -- _run_dual_provider_extraction() present
commands/source_commands.py                    -- _merge_provider_tables() present
commands/source_commands.py                    -- _store_docling_tables() writes consensus_tier + consensus_scores
commands/source_commands.py                    -- process_source_command uses _run_dual_provider_extraction()
tests/test_dual_provider_pipeline.py           -- created with >= 20 test functions
tests/test_strategy_registry.py               -- count assertion updated to 10
```

---

## 8. Risk Notes

**Risk: HIGH** — This story modifies the hot path of `process_source_command`, the single most
critical function in the worker. The following mitigations are in place:

1. **Non-fatal ProviderError handling preserved.** The outer `try/except ProviderError` block
   in `process_source_command` is kept. If `_run_dual_provider_extraction` itself raises
   unexpectedly, PyMuPDF full_text is already saved and the command can report partial success.

2. **MinerU failure is non-fatal.** Inside `_run_dual_provider_extraction`, a `ProviderError`
   from MinerU falls back to Docling-only result — it does not propagate up.

3. **Feature flag allows instant rollback.** Setting `V3_DUAL_PROVIDER=false` in `.env`
   immediately reverts to single-provider behavior without a deployment.

4. **Pre-existing test failure is not regressions.** The known failure in
   `test_source_commands_docling.py::test_creates_acm_table_section_records` (RecordID vs
   string assertion) is pre-existing (E31-S4 era) and is not caused by E31-S5 changes.

5. **No migration needed.** The `consensus_tier` and `consensus_scores` columns on
   `acm_table_section` were created in migration 42 (E31-S4). This story only writes to
   them — no schema change is required.

---

## 9. Out of Scope

- Any frontend display of `consensus_tier` or `consensus_scores` (deferred to E33 stories)
- Post-LLM `ACMExtractionRecord` consensus (that is the E31-S3 `ConsensusEngine` concern,
  which operates after the LLM has run — this story's consensus is pre-LLM at the
  `NormalizedTable` / `acm_table_section` level)
- MinerU VRAM profiling or automatic threshold tuning
- Writing to the `officer_edits` field (populated in a future review UI story)
- Parallel provider execution (explicitly out of scope due to VRAM contention risk)
