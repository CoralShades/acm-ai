# Sprint Progress — ACM-AI

Updated: 2026-02-21
Source of truth: `docs/sprint-artifacts/sprint-status.yaml`

## Summary

| Status | Count |
|--------|-------|
| Done | 74 |
| Ready for Dev | 7 |
| Drafted | 11 |
| Backlog | 2 |
| Archived | 10 |
| **Total** | **104** |

Completion: **74/94 active stories (79%)** — excludes 10 archived E8 stories.

---

## Done (74)

### Epic 1 — ACM Data Extraction Pipeline (26/27)

| Story | Title | Status |
|-------|-------|--------|
| E1-S1 | Create ACM Data Model | done |
| E1-S2 | Create ACM Record Domain Model | done |
| E1-S3 | Implement ACM Extraction Transformation | done |
| E1-S4 | Create ACM API Endpoints | done |
| E1-S5 | Integrate ACM Extraction into Source Processing | done |
| E1-S6 | Configure Local Embedding Pipeline | done |
| E1-S7 | AI-Powered ACM Extraction | done |
| E1-S8 | Site Configuration Data Entry | done |
| E1-S9 | ACM Product Classification | done |
| E1-S10 | MinerU Table Extraction Integration | done |
| E1-S11 | Generic Configurable Parser (BAR Field Schema) | done |
| E1-S12 | Consultant Wording Normalization | done |
| E1-S13 | Fix Page Reference Tracking | done |
| E1-S14 | Contextual Embedding Enrichment | done |
| E1-S15 | Corrective RAG Validation Loop | done |
| E1-S16 | Document Structure & TOC Extraction | done |
| E1-S17 | Building Inventory Compilation | done |
| E1-S18 | Page-Level Section Tagging | done |
| E1-S19 | Document Metadata Extraction Enhancement | done |
| E1-S20 | Agentic Extraction Orchestrator | done |
| E1-S21 | Extraction Pipeline Observability | done |
| E1-S22 | Extraction Output Token Limit Fix | done |
| E1-S24 | Fix Assumed Positive Detection | done |
| E1-S25 | Fix External/Internal Location Merging | done |
| E1-S26 | Reduce False Positive Extraction | done |
| E1-S27 | Handle Duplicate Room Items Edge Case | done |

Remaining: E1-S23 (Token Limit Quality Validation) — ready-for-dev

### Epic 2 — AG Grid Spreadsheet Integration (10/12)

| Story | Title | Status |
|-------|-------|--------|
| E2-S1 | Install and Configure AG Grid | done |
| E2-S2 | Create ACMSpreadsheet Component | done |
| E2-S3 | Implement Column Sorting and Filtering | done |
| E2-S4 | Implement Row Grouping | done |
| E2-S5 | Implement Risk Status Color Coding | done |
| E2-S6 | Add Search Bar to Spreadsheet | done |
| E2-S7 | Implement Building Tab Navigation | done |
| E2-S9 | ACM Grid UX Improvements | done |
| E2-S10 | Fix Test Portability | done |
| E2-S12 | Missing BAR Fields in Grid | done |

Remaining: E2-S8 (Column Visibility Management), E2-S11 (BAR Field Type Safety) — ready-for-dev

### Epic 3 — Cell Citations & PDF Viewer (4/4 — Complete)

| Story | Title | Status |
|-------|-------|--------|
| E3-S1 | Make Cells Clickable | done |
| E3-S2 | Create PDF Viewer Modal | done |
| E3-S3 | Implement ACM Citation Reference Type | done |
| E3-S4 | Store Page Numbers During Extraction | done |

### Epic 4 — Chat with ACM Context (4/4 — Complete)

| Story | Title | Status |
|-------|-------|--------|
| E4-S1 | Add ACM Records to Chat Context | done |
| E4-S2 | Create ACM Context Toggle | done |
| E4-S3 | Generate ACM-Aware Chat Responses | done |
| E4-S4 | Support ACM-Specific Questions | done |

### Epic 5 — Export Functionality (2/4)

| Story | Title | Status |
|-------|-------|--------|
| E5-S1 | Implement CSV Export | done |
| E5-S2 | Implement Excel Export | done |

Remaining: E5-S3 (BAR Template Management), E5-S4 (Export Field Mapping Config) — ready-for-dev

### Epic 6 — Rebranding to ACM-AI (4/4 — Complete)

