# Bug Fix 12: Extraction Audit + Per-Run Log Categorization

## Status

| Item | Status |
|------|--------|
| Overall | in_progress |
| Issue docs (N1-N9) | Done (8 files created) |
| GitHub tracking issue | Done (#103) |
| `pipeline_logger.py` per-run dirs | Done |
| `run_worker.py` tee sink | Done |
| `scripts/split_logs.py` | Done |
| Run splitter on existing logs | Pending |
| Live verification | Pending |

---

## Date: 2026-03-12

## Session Summary

### Problem

After Bug Fix 11 (Phase 8b), extraction reached 31/31 records for Broadmead.pdf. A systematic audit of the extraction logs and LangSmith traces for ALL runs in `logs/` was performed to identify the next set of quality and reliability issues before closing the gap-analysis phase.

### Audit Scope

- Monolithic log: `logs/acm-extraction.log` (full history)
- Worker log: `logs/worker.log`
- Worker debug log: `logs/worker-debug.log`
- LangSmith traces: 3 traces reviewed (`eed83b6e` and others)
- Sources audited: Clutch_Broadmead.pdf, Broadmead.pdf, C_Broadmead.pdf, CF_Broadmead.pdf

### Issues Found During Audit (N1-N9)

| # | Issue ID | Priority | Description |
|---|----------|----------|-------------|
| N1 | `bug-two-building-silent-abort` | P1 | Two-building extractions stop after building 1 — no error, no records for building 2 |
| N2 | `bug-correction-stage-bypassed-on-rejection` | P0 | CORRECT stage gate checks `with_issues > 0` but rejected records have `with_issues=0` → 86% of records silently discarded |
| N3 | `bug-mass-rejection-c-broadmead-variants` | P0 | 14%-50% acceptance rate on C_Broadmead / CF_Broadmead document variants; `records_failed` metric conflates intentional filtering with real failures |
| N4 | `bug-compound-sample-result-correction-failure` | P1 | LLM concatenates adjacent columns into `sample_result` (e.g., `"Positive Assumed Positive"`); correction loop returns empty JSON (`{}`) for all 39 attempts → zero fixes |
| N5 | `bug-cloud-retry-model-id-none-ollama` | P1 | Cloud retry fires with `model_id=None` in Ollama-only mode — misleading logs, wasted code path |
| N6 | (combined with N4) | P1 | Empty correction JSON causes `JSONDecodeError` — no graceful skip |
| N7 | `bug-save-records-timer-measures-pipeline-total` | P2 | `save_records` stage timer reports ~2001s (pipeline total) instead of actual DB write time (~0.7s) |
| N8 | `bug-structure-stage-latency-ollama` | P2 | STRUCTURE stage takes 148-208s on Ollama (llama3.1:8b) for 27-page docs; produces `consultant=Unknown, buildings=0` |
| N9 | `bug-building-name-dedup-all-identical` | P2 | All buildings named identically (site name); building category hallucinated (`Educational` for a Police Station) |

### LangSmith Observations (L1-L3)

| # | Trace | Observation |
|---|-------|-------------|
| L1 | `eed83b6e` | `records_failed=28` in Langfuse tags conflates intentional Negative-result filtering with actual extraction failures — rename to `records_filtered` |
| L2 | `eed83b6e` | `metadata_and_structure` node: 136.8s, 11,409 prompt tokens, output `consultant_name="Unknown"` — 40% of 343.9s pipeline total wasted on a failed LLM call |
| L3 | `eed83b6e` | `extract_building` hallucinated `building_category="Educational and training facilities"` for Broadmeadows Police Station |

### Per-Run Log Categorization Implementation

New infrastructure implemented to replace monolithic `acm-extraction.log` with per-run directories:

**`open_notebook/extractors/pipeline_logger.py`**
- `_setup_run_directory()` — creates `logs/runs/<YYYY-MM-DDTHH-MM-SS>_<source_suffix>/` on `PipelineLogger.__init__`
- `_write_to_run_file()` — all `[PIPELINE]` entries written to `extraction.log` in the run dir
- `_finalize_run_directory()` — closes file handles, writes `summary.txt`, unregisters from `_run_registry`, prunes dirs older than `LOG_RUN_RETENTION_DAYS`
- `_run_registry` (`_RunRegistry`) — thread-safe registry of active runs; maps `run_id` to `_ActiveRun` (with open `extraction_fh` and `worker_fh`)

**`run_worker.py`**
- `_per_run_worker_tee` loguru sink — routes all worker log lines to active run directories by checking `_run_registry`; added after surreal-commands `configure_logging()` monkey-patch to survive `logger.remove()` resets

**`scripts/split_logs.py`**
- Historical backfill utility — parses monolithic `logs/acm-extraction.log`, detects run boundaries via `[PIPELINE] Starting extraction` / `EXTRACTION COMPLETE|FAILED` markers, slices matching time windows from `worker.log` and `api.log` into per-run directories
- Skips test fixture sources by default (`source:test`, `source:broadmeadows_e2e_test`, etc.)
- Handles timestamp collisions, unclosed runs (crash/kill)
- Usage: `uv run python scripts/split_logs.py [--log-dir logs] [--dry-run] [--source-id SOURCE_ID]`

### Run Directory Structure

```
logs/
  runs/
    2026-03-12T01-16-57_b73el5y25bpc/    # Clutch_Broadmead.pdf run
      extraction.log   — [PIPELINE] lines
      worker.log       — worker loguru lines (tee sink)
      summary.txt      — source_id, run_id, duration, record_count, stage breakdown
    2026-03-12T03-33-00_l6xcf7tlv78b/    # C_Broadmead.pdf run
      extraction.log
      worker.log
      summary.txt
```

### Completed Items

| Item | Details |
|------|---------|
| 8 issue docs created | `docs/issues/bug-two-building-silent-abort.md`, `bug-correction-stage-bypassed-on-rejection.md`, `bug-mass-rejection-c-broadmead-variants.md`, `bug-compound-sample-result-correction-failure.md`, `bug-cloud-retry-model-id-none-ollama.md`, `bug-save-records-timer-measures-pipeline-total.md`, `bug-structure-stage-latency-ollama.md`, `bug-building-name-dedup-all-identical.md` |
| GitHub #103 | Tracking issue created for Bug Fix 12 audit findings |
| `pipeline_logger.py` | Per-run directory creation, `_run_registry`, `_finalize_run_directory`, monolithic handler deprecated |
| `run_worker.py` | `_per_run_worker_tee` loguru sink routes worker logs to active run dirs |
| `scripts/split_logs.py` | Historical log splitter for backfilling existing monolithic logs |

### Pending Items

| Item | Details |
|------|---------|
| Run splitter on existing logs | `uv run python scripts/split_logs.py` against current `logs/acm-extraction.log` |
| Live verification | Confirm new extraction produces `logs/runs/<ts>_<suffix>/` directory with all 3 files |
| Fix N1-N9 | Separate implementation phases; priority order: N2, N3 (P0) → N1, N4, N5, N6 (P1) → N7, N8, N9 (P2) |
