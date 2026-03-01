# Progress — E29: Pipeline Unification Story Specs

## Session: 2026-03-01

### Entry 1 — Session Start
- Activated SM agent (Bob)
- Loaded all 3 mandatory pre-read documents
- Created/refreshed planning files
- Starting codebase verification + story spec generation

### Entry 2 — Codebase Verification (DONE)
- Verified all key files: utils.py:497, orchestrator.py:322/915, acm_extraction.py:2913-2917
- Confirmed: `should_use_orchestrator()` at orchestrator.py:322 (the fork to eliminate)
- Confirmed: conditional edge at acm_extraction.py:2913 (what S3 replaces)
- Confirmed: legacy nodes "prepare" (line 2899), "extract" (line 2900) still in graph
- Confirmed: `benchmarks/` dir does NOT exist (S2 creates it)
- Confirmed: ground truth CSVs exist for Broadmeadows + Alexander
- Confirmed: `ExportDialog.tsx` does NOT exist (S8 creates or modifies existing)

### Entry 3 — Story Specs (DONE)
- Generated all 8 story specs (S1-S8) to `docs/sprint-artifacts/e29-story-specs.md`
- Each spec includes: user story, ACs, tasks/subtasks, dependencies, test strategy, touched files
- Added 4 decision gate Go/No-Go checklists
- Added parallelization opportunities analysis
- Quality rules verified:
  - Every story has measurable acceptance checks (AC tables with specific checks)
  - S7 references Gate 3 criteria explicitly (cross-reference table)
  - S7 calls out Broadmeadows 31/31 and Alexander >=40/43 targets
  - S2, S7, S8 include repeatable command entrypoints (bash blocks)

### STATUS: COMPLETE
Output: `docs/sprint-artifacts/e29-story-specs.md`
