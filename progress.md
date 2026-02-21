# Sprint Status — 2026-02-21

> Source: `docs/sprint-artifacts/sprint-status.yaml` (updated 2026-02-21)
> Last reconciled: 2026-02-21 — E16-S2 ACM Record Detail Panel implemented

---

## Done ✅ (75 stories)

### Epic 1 — ACM Data Extraction Pipeline (26/27 done)
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

### Epic 2 — AG Grid Spreadsheet Integration (10/12 done)
| Story ID | Title |
|----------|-------|
| E2-S1  | Install and Configure AG Grid |
| E2-S2  | Create ACMSpreadsheet Component |
| E2-S3  | Implement Column Sorting and Filtering |
| E2-S4  | Implement Row Grouping |
| E2-S5  | Implement Risk Status Color Coding |
| E2-S6  | Add Search Bar to Spreadsheet |
| E2-S7  | Implement Building Tab Navigation |
| E2-S9  | ACM Grid UX Improvements |
| E2-S10 | Fix Test Portability (hardcoded paths) |
| E2-S12 | Missing BAR Fields in Grid (7 BAR columns) |

### Epic 3 — Cell Citations & PDF Viewer (4/4 done) ✓
| Story ID | Title |
|----------|-------|
| E3-S1 | Make Cells Clickable |
| E3-S2 | Create PDF Viewer Modal |
| E3-S3 | Implement ACM Citation Reference Type |
| E3-S4 | Store Page Numbers During Extraction |

### Epic 4 — Chat with ACM Context (4/4 done) ✓
| Story ID | Title |
|----------|-------|
| E4-S1 | Add ACM Records to Chat Context |
| E4-S2 | Create ACM Context Toggle |
| E4-S3 | Generate ACM-Aware Chat Responses |
| E4-S4 | Support ACM-Specific Questions |

### Epic 5 — Export Functionality (2/4 done)
| Story ID | Title |
|----------|-------|
| E5-S1 | Implement CSV Export |
| E5-S2 | Implement Excel Export |

### Epic 6 — Rebranding to ACM-AI (4/4 done) ✓
| Story ID | Title |
|----------|-------|
| E6-S1 | Update Application Name and Title |
| E6-S2 | Create New Logo and Favicon |
| E6-S3 | Update Color Theme |
| E6-S4 | Update Landing/Home Page |

### Epic 7 — Upload Wizard (7/7 done) ✓
| Story ID | Title |
|----------|-------|
| E7-S1 | Create Wizard Framework Component |
| E7-S2 | File Upload Step with Drag-Drop |
| E7-S3 | Document Type Detection Step |
| E7-S4 | Processing Options Step |
| E7-S5 | Review & Confirm Step |
| E7-S6 | Upload Progress & Results Step |
| E7-S7 | Site Configuration During Upload |

### Epic 8 — UI Refresh (1 active story done, rest archived)
| Story ID | Title |
|----------|-------|
| E8-S11 | ACM Register Grid UI Polish |

### Epic 9 — Document Library Management (2/3 done)
| Story ID | Title |
|----------|-------|
| E9-S1 | Create Document Library View |
| E9-S2 | Document Processing Status Dashboard |

### Epic 11 — Search & Retrieval Enhancement (1/2 done)
| Story ID | Title |
|----------|-------|
| E11-S1 | Parent Document Retrieval |

### Epic 16 — UX Enhancement Sprint (1/3 done)
| Story ID | Title |
|----------|-------|
| E16-S2 | ACM Record Detail Slide-Out Panel |

### Epic 14 — UX & Enterprise Readiness (11/11 done) ✓
| Story ID | Title |
|----------|-------|
| E14-S1  | VAEA Branding & Design Tokens |
| E14-S2  | Sidebar Navigation Redesign |
| E14-S3  | Hide Brownfield Features |
| E14-S4  | Skeleton Loading Screens |
| E14-S5  | Toast System Enhancement |
| E14-S6  | WCAG 2.1 AA Accessibility Compliance |
| E14-S7  | Unified Documents View |
| E14-S8  | Error Recovery & Disconnect Handling |
| E14-S9  | Keyboard Navigation & Shortcuts |
| E14-S10 | Breadcrumb Navigation |
| E14-S11 | Pydantic-TypeScript Type Generation |

### Infrastructure
| Key | Title |
|-----|-------|
| bug-extraction-status-tracking-gap | Extraction Status Tracking Bug Fix |
| e2e-ci-github-actions-setup | E2E CI GitHub Actions Setup |

---

## Ready for Dev 🚀 (9 stories)

Recommended implementation order (from sprint-status.yaml):

| # | Story ID | Title | Notes |
|---|----------|-------|-------|
| 1 | **E15-S1** | Extraction Log Panel in Document Library | Unblocks E15-S2 |
| 2 | **E9-S3**  | Document Actions & Bulk Operations | Independent |
| 3 | **E16-S1** | Dashboard Home with ACM Stats | Large effort |
| 4 | **E16-S3** | Empty States & Onboarding Hints | Quick win |
| 5 | **E10-S1** | Simplify Navigation | Independent |
| 6 | **E2-S8**  | Column Visibility Management | Partial coverage from PR #30 |
| 7 | **E5-S3**  | BAR Template Management | Unblocks E5-S4 |
| 8 | **E1-S23** | Token Limit Quality Validation | Haiku 8K vs Sonnet 32K quality |
| 9 | **E2-S11** | BAR Field Type Safety | Partial coverage from PR #30 |

---

## Drafted 📝 (8 stories — needs promotion to ready-for-dev)

| Story ID | Title | Blocked By |
|----------|-------|------------|
| E5-S4  | Export Field Mapping Configuration | E5-S3 |
| E11-S2 | Hybrid Search Service | — (large effort) |
| E12-S1 | Extraction Method Settings UI | — |
| E12-S2 | AI Model Configuration UI | E12-S1 |
| E12-S3 | Processing Options Configuration | E12-S1 |
| E12-S4 | BAR Field Schema Config UI | E12-S1 |
| E13-S1 | SurrealDB Graph Entity Schema | — |
| E15-S2 | Dedicated Extraction Monitor Page | E15-S1 |

---

## Backlog 📋 (2 stories)

| Story ID | Title | Blocked By |
|----------|-------|------------|
| E13-S2 | Knowledge Graph API Data Service | E13-S1 |
| E13-S3 | React Flow Knowledge Graph Visualization | E13-S2 |

---

## Archived 🗂️ (10 stories — Epic 8 UI Refresh skipped)

E8-S1 through E8-S10 (Bento Grid Design — decision: skipped)

---

## Summary

| Status | Count |
|--------|-------|
| ✅ Done | 75 (72%) |
| 🚀 Ready-for-dev | 9 |
| 📝 Drafted | 8 |
| 📋 Backlog | 2 |
| 🗂️ Archived | 10 |
| **Total** | **104** |

**Epics:** 5 done (E3, E4, E6, E7, E14) · 6 in-progress (E1, E2, E5, E9, E11, E16) · 4 backlog (E10, E12, E13, E15) · 1 archived (E8)

**Next up:** E15-S1 Extraction Log Panel → E9-S3 Bulk Document Actions → E16-S1 Dashboard Home
