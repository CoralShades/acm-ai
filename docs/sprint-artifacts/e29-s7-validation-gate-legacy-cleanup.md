# E29-S7: Dual-Benchmark Validation Gate + Legacy Dead-Code Cleanup

> **Epic**: E29 — Pipeline Unification
> **Story Points**: 2 | **Phase**: 4 | **Owner**: Backend Dev + QA
> **Requires**: Gate 3 PASS
> **Source of Truth**: [Execution Contract](../../V3/epic-29-execution-contract.md) | [Architecture Delta](../../docs/architecture/e29-architecture-delta.md)

---

## Story Status

| Field | Value |
|-------|-------|
| Status | `drafted` |
| Sprint | E29 Phase 4 |
| Assigned To | — |
| Started | — |
| Completed | — |
| PR | — |
| Blocked By | Gate 3 (after S6) |

---

## User Story

> As a **pipeline developer**, I want the legacy dual-path code (`prepare_context`, `extract_records`, `should_use_orchestrator`) removed after confirming Broadmeadows remains 31/31 and Alexander reaches >=40/43, so that there is zero dead code and a single maintainable extraction path.

---

## Dependencies

| Type | Item | Status |
|------|------|--------|
| Story | E29-S6 (agent decomposition complete) | Must be merged |
| Gate | Gate 3 — Cleanup Permission | Must PASS |

---

## Acceptance Criteria

| # | Criterion | Measurable Check |
|---|-----------|------------------|
| AC-1 | **Broadmeadows: 31/31** after full decomposition | Benchmark run: `broadmeadows.record_count == 31` |
| AC-2 | **Alexander: >= 40/43** (stretch target) OR PM-approved lower threshold >= 36/43 | Benchmark run: `alexander.record_count >= 40` OR documented PM sign-off on approved threshold |
| AC-3 | `prepare_context` function removed | `grep -rc "def prepare_context" open_notebook/` returns 0 |
| AC-4 | `extract_records` function removed | `grep -rc "def extract_records" open_notebook/` returns 0 |
| AC-5 | `should_use_orchestrator` function removed | `grep -rc "def should_use_orchestrator" open_notebook/` returns 0 |
| AC-6 | Legacy feature flags and dead branches removed | No unreachable conditional paths referencing removed functions |
| AC-7 | `ruff check .` passes after cleanup | Zero lint errors |
| AC-8 | `pytest tests/ -x` passes after cleanup | All tests green |
| AC-9 | Validation gate results published | `docs/reviews/e29-validation-gate-results.md` exists with evidence |

### Threshold Clarification

> **Authoritative thresholds** (resolves wording drift across E29 artifacts):
>
> | Metric | Gate 2 Floor (S4) | S7 Stretch Target | S7 PM-Approved Fallback |
> |--------|-------------------|--------------------|-------------------------|
> | Broadmeadows | 31/31 | 31/31 | 31/31 (non-negotiable) |
> | Alexander | >= 36/43 | **>= 40/43** | **>= 36/43** (requires PM sign-off) |
>
> - Gate 2 (after S4) sets the **floor** at Alexander >= 36/43.
> - S7 (this story) targets Alexander **>= 40/43** as a stretch goal after agent decomposition improvements.
> - If Alexander is >= 36/43 but < 40/43, the story can still pass with **explicit PM approval** documented in the validation gate results.

---

## Gate 3 Criteria Referenced

Per the Execution Contract Gate 3:

| Gate 3 Criterion | How This Story Validates |
|-----------------|--------------------------|
| No benchmark regression beyond +/-2 records of Gate 2 | AC-1 (Broadmeadows exact), AC-2 (Alexander threshold) |
| Latency <= Gate 2 baseline OR approved tradeoff | Validation gate report includes latency comparison |
| Token usage <= Gate 2 baseline OR approved tradeoff | Validation gate report includes token comparison |
| Fallback/correction deterministic under test | Test suite from S4-S6 must pass post-cleanup |

---

## Tasks / Subtasks

