# ADR-001: Table Extraction Strategy — TableFormer Activation

| Field       | Value                                        |
|-------------|----------------------------------------------|
| **Status**  | Proposed                                     |
| **Date**    | 2026-02-27                                   |
| **Authors** | Winston (Architect), Mary (Research Spike)   |
| **Deciders**| Demi (Owner)                                 |

---

## Context

### Current State

ACM-AI extracts Asbestos Containing Material records from PDF survey reports.
The extraction pipeline is:

```
PDF → Docling (markdown only) → source.full_text → LLM extraction → ACMRecord
```

Docling converts PDFs to markdown text with **basic table rendering**. The LLM
(Claude via OpenRouter) receives this markdown and extracts structured records.
Current accuracy on the Broadmeadows benchmark: **28/31 (90.3%)**.

The 3 missing records are all "Not Sampled" / "No Access" entries that appear
in the PDF as table rows with minimal data. The LLM fails to extract them because
the Docling markdown poorly represents merged cells, sparse rows, and multi-line
column values.

### Research Findings (Mary's Spike, 2026-02-27)

1. **TableFormer is already in the dependency chain.** Docling bundles TableFormer
   but it requires explicit activation. torch 2.10.0 is confirmed installed.
2. **Activation is configuration-only.** Three `content_state` keys in
   `source.py:content_process()` — no new dependencies, no new library.
3. **Expected accuracy improvement:** 90.3% → 97–100% (30–31/31).
4. **Processing time impact:** +15–30s per PDF (from ~5s to ~20–35s).
5. **Memory impact:** +2–4 GB during table inference.
6. **Automatic fallback:** If TableFormer fails, Docling falls back to basic
   markdown with no intervention required.

### Competing Alternatives

| Option | Accuracy | Dependencies | Effort | Risk |
|--------|----------|-------------|--------|------|
| **Status Quo** (Docling markdown) | 90.3% | None new | 0 | None |
| **TableFormer** (activate Docling) | 97–100% (projected) | Already installed | Config change | Low |
| **MinerU** (fix dead code) | Unknown | Needs paddle, GPU | Major rebuild | High |
| **External OCR** (e.g., Textract) | Unknown | New SaaS dependency | Medium | Medium |

### MinerU Dead Code Inventory

| File | Lines | Tests | Status |
|------|-------|-------|--------|
| `open_notebook/extractors/mineru_table_extractor.py` | 557 | 1 file (37 tests in `test_mineru_table_extractor.py`) |  Dead — `magic_pdf` import fails (no paddle) |
| `open_notebook/extractors/acm_extractor.py` (`_extract_with_mineru()`) | ~40 | 5 tests in `test_acm_extractor.py` | Dead — returns `[]` with TODO |
| `commands/source_commands.py` (`_store_mineru_tables()`) | ~75 | 1 file (`test_source_commands_mineru.py`) | Dead — MinerU always returns 0 tables |
| `open_notebook/extractors/orchestrator.py` (`_get_mineru_tables_for_building()`) | ~30 | 1 test in `test_orchestrator.py` | Dead — no data to fetch |
| `open_notebook/graphs/acm_extraction.py` (`prepare_context` MinerU HTML path) | ~25 | — | Dead — no `acm_table_section` rows with `raw_html` |

**Total dead code:** ~727 lines of production code + ~43 tests across 4 files.

---

## Decision

### D1: Activate TableFormer — YES

We activate Docling TableFormer as the primary table extraction enhancement.

**Rationale:**
- Zero new dependencies (torch, Docling, TableFormer all installed)
- Configuration change only — 3 lines in `source.py:content_process()`
- Built-in fallback — if model inference fails, Docling reverts to basic markdown
- Addresses the exact root cause: poor table structure in markdown that causes
  the LLM to miss sparse rows (Not Sampled, No Access)
- Mary's research confirms +6.5–9.7% accuracy improvement is realistic

### D2: Remove MinerU Dead Code — YES (in a separate cleanup story)

MinerU code should be removed, not kept "for the future."

**Rationale:**
- MinerU requires `paddle` which is not installed and conflicts with torch
- 727 lines of dead production code + 43 dead tests add maintenance burden
- The `_get_mineru_tables_for_building()` function in the orchestrator adds
  a DB query to every building extraction that always returns empty results
- TableFormer fulfills the same need through a simpler integration path
- If MinerU is needed in the future, it can be re-implemented against the
  same `acm_table_section` schema — the code is in git history

### D3: TableFormer Output → Enhanced Markdown → LLM (do NOT bypass LLM)

TableFormer output should feed into the existing LLM extraction pipeline as
enhanced markdown, not as a direct field mapping bypass.

**Rationale:**
- The LLM handles far more than table parsing: building/room context,
  SAMP vs ARA format detection, product normalization, data quality flags
- Direct field mapping would require a separate parser per document format
  (SAMP, ARA, custom consultant formats) — the LLM handles all formats today
