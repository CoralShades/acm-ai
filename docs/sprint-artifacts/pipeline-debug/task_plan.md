# Pipeline Debug Task Plan

## Objective
Debug ACM extraction pipeline — trace analysis, prompt overhaul, persistence fixes.
Target: Broadmeadows PDF → 31 records, 1 building.

## Phase 1 — Trace Analysis & Code Audit (parallel subagents)
- [x] 1.1 Langfuse trace analysis (traces `8270cdb0...`, `38c0555b...`)
- [x] 1.2 LangSmith run analysis (runs `fdfc9f9d...`, `6a010e5d...`)
- [x] 1.3 Prompt template audit (all `prompts/acm/*.jinja`)
- [x] 1.4 Persistence path audit (save_records, ObjectModel.save, building ID gen)

## Phase 2 — Root Cause Synthesis
- [x] 2.1 Synthesize subagent findings into ranked issue list
- [x] 2.2 Draft prompt rewrites for each affected node
- [x] 2.3 Draft code fixes for persistence/logic bugs
- [x] 2.4 Present all changes to user for approval

## Phase 3 — Apply Fixes
- [x] 3.1 Apply approved prompt rewrites
- [x] 3.2 Apply approved code fixes
- [x] 3.3 Run lint (`ruff check .`)
- [x] 3.4 Run tests (`pytest tests/ -x`)

## Phase 4 — Verification
- [x] 4.1 Re-run Broadmeadows extraction
- [x] 4.2 Compare output vs ground truth — achieved 29/31 (93.5%)
- [x] 4.3 Verify SurrealDB persistence
- [x] 4.4 Update findings.md and progress.md
