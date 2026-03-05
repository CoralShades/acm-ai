# E36 Task Plan — E2E Verification & Agent Orchestration

## Reboot Check (read this FIRST every session)

- **Last completed milestone**: E36-S2 (E35 Fix Re-verification)
- **Current active task**: None — ready for E36-S3
- **Blockers**: None known
- **Last modified files**: `docs/sprint-artifacts/e36/evidence/e35-s*/verification.md`, `prd.json`, `progress.md`
- **Next planned action**: E36-S3 (Route/Coverage Gap Fixes)

---

## Phase 1: Setup (E36-S1) — 3 SP

- [x] Create 6 agent files (e36-lead, e36-browser-tester, e36-log-sentinel, e36-devils-advocate, e36-bmad-scribe, e36-ux-auditor)
- [x] Edit 3 existing agents (acm-e2e-tester, qa-specialist, docs-specialist)
- [x] Create directory structure `docs/sprint-artifacts/e36/`
- [x] Create state files (task_plan.md, progress.md, findings.md)
- [x] Update prd.json with E36 epic (8 stories)
- [x] Update sprint-status.yaml with E36 entries
- [x] Add 8 missing DYNAMIC_ROUTES to route-walker.ts

## Phase 2: E35 Re-verify + Route Gaps (E36-S2 + E36-S3) — 8 SP

### E36-S2: E35 Fix Re-verification (5 SP) — DONE
- [x] S1: Sync upload — upload PDF, verify no asyncio error
- [x] S2: Model defaults — change, restart, verify persistence
- [x] S3: Ollama hardening — extraction with Ollama, verify completion
- [x] S4: Anthropic provider — verify provider priority in logs
- [x] S5: SSE terminal — completed job, verify no spinner
- [x] S6: Building backfill — /api/acm/buildings for pre-V3 sources
- [x] S7: SF-first validation — verify SF picklist values
- [x] S8: Frontend polish — source with 0 buildings, verify empty state

### E36-S3: Route Coverage Gaps (3 SP)
- [ ] Verify 12 DYNAMIC_ROUTES in route-walker.ts
- [ ] Run smoke-walker spec
- [ ] Update cheat-sheet.md routes section
- [ ] Confirm 36/36 routes covered

## Phase 3: Ollama Benchmark (E36-S4) — 5 SP

- [ ] qwen2.5:7b x Broadmeadows
- [ ] qwen2.5:7b x Alexander
- [ ] llama3.1:8b x Broadmeadows
- [ ] llama3.1:8b x Alexander
- [ ] mistral:7b x Broadmeadows
- [ ] mistral:7b x Alexander
- [ ] qwen3:32b x Broadmeadows
- [ ] qwen3:32b x Alexander
- [ ] qwen2.5:32b x Broadmeadows
- [ ] qwen2.5:32b x Alexander
- [ ] phi4:latest x Broadmeadows
- [ ] phi4:latest x Alexander
- [ ] Write summary.md with comparison table

## Phase 4: Functional + UX (E36-S5 + E36-S6) — 7 SP

### E36-S5: Functional Verification (5 SP)
- [ ] Dashboard stats cards
- [ ] Upload wizard full workflow
- [ ] Docling/MinerU extraction visible
- [ ] Raw table tab
- [ ] PDF provenance viewer
- [ ] Building sidebar + item grid
- [ ] ACM register global grid
- [ ] Source/job detail pages
- [ ] Ground truth comparison

### E36-S6: UX Audit (2 SP)
- [ ] Desktop viewport (1280x720) — all 36 routes
- [ ] Tablet viewport (768x1024) — all 36 routes
- [ ] Mobile viewport (375x667) — all 36 routes
- [ ] Loading/empty/error states
- [ ] data-testid coverage report

## Phase 5: Adversarial Review (E36-S7) — 2 SP

- [ ] E35-S1 review
- [ ] E35-S2 review
- [ ] E35-S3 review
- [ ] E35-S4 review
- [ ] E35-S5 review
- [ ] E35-S6 review
- [ ] E35-S7 review
- [ ] E35-S8 review
- [ ] Synthesis document

## Phase 6: BMAD Closeout (E36-S8) — 1 SP

- [ ] Update prd.json with final statuses
- [ ] Update sprint-status.yaml
- [ ] Update CLAUDE.md if needed
- [ ] Update MEMORY.md with E36 findings
- [ ] Finalize task_plan.md and progress.md
