# BMAD Full Audit Prompt — ACM-AI Pipeline & UX
**Date**: 2026-02-25
**Purpose**: Run this prompt with `bmad-master` or via `/party-mode` for a comprehensive audit
**Pre-read**: `docs/temp/pipeline-analysis-20260225.md`

---

```
/party-mode

You are activating a full BMAD party for a comprehensive pipeline and UX audit of ACM-AI.
This is an AUDIT session — primary goal is to produce an actionable findings report, not to implement fixes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTEXT — READ THESE FILES FIRST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PIPELINE ANALYSIS (start here — this is the pre-audit research):
- docs\PIPELINE-AUDIT-FEB-25\pipeline-analysis-20260225.md — FULL READ REQUIRED (comprehensive pipeline trace with findings)

SPRINT STATE:
- docs/sprint-artifacts/sprint-status.yaml
- docs/sprint-artifacts/party-mode-20260224/findings.md
- docs/sprint-artifacts/party-mode-20260224/progress.md

SPRINT PLANS:
- docs/temp/fix-sprint-plan-20260225.md
- docs/temp/fix-sprint-prompt-20260225.md

AG-UI SPEC:
- docs/ag-ui-pipeline-spec.md — FULL READ (1743 lines). Map spec requirements vs implementation gaps.

RECENT COMMITS (check what's actually been implemented):
- Run: git log --oneline -10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUDIT SCOPE — 7 AREAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Each BMAD agent owns one or more audit areas:

**Winston (Architect)** — AREA 1: Pipeline Architecture Audit
- Trace the actual execution path vs designed path
- Identify dead code: MinerU, acm_extractor.py regex parser, unused hooks
- Assess the dual SSE system (PipelineLogger + AGUIEventEmitter): consolidate or keep both?
- Evaluate the structured output failure: is `with_structured_output()` worth keeping, or should we skip to JSON parsing always?
- Check the A2A protocol stub: should it be completed or removed?
- Produce: ARCHITECTURE_FINDINGS with recommendations

**Winston (Architect)** — AREA 2: AG-UI Implementation Gap Analysis
- Read docs/ag-ui-pipeline-spec.md fully
- For each spec requirement, check: implemented / stubbed / missing
- Focus on Section 4 (CopilotKit), Section 5 (Real-Time Events), Section 11 (Backend Changes)
- Check: Does the CopilotKit runtime exist? Is `useCoAgent` wired up? Does the extraction agent have a CopilotKit runtime endpoint?
- Map the 7 pipeline stages and verify emit points in acm_extraction.py
- Produce: AG_UI_GAP_MATRIX (spec requirement → implementation status → file/line → action needed)

**Mary (Analyst)** — AREA 3: Extraction Accuracy Audit
- Current state: 28/31 records with fixes applied (but worker needs restart)
- 3 missing records: all "Not Sampled" / "No Access" items
- Analyze WHY these specific items are missed (prompt limitation? text formatting? chunk boundary?)
- Check the CSV ground truth (docs/samplePDF/Clutch_Broadmeadows.csv) against extraction output
- Assess: Is 28/31 (90%) acceptable for V1? What's needed for 100%?
- Produce: ACCURACY_FINDINGS with root causes and recommendations

**Quinn (QA)** — AREA 4: UX Flow Audit
- Map the actual user flow: upload → ? → results
- Verify: Does the user see extraction progress? Or just an empty grid?
- Check: AddSourceDialog.tsx navigates to /review/buildings — should it go to /extract?
- Check: Building review page has no extraction awareness (no "in progress" banner)
- Check: Job detail "Extraction Log" tab — does it work? Does it show historical data?
- Run browser verification if services are running:
  1. Navigate to http://localhost:8502
  2. Upload docs/samplePDF/Clutch_Broadmeadows.pdf
  3. Take screenshots at each step
  4. Document what the user actually sees
- Produce: UX_FINDINGS with screenshots and recommendations

**Quinn (QA)** — AREA 5: Frontend Build & Type Verification
- Run: cd frontend && npm run build
- Run: cd frontend && npm run lint
- Run: cd frontend && npm run generate:types
- Check for missing imports, dead imports, unused components
- Verify all routes under /jobs/ render without errors
- Check for any TypeScript errors related to AG-UI or extraction types
- Produce: BUILD_FINDINGS

**Amelia (Dev)** — AREA 6: Worker & Deployment Audit
- Is the worker running? What PID?
- Is it running the LATEST code? (Check if commit d44e211 is loaded)
- How to restart the worker properly on Windows?
- Check: Are there stale commands in the queue? (query command table for status='new' or 'running')
- Check: Is SurrealDB accessible? Run a test query
- Check: Is Ollama running for embeddings?
- Produce: DEPLOYMENT_FINDINGS

**Bob (SM)** — AREA 7: Sprint Status & Story Closure
- What stories from the fix-sprint-plan are actually done?
- What's still open?
- What should be filed as new issues?
- Update: docs/sprint-artifacts/sprint-status.yaml
- Produce: SPRINT_STATUS_UPDATE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write the combined audit report to:
docs/temp/pipeline-audit-report-20260225.md

Format:
# ACM-AI Pipeline & UX Audit Report — 2026-02-25

## Executive Summary
(3-5 bullet summary of critical findings)

## Area 1: Pipeline Architecture (Winston)
### Findings
### Recommendations
### Dead Code Inventory

## Area 2: AG-UI Gap Analysis (Winston)
### Spec vs Implementation Matrix
| Spec Section | Requirement | Status | File | Action |
### Missing Components

## Area 3: Extraction Accuracy (Mary)
### Current State
### Root Cause Analysis for 3 Missing Records
### Recommendations

## Area 4: UX Flow (Quinn)
### Current User Journey
### Screenshots (if available)
### Gap Analysis
### Recommendations

## Area 5: Build & Types (Quinn)
### Build Results
### Type Generation Results
### Issues Found

## Area 6: Worker & Deployment (Amelia)
### Service Status
### Worker Code Version
### Queue State
### Recommendations

## Area 7: Sprint Status (Bob)
### Completed Items
### Open Items
### New Issues to File
### Updated Sprint Status

## Priority Action Items
| # | Action | Owner | Priority | Size |
(Ordered by impact)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXECUTION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- This is an AUDIT — read and document, do NOT implement fixes
- Read files before making claims about their content
- Use git log and git diff to verify what's actually committed vs what's planned
- For frontend checks: run build and lint commands, capture output
- For backend checks: run ruff check, capture output
- For deployment: query SurrealDB directly, check process list
- If services aren't running: document that as a finding, don't try to start them
- Every finding MUST reference specific file:line or command output
- Every recommendation MUST be actionable (specific file, specific change)
```
