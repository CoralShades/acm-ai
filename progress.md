# Sprint Status — 2026-02-21

> Source: `docs/sprint-artifacts/sprint-status.yaml` (updated 2026-02-21)
> Last reconciled: 2026-02-21 — Bug Triage Plan: 10 stories implemented + BMAD artifacts created

---

## Done (85 stories, 75%)

### Epic 1 — ACM Data Extraction Pipeline (29/30 done)
| Story ID | Title |
|----------|-------|
| E1-S1  | Create ACM Data Model |
| E1-S2  | Create ACM Record Domain Model |
| E1-S3  | Implement ACM Extraction Transformation |
| E1-S4  | Create ACM API Endpoints |
| E1-S5  | Integrate ACM Extraction into Source Processing |
| E1-S6  | Configure Local Embedding Pipeline |
| E1-S7  | AI-Powered ACM Extraction |
| E1-S8  | Site Configuration Data Entry |
| E1-S9  | ACM Product Classification |
| E1-S10 | MinerU Table Extraction |
| E1-S11 | Generic Configurable Parser |
| E1-S12 | Consultant Wording Normalization |
| E1-S13 | Fix Page Reference Tracking |
| E1-S14 | Contextual Embedding Enrichment |
| E1-S15 | Corrective RAG Validation Loop |
| E1-S16 | Document Structure TOC Extraction |
| E1-S17 | Building Inventory Compilation |
| E1-S18 | Page-Level Section Tagging |
| E1-S19 | Document Metadata Extraction Enhancement |
| E1-S20 | Agentic Extraction Orchestrator |
| E1-S21 | Extraction Pipeline Observability |
| E1-S22 | Extraction Output Token Limit Fix |
| E1-S24 | Fix Assumed Positive Detection |
| E1-S25 | Fix External/Internal Location Merging |
| E1-S26 | Reduce False Positive Extraction |
| E1-S27 | Handle Duplicate Room Items Edge Case |
| BUG-negative-results-regression | Negative Results Silent Dropping Fix |
| E1-S28 | Model Capabilities Schema & Configuration |
| E1-S29 | Replace Hardcoded Token Limits |
| E1-S30 | Dynamic Embedding Dimensions |

### Epic 2 — AG Grid Spreadsheet Integration (10/12 done)
(unchanged — E2-S8, E2-S11 remain ready-for-dev)

### Completed Epics
- Epic 3 (4/4), Epic 4 (4/4), Epic 6 (4/4), Epic 7 (7/7), Epic 14 (11/11)

### Other Done Stories
- E5-S1, E5-S2 (Epic 5)
- E9-S1, E9-S2 (Epic 9)
- E8-S11 (Epic 8)
- E11-S1 (Epic 11)
- E15-S1 (Epic 15)
- E16-S2 (Epic 16)
- bug-extraction-status-tracking-gap, e2e-ci-github-actions-setup (Infrastructure)

### Bug Triage Sprint (2026-02-21) — 10 Stories Done
| Story ID | Title | Epic |
|----------|-------|------|
| bug-site-config-query-fix | Null guard on getConfigTemplates() | Standalone |
| bug-grid-column-fixes | Building Code rename, merged ACM Product Type | E2 |
| bug-post-upload-navigation | Navigate to source detail after upload | E7 |
| bug-ui-ux-vaea-branding | VAEA branding, command palette, TabsList | E14 |
| bug-auth-loading-ux | Skeleton layout replacing blank spinner | E14 |
| bug-extraction-progress-fix | Semantic design tokens for progress panel | E15 |
| bug-negative-results-regression | Extended Unknown placeholders to negatives | E1 |
| E1-S28 | Model Capabilities Schema & Configuration | E1 |
| E1-S29 | Replace Hardcoded Token Limits | E1 |
| E1-S30 | Dynamic Embedding Dimensions | E1 |

---

## Ready for Dev (8 stories)

| # | Story ID | Title | Notes |
|---|----------|-------|-------|
| 1 | **E9-S3**  | Document Actions & Bulk Operations | Independent |
| 2 | **E16-S1** | Dashboard Home with ACM Stats | Large effort |
| 3 | **E16-S3** | Empty States & Onboarding Hints | Quick win |
| 4 | **E10-S1** | Simplify Navigation | Independent |
| 5 | **E2-S8**  | Column Visibility Management | Partial coverage from PR #30 |
| 6 | **E5-S3**  | BAR Template Management | Unblocks E5-S4 |
| 7 | **E1-S23** | Token Limit Quality Validation | Haiku 8K vs Sonnet 32K quality |
| 8 | **E2-S11** | BAR Field Type Safety | Partial coverage from PR #30 |

---

## Drafted (8 stories)

| Story ID | Title | Blocked By |
|----------|-------|------------|
| E5-S4  | Export Field Mapping Configuration | E5-S3 |
| E11-S2 | Hybrid Search Service | — (large effort) |
| E12-S1 | Extraction Method Settings UI | — |
| E12-S2 | AI Model Configuration UI | E12-S1 |
| E12-S3 | Processing Options Configuration | E12-S1 |
| E12-S4 | BAR Field Schema Config UI | E12-S1 |
| E13-S1 | SurrealDB Graph Entity Schema | — |
| E15-S2 | Dedicated Extraction Monitor Page | E15-S1 (now done) |

---

## Summary

| Status | Count |
|--------|-------|
| Done | 85 (75%) |
| Ready-for-dev | 8 |
| Drafted | 8 |
| Backlog | 2 |
| Archived | 10 |
| **Total** | **114** |

**Epics:** 5 done (E3, E4, E6, E7, E14) · 7 in-progress (E1, E2, E5, E9, E11, E15, E16) · 3 backlog (E10, E12, E13) · 1 archived (E8)

**Next up:** E9-S3 Bulk Document Actions → E16-S1 Dashboard Home → E16-S3 Empty States

---

## Session Log

### 2026-02-21 — Bug Triage Plan Implementation
- **Scope**: 11 bugs triaged → 10 stories implemented across 4 phases
- **Implementation**: 29 files changed, +222/-86 lines
- **Build status**: Frontend build PASS, Backend lint PASS
- **BMAD artifacts**: 10 story files created in docs/sprint-artifacts/, sprint-status.yaml updated
- **Deferred**: Favicon conversion (needs image tools), SSE state persistence (extraction-progress hook)
- **Key insight**: "haiku" string-match pattern was testing SurrealDB record IDs, not model names — fundamentally broken
