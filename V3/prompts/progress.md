# V3 Prompt Pack — Progress

## Session: 2026-03-03

### Completed
- [x] P0: Extract HTML to Markdown
- [x] 01: Correct Course (E29/E30 archived)
- [x] 02: Technical Research (extraction providers — Docling + MinerU recommended)
- [x] 03: Party Mode — INITIAL RUN complete
- [x] 03: Party Mode — Continuation 1: Q1-Q6 answers + OpenRouter/Ollama clarification
- [x] 03: Party Mode — Continuation 2: MinerU audit corrections (torch compat, backend selection, Alexander fix)
- [x] 04: Edit PRD — V3 FRs added (FR-1400 through FR-1800 series)
- [x] 05: Create Architecture — V3 architecture doc with 14 sections
- [x] 06: Create UX — 6 UI flows, wireframes, AG Grid specs
- [x] 07: Create Epics & Stories — E30-E34 (33 stories, ~95 SP)
- [x] 08: Readiness Check — CONDITIONAL GO (4 critical issues identified)

### Completed (Implementation)
- [x] E30-S1: SF Schema Config Loader (5 SP)
- [x] E30-S2: Building Record Table + Domain Model (5 SP)
- [x] E30-S3: ACM Record SF Item__c Alignment (3 SP)
- [x] E30-S4: Dependent Picklist Validator (5 SP)
- [x] E30-S6: BAR→SF Vocabulary Transition (2 SP) — **SCHEMA_FREEZE GATE UNLOCKED**
- [x] Sprint V3-1: COMPLETE (4/4 stories, 18 SP)
- [x] E30-S4 Audit: instructions-sample vs Salesforce picklist mismatch (findings only, no code changes)
  - **Result:** 8 findings (F1-F8), 3 HIGH severity
  - **Post-S4/S6 reconciliation:** F1 fixed, F2/F3/F7 partially addressed, **F4 NOT FIXED (critical)**
  - **Location:** V3/prompts/findings.md + V3/output/github-issue-e30s4-audit.md (updated)
- [x] Story file Dev Agent Records updated (E30-S4, E30-S6)
- [x] GitHub issue updated with post-implementation finding statuses

### In Progress
- [ ] 08b: Readiness Fixes — Prompt ready at V3/prompts/08b-readiness-fixes.md (NOT YET RUN)

### Pending
- [ ] Step 3: Create F4 micro-story (E32-S4 Classifier Update — SF Taxonomy)
- [ ] Step 4: Run 08b readiness fixes
- [ ] Step 5: Verify sprint plan after 08b
- [ ] 10-15: Implementation phase continues (E30-S5, E30-S8 next)

### Key Decisions This Session
- SSE timing fix: Move E34-S1 (PipelineEventBus) to E31-S7 (Option A)
- MinerU hybrid backend selected as default
- torch 2.10.0 confirmed compatible with MinerU (>2.6.0,<3)
- Alexander benchmark: ≥40/43 baseline, ≥42/43 stretch
- F4 fix approach: Option (b) — add case-normalization in sf_picklist_validator.py (lowest risk)
- E32-S4 (Classifier Update) will address F4 casing fix

### 5-Question Reboot Check
1. **Last completed milestone?** Sprint V3-1 complete (E30-S1/S2/S3/S4), V3-2 partial (E30-S6 done), SCHEMA_FREEZE unlocked
2. **Current active task?** Step 08b (Readiness Fixes) — prompt ready, needs execution in fresh context
3. **Blockers?** 4 BMAD artifact issues from readiness check (prompt 08b resolves them). F4 casing bug needs story.
4. **Last modified files?** docs/sprint-artifacts/e30-s4-*.md, e30-s6-*.md, V3/output/github-issue-e30s4-audit.md, V3/prompts/progress.md
5. **Next planned action?** Create F4 story → Run 08b fixes → Verify sprint plan → Resume implementation (E30-S5, E30-S8)
