# Sprint Change Proposal - Epic 24: Docling TableFormer Activation

**Date:** 2026-02-27
**ID:** SCP-20260227
**Status:** PROPOSED
**Priority:** P0
**Scope:** Medium (4 stories, 5 SP)
**Risk:** Low
**Path:** New Epic 24 (4 stories)
**Trigger:** E23 validation closed at 28/31 (90.3%). E20-S6 investigation proved 17/31 was the Docling input quality ceiling. Mary's research spike confirmed TableFormer is already installed and requires configuration-only activation. Winston's ADR (ADR-001) and technical design provide the implementation blueprint.

---

## 1. Motivation

### Problem Statement

E23 achieved 28/31 (90.3%) on Broadmeadows through prompt engineering and content normalization. However, E20-S6 proved that the remaining 3 missing records represent a **Docling input quality ceiling** — no amount of prompt iteration can recover records whose table structure is lost during PDF-to-markdown conversion.

The 3 missing records are all "Not Sampled" / "No Access" entries that appear in the PDF as table rows with merged cells, sparse data, and multi-line column values. Docling's basic markdown mode produces broken pipe-delimited rows for these cases.

### Solution

TableFormer is a deep learning table structure recognition model **already bundled with Docling** in ACM-AI's dependency chain. Activation requires only 3 configuration keys in `source.py:content_process()`. TableFormer detects cell boundaries, merged cells, and multi-line values, producing clean markdown tables that the LLM can parse without ambiguity.

### Evidence Base

| Source | Finding |
|--------|---------|
| Mary's Research Spike (2026-02-27) | TableFormer available, config-only activation, +6.5-9.7% accuracy projected |
| Winston's ADR-001 | Decision: Activate TableFormer (D1), Remove MinerU (D2), Enhanced markdown not bypass (D3) |
| Winston's Technical Design | 4-story Phase 1 MVP at 5 SP, zero new dependencies, automatic fallback |
| E20-S6 Investigation | Proved 17/31 is Docling quality ceiling, not a prompt gap |
| E23 Validation | 28/31 achieved via prompt engineering, 3 remaining = table structure gap |

---

## 2. Proposed Change - New Epic 24

### Epic 24: Docling TableFormer Activation & Structured Table Extraction

**Goal:** Activate Docling's TableFormer model for structured table extraction, replacing raw markdown with DataFrame-quality table input for the LLM.

**Success Metric:** Broadmeadows >= 30/31 (96.8%), Alexander maintains 54/54 (100%)

| Story | Title | Priority | Effort | Area | Outcome |
|-------|-------|----------|--------|------|---------|
| E24-S1 | Activate TableFormer in Source Processing | P0 | S/M (2 SP) | Backend | TableFormer enabled via feature flag, enhanced markdown in full_text |
| E24-S2 | Broadmeadows & Alexander Accuracy Validation | P0 | S (1 SP) | Testing | Evidence-based decision gate for flag promotion |
| E24-S3 | Remove MinerU Dead Code | P1 | S (1 SP) | Backend | 727 lines dead code + 43 dead tests removed |
| E24-S4 | Docker Model Weight Pre-Download | P1 | S (1 SP) | DevOps | Containerized deployments work offline |

**Total Phase 1 (MVP):** 4 stories, 5 story points

### Stories NOT Included (Deferred to Phase 2)

Per Winston's technical design, these are explicitly **Phase 2 (future epic)** items:

| Deferred Item | Winston's Rationale |
|---------------|---------------------|
| Store structured tables in acm_table_section | "Phase 1: No schema changes required" (Section 4A) |
| Feed TableFormer data to orchestrator | "No change required for Phase 1" (Section 3A) — full_text already improved |
| Frontend structured table viewer | "No changes needed for Phase 1" (Section 5B) |

These become candidates for a future Epic 25 if Phase 1 validation confirms value.

---

## 3. Dependency Chain

Implementation order for lowest risk and fastest feedback:

```
E24-S1 (Activate)  ─────────────────┐
         │                           │
         ▼                           │  (parallel track)
E24-S2 (Validate)                    │
         │                           │
         ▼                           ▼
E24-S4 (Docker) ◄──── E24-S3 (MinerU Cleanup)
```

1. **E24-S1 first** — minimum viable change, ships with flag OFF
2. **E24-S2 immediately after S1** — validates accuracy before promoting flag
3. **E24-S3 in parallel** — no dependency on S1, can start immediately
4. **E24-S4 last** — requires S1 code to exist for Docker build step

---

## 4. Story Artifacts Created

- `docs/sprint-artifacts/e24-s1-activate-tableformer.md`
- `docs/sprint-artifacts/e24-s2-accuracy-validation.md`
- `docs/sprint-artifacts/e24-s3-remove-mineru-dead-code.md`
- `docs/sprint-artifacts/e24-s4-docker-model-predownload.md`

---

## 5. Impact Analysis

### Product Impact

- Extraction accuracy improvement: 90.3% -> 97-100% (projected) on Broadmeadows
- Alexander regression protection: explicit validation gate in E24-S2
- No user-facing changes — same API shape, better data quality

### Technical Impact

- **Zero new dependencies** — torch, Docling, TableFormer all installed
- Processing time increase: +15-30s per PDF (5s -> 20-35s), within 120s polling budget
- Memory increase: +2-4 GB during table inference
- Codebase reduction: -727 lines dead code, -43 dead tests (MinerU removal)

### Quality Impact

- Feature flag (`DOCLING_TABLE_STRUCTURE`) enables safe A/B testing
- Automatic fallback: TableFormer failure -> basic Docling markdown
- Explicit decision gate: no flag promotion without >= 30/31 validation

### Rollback Plan

1. Set `DOCLING_TABLE_STRUCTURE=false` in `.env`
2. Restart worker process
3. Reprocess affected sources
4. No data migration needed — `source.full_text` is overwritten on reprocess

---

## 6. Files Changed by This Proposal

| File | Change |
|------|--------|
| `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260227-tableformer.md` | This SCP |
| `docs/sprint-artifacts/e24-s1-activate-tableformer.md` | New story |
| `docs/sprint-artifacts/e24-s2-accuracy-validation.md` | New story |
| `docs/sprint-artifacts/e24-s3-remove-mineru-dead-code.md` | New story |
| `docs/sprint-artifacts/e24-s4-docker-model-predownload.md` | New story |
| `docs/sprint-artifacts/sprint-status.yaml` | Added Epic 24 and story statuses |

---

## 7. Guard Rails

- Planning only: this SCP adds and updates planning artifacts only, no product code modifications.
- Scope locked to Winston's Phase 1 MVP (4 stories, 5 SP). Phase 2 items explicitly deferred.
- Feature flag default is OFF — promotion requires passing E24-S2 decision gate.
- Dependency order enforced: E24-S1 first, E24-S2 validates, E24-S3 parallel, E24-S4 last.

---

## 8. Related Documents

- ADR: `docs/architecture/adr-tableformer-integration.md`
- Technical Design: `docs/architecture/tableformer-technical-design.md`
- Research Spike: `docs/research/tableformer-research-spike-20260227.md`
- E23 Validation: `docs/reviews/e23-validation-results.md`
- E20-S6 Investigation: `docs/reviews/e20-s6-validation-results.md`
