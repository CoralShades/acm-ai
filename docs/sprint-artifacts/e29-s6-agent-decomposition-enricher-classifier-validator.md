# E29-S6: Agent Decomposition II — Enricher/Classifier/Validator

> **Epic**: E29 — Pipeline Unification
> **Story Points**: 3 | **Phase**: 3 | **Owner**: Backend Dev
> **Decision Gate**: Gate 3 (Cleanup Permission) exits after this story
> **Source of Truth**: [Execution Contract](../../V3/epic-29-execution-contract.md) | [Architecture Delta](../../docs/architecture/e29-architecture-delta.md)

---

## Story Status

| Field | Value |
|-------|-------|
| Status | `drafted` |
| Sprint | E29 Phase 3 |
| Assigned To | — |
| Started | — |
| Completed | — |
| PR | — |
| Blocked By | S5 (table parser + BAR mapper) |

---

## User Story

> As a **pipeline developer**, I want product classification handled by regex first (with LLM only for ambiguous cases), context enrichment batched and targeted (not full-document), and validation retries capped and deterministic, so that extraction is faster and cheaper while maintaining quality.

---

## Dependencies

| Type | Item | Status |
|------|------|--------|
| Story | E29-S5 (table parser + BAR mapper) | Must be merged |

---

## Acceptance Criteria

| # | Criterion | Measurable Check |
|---|-----------|------------------|
| AC-1 | Regex-first classifier resolves majority of product types | `agent.classifier.regex_hit_rate` >= 0.6 (60% resolved without LLM) |
| AC-2 | LLM enrichment is batched and targeted (not full-document per record) | `agent.enricher.records_enriched` < total records (only ambiguous ones) |
| AC-3 | Validation retries capped at 3 and deterministic | Test: 4th retry attempt is rejected; same input produces same retry path |
| AC-4 | Benchmark delta meets or exceeds Gate 2 baseline | **Broadmeadows >=31/31**, **Alexander >=36/43** |
| AC-5 | Latency <= Gate 2 baseline * 1.2 (20% tolerance) | Benchmark latency comparison documented |
| AC-6 | Token usage <= Gate 2 baseline * 1.3 (30% tolerance) | Benchmark token comparison documented |

---

## Tasks / Subtasks

| # | Task | File(s) | Est |
|---|------|---------|-----|
| T1 | Implement `classifier.py` | `open_notebook/extractors/classifier.py` (new) | 60m |
| T1.1 | — Regex classification rules for known ACM product types | | |
| T1.2 | — LLM fallback for ambiguous classifications | | |
| T1.3 | — Emit `agent.classifier.regex_hit_rate` metric | | |
| T2 | Implement `context_enricher.py` | `open_notebook/extractors/context_enricher.py` (new) | 60m |
| T2.1 | — Identify records needing enrichment (missing fields, low confidence) | | |
| T2.2 | — Batch LLM enrichment call for targeted records only | | |
| T2.3 | — Emit `agent.enricher.records_enriched` metric | | |
| T3 | Implement `validator.py` | `open_notebook/extractors/validator.py` (new) | 45m |
| T3.1 | — Pydantic validation against `ACMExtractionRecord` schema | | |
| T3.2 | — Deterministic retry: max 3, accept partials after exhaustion (F5/F6) | | |
| T3.3 | — Emit correction metrics: retry_count, records_fixed, records_dropped | | |
| T4 | Wire all three agents into orchestrator loop | `open_notebook/graphs/acm_extraction.py` | 30m |
| T5 | Write classifier tests | `tests/test_classifier.py` (new) | 45m |
| T6 | Write enricher tests | `tests/test_context_enricher.py` (new) | 45m |
| T7 | Write validator tests | `tests/test_validator.py` (new) | 45m |
| T8 | Run benchmark: quality + latency + cost comparison | Benchmark harness | 30m |
| T9 | Lint + full test suite pass | `ruff check . --fix && pytest tests/ -x` | 10m |

**Within-story parallelism**: T1 (classifier), T2 (enricher), and T3 (validator) can be developed in parallel.

---

## Test Strategy

- **Unit tests** (`tests/test_classifier.py`):
  - Known ACM products resolved by regex (cement sheet, vinyl tiles, etc.)
  - Unknown product falls through to LLM (mock LLM call)
  - Regex hit rate metric calculation
- **Unit tests** (`tests/test_context_enricher.py`):
  - Records with missing fields flagged for enrichment
  - Records with all fields skip enrichment (no LLM call)
  - Batch enrichment call structure (mock LLM)
- **Unit tests** (`tests/test_validator.py`):
  - Valid records pass immediately (no retry)
  - Invalid records trigger correction (mock LLM)
  - Retry cap: 4th attempt rejected
  - Partial acceptance: some records pass, some dropped after exhaustion
  - Determinism: same input -> same output path
- **Benchmark validation**: Quality >=Gate 2, latency <=1.2x, tokens <=1.3x

---

## Touched Files

| File | Action | Lines (est) |
|------|--------|-------------|
| `open_notebook/extractors/context_enricher.py` | Add (new) | ~150 |
| `open_notebook/extractors/classifier.py` | Add (new) | ~150 |
| `open_notebook/extractors/validator.py` | Add (new) | ~120 |
| `open_notebook/graphs/acm_extraction.py` | Modify | ~30 |
| `tests/test_context_enricher.py` | Add (new) | ~120 |
| `tests/test_classifier.py` | Add (new) | ~120 |
| `tests/test_validator.py` | Add (new) | ~150 |

---

## Gate 3 Exit — Go/No-Go Reference

This story exits **Gate 3 (Cleanup Permission)**. Full checklist in [e29-gate-decisions.md](./e29-gate-decisions.md#gate-3--cleanup-permission-after-s6).

| # | Criterion | Status |
|---|-----------|--------|
| G3.1 | No regression beyond +/-2 records | Pending |
| G3.2 | Latency <= baseline * 1.2 | Pending |
| G3.3 | Token usage <= baseline * 1.3 | Pending |
| G3.4 | Fallback/correction deterministic | Pending |
| G3.5 | Classifier regex hit rate >= 60% | Pending |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Regex classifier misses too many products | Start with known Broadmeadows+Alexander product types; LLM fallback catches rest |
| Agent decomposition increases latency | Regex-first classifier reduces LLM calls; batched enrichment limits total calls |
| Agent decomposition increases cost | Gate 3 enforces token budget; targeted enrichment reduces per-record token usage |

---

## QA Checklist

- [ ] AC-1: Regex hit rate >= 60%
- [ ] AC-2: Targeted enrichment (not all records)
- [ ] AC-3: Retry cap at 3, deterministic
- [ ] AC-4: No benchmark quality regression
- [ ] AC-5: Latency within 20% of baseline
- [ ] AC-6: Token usage within 30% of baseline
- [ ] Gate 3 criteria all PASS

---

## Post-Dev Notes

_To be filled by the developer after implementation._

---

## Post-QA Notes

_To be filled by QA after verification._
