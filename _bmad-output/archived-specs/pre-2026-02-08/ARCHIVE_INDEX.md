# Archive Index: Pre-2026-02-08 Tech Specs

**Archive Date:** 2026-02-10
**Reason:** Course corrections on 2026-02-08 made these specs outdated
**Archived By:** BMad Master + Claude Sonnet 4.5
**Source Location:** `docs/sprint-artifacts/`

---

## Why These Specs Were Archived

On February 8, 2026, significant course corrections were made to the ACM-AI project:

1. **E1-S11 Redefined:** Changed from "Extensible Consultant Parser Framework" (3 parsers) to "Generic Configurable Parser with BAR Field Schema" (1 configurable parser)
2. **New Epic 1 Stories Added:** E1-S13 through E1-S20 added for RAG Strategy and Document Intelligence Pipeline
3. **PRD, Architecture, and Epics & Stories Updated:** New requirements superseded old tech specs

All tech specs created before 2026-02-08 reflect the pre-course-correction requirements and implementation approach, making them outdated for current development.

---

## Archive Organization

Specs are organized by epic in subdirectories:
- `epic-1/` - ACM Data Extraction Pipeline (E1-S1 through E1-S6)
- `epic-2/` - AG Grid Spreadsheet Integration (E2-S1 through E2-S7)
- `epic-3/` - Cell Citations & PDF Viewer (E3-S1 through E3-S4)
- `epic-4/` - Chat with ACM Context (E4-S1 through E4-S4)
- `epic-5/` - Export Functionality (E5-S1, E5-S2)
- `epic-6/` - Rebranding to ACM-AI (E6-S1 through E6-S4)
- `epic-7/` - Upload Wizard (E7-S1 through E7-S6)
- `epic-8/` - UI Refresh (E8-S1 through E8-S10)
- `epic-9/` - Document Library Management (E9-S1 through E9-S3)
- `epic-10/` - ACM-AI UI Simplification (E10-S1)
- `other/` - Specs not tied to a specific epic

---

## Archived Files (47 total)

### Epic 1: ACM Data Extraction Pipeline (6 files)

Created 2025-12-07:
- `tech-spec-e1-s1-acm-data-model.md` (Complete)
- `tech-spec-e1-s2-acm-domain-model.md` (Done)
- `tech-spec-e1-s3-acm-extraction.md` (Complete - All Issues Resolved)
- `tech-spec-e1-s4-acm-api-endpoints.md` (Ready for Development)

Created 2025-12-08:
- `tech-spec-e1-s5-acm-source-integration.md` (Done)

No date:
- `tech-spec-e1-s6-local-embedding-pipeline.md` (done - no Created field)

### Epic 2: AG Grid Spreadsheet Integration (7 files)

Created 2025-12-07:
- `tech-spec-e2-s2-acm-spreadsheet.md` (Done)

Created 2025-12-08:
- `tech-spec-e2-s1-ag-grid-install.md` (Done)
- `tech-spec-e2-s3-column-sorting-filtering.md` (Done)
- `tech-spec-e2-s4-row-grouping.md` (Done)
- `tech-spec-e2-s5-risk-color-coding.md` (Done)
- `tech-spec-e2-s6-search-bar.md` (Draft)

No date:
- `tech-spec-e2-s7-building-tab-navigation.md` (no Created field)

### Epic 3: Cell Citations & PDF Viewer (4 files)

Created 2025-12-07:
- `tech-spec-e3-s2-pdf-viewer-modal.md` (Done)
- `tech-spec-e3-s3-acm-citation-type.md` (Done)

Created 2025-12-08:
- `tech-spec-e3-s1-clickable-cells.md` (Done)
- `tech-spec-e3-s4-page-numbers.md` (Done)

### Epic 4: Chat with ACM Context (4 files)

Created 2025-12-07:
- `tech-spec-e4-s1-acm-chat-context.md` (Done)
- `tech-spec-e4-s3-acm-aware-responses.md` (Done)

Created 2025-12-08:
- `tech-spec-e4-s2-acm-context-toggle.md` (Done - Code Review Passed 2026-01-09)
- `tech-spec-e4-s4-acm-questions.md` (Done)

### Epic 5: Export Functionality (2 files)

Created 2025-12-08:
- `tech-spec-e5-s1-csv-export.md` (Done)
- `tech-spec-e5-s2-excel-export.md` (Done)

