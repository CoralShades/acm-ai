# Epic 29 — Pipeline Unification: Story Index

> **Epic**: E29 — Unified Agent Pipeline
> **Total**: 8 stories, 19 SP
> **Strategy**: Measure first -> unify -> decompose -> clean up
> **Generated**: 2026-03-01 by Bob (SM Agent)
> **Source of Truth**: [Execution Contract](../../V3/epic-29-execution-contract.md) (PM charter)

---

## Story Files

| ID | Title | SP | Phase | Status | File |
|----|-------|----|-------|--------|------|
| S1 | JSON Parser Resilience | 1 | 1 | `done` | [e29-s1-json-parser-resilience.md](./e29-s1-json-parser-resilience.md) |
| S2 | Benchmark Harness + Baseline Capture | 3 | 1 | `done` | [e29-s2-benchmark-harness-baseline-capture.md](./e29-s2-benchmark-harness-baseline-capture.md) |
| S3 | Unified Orchestrator Path | 3 | 2 | `done` | [e29-s3-unified-orchestrator-path.md](./e29-s3-unified-orchestrator-path.md) |
| S4 | Capability Registry + Fallback Contract | 2 | 2 | `done` | [e29-s4-capability-registry-fallback-contract.md](./e29-s4-capability-registry-fallback-contract.md) |
| S5 | Agent Decomposition I — Table Parser + BAR Mapper | 3 | 3 | `drafted` (blocked Gate 2) | [e29-s5-agent-decomposition-table-parser-bar-mapper.md](./e29-s5-agent-decomposition-table-parser-bar-mapper.md) |
| S6 | Agent Decomposition II — Enricher/Classifier/Validator | 3 | 3 | `drafted` (blocked Gate 2) | [e29-s6-agent-decomposition-enricher-classifier-validator.md](./e29-s6-agent-decomposition-enricher-classifier-validator.md) |
| S7 | Dual-Benchmark Validation + Legacy Cleanup | 2 | 4 | `drafted` (blocked Gate 2) | [e29-s7-validation-gate-legacy-cleanup.md](./e29-s7-validation-gate-legacy-cleanup.md) |
| S8 | Export Hardening + Integration Tests + Doc Alignment | 2 | 4 | `drafted` (blocked Gate 2) | [e29-s8-export-hardening-integration-doc-alignment.md](./e29-s8-export-hardening-integration-doc-alignment.md) |
| **R1** | **Benchmark Fidelity + Docling Table Testability** | **2** | **Recovery** | `drafted` | [e29-gate2-recovery-spec.md](./e29-gate2-recovery-spec.md#e29-r1-benchmark-fidelity--docling-table-testability-2-sp) |
| **R2** | **Match-Gap Remediation** | **2** | **Recovery** | `drafted` | [e29-gate2-recovery-spec.md](./e29-gate2-recovery-spec.md#e29-r2-match-gap-remediation--inventory-typing--normalization-2-sp) |

---

## Decision Gates

Full gate tracking: [e29-gate-decisions.md](./e29-gate-decisions.md)

| Gate | After | Blocks | Key Criteria | Status |
|------|-------|--------|--------------|--------|
| Gate 1 | S2 | S3-S8 | >=3 benchmarks, ground truth, baseline metrics, CI entry | **PASS** (2026-03-01) |
| Gate 2 | S4 | S5-S8 | Broadmeadows 31/31, Alexander >=36/43, Docling confirmed | **FAIL** (2026-03-01) — Recovery R1+R2 in progress |
| Gate 3 | S6 | S7-S8 | No regression +/-2, latency/cost within thresholds | PENDING |
| Gate 4 | S8 | — | E2E tests, benchmark pass, docs aligned, CI green | PENDING |

---

## Dependency Graph

```
S1 (JSON Parser) ─────────┐
                           ▼
S2 (Benchmark Harness) ──► GATE 1 ✅ PASS (baseline captured)
                           │
                           ▼
S3 (Unified Path) ─────┐
                        ▼
S4 (Strategy Registry) ► GATE 2 ❌ FAIL (parity not yet met)
                           │
                           ▼  ◄── RECOVERY LOOP
                     R1 (Benchmark Fidelity)
                           │
                           ▼
                     R2 (Match-Gap Remediation)
                           │
                           ▼
                     GATE 2 RERUN
                           │
                           ▼
S5 (Table Parser + BAR) ──┐
                           ▼
S6 (Enricher/Classifier) ► GATE 3 (no regression)
                           │
                           ▼
S7 (Validation + Cleanup) ─┐
                            ▼
S8 (Export + Docs) ────────► GATE 4 (release ready)
```

---

## Parallelization Opportunities

### Confirmed Parallel Tracks

| Track A | Track B | Constraint |
|---------|---------|------------|
| **S1** (JSON Parser) | **S2** (Benchmark Harness) — ground truth creation, harness structure | S2 cannot PASS Gate 1 until S1 is merged |

### Within-Story Parallelization

| Story | Parallel Subtasks |
|-------|-------------------|
| S2 | Ground truth creation (T2-T3) can run parallel to harness implementation (T4) |
| S5 | `table_parser.py` (T1) and `bar_mapper.py` (T2) can be developed in parallel |
| S6 | `classifier.py` (T1), `context_enricher.py` (T2), and `validator.py` (T3) in parallel |
| S8 | Backend (T1) and frontend (T2) in parallel; doc updates (T6-T9) independent of tests (T3-T4) |

---

## Threshold Reference

> **Authoritative thresholds** (resolves wording drift across E29 artifacts):
>
> | Metric | Gate 2 Floor (S4) | S7 Stretch Target | S7 PM-Approved Fallback |
> |--------|-------------------|--------------------|-------------------------|
> | Broadmeadows | 31/31 | 31/31 | 31/31 (non-negotiable) |
> | Alexander | >= 36/43 | >= 40/43 | >= 36/43 (requires PM sign-off) |

---

## Related Documents

- [Execution Contract](../../V3/epic-29-execution-contract.md) — PM charter (supersedes all prior E29 artifacts)
- [Architecture Delta](../../docs/architecture/e29-architecture-delta.md) — Current-state vs target-state, fallback matrix, file impact map
- [Reconciled YAML](../../V3/epic-29-pipeline-unification.reconciled.yaml) — Reconciliation source (superseded by execution contract)
- [Gate Decisions](./e29-gate-decisions.md) — Gate pass/fail tracking

---

*Index generated 2026-03-01 by Bob (SM Agent).*
