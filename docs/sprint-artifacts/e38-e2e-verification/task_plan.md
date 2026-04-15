# E38 E2E Verification — Task Plan

**Date:** 2026-04-15
**Branch:** `feat/sf-reconciliation-20260411`
**PDF:** `data/uploads/Clutch_Broadmeadows.pdf` (31 expected ACM records)
**Change Proposal:** `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md`
**Max iterations:** 3

## Phase 0: Setup
- [x] Write planning files
- [ ] Start services via PowerShell `start-all.bat`
- [ ] Verify SurrealDB (8000), API (5055), Worker, Frontend (8502) healthy
- [ ] Check for startup errors in logs

## Phase 1: Team Launch (tmux teammate mode)
- [ ] Launch **team-lead** — coordinates all agents, reads findings, dispatches fixes
- [ ] Launch **log-monitor** — tails SurrealDB, API, worker, frontend logs for errors
- [ ] Launch **frontend-auditor** — browser automation: UI/UX audit, accessibility, responsiveness
- [ ] Launch **devils-advocate** — adversarial review of extraction, UI, data quality
- [ ] Launch **documenter** — updates sprint-status.yaml, creates bug stories, changelog

## Phase 2: E2E Extraction Run
- [ ] Upload `Clutch_Broadmeadows.pdf` via frontend UI (browser automation)
- [ ] Monitor SSE streaming events during extraction
- [ ] Wait for extraction completion or timeout
- [ ] Log-monitor captures all errors during extraction
- [ ] Frontend-auditor verifies progress UI, job cards, SSE banners

## Phase 3: Result Verification
- [ ] Compare extracted records against 31 expected (Broadmeadows baseline)
- [ ] Verify Building__c fields map to real SF API names (per sf-schema-snapshot.json)
- [ ] Verify Item__c fields map to real SF API names
- [ ] Verify picklist values use SF vocabulary (Stable not Good, Moderate not Medium)
- [ ] Verify Labelled__c column is populated (E38-S7 fix check)
- [ ] Verify _merge_site_config writes Responsible_Agency_Department__c (E38-S6 check)
- [ ] Verify External_ID generation is deterministic hash
- [ ] Devils-advocate challenges data quality, edge cases, false positives
- [ ] Frontend-auditor checks AG Grid rendering, tab navigation, export

## Phase 4: Fix Iterations (max 3)
### Iteration 1
- [ ] Collect findings from all teams
- [ ] Triage: critical bugs → fix immediately, minor → document as stories
- [ ] Fix critical bugs
- [ ] Re-run verification checks
- [ ] Document new bug stories as E38-S14+

### Iteration 2 (if needed)
- [ ] Collect new findings
- [ ] Fix remaining critical bugs
- [ ] Re-verify
- [ ] Update documentation

### Iteration 3 (if needed)
- [ ] Final findings collection
- [ ] Final fixes
- [ ] Final verification
- [ ] Comprehensive report

## Phase 5: Documentation
- [ ] Update sprint-status.yaml with new story statuses
- [ ] Create/update bug stories in E38 (S14, S15, ...)
- [ ] Update progress.md with session summary
- [ ] Update findings.md with all discoveries
- [ ] Align all changes to E38 SF Reconciliation SCP
