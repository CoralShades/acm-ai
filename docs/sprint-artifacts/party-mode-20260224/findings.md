# Party Mode Findings — 2026-02-24

## Context Loaded

### Sprint State
- 130 total stories, 116 done (89%), E18 in-progress (Production Hardening)
- E18 has stories s1-s7, with s4 (demo-validation) still in-progress
- E20 referenced in PRD (Marketing/Cross-site) but NOT yet in sprint-status.yaml
- Next available epic numbers: **E19** and **E20** (or E20/E21 if E20 marketing is formalized)

### CRITICAL NUMBERING ISSUE
Brief says create Epic 18 (standard user UX) and Epic 19 (extraction completeness)
BUT E18 already exists as "Production Hardening & Demo Stability"
MUST RAISE IN ROUND 1 — new epics should be E19 and E20 (or E20/E21)

### UI Components Available in /frontend/src/components/acm/
- ACMGrid.tsx — AG Grid spreadsheet
- BuildingTabs.tsx — already exists! Per-building tab navigation
- ACMTab.tsx — parent component
- ACMToolbar.tsx — grid toolbar
- ExtractionProgressPanel.tsx — SSE log panel
- SiteConfigForm.tsx / SiteConfigPanel.tsx — site configuration
- ACMRecordDetailPanel.tsx — slide-out panel (done in E16-S2)

### Extraction Pipeline Key Code
- building_inventory.py: _BUILDING_HEADER regex only matches SAMP IDs (B00A, D01)
  - ARA/Prensa/Greencap buildings use name-based IDs — NOT matched by SAMP pattern
- orchestrator.py: _SAMP_BUILDING_ID used to select strategy
  - ARA buildings (non-SAMP ID) → always FULL_LLM ✓
  - SAMP buildings → may get REGEX_ONLY if classified SIMPLE
- Root causes of Issue 4:
  1. Page boundary truncation: building page_end may not include all pages before next header
  2. REGEX_ONLY over-classification: SAMP buildings with few rooms get SIMPLE/REGEX_ONLY but actually need LLM

### PRD Status
- v1.6 (2026-02-23) — includes FR-1100 series (marketing/cross-site nav)
- All primary FR series (FR-100 through FR-1000) are feature-complete

### SCP Format Reference
From sprint-change-proposal-20260220-extraction-monitor-ux.md:
1. Header (date, status, priority, scope, risk)
2. Motivation (gap analysis)
3. State reconciliation
4. Change Proposals (per CP, with stories and ACs)
5. Impact Analysis
6. Updated Story Counts
7. Implementation Order
8. Files Changed

### Story Format Reference (from E16-S2)
- Header: Epic, Priority, Status, Change Proposal
- User Story
- Background
- Acceptance Criteria (checkbox format)
- Technical Notes
- Key Files Created/Modified (table)
- Dev Agent Record (post-implementation)
- Verification section

## Issue Analysis

### Issue 1: UI Complexity
Current: Exposes extraction monitoring, AI model config, notebooks, chat, admin features
Fix: Standard User role that hides complexity; Architect/Admin role retains access
Existing: E10-S1 simplified navigation with ACM mode — check what's currently hidden

### Issue 2: Jobs Mental Model
Current: "Documents" library with sources
Fix: "Jobs" dashboard — each uploaded doc = 1 job; familiar task management UX
Key fields per job: file name, uploaded date, status, record count, buildings found, export action
Question: Is this purely a UI rename, or does it require backend data model changes?

### Issue 3: Extraction UX Flow
Current: Global ACM Register shows all records from all documents
Correct flow:
  Step 1: After upload → site-specific view filtered to records WITH building_id/building_name
  Step 2: Per-building tab view (BuildingTabs.tsx already exists!)
  Step 3: Export as combined CSV + per-building Excel sheets
Question: Does "site" mean per-source document, or per-agency/site_name field?

### Issue 4: Extraction Completeness
Root cause A: building_inventory.py page_end doesn't extend to last record before next building
Root cause B: REGEX_ONLY applied to SAMP buildings even when multi-page
Fix A: Extend page_end to cover all content until next building header OR EOF
Fix B: Add minimum-records-per-page heuristic; flag low-yield REGEX_ONLY extractions for retry
Fix C: ARA building header detection improvement (name-based not just SAMP pattern)

## Post-Review Fixes Applied — 2026-02-25

### Frontend closures
- E19-S2: upload flow now redirects to `/jobs/{id}/review/buildings`; Jobs detail CTA and card routing aligned to `/jobs/{id}`.
- E19-S2: `building_count` surfaced from API and shown on published job cards.
- E19-S6: `BuildingTabs` now renders `All Records` + amber `Unassigned` tab.
- E19-S6: `RecordMergeModal` is now connected in `ACMReviewGrid` with two-row merge flow.
- E19-S6: missing ACM fields added to editable grid columns.
- E19-S7: inline job title editing implemented in header.
- E19-S7: Extraction Log tab now renders `ExtractionProgressPanel` using extraction-progress API.
- E19-S7: CSV export endpoint aligned to `/api/acm/export/csv` (added backend alias route).

### Backend reliability closure
- Added extraction runtime auth-fallback routing in both legacy graph extraction and orchestrator extraction:
  - Detect provider authentication failures.
  - Attempt fallback routing without breaking configured Sonnet path.
  - Preserve Ollama/Qwen fallback support.

### UX responsiveness closure
- Added `jobs/loading.tsx` route loading UI.
- Added route prefetching for frequently visited job pages from the Jobs dashboard.

### Remaining follow-up
- Full end-to-end command validation (frontend build + targeted extraction pytest) is partially blocked by local shell/runtime constraints; static diagnostics on changed files are clean.
- E20-S5 still requires targeted 31/31 re-validation and final closure.
