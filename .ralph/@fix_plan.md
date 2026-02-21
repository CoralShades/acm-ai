# Fix Plan: Extraction Log Panel in Document Library

## Source
- **Story file**: docs/sprint-artifacts/e15-s1-extraction-log-panel.md
- **Story ID**: E15-S1
- **Generated**: 2026-02-21T17:25:00+11:00

## Tasks
- [x] AC1: Each document row in the Document Library has an expand/collapse chevron
- [x] AC2: Clicking the chevron expands an inline panel showing `ExtractionProgressPanel`
- [x] AC3: The panel is populated via `commandId` stored on the source record
- [x] AC4: For **completed** documents: loads historical log from REST endpoint (polling fallback)
- [x] AC5: For **active/in-progress** documents: connects live SSE stream
- [x] AC6: Stage pills show all 7 stages: `STRUCTURE`, `PREFLIGHT`, `ORCHESTRATOR`, `EXTRACT`, `VALIDATE`, `CORRECT`, `STORE`
- [x] AC7: Log terminal is scrollable, monospace, with Copy All button
- [x] AC8: Failed/partial extractions show a **Retry Extraction** button
- [x] AC9: Panel can be collapsed by clicking chevron again
- [x] AC10: Works for both success and failure states
- [x] AC11: Accessible: keyboard operable (Enter/Space to expand, Escape to collapse)
- [x] AC12: Only one panel open at a time (expanding another collapses previous)

## Completion Criteria
- All tasks above are checked off
- All tests passing: `pytest tests/ -x`
- No lint errors: `ruff check .`
- Frontend builds: `cd frontend && npm run lint && npm run build`
- Changes committed with conventional commit message