| # | Task | File(s) | Est |
|---|------|---------|-----|
| T1 | Run dual-benchmark validation gate script | `scripts/research/e29_validation_gate.py` (new) | 60m |
| T1.1 | — Run Broadmeadows E2E, compare to ground truth | | |
| T1.2 | — Run Alexander E2E, compare to ground truth (per-building breakdown) | | |
| T1.3 | — Compare latency/tokens to Gate 2 baseline | | |
| T1.4 | — Generate validation gate results report | | |
| T2 | Remove `prepare_context()` function | `open_notebook/graphs/acm_extraction.py` | 15m |
| T3 | Remove `extract_records()` function | `open_notebook/graphs/acm_extraction.py` | 15m |
| T4 | Remove `should_use_orchestrator()` function | `open_notebook/extractors/orchestrator.py` | 10m |
| T5 | Remove "prepare" and "extract" nodes from graph | `open_notebook/graphs/acm_extraction.py` | 10m |
| T6 | Remove legacy feature flags and dead conditional branches | `open_notebook/graphs/acm_extraction.py`, `commands/source_commands.py` | 20m |
| T7 | Remove/update tests that reference legacy functions | `tests/test_orchestrator.py` | 20m |
| T8 | Publish validation gate results | `docs/reviews/e29-validation-gate-results.md` (new) | 15m |
| T9 | Lint + full test suite pass | `ruff check . --fix && pytest tests/ -x` | 15m |

---

## Repeatable Command Entrypoints

```bash
# Run validation gate (pre-cleanup, captures evidence)
uv run python scripts/research/e29_validation_gate.py --all

# Run validation gate for single document
uv run python scripts/research/e29_validation_gate.py --doc broadmeadows
uv run python scripts/research/e29_validation_gate.py --doc alexander

# Verify cleanup (post-deletion)
grep -rc "def prepare_context\|def extract_records\|def should_use_orchestrator" open_notebook/
uv run ruff check .
uv run pytest tests/ -x
```

---

## Test Strategy

- **Validation gate** (`scripts/research/e29_validation_gate.py`):
  - **Broadmeadows: 31/31** exact match
  - **Alexander: >= 40/43** with per-building breakdown (or PM-approved >= 36/43)
  - Latency comparison to Gate 2 baseline
  - Token/cost comparison to Gate 2 baseline
- **Post-cleanup verification**:
  - `ruff check .` — zero errors (no dead imports, unreachable code)
  - `pytest tests/ -x` — all tests pass
  - `grep` for removed function names — zero hits

---

## Touched Files

| File | Action | Lines (est) |
|------|--------|-------------|
| `scripts/research/e29_validation_gate.py` | Add (new) | ~200 |
| `docs/reviews/e29-validation-gate-results.md` | Add (new) | ~80 |
| `open_notebook/graphs/acm_extraction.py` | Modify (delete ~200 lines) | -200 |
| `open_notebook/extractors/orchestrator.py` | Modify (delete ~10 lines) | -10 |
| `commands/source_commands.py` | Modify | ~10 |
| `tests/test_orchestrator.py` | Modify | ~30 |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Legacy removal breaks downstream stages | Post-extraction stages only depend on `raw_records` shape (verified in Arch Delta Appendix A) |
| Alexander doesn't reach 40/43 | PM approval for >= 36/43 is an explicit AC option |
| Dead import discovered after deletion | `ruff check .` catches unused imports immediately |

---

## QA Checklist

- [ ] AC-1: Broadmeadows 31/31 confirmed
- [ ] AC-2: Alexander >= 40/43 OR PM sign-off on lower threshold
- [ ] AC-3: `prepare_context` removed (grep returns 0)
- [ ] AC-4: `extract_records` removed (grep returns 0)
- [ ] AC-5: `should_use_orchestrator` removed (grep returns 0)
- [ ] AC-6: No dead branches referencing removed functions
- [ ] AC-7: `ruff check .` clean
- [ ] AC-8: `pytest tests/ -x` green
- [ ] AC-9: Validation gate results published
- [ ] Gate 3 referenced criteria validated

---

## Post-Dev Notes

_To be filled by the developer after implementation._

---

## Post-QA Notes

_To be filled by QA after verification._
