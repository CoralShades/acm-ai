# Pipeline Debug Task Plan

## Objective
Debug ACM extraction pipeline — trace analysis, prompt overhaul, persistence fixes.
Target: Broadmeadows PDF → 31 records, 1 building.

## Phase 1 — Trace Analysis & Code Audit (parallel subagents)
- [ ] 1.1 Langfuse trace analysis (traces `8270cdb0...`, `38c0555b...`)
- [ ] 1.2 LangSmith run analysis (runs `fdfc9f9d...`, `6a010e5d...`)
- [ ] 1.3 Prompt template audit (all `prompts/acm/*.jinja`)
- [ ] 1.4 Persistence path audit (save_records, ObjectModel.save, building ID gen)

## Phase 2 — Root Cause Synthesis
- [ ] 2.1 Synthesize subagent findings into ranked issue list
- [ ] 2.2 Draft prompt rewrites for each affected node
- [ ] 2.3 Draft code fixes for persistence/logic bugs
- [ ] 2.4 Present all changes to user for approval

## Phase 3 — Apply Fixes
- [ ] 3.1 Apply approved prompt rewrites
- [ ] 3.2 Apply approved code fixes
- [ ] 3.3 Run lint (`ruff check .`)
- [ ] 3.4 Run tests (`pytest tests/ -x`)

## Phase 4 — Verification
- [ ] 4.1 Re-run Broadmeadows extraction
- [ ] 4.2 Compare output vs ground truth (target: 30-31 records)
- [ ] 4.3 Verify SurrealDB persistence
- [ ] 4.4 Update findings.md and progress.md
