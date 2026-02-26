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

---

## Consequences

### What Improves

1. **Extraction accuracy:** 90.3% → 97–100% projected on Broadmeadows
2. **Table structure quality:** Merged cells, multi-line values, sparse rows
   are preserved in markdown
3. **Reduced LLM error surface:** Better-structured input = fewer hallucinated
   or missed records
4. **Codebase cleanliness:** Removing MinerU dead code eliminates 727 lines
   of confusion and removes unnecessary DB queries from the hot path

### What Gets Worse

1. **Processing time:** +15–30s per PDF during source processing
2. **Memory usage:** +2–4 GB during TableFormer inference
3. **First-run latency:** TableFormer model weights download (~500 MB) on
   first use; cached thereafter in `$HOME/.cache/docling/models`

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| TableFormer degrades accuracy on some formats | Low | Medium | A/B test with Broadmeadows before removing status quo path |
| Memory exhaustion on small VMs | Low | High | Document minimum 8 GB RAM requirement; monitor with health check |
| Processing time exceeds 120s timeout | Very Low | High | TableFormer runs inside `process_source`, not `acm_extract`; 35s << 120s |
| Model weight download fails in CI/air-gapped | Low | Medium | Pre-download in Docker build; graceful fallback to basic Docling |

### Migration Path

1. Feature flag: `DOCLING_TABLE_STRUCTURE=true` in `.env` (default: `false`)
2. A/B test: Run Broadmeadows extraction with flag on vs off, compare results
3. Promote: Set `true` as default after validation
4. Cleanup: Remove MinerU code in a separate PR

---

## Related Documents

- Research Spike: `docs/research/tableformer-research-spike-20260227.md`
- Pipeline Audit: `docs/PIPELINE-AUDIT-FEB-25/pipeline-analysis-20260225.md`
- Technical Design: `docs/architecture/tableformer-technical-design.md`
