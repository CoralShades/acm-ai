# Bug Fix 12: Extraction Audit + Per-Run Log Categorization — Task Plan

**Created**: 2026-03-12
**Source**: Multi-run audit of `logs/acm-extraction.log`, `logs/worker.log`, `logs/worker-debug.log`
**LangSmith Traces**: `eed83b6e` (primary), 2 additional traces
**GitHub**: #103

---

## Audit Findings — Issues (N1-N9)

### N1 — Two-Building Extractions Silently Abort After Building 1
**Priority**: P1
**Issue file**: `docs/issues/bug-two-building-silent-abort.md`
**Status**: Open

**Evidence**:
- `acm-extraction.log` 01:16:57: `Building extraction: 2 buildings`
- `acm-extraction.log` 01:17:09: `Building extraction: 1/2 saved` — no `2/2 saved`, no `[EXTRACT]`, no `EXTRACTION COMPLETE/FAILED` banner
- Same pattern for two distinct sources: `b73el5y25bpcmckk4xa3` and `0zt30ynmsactoaf2kx9h`

**Root cause hypothesis**: Exception swallowed in `asyncio.gather` error handling for building 2 save path

**Files to modify**:
| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Investigate building save loop in `extract_items_node`; add explicit per-building error logging |

---

### N2 — CORRECT Stage Bypassed When `rejected > 0` but `with_issues = 0`
**Priority**: P0
**Issue file**: `docs/issues/bug-correction-stage-bypassed-on-rejection.md`
**Status**: Open

**Evidence**:
- `acm-extraction.log` 03:40:11: `49 rejected | with_issues=0` → next line: `[STORE] STARTED` (CORRECT skipped)
- `acm-extraction.log` 09:07:31: `28 rejected | with_issues=0` → CORRECT skipped
- Contrast 01:42: `18 rejected | with_issues=52` → CORRECT triggered, 58 LLM corrections
- LangSmith trace `eed83b6e`: `should_correct` node routed to `deduplicate` in 0.003s (bypassed)

**Root cause**: `should_correct` gate checks `with_issues > 0`. Records rejected for missing required fields have `data_issues=[]` — rejection reason is not added to `data_issues`.

**Files to modify**:
| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Change `should_correct` gate: `rejected > 0 OR with_issues > 0` |
| `open_notebook/extractors/` | Ensure rejected records populate `data_issues` with rejection reason |

---

### N3 — Mass Rejection on C_Broadmead / CF_Broadmead Variants
**Priority**: P0
**Issue file**: `docs/issues/bug-mass-rejection-c-broadmead-variants.md`
**Status**: Open

**Evidence**:
- 03:40: `8 accepted, 49 rejected` (14% acceptance)
- 09:07: `28 accepted, 28 rejected` (50% acceptance)
- LangSmith trace `eed83b6e`: 28 rejected = all `result=Negative` (intentional filter), NOT extraction failures
- LangSmith: `normalize_to_sf` generated 81 `data_issues` but 0 `validation_errors` — conflated metrics

**Root cause**: `records_failed` metric conflates intentional Negative-result filtering with real extraction failures; 03:40 high rejection rate (49) suggests additional field-level failures beyond the filter.

**Files to modify**:
| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Rename `records_failed` → `records_filtered`; separate intentional-filter count from validation-failure count |
| `open_notebook/extractors/pipeline_logger.py` | Add `records_filtered` field to stage completion metrics |

---

### N4 — Compound `sample_result` Values + Empty Correction JSON
**Priority**: P1
**Issue file**: `docs/issues/bug-compound-sample-result-correction-failure.md`
**Status**: Open

**Evidence**:
- `worker.log` 07:05: 10 unique bad values across 13/18 records — `"Positive Assumed Positive"`, `"Negative No Access"`, `"Positive Stable"`, etc.
- 39 correction attempts all return `json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`
- `auto=0, llm=0` — zero successful fixes from entire correction loop
- Model: `llama3.1:8b` with `format="json"`

**Root cause (dual)**:
1. Row extractor prompt does not constrain `sample_result` to enum values; LLM concatenates adjacent table columns
2. `llama3.1:8b` returns empty `{}` for correction prompts on these records; no graceful skip

**Files to modify**:
| File | Change |
|------|--------|
| `open_notebook/extractors/orchestrator.py` | Add compound `sample_result` splitting to `_normalize_extraction_json()` |
| `prompts/acm/` | Add explicit enum constraints to correction prompt |
| `open_notebook/graphs/acm_extraction.py` | Handle empty correction JSON: skip record, don't crash |

---

### N5 — Cloud Retry Fires with `model_id=None` in Ollama-Only Mode
**Priority**: P1
**Issue file**: `docs/issues/bug-cloud-retry-model-id-none-ollama.md`
**Status**: Open

**Evidence**:
- `worker-debug.log` 20:15, 20:24, 20:33: `retrying chunk with cloud provider (model_id=None)` × 3
- All retries produce no output (no API call possible without model_id)

**Root cause**: `cloud_available` guard exists at the single-chunk level but chunk-level retry code path still executes with `model_id=None`.

**Files to modify**:
| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Add `cloud_available` guard before chunk-level retry; log `Truncation detected but no cloud API keys configured — skipping chunk retry` |

---

### N6 — Empty Correction JSON Causes `JSONDecodeError`
**Priority**: P1
**Combined with N4** (same issue file: `bug-compound-sample-result-correction-failure.md`)

Empty `{}` from `llama3.1:8b` correction calls causes `json.JSONDecodeError: Expecting value` at the parse step. The correction loop crashes rather than skipping the unresolvable record.

**Fix**: In correction response handler, catch empty/blank JSON before parse; log and continue to next record.

---