- Enhanced markdown gives the LLM **better input** without changing the
  extraction logic, prompt templates, or validation pipeline
- Bypass is a valid stretch goal for a future epic (standard SAMP tables
  with consistent column layouts), but not for the initial integration

### D4: Timing Strategy — full_text FIRST, then TableFormer (Phase 2)

The 120-second polling timeout in `acm_commands.py` is a hard constraint.
The `acm_extract` command polls for `source.full_text` to be populated.

**Phase 1 (immediate):** Activate TableFormer in Docling's pipeline.
Docling produces enhanced markdown as `source.full_text`. No separate
TableFormer step — TableFormer runs *inside* Docling and improves the
markdown quality that gets stored as `full_text`. Processing time increases
from ~5s to ~20–35s, well within the 120s budget.

**Phase 2 (future, optional):** Store structured table data (DataFrame/JSON)
in `acm_table_section` alongside the enhanced markdown. This enables
direct table rendering in the frontend and future LLM-bypass optimization.
Phase 2 requires a new `table_type = 'tableformer_structured'` value and
additional fields on `acm_table_section`.

### D5: Integrate Docling Direct API for Structured Table Extraction — YES

**Date**: 2026-02-27
**Evidence**: E25 research spike (`docs/reviews/e25-table-extraction-comparison.md`)
**Raw data**: `research-output/e25/comparison_summary.json`

We integrate the Docling Direct API as a **parallel extraction path** alongside
the existing PyMuPDF text extraction. This replaces the failed E24 approach of
using content-core's markdown serialization.

**Key difference from E24**: E24 used content-core → Docling → markdown (broken
serialization — column-major cell ordering destroyed row coherence, producing
17/31). E25 uses `DocumentConverter` → `table.export_to_dataframe(doc=doc)`
directly, bypassing content-core entirely and preserving row-major DataFrames.

**Architecture**: Hybrid Approach A
- PyMuPDF: continues to produce `source.full_text` (unchanged, proven 28/31)
- Docling Direct API: runs in parallel during `process_source`, stores DataFrames
  in `acm_table_section` as structured JSON
- Orchestrator: injects DataFrame markdown into LLM context as supplementary
  table data alongside the existing full_text

**Rationale (citing E25-S2 empirical evidence)**:

1. **DataFrame accuracy**: Docling DataFrames alone achieve 29/31 (93.5%) on
   Broadmeadows, exceeding E23 baseline of 28/31 without any LLM involvement.
   Combined with PyMuPDF text (which covers page 8 content), projected accuracy
   is 30-31/31 (96.8-100%).

2. **Row coherence**: All 30 register rows across 3 tables (pages 5-7) are
   extracted as row-major DataFrames. Each row is a complete ACM record with
   level, room, feature, item, hazard status, sample number, and friability
   intact in a single DataFrame row.

3. **"Same as" recovery**: 9/9 (100%) "As Per" reference rows present as
   complete DataFrame rows. E24's content-core approach lost all 9 of these.

4. **"Not Sampled" improvement**: 4/6 (67%) vs E23's 3/6 (50%). Record #9
   (Switch Room / Battery Charger / Fuses) was always in the PDF but missed
   by the LLM — now directly extractable from DataFrame Table 2, Row 9.

5. **Processing time acceptable**: 22.41s for Docling extraction. Adds ~10%
   overhead to the existing ~222s LLM extraction pipeline. Well within the
   120s `process_source` timeout budget.

6. **Column-to-BAR mapping feasible**: Despite compound header names that vary
   across tables, column semantics are consistent by position:
   cols 0-3 = location data (Level/Room/Feature/Item),
   col 4 = hazard type+status, col 5 = sample number, col 6 = friability.
   Positional mapping produces BAR-compatible output.

7. **Known data quality issues are all fixable**:
   - Split sample numbers (`34511-039- 001`) → regex fix: `re.sub(r'(\d+)-\s+(\d+)', r'\1-\2', v)`
   - "Same as" ↔ "As Per" → string normalization
   - "Asbestos " prefix → strip
   - Merged cell artifacts → detect and special-parse

8. **Page 8 gap covered by PyMuPDF**: Docling detects no table on page 8
   (2-3 continuation rows below TableFormer threshold). Records #30 and #31
   ("No Access" entries) are present ONLY in PyMuPDF text. The hybrid approach
   ensures these records remain accessible to the LLM via `source.full_text`.

**What this replaces**:
- E24's content-core TableFormer approach (17/31 regression — Decision gate: DO NOT PROMOTE)
- The deprecated MinerU path (removed in E24-S3)

**What remains unchanged**:
- PyMuPDF as primary text extraction (`source.full_text`)
- LLM extraction pipeline (`acm_extraction.py` graph + orchestrator)
- Orchestrator structure (per-building parallel extraction)
- Frontend display (Raw Tables tab auto-picks up `acm_table_section` data)
- E24's `DOCLING_TABLE_STRUCTURE` flag (remains `false`, separate concern)

