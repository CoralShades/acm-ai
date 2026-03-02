# E29-S8: Export Hardening + Integration Tests + Documentation Alignment

> **Epic**: E29 — Pipeline Unification
> **Story Points**: 2 | **Phase**: 4 | **Owner**: Full-Stack Dev
> **Decision Gate**: Gate 4 (Release Readiness) exits after this story
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
| Blocked By | S7 (validation + cleanup) |

---

## User Story

> As a **compliance officer**, I want to export ACM records filtered by building and ACM type (not just by source), and I want the export column structure driven by `field_schema`, so that I can generate targeted compliance reports.

---

## Dependencies

| Type | Item | Status |
|------|------|--------|
| Story | E29-S7 (cleanup complete) | Must be merged |

---

## Acceptance Criteria

| # | Criterion | Measurable Check |
|---|-----------|------------------|
| AC-1 | Per-building export: filter records by `building_name` | API endpoint accepts `?building=X` parameter; CSV contains only that building's records |
| AC-2 | Per-ACM-type export: filter records by `product_type` | API endpoint accepts `?acm_type=Y` parameter; CSV filtered accordingly |
| AC-3 | Export columns are schema-driven from `field_schema` | Column order matches active `field_mapping` (already partially implemented) |
| AC-4 | Integration test: upload -> extract -> validate -> save -> export | `test_unified_pipeline.py` passes |
| AC-5 | Performance baseline documented | Pre-E29 vs post-E29 comparison in report |
| AC-6 | PRD updated to E29 reality | `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` updated |
| AC-7 | Architecture doc updated | `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` updated |
| AC-8 | Epics list updated | `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` updated |
| AC-9 | Sprint status updated | `docs/sprint-artifacts/sprint-status.yaml` updated |
| AC-10 | `ruff check .` + `pytest tests/ -x` + `npm run build` all pass | CI green |

---

## Tasks / Subtasks

| # | Task | File(s) | Est |
|---|------|---------|-----|
| T1 | Add per-building and per-ACM-type query parameters to export endpoints | `api/routers/acm.py` | 30m |
| T1.1 | — Add `building` optional query param to `/export/csv` and `/export/excel` | | |
| T1.2 | — Add `acm_type` optional query param to both endpoints | | |
| T1.3 | — Filter records before CSV/Excel generation | | |
| T2 | Update/create frontend export UI | `frontend/src/components/ExportDialog.tsx` or existing export component | 45m |
| T2.1 | — Building selector dropdown (populated from extracted buildings) | | |
| T2.2 | — ACM type selector dropdown | | |
| T2.3 | — Export format selection (CSV/Excel) | | |
| T3 | Write export integration tests | `tests/test_export.py` (new) | 45m |
| T4 | Write E2E unified pipeline test | `tests/test_unified_pipeline.py` (new) | 60m |
| T4.1 | — Upload document | | |
| T4.2 | — Trigger extraction (unified path) | | |
| T4.3 | — Validate records saved | | |
| T4.4 | — Export and verify CSV content | | |
| T5 | Document performance baseline (pre-E29 vs post-E29) | `docs/reviews/e29-baseline-benchmark-report.md` (append) | 20m |
| T6 | Update PRD | `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` | 20m |
| T7 | Update architecture doc | `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` | 20m |
| T8 | Update epics and stories list | `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` | 15m |
| T9 | Update sprint status | `docs/sprint-artifacts/sprint-status.yaml` | 10m |
| T10 | Full CI check | `ruff check . && pytest tests/ -x && cd frontend && npm run build` | 15m |

**Within-story parallelism**: T1 (backend) and T2 (frontend) can run in parallel. T6-T9 (doc updates) are independent of T3-T4 (tests).

---

## Repeatable Command Entrypoints

```bash
# Run E2E pipeline test
uv run pytest tests/test_unified_pipeline.py -x -v

# Run export tests
uv run pytest tests/test_export.py -x -v

# Run full benchmark suite (final)
uv run python scripts/research/e29_benchmark_harness.py --all

# Full CI check
uv run ruff check . && uv run pytest tests/ -x && cd frontend && npm run build
```

---

## Test Strategy

- **Integration tests** (`tests/test_export.py`):
  - Export all records (default) — backward compatible
  - Export filtered by building — only that building's records
  - Export filtered by ACM type — only matching records
  - Export filtered by both building + ACM type
  - Schema-driven columns match field_mapping
- **E2E tests** (`tests/test_unified_pipeline.py`):
  - Full pipeline: upload -> extract -> validate -> save -> export
  - Verify record count matches expected
  - Verify export CSV content matches saved records
- **Frontend build**: `npm run build` passes
- **Benchmark**: Full suite passes, all documents >= final gate thresholds

---

## Touched Files

| File | Action | Lines (est) |
|------|--------|-------------|
| `api/routers/acm.py` | Modify | ~30 |
| `frontend/src/components/ExportDialog.tsx` | Add/Modify | ~100 |
| `tests/test_export.py` | Add (new) | ~150 |
| `tests/test_unified_pipeline.py` | Add (new) | ~200 |
| `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` | Modify | ~30 |
| `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` | Modify | ~50 |
| `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` | Modify | ~20 |
| `docs/sprint-artifacts/sprint-status.yaml` | Modify | ~10 |

---

## Gate 4 Exit — Go/No-Go Reference

This story exits **Gate 4 (Release Readiness)**. Full checklist in [e29-gate-decisions.md](./e29-gate-decisions.md#gate-4--release-readiness-after-s8).

| # | Criterion | Status |
|---|-----------|--------|
| G4.1 | E2E tests pass | Pending |
| G4.2 | Benchmark suite passes | Pending |
| G4.3 | PRD updated | Pending |
| G4.4 | Architecture doc updated | Pending |
| G4.5 | Epics list updated | Pending |
| G4.6 | Sprint status updated | Pending |
| G4.7 | ruff clean | Pending |
| G4.8 | pytest green | Pending |
| G4.9 | npm build green | Pending |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Export filtering breaks existing downloads | Filters are optional params; default behavior unchanged |
| Frontend ExportDialog.tsx doesn't exist | May need to modify existing export trigger in source detail page |
| Doc updates miss something | Checklist-driven; Gate 4 requires diff evidence for all 4 doc files |

---

## QA Checklist

- [ ] AC-1: Per-building export works
- [ ] AC-2: Per-ACM-type export works
- [ ] AC-3: Export columns match field_mapping
- [ ] AC-4: E2E pipeline test passes
- [ ] AC-5: Performance baseline documented
- [ ] AC-6: PRD updated
- [ ] AC-7: Architecture doc updated
- [ ] AC-8: Epics list updated
- [ ] AC-9: Sprint status updated
- [ ] AC-10: Full CI green (ruff + pytest + npm build)
- [ ] Gate 4 criteria all PASS

---

## Post-Dev Notes

_To be filled by the developer after implementation._

---

## Post-QA Notes

_To be filled by QA after verification._
