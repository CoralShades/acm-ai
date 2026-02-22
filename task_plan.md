# Task Plan — Next Sprint: 7 Remaining Stories

Updated: 2026-02-22 (Sprint Planning)
Source of truth: `docs/sprint-artifacts/sprint-status.yaml`

---

## Sprint Summary

- **Total Stories**: 122
- **Done**: 104 (85%)
- **Ready for Dev**: 7
- **Archived**: 10 (E8)
- **Completed Epics**: E1, E2, E3, E4, E5, E6, E7, E11, E14, E15, E16, E17 (12/17)
- **Remaining Epics**: E9 (1 story), E10 (1 story), E12 (3 stories), E13 (2 stories)

---

## Sprint Order (7 Stories)

| # | Story | Title | Size | Epic | Deps |
|---|-------|-------|------|------|------|
| 1 | E10-S1 | Simplify Navigation | S | E10 | None |
| 2 | E9-S3 | Document Actions & Bulk Operations | M | E9 | None |
| 3 | E12-S2 | AI Model Configuration UI | M | E12 | E12-S1 (done) |
| 4 | E12-S3 | Processing Options Configuration | M | E12 | E12-S1 (done) |
| 5 | E12-S4 | BAR Field Schema Config UI | M | E12 | E12-S1 (done) |
| 6 | E13-S2 | Knowledge Graph API & Data Service | M | E13 | E13-S1 (done) |
| 7 | E13-S3 | React Flow Knowledge Graph Visualization | L | E13 | E13-S2 |

### Dependency Matrix

```
TIER 0 — Independent (ready now):
  E10-S1  Simplify Navigation              [Frontend, S]
  E9-S3   Document Actions & Bulk Ops      [Frontend+Backend, M]

TIER 1 — Unblocked (deps done):
  E12-S2  AI Model Configuration UI        [Frontend+Backend, M]
  E12-S3  Processing Options Configuration [Frontend+Backend, M]
  E12-S4  BAR Field Schema Config UI       [Frontend+Backend, M]
  E13-S2  Knowledge Graph API & Data       [Backend, M]

TIER 2 — Blocked by Tier 1:
  E13-S3  React Flow Knowledge Graph Viz   [Frontend, L] → blocked by E13-S2
```

---

## Previous Sprints

### Ralph Sprint (2026-02-22): 11 stories completed
E2-S8, E2-S11, E16-S3, E1-S23, E5-S3, E16-S1, E12-S1, E13-S1, E15-S2, E5-S4, E11-S2

### Epic 17 (2026-02-22): 6 stories implemented
E17-S1..S6 (AG-UI extraction, A2A agent card, OpenRouter models)

### Bug Triage (2026-02-21): 10 stories completed
7 bug fixes + E1-S28/S29/S30 (model capabilities, dynamic token limits)