**New feature flag**: `DOCLING_DIRECT_TABLE_EXTRACTION` (default: `false`)
- Separate from E24's `DOCLING_TABLE_STRUCTURE` flag
- Controls the new parallel path, not content-core's serialization
- Rollback: set to `false`, restart worker, no data migration needed

---

## Consequences

### What Improves

1. **Extraction accuracy:** 90.3% → 96.8-100% projected on Broadmeadows
   (D5: empirically validated — DataFrames alone achieve 93.5%)
2. **Table structure quality:** Merged cells, multi-line values, sparse rows
   are preserved in markdown (D1) and as structured DataFrames (D5)
3. **Reduced LLM error surface:** Better-structured input = fewer hallucinated
   or missed records. D5 provides the LLM with row-coherent table data
   as supplementary context, eliminating the reading-order ambiguity that
   caused E23's 3 missing records
4. **Codebase cleanliness:** Removing MinerU dead code eliminates 727 lines
   of confusion and removes unnecessary DB queries from the hot path (D2)
5. **Structured data storage (D5):** DataFrames stored in `acm_table_section`
   enable future direct field mapping, AG Grid rendering, and programmatic
   table access without re-processing PDFs
6. **"Same as" / "Not Sampled" recovery (D5):** 9/9 "Same as" rows preserved
   in DataFrames (E24 lost all 9). 4/6 "Not Sampled" rows found (up from
   E23's 3/6). Record #9 (Switch Room / Battery Charger) now directly
   extractable from DataFrame row data

### What Gets Worse

1. **Processing time:** +22s per PDF for Docling Direct API extraction (D5).
   Combined with existing ~222s LLM pipeline = ~244s total. Still within
   acceptable bounds. D1's TableFormer-in-content-core adds +15-30s if enabled.
2. **Memory usage:** +2–4 GB during TableFormer inference (D1/D5). Docling
   Direct API uses the same TableFormer model in `accurate` mode.
3. **First-run latency:** TableFormer model weights download (~500 MB) on
   first use; cached thereafter in `$HOME/.cache/docling/models`
4. **Two Docling code paths (D5):** The parallel extraction path adds a second
   Docling invocation. This is intentional — content-core/PyMuPDF path remains
   unchanged for `source.full_text`, while Direct API runs separately for
   structured tables. Managed via separate feature flag.

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| TableFormer degrades accuracy on some formats | Low | Medium | A/B test with Broadmeadows before removing status quo path |
| Memory exhaustion on small VMs | Low | High | Document minimum 8 GB RAM requirement; monitor with health check |
| Processing time exceeds 120s timeout | Very Low | High | Docling Direct API runs AFTER `process_source` saves `full_text`; does not block polling |
| Model weight download fails in CI/air-gapped | Low | Medium | Pre-download in Docker build; graceful fallback to basic Docling |
| Page 8 gap in Docling (D5) | High | Low | PyMuPDF text covers page 8 content; LLM has both sources |
| Column header variation across PDFs (D5) | Medium | Medium | Positional mapping (cols 0-3 = location) validated on Broadmeadows; expand to Alexander in E26-S2 |
| Docling Direct API version drift | Low | Medium | Pin docling version in pyproject.toml; test on upgrade |

### Migration Path

**D1-D4 (E24 path — completed, flag remains OFF):**
1. Feature flag: `DOCLING_TABLE_STRUCTURE=false` in `.env` (default: `false`)
2. E24 validation showed 17/31 regression — flag NOT promoted
3. MinerU dead code removed in E24-S3

**D5 (E26 path — new):**
1. Feature flag: `DOCLING_DIRECT_TABLE_EXTRACTION=false` in `.env` (default: `false`)
2. E26-S1: Implement Docling Direct API extraction in `process_source_command`
3. E26-S2: Validate DataFrames on Broadmeadows (verify 30 register rows, 8 tables)
4. E26-S3: Inject DataFrame markdown into orchestrator LLM context
5. E26-S4: Full accuracy validation — decision gate: >= 30/31 → promote flag
6. Rollback: Set `DOCLING_DIRECT_TABLE_EXTRACTION=false`, restart worker

---

## Related Documents

- E25 Spike Results: `docs/reviews/e25-table-extraction-comparison.md`
- E25 Raw Data: `research-output/e25/comparison_summary.json`
- E24 Validation (regression): `docs/reviews/e24-validation-results.md`
- E23 Baseline: `docs/reviews/e23-validation-results.md`
- E26 Technical Design: `docs/architecture/e26-table-extraction-technical-design.md`
- D1-D4 Technical Design: `docs/architecture/tableformer-technical-design.md`
- Research Spike (D1): `docs/research/tableformer-research-spike-20260227.md`
- Pipeline Audit: `docs/PIPELINE-AUDIT-FEB-25/pipeline-analysis-20260225.md`
- Schema: `migrations/18.surrealql` (acm_table_section)
