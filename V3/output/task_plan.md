# V3 Planning — Task Plan

## Phase: Party Mode Multi-Agent Debate + Synthesis
*(all completed — collapsed for context)*

- [x] All party mode tasks (see prior phases)
- [x] All follow-up tasks (Q1-Q6, MinerU audit)
- [x] PRD v3.0 edit
- [x] Architecture v3.0
- [x] Epics & Stories v3.0

## Phase: Post-Sprint Housekeeping + 08b Execution

### Step 1: Update Story Files (Dev Agent Records)
- [ ] Update E30-S4 Dev Agent Record → Completed
- [ ] Update E30-S6 Dev Agent Record → Completed

### Step 2: Update GitHub Issue (Audit Finding Reconciliation)
- [ ] Update V3/output/github-issue-e30s4-audit.md with current finding statuses:
  - F1: FIXED (confirmed)
  - F2: PARTIALLY ADDRESSED (sf_picklist_validator has BAR→SF normalization, WARN policy)
  - F3: PARTIALLY ADDRESSED (T-prefix stripped at runtime, 4 missing taxonomy groups remain)
  - F4: NOT FIXED — CRITICAL (Title Case vs sentence case in CLASSIFICATION_PATTERNS)
  - F5: NOT ADDRESSED (no code comment gate)
  - F6: NOT FIXED (low priority)
  - F7: PARTIALLY ADDRESSED (SF schema now authoritative via E30-S4)
  - F8: DEFERRED (correct)

### Step 3: Create F4 Micro-Story (Product Type Casing Fix)
- [ ] Write tech spec for new story: E30-S9 (or next available) — Product Type Casing Normalization
- [ ] Agent: Bob (SM) via `/bmad-bmm-create-story`
- [ ] Pre-reads: taxonomy.py (lines 139-579), sf_picklist_validator.py, V3/output/picklist-dependency-mappings.md, V3/prompts/findings.md (F4 section)

### Step 4: Run 08b Readiness Fixes
- [ ] Run V3/prompts/08b-readiness-fixes.md in fresh context window
- [ ] Agent: Any (direct edits to BMAD planning artifacts)
- [ ] Fixes: FIX 1 (FR orphans), FIX 2 (SSE timing), FIX 3 (SP discrepancies), FIX 4 (arch story ref)
- [ ] Verify all 8 checklist items

### Step 5: Verify/Update Sprint Plan
- [ ] Sprint plan already exists at docs/sprint-artifacts/v3-sprint-plan.md
- [ ] Add F4 story to appropriate sprint slot (V3-2 or V3-3)
- [ ] Verify v3-progress.md sprint counts match sprint plan

## Phase: TASK 2 (LATER) — Architecture Explainer
- [ ] Explain backend data architecture in simple terms
- [ ] Cover: SF models, building/item picklists, classification chains, consulting wording rules, enums
- [ ] Use upload→extract→fill SF values use case as walkthrough
- [ ] Reference V3/output/ files for visuals
