# ACM-AI Demo Validation — Task Plan

## Phase 0: Environment Setup (P0)
- [ ] 0.1 Verify frontend at localhost:8502
- [ ] 0.2 Verify API at localhost:5055
- [ ] 0.3 Browser setup — resize 1920x1080, screenshot

## Phase 2: Document Upload (P0) — CRITICAL
- [ ] 2.1 Navigate to /documents, find upload button
- [ ] 2.2 Upload Broadmeadows PDF via file upload
- [ ] 2.3 Step through upload wizard
- [ ] 2.4 Verify upload completes
- [ ] 2.5 Verify post-upload navigation to source detail

## Phase 3: Extraction Pipeline (P0) — CRITICAL
- [ ] 3.1 Trigger ACM extraction on uploaded source
- [ ] 3.2 Verify 7-stage pills appear (STRUCTURE→STORE)
- [ ] 3.3 Monitor SSE progress with screenshots
- [ ] 3.4 Verify extraction completes (~27 records)
- [ ] 3.5 Check extraction monitor page

## Phase 4: AG Grid Spreadsheet (P0) — CRITICAL
- [ ] 4.1 ACM Register page loads with AG Grid
- [ ] 4.2 Building tabs visible
- [ ] 4.3 Column headers correct (BAR spec)
- [ ] 4.4 Stats cards (risk counts)
- [ ] 4.5 Search/filter works
- [ ] 4.6 Record count verification

## Phase 8: Export CSV & Excel (P0) — CRITICAL
- [ ] 8.1 CSV export downloads
- [ ] 8.2 Excel export downloads
- [ ] 8.3 Verify column count/headers

## Phase 5: Cell Click → PDF Viewer (P1)
- [ ] 5.1 Click grid row → detail dialog
- [ ] 5.2 PDF citation link visible
- [ ] 5.3 PDF viewer opens at correct page

## Phase 7: Chat with ACM Context (P1)
- [ ] 7.1 Chat panel visible
- [ ] 7.2 Ask question, get contextual response

## Phase 6: Knowledge Graph (P2)
- [ ] 6.1 React Flow renders with nodes/edges
- [ ] 6.2 Hierarchy and risk colors correct

## Phase 1: Dashboard & Navigation (P2)
- [ ] 1.1 Dashboard loads with bento grid
- [ ] 1.2 Sidebar nav items (ACM mode)
- [ ] 1.3 All nav links load without 404

## Phase 9-10: Settings & Monitor (P3)
- [ ] 9.1 Settings pages load (extraction, models, field-schema, processing)
- [ ] 10.1 Extraction monitor page loads

## Wrap-Up
- [ ] Compile failure report with severity counts
- [ ] Write executive summary
- [ ] Update findings.md and progress.md
