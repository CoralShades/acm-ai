# Task Plan — Remaining Stories

Updated: 2026-02-21
Source of truth: `docs/sprint-artifacts/sprint-status.yaml`

**30 stories remaining** (7 ready-for-dev, 11 drafted, 2 backlog, 10 archived)

---

## P0 — Tier 1: High Value, All Dependencies Satisfied

All have tech-specs in `docs/sprint-artifacts/`. Implement in this order:

| # | Story | Title | Size | Notes |
|---|-------|-------|------|-------|
| 1 | E16-S2 | ACM Record Detail Slide-Out Panel | M | High user value |
| 2 | E15-S1 | Extraction Log Panel in Document Library | M | Unblocks E15-S2 |
| 3 | E9-S3 | Document Actions & Bulk Operations | M | Has tech-spec |
| 4 | E16-S1 | Dashboard Home Page with ACM Stats | L | |
| 5 | E16-S3 | Empty States & Onboarding Hints | S | Quick win |
| 6 | E10-S1 | Simplify Navigation | S | Independent |

## P1 — Tier 2: Foundation Work

| # | Story | Title | Size | Notes |
|---|-------|-------|------|-------|
| 7 | E12-S1 | Extraction Method Settings UI | M | Unblocks E12-S2, E12-S3 |
| 8 | E2-S8 | Column Visibility Management | M | PR #30 partial coverage (hide:true) |
| 9 | E5-S3 | BAR Template Management | M | Unblocks E5-S4 |
| 10 | E1-S23 | Token Limit Quality Validation | M | Haiku 8K vs Sonnet 32K on large buildings |
| 11 | E2-S11 | BAR Field Type Safety | S | PR #30 partial coverage (Pydantic schema) |

## P2 — Tier 3: Blocked Until Tier 2

| # | Story | Title | Blocked By |
|---|-------|-------|------------|
| 12 | E15-S2 | Dedicated Extraction Monitor Page | E15-S1 |
| 13 | E5-S4 | Export Field Mapping Configuration | E5-S3 |
| 14 | E12-S2 | AI Model Configuration UI | E12-S1 |
| 15 | E12-S3 | Processing Options Configuration | E12-S1 |
| 16 | E12-S4 | BAR Field Schema Configuration UI | E12-S1 |
| 17 | E13-S1 | SurrealDB Graph Entity Schema | — (lowest priority) |
| 18 | E13-S2 | Knowledge Graph API & Data Service | E13-S1 |
| 19 | E13-S3 | React Flow Knowledge Graph Visualization | E13-S2 |
| 20 | E11-S2 | Hybrid Search Service | Large effort, after E11-S1 settles |

## Archived (10)

E8-S1 through E8-S10 — Bento Grid Design epic skipped by decision 2026-02-08.

---

### Notes

- Stories are prioritized by the NEXT RECOMMENDED ACTIONS section in `sprint-status.yaml`.
- E1-S23 is the only incomplete E1 story (26/27 done).
- Completed epics: E3, E4, E6, E7, E14 (all stories done).
- New stories should be added through the BMAD workflow (`/bmad:bmm:workflows:create-story`).