| Story | Title | Status |
|-------|-------|--------|
| E6-S1 | Update Application Name and Title | done |
| E6-S2 | Create New Logo and Favicon | done |
| E6-S3 | Update Color Theme | done |
| E6-S4 | Update Landing/Home Page | done |

### Epic 7 — Upload Wizard (7/7 — Complete)

| Story | Title | Status |
|-------|-------|--------|
| E7-S1 | Create Wizard Framework Component | done |
| E7-S2 | File Upload Step with Drag & Drop | done |
| E7-S3 | Document Type Detection Step | done |
| E7-S4 | Processing Options Step | done |
| E7-S5 | Review & Confirm Step | done |
| E7-S6 | Upload Progress & Results Step | done |
| E7-S7 | Site Configuration During Upload | done |

### Epic 8 — UI Refresh: Bento Grid Design (1 done, 10 archived)

| Story | Title | Status |
|-------|-------|--------|
| E8-S11 | ACM Register Grid UI Polish | done |

E8-S1 through E8-S10 archived (epic skipped by decision 2026-02-08).

### Epic 9 — Document Library Management (2/3)

| Story | Title | Status |
|-------|-------|--------|
| E9-S1 | Create Document Library View | done |
| E9-S2 | Document Processing Status Dashboard | done |

Remaining: E9-S3 (Document Actions & Bulk Operations) — ready-for-dev

### Epic 11 — Search & Retrieval Enhancement (1/2)

| Story | Title | Status |
|-------|-------|--------|
| E11-S1 | Parent Document Retrieval | done |

Remaining: E11-S2 (Hybrid Search Service) — drafted

### Epic 14 — UX & Enterprise Readiness (11/11 — Complete)

| Story | Title | Status |
|-------|-------|--------|
| E14-S1 | VAEA Branding & Design Tokens | done |
| E14-S2 | Sidebar Navigation Redesign | done |
| E14-S3 | Hide Brownfield Features | done |
| E14-S4 | Skeleton Loading Screens | done |
| E14-S5 | Toast System Enhancement | done |
| E14-S6 | WCAG 2.1 AA Accessibility Compliance | done |
| E14-S7 | Unified Documents View | done |
| E14-S8 | Error Recovery & Disconnect Handling | done |
| E14-S9 | Keyboard Navigation & Shortcuts | done |
| E14-S10 | Breadcrumb Navigation | done |
| E14-S11 | Pydantic-TypeScript Type Generation | done |

### Standalone / Infrastructure

| Story | Title | Status |
|-------|-------|--------|
| bug-extraction-status-tracking-gap | Upload Dialog Extraction Progress Tracking | done |
| e2e-ci-github-actions-setup | GitHub Actions E2E Pipeline | done |

---

## Ready for Dev (7)

| Story | Title | Epic |
|-------|-------|------|
| E1-S23 | Token Limit Quality Validation (Haiku 8K vs Sonnet 32K) | E1 |
| E2-S8 | Column Visibility Management | E2 |
| E2-S11 | BAR Field Type Safety | E2 |
| E5-S3 | BAR Template Management | E5 |
| E5-S4 | Export Field Mapping Configuration | E5 |
| E9-S3 | Document Actions & Bulk Operations | E9 |
| E10-S1 | Simplify Navigation | E10 |

## Drafted (11)

| Story | Title | Epic |
|-------|-------|------|
| E11-S2 | Hybrid Search Service | E11 |
| E12-S1 | Extraction Method Settings UI | E12 |
| E12-S2 | AI Model Configuration UI | E12 |
| E12-S3 | Processing Options Configuration | E12 |
| E12-S4 | BAR Field Schema Configuration UI | E12 |
| E13-S1 | SurrealDB Graph Entity Schema | E13 |
| E15-S1 | Extraction Log Panel in Document Library | E15 |
| E15-S2 | Dedicated Extraction Monitor Page | E15 |
| E16-S1 | Dashboard Home Page with ACM Stats | E16 |
| E16-S2 | ACM Record Detail Slide-Out Panel | E16 |
| E16-S3 | Empty States & Onboarding Hints | E16 |

## Backlog (2)

| Story | Title | Epic |
|-------|-------|------|
| E13-S2 | Knowledge Graph API & Data Service | E13 |
| E13-S3 | React Flow Knowledge Graph Visualization | E13 |

## Archived (10)

Epic 8 stories E8-S1 through E8-S10 — Bento Grid Design epic skipped by decision 2026-02-08.
