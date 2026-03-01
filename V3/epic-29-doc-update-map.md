# Epic 29 Documentation Update Map

This map identifies exactly where PRD/architecture/epics artifacts should be patched
to align with the reconciled Epic 29 plan.

Reference plan: `V3/epic-29-pipeline-unification.reconciled.yaml`

---

## P0 Updates (must update before implementation starts)

### 1) PRD

File: `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md`

| Section | Location | Change Type | Required Patch |
|---|---|---|---|
| `### 3.1 Performance (NFR-100 Series)` | `03-prd.md:196` | Replace table rows | Add benchmark-gated NFRs: benchmark recall/precision/field-accuracy thresholds, latency/token budgets, and regression policy (no unapproved degradation). |
| `### 5.4 Extraction Pipeline Architecture` | `03-prd.md:581` | Rewrite section | Replace old 7-stage narrative with unified orchestrator path contract, fallback contract, and decision-gate model for E29. |
| `### 7.1 Test Data` and `### 7.2 Test Scenarios` | `03-prd.md:728`, `03-prd.md:743` | Expand scenarios | Add 3+ benchmark harness requirement and explicit Broadmeadows/Alexander/third-format regression tests tied to gate criteria. |
| `### C. Change Log` | `03-prd.md:820` | Append entry | Add dated E29 entry summarizing pipeline unification, benchmark harness, and cleanup gating. |

---

### 2) Technical Architecture (BMAD artifact)

File: `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md`

| Section | Location | Change Type | Required Patch |
|---|---|---|---|
| `## 5. ACM Extraction Pipeline` | `04-architecture.md:551` | Rewrite (major) | Replace stale/corrupted pipeline diagram block with clean ASCII/Markdown diagram of unified routing and gate checkpoints. |
| `### 5.1.3 MinerU Integration` | `04-architecture.md:651` | Replace section | Remove legacy MinerU-primary framing; document current Docling Direct + orchestrator table injection behavior. |
| `### 5.2 Generic Configurable Parser Architecture` | `04-architecture.md:678` | Extend section | Add strategy/capability registry and decomposition touchpoints (Table Parser, BAR Mapper, Enricher, Validator). |
| `### 5.4 Pipeline Observability` | `04-architecture.md:814` | Expand section | Add benchmark telemetry model and decision-gate pass/fail event model. |
| `## Appendix A: File Locations Summary` | `04-architecture.md:1733` | Append entries | Add new E29 files/modules and benchmark artifacts. |

---

### 3) Epics and Stories

File: `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md`

| Section | Location | Change Type | Required Patch |
|---|---|---|---|
| Header metadata and change log | `05-epics-and-stories.md:4`, `05-epics-and-stories.md:6` | Update header | Update date/status and append 2026-03-01 reconciliation note for Epic 29. |
| `## Epic Overview` table | `05-epics-and-stories.md:10` | Update rows | Add E28 and E29 rows, and correct stale statuses where needed to match current sprint tracker. |
| `## Story Dependencies` | `05-epics-and-stories.md:925` | Append chain | Add E29 dependency chain and decision gates (S1->S2->S3->S4->S5->S6->S7->S8). |
| End of file (after Epic 28) | `05-epics-and-stories.md:2627` | Append new epic | Add full Epic 29 section with S1-S8 story definitions, AC summaries, and gate criteria. |

---

### 4) Sprint Tracker

File: `docs/sprint-artifacts/sprint-status.yaml`

| Section | Location | Change Type | Required Patch |
|---|---|---|---|
| Top-level `updated` + reconciliation note | `sprint-status.yaml:37`, `sprint-status.yaml:44` | Update fields | Set new updated date and add E29 reconciliation note with baseline goals and gate framing. |
| Development status block | Around `sprint-status.yaml:368` (after epic-28) | Append statuses | Add `epic-29` and `e29-s1..e29-s8` entries (initially `drafted`/`backlog` per readiness). |
| Summary comments | `sprint-status.yaml:417` onward | Update counts | Adjust total epic/story counts and completed/in-progress lists once E29 entries are added. |

---

## P1 Updates (align supporting architecture docs)

### 5) Structured Output Assessment

File: `docs/architecture/pipeline-structured-output-assessment.md`

| Section | Location | Change Type | Required Patch |
|---|---|---|---|
| Executive summary and recommendation framing | `pipeline-structured-output-assessment.md:11`, `pipeline-structured-output-assessment.md:15` | Addendum update | Add a 2026-03 addendum noting what is now complete vs pending under E27/E29. |
| Recommendations | `pipeline-structured-output-assessment.md:171` | Status update | Mark completed recommendations and re-scope remaining items into E29 stories/gates. |
| Priority and scoping | `pipeline-structured-output-assessment.md:223` | Refresh table | Replace old epic mapping with current E29 mapping and benchmark-gated execution order. |

---

### 6) TableFormer Technical Design

File: `docs/architecture/tableformer-technical-design.md`

| Section | Location | Change Type | Required Patch |
|---|---|---|---|
| Document status | `tableformer-technical-design.md:8` | Update status | Mark as superseded/historical so it does not conflict with current production path. |
| Architecture principle and flow claims | `tableformer-technical-design.md:35`, `tableformer-technical-design.md:42` | Annotate | Add "historical design" note and point to active pipeline docs. |
| Legacy pipeline references | `tableformer-technical-design.md:223` | Clarify references | Mark `prepare_context/extract_records` references as legacy-only to avoid contradiction with unified path. |

---

## Suggested Patch Order

1. `03-prd.md` (requirements contract)
2. `04-architecture.md` (technical contract)
3. `05-epics-and-stories.md` (execution contract)
4. `sprint-status.yaml` (tracker contract)
5. Supporting docs under `docs/architecture/`

This order keeps requirements -> design -> execution -> tracking aligned and reduces
cross-document drift during Epic 29 rollout.
