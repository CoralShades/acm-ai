# Party Mode Session — 2026-02-24 Task Plan

## Phase: Context Loading
- [ ] Read sprint-status.yaml
- [ ] Read 03-prd.md
- [ ] Read 04-architecture.md
- [ ] Read 05-epics-and-stories.md
- [ ] Read project-retrospective-2026-02-22.md
- [ ] Read bmm-workflow-status.yaml
- [ ] Find and read existing SCPs
- [ ] List frontend/src/components/acm/ directory
- [ ] Read orchestrator.py
- [ ] Read building_inventory.py

## Phase: Interview
- [ ] Round 1 — Scope Clarity (PM + UX lead)
- [ ] Round 2 — UX Design Decisions
- [ ] Round 3 — Technical Risk & Architecture
- [ ] Round 4 — Sprint Planning

## Phase: Output Generation
- [ ] File 1: sprint-change-proposal-20260224-stakeholder-ux-redesign.md
- [ ] File 2: epic-18-standard-user-ux.md
- [ ] File 3: epic-19-extraction-completeness.md
- [ ] File 4: Individual story files (e18-s{N}-*.md, e19-s{N}-*.md)
- [ ] File 5: sprint-status.yaml (append new epics)
- [ ] File 6: e18-e19-implementation-prompts.md
- [ ] File 7: prd-update-notes-20260224.md

## Post-Review Stabilization — 2026-02-25
- [x] Apply E19-S2 review fixes (redirect + jobs routing + building count)
- [x] Apply E19-S6 review fixes (Unassigned tab + merge modal + missing fields)
- [x] Apply E19-S7 review fixes (inline edit + log tab + CSV URL)
- [x] Add extraction runtime auth/model fallback routing with Ollama/Qwen compatibility preserved
- [x] Add route loading/prefetch improvements for perceived Next.js compile stalls
- [ ] Complete full command-level validation run (environment dependent)
- [x] Update sprint/workflow/progress/findings artifacts