### N7 — `save_records` Timer Reports Pipeline Total Instead of DB Write Time
**Priority**: P2
**Issue file**: `docs/issues/bug-save-records-timer-measures-pipeline-total.md`
**Status**: Open

**Evidence**:
- `worker-debug.log` 20:37: `save_records` reports ~2001s duration
- LangSmith trace `eed83b6e`: `save` node actual duration = 0.684s

**Root cause**: Timer captures pipeline start time, not save operation start time.

**Files to modify**:
| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Capture `time.monotonic()` at save start in `store_results_node` |

---

### N8 — STRUCTURE Stage 148-208s Latency on Ollama
**Priority**: P2
**Issue file**: `docs/issues/bug-structure-stage-latency-ollama.md`
**Status**: Open

**Evidence**:
- `acm-extraction.log` 03:33-03:37: STRUCTURE took 208s for `l6xcf7tlv78bo3vrdeqj`
- `acm-extraction.log` 09:01-09:04: STRUCTURE took 148s for `8u2ht8upok65bcz7vvd3`
- LangSmith trace `eed83b6e`: 136.8s, 11,409 prompt tokens → `consultant=Unknown, buildings=0`
- Compare: Broadmead.pdf at 01:27 took ~20s with same model

**Root cause**: 11,409 prompt tokens exceeds effective context for llama3.1:8b; output degrades to generic unknowns.

**Files to modify**:
| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Add content truncation for metadata extraction (first 5 pages + TOC) |
| `prompts/acm/` | Review metadata extraction prompt for token efficiency |

---

### N9 — Building Name Dedup Failure — All Buildings Named Identically
**Priority**: P2
**Issue file**: `docs/issues/bug-building-name-dedup-all-identical.md`
**Status**: Open

**Evidence**:
- `worker-debug.log` 20:04: all 3 buildings assigned identical names (site name)
- LangSmith trace `eed83b6e` (L3): `building_category="Educational and training facilities"` for Broadmeadows Police Station

**Root cause**: Building name assignment uses site name unconditionally; no differentiation by address/floor/wing. Building category prompt has no enum constraint.

**Files to modify**:
| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Add building name differentiation logic |
| `prompts/acm/` | Add constrained enum for `building_category` |

---

## LangSmith Observations (L1-L3)

| # | Trace | Finding | Action |
|---|-------|---------|--------|
| L1 | `eed83b6e` | `records_failed` tag in Langfuse conflates intentional Negative-result filtering with extraction failures | Rename to `records_filtered`; add separate `records_validation_failed` tag |
| L2 | `eed83b6e` | `metadata_and_structure` node: 136.8s (40% of 343.9s total), 11,409 prompt tokens, output = `consultant=Unknown` | Cap prompt tokens for STRUCTURE stage to improve performance and quality |
| L3 | `eed83b6e` | `extract_building` node hallucinated `building_category="Educational and training facilities"` for a Police Station | Constrain `building_category` field to valid SF picklist values in extraction prompt |

---

## Per-Run Log Categorization — Implementation Details

### What was implemented

Replaces monolithic `logs/acm-extraction.log` (mixed interleaved runs) with per-run directories under `logs/runs/`.

### Files Modified

| File | Change |
|------|--------|
| `open_notebook/extractors/pipeline_logger.py` | Added `_setup_run_directory()`, `_write_to_run_file()`, `_finalize_run_directory()`, `_write_summary()`, `_cleanup_old_run_dirs()`, `_run_registry` (`_RunRegistry`), `_ActiveRun` dataclass; deprecated `_file_handler` / `_write_to_file()` / `_get_file_handler()` |
| `run_worker.py` | Added `_per_run_worker_tee` loguru sink that routes worker log lines to active run dirs via `_run_registry`; added monkey-patch to re-add sinks after `surreal_commands.core.worker.configure_logging()` calls `logger.remove()` |
| `scripts/split_logs.py` | New script — historical log splitter for backfilling monolithic `acm-extraction.log` into per-run directories |

### Run Directory Layout

```
logs/runs/<YYYY-MM-DDTHH-MM-SS>_<source_suffix_12chars>/
  extraction.log   — [PIPELINE] log lines (written by PipelineLogger._write_to_run_file)
  worker.log       — worker loguru lines (written by run_worker._per_run_worker_tee)
  summary.txt      — source_id, run_id, duration, records, stage breakdown
```

### Retention

`PipelineLogger._cleanup_old_run_dirs()` removes directories older than `LOG_RUN_RETENTION_DAYS` (default: 30 days) on every run completion.

### Historical Backfill

```bash
# Dry run — preview what would be created
uv run python scripts/split_logs.py --dry-run

# Full run — create per-run dirs from monolithic logs
uv run python scripts/split_logs.py

# Filter to specific source
uv run python scripts/split_logs.py --source-id source:aysaqf0b26jc0g5rpr4g
```

---

## Execution Priority Order

| Priority | Issues | Rationale |
|----------|--------|-----------|
| P0 first | N2, N3 | Silent data loss at validation — highest production impact |
| P1 next | N1, N4, N5, N6 | Multi-building abort + compound values blocking correction loop |
| P2 last | N7, N8, N9 | Metrics accuracy and performance; no data loss |

---

## Success Criteria

- [ ] N2 fixed: CORRECT stage fires when `rejected > 0` regardless of `with_issues`
- [ ] N3 fixed: `records_filtered` vs `records_validation_failed` separated in logs and Langfuse tags
- [ ] N1 fixed: Two-building extractions complete both buildings (no silent abort)
- [ ] N4/N6 fixed: Compound `sample_result` split pre-correction; empty JSON handled gracefully
- [ ] N5 fixed: Cloud retry skipped with clear log message in Ollama-only mode
- [ ] All existing tests pass
- [ ] Ruff lint clean
- [ ] Per-run log dirs created for each live extraction run