### Epic 6: Rebranding to ACM-AI (4 files)

Created 2025-12-08:
- `tech-spec-e6-s1-app-name.md` (Done)
- `tech-spec-e6-s2-logo-favicon.md` (Done)
- `tech-spec-e6-s3-color-theme.md` (Done)
- `tech-spec-e6-s4-landing-page.md` (Done)

### Epic 7: Upload Wizard (6 files)

Created 2025-12-08:
- `tech-spec-e7-s1-wizard-framework.md` (Done)
- `tech-spec-e7-s2-file-upload-step.md` (Done)
- `tech-spec-e7-s3-document-type-step.md` (Done)
- `tech-spec-e7-s4-processing-options.md` (Done)
- `tech-spec-e7-s5-review-step.md` (Done)
- `tech-spec-e7-s6-upload-progress.md` (Done)

### Epic 8: UI Refresh (10 files)

Created 2025-12-08:
- `tech-spec-e8-s1-ui-skill-install.md` (Done)
- `tech-spec-e8-s2-design-tokens.md` (Done)
- `tech-spec-e8-s3-bento-card.md` (Done)
- `tech-spec-e8-s4-bento-grid.md` (Done)
- `tech-spec-e8-s5-dashboard-redesign.md` (Done)
- `tech-spec-e8-s6-sources-list.md` (Done)
- `tech-spec-e8-s7-source-detail.md` (Done)
- `tech-spec-e8-s8-navigation-sidebar.md` (Done)
- `tech-spec-e8-s9-typography.md` (Done)
- `tech-spec-e8-s10-dark-mode.md` (Done)

### Epic 9: Document Library Management (3 files)

Created 2025-12-19:
- `tech-spec-e9-s1-document-library-view.md` (Done)
- `tech-spec-e9-s2-processing-status-dashboard.md` (Done)
- `tech-spec-e9-s3-document-actions-bulk-operations.md` (Drafted)

### Epic 10: ACM-AI UI Simplification (1 file)

Created 2025-12-19:
- `tech-spec-e10-s1-ui-simplification.md` (Drafted)

### Other/Standalone (1 file)

Created 2025-12-20:
- `tech-spec-ai-powered-acm-extraction.md` (Ready for Development)

---

## Current Specs (NOT Archived)

These specs remain in `docs/sprint-artifacts/` as they reflect current requirements:

### Epic 14: UX & Enterprise Readiness (11 files - Created 2026-02-08)
- E14-S1 through E14-S11 (all "Ready for Dev")

---

## New Implementation Artifacts (Post-Course Correction)

These artifacts are in `_bmad-output/implementation-artifacts/` and reflect the updated requirements:

### Epic 1 (Continued):
- `e1-s11-generic-configurable-parser.md` (done)
- `e1-s13-fix-page-reference-tracking.md`
- `e1-s14-contextual-embedding-enrichment.md`
- `e1-s15-corrective-rag-validation-loop.md`
- `e1-s16-document-structure-toc-extraction.md`
- `e1-s17-building-inventory-compilation.md`
- `e1-s18-page-level-section-tagging.md`
- `e1-s19-document-metadata-extraction-enhancement.md`
- `e1-s20-agentic-extraction-orchestrator.md`

### Epic 2 (Continued):
- `e2-s8-column-visibility-management.md`

### Epic 5 (Continued):
- `e5-s3-bar-template-management.md`
- `e5-s4-export-field-mapping-configuration.md`

### Epic 11:
- `e11-s1-parent-document-retrieval.md`

---

## Git History

Original file locations and git history are preserved. Use `git log --follow` to trace file movements:

```bash
git log --follow _bmad-output/archived-specs/pre-2026-02-08/epic-1/tech-spec-e1-s1-acm-data-model.md
```

---

## Restoration

To restore an archived spec (if needed):

```bash
# Example: Restore E1-S1
git mv _bmad-output/archived-specs/pre-2026-02-08/epic-1/tech-spec-e1-s1-acm-data-model.md \
       docs/sprint-artifacts/tech-spec-e1-s1-acm-data-model.md
```

---

## References

- **Sprint Change Proposal:** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-08.md`
- **Updated PRD:** `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md`
- **Updated Epics & Stories:** `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md`
- **Updated Architecture:** `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md`
