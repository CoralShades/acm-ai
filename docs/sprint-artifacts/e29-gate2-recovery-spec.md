# E29 Gate 2 Recovery Spec — R1 + R2

> **Epic**: E29 — Pipeline Unification
> **Trigger**: Gate 2 FAIL (2026-03-01) — PM authorized recovery loop, no rollback
> **Total**: 2 recovery stories, 4 SP
> **Execution order**: R1 first → R2 (R2 depends on R1 for accurate measurement)
> **Source of Truth**: [Gate Decisions — PM Sign-Off](./e29-gate-decisions.md#pm-sign-off--gate-2) | [Execution Contract](../../V3/epic-29-execution-contract.md)

---

## Gate 2 Shortfall Summary

| Criterion | Required | Actual | Gap | Root Cause |
|-----------|----------|--------|-----|------------|
| G2.1 Broadmeadows | 31/31 | 28/31 | -3 | Matching normalization + no Docling tables |
| G2.2 Alexander | >= 36/43 | 31/43 | -5 | RoomMeta typing bug + normalization + no Docling tables |
| G2.3 Docling injection | Confirmed | Not testable | N/A | No Docling tables seeded in benchmark DB |

**No regression**: Both documents improved from Gate 1 baseline (Broadmeadows +4, Alexander +1).

---

## E29-R1: Benchmark Fidelity + Docling Table Testability (2 SP)

### User Story

> As a **pipeline developer**, I want the benchmark harness to use normalized matching and have Docling tables available for injection, so that Gate 2 metrics accurately reflect the unified pipeline's true capability.

### Dependencies

| Type | Item | Status |
|------|------|--------|
| Story | E29-S3 (unified path) | Done |
| Story | E29-S4 (capability registry) | Done |
| External | Docling tables for benchmark documents | Must be generated/seeded |

### Acceptance Criteria

| # | Criterion | Measurable Check |
|---|-----------|------------------|
| R1-AC1 | Docling tables seeded for Broadmeadows and Alexander in benchmark DB or test fixture | `SELECT count() FROM acm_table_section WHERE source = "source:broadmeadows"` returns > 0 |
| R1-AC2 | Benchmark matching normalizes room names before comparison | `test_benchmark_matching_normalization` passes: "Room 1" == "room 1" == "ROOM 1" |
| R1-AC3 | Benchmark matching normalizes material descriptions (casing, whitespace, common abbreviations) | `test_material_description_normalization` passes |
| R1-AC4 | Baseline Gate 2 results pinned as immutable JSON snapshots | `benchmarks/baselines/gate2_baseline.json` exists with timestamped metrics |
| R1-AC5 | Re-run benchmarks with Docling injection active — F2 fallback does NOT fire | Benchmark log: no `[fallback.no_docling_tables]` entries |
| R1-AC6 | `ruff check .` clean | Zero errors |
| R1-AC7 | `pytest tests/` — no new failures introduced | Same or fewer failures than Gate 2 baseline (13 pre-existing) |

### Tasks

| # | Task | File(s) | Est |
|---|------|---------|-----|
| R1-T1 | Generate Docling tables for Broadmeadows and Alexander PDFs | `benchmarks/fixtures/` or DB seed script | 45m |
| R1-T2 | Create benchmark DB seeding script/fixture for Docling tables | `benchmarks/seed_docling_tables.py` or `conftest.py` | 30m |
| R1-T3 | Implement normalized matching in benchmark comparator | `scripts/research/e29_benchmark_harness.py` or `benchmarks/comparator.py` | 45m |
| R1-T3.1 | — Normalize room names: lowercase, strip whitespace, expand abbreviations | | |
| R1-T3.2 | — Normalize material descriptions: lowercase, strip, common variant mapping | | |
| R1-T3.3 | — Normalize casing for all string comparison fields | | |
| R1-T4 | Pin Gate 2 baseline results as immutable JSON snapshot | `benchmarks/baselines/gate2_baseline.json` | 15m |
| R1-T5 | Re-run benchmarks and verify Docling injection fires | Benchmark harness | 20m |
| R1-T6 | Write/update tests for normalization functions | `tests/test_benchmark_harness.py` or new test file | 30m |
| R1-T7 | Lint + full test suite pass | `ruff check . && pytest tests/ -x` | 10m |

### Test Commands

```bash
# Verify Docling tables seeded
uv run pytest tests/integration/test_benchmark_harness.py -k "docling" -x -v

# Verify normalization
uv run pytest tests/test_benchmark_matching.py -x -v  # or wherever normalization tests live

# Full harness run
uv run python scripts/research/e29_benchmark_harness.py

# Lint
uv run ruff check .

# Full suite
uv run pytest tests/ -x
```

---

## E29-R2: Match-Gap Remediation — Inventory Typing + Normalization (2 SP)

### User Story

> As a **pipeline developer**, I want the LLM inventory compilation to return proper `RoomMeta` objects and extraction output to use normalized room/material names, so that Gate 2 thresholds are met.

### Dependencies

| Type | Item | Status |
|------|------|--------|
| Story | E29-R1 (benchmark fidelity) | Must be complete (accurate measurement required) |

### Acceptance Criteria

| # | Criterion | Measurable Check |
|---|-----------|------------------|
| R2-AC1 | LLM inventory compilation returns `RoomMeta` objects, not strings | `test_inventory_returns_roommeta` passes; no heuristic fallback logged for inventory-available docs |
| R2-AC2 | Room/location names normalized in extraction output (casing, whitespace, abbreviation) | Extracted records use consistent naming vs ground truth |
| R2-AC3 | Material/item description matching improved | Alexander matched records increase (target: >= 36/43) |
| R2-AC4 | **Broadmeadows >= 31/31** on Gate 2 rerun | Benchmark confirmed |
| R2-AC5 | **Alexander >= 36/43** with all 6 buildings producing records | Per-building counts documented, all > 0 |
| R2-AC6 | Docling injection confirmed firing (not F2 fallback) for benchmark documents | Log: `_inject_docling_tables()` fired, no `[fallback.no_docling_tables]` |
| R2-AC7 | `ruff check .` clean | Zero errors |
| R2-AC8 | `pytest tests/` — no new failures introduced | Same or fewer failures than R1 baseline |

### Tasks

| # | Task | File(s) | Est |
|---|------|---------|-----|
| R2-T1 | Fix `RoomMeta` typing in LLM inventory compilation | `open_notebook/extractors/orchestrator.py` (or relevant inventory function) | 45m |
| R2-T1.1 | — Ensure LLM returns list of `RoomMeta` objects, not strings | | |
| R2-T1.2 | — Add type validation/coercion at inventory compilation boundary | | |
| R2-T2 | Normalize room/location names in extraction output | `open_notebook/extractors/orchestrator.py` or relevant extraction function | 30m |
| R2-T3 | Improve material/item description normalization | Extraction pipeline (prompt or post-processing) | 30m |
| R2-T4 | Write tests for RoomMeta typing fix | `tests/test_orchestrator.py` | 20m |
| R2-T5 | Run Gate 2 benchmark suite (full rerun) | Benchmark harness | 20m |
| R2-T6 | Document per-building Alexander counts | Benchmark report | 10m |
| R2-T7 | Lint + full test suite pass | `ruff check . && pytest tests/ -x` | 10m |

### Test Commands

```bash
# Verify RoomMeta typing fix
uv run pytest tests/test_orchestrator.py -k "roommeta or inventory" -x -v

# Full benchmark run (Gate 2 rerun)
uv run python scripts/research/e29_benchmark_harness.py

# Verify thresholds
uv run pytest tests/integration/test_benchmark_harness.py -x -v

# Lint
uv run ruff check .

# Full suite
uv run pytest tests/ -x
```

---

## Gate 2 Rerun — Go/No-Go Conditions

Gate 2 will be re-evaluated after R1 and R2 are both complete. The rerun must satisfy:

| # | Condition | Required |
|---|-----------|----------|
| 1 | R1 and R2 both merged to ACMV3 | Yes |
| 2 | Docling tables seeded in benchmark DB for Broadmeadows and Alexander | Yes |
| 3 | Broadmeadows >= 31/31 matched | Yes (hard floor) |
| 4 | Alexander >= 36/43 matched, all 6 buildings producing | Yes (hard floor) |
| 5 | Docling injection confirmed firing (not F2 fallback) | Yes |
| 6 | No new test failures introduced by R1/R2 | Yes |
| 7 | `ruff check .` clean | Yes |

**If Gate 2 rerun PASSES**: S5 is unblocked immediately.
**If Gate 2 rerun FAILS again**: PM will evaluate whether to adjust thresholds or add R3 remediation. No automatic waiver.

---

## Blocker List (Dev Handoff)

| # | Blocker | Affects | Owner | Resolution |
|---|---------|---------|-------|------------|
| B1 | No Docling tables in benchmark DB | R1-AC1, R1-AC5, G2.3 | Dev (R1) | Generate tables from PDFs, create seed script/fixture |
| B2 | RoomMeta typing bug — rooms as strings | R2-AC1, G2.1, G2.2 | Dev (R2) | Fix type coercion in inventory compilation |
| B3 | Matching normalization too strict | R1-AC2, R1-AC3, G2.1, G2.2 | Dev (R1) | Implement case/whitespace/abbreviation normalization |
| B4 | 7 pre-existing test failures (S3 graph wiring) | Test suite noise | Deferred to S7 | Unconditional edge invalidated old conditional tests |
| B5 | 4 pre-existing `test_field_config_api` failures | Test suite noise | Unrelated | API/DB test — not E29 scope |
| B6 | 1 pre-existing `test_source_commands_docling` failure | Test suite noise | E27-S2 | RecordID object vs string issue |
| B7 | OpenRouter token cost tracking (API 404) | G3.3 future | Deferred to Gate 3 | PM will evaluate waiver/manual estimation |

---

## Execution Timeline

```
R1 (benchmark fidelity)     ──────► R2 (match-gap remediation)  ──────► Gate 2 Rerun
  - Seed Docling tables                - Fix RoomMeta typing              - QA evaluates G2.1-G2.5
  - Normalize matching                 - Normalize room/material          - PM sign-off
  - Pin baseline artifacts             - Re-run benchmarks                - S5 unblocked if PASS
```

---

*Recovery spec generated 2026-03-01 by Bob (SM Agent). PM authorization: John (PM Agent) — see [Gate 2 PM Sign-Off](./e29-gate-decisions.md#pm-sign-off--gate-2).*
