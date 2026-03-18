# Multi-Consultant Story 6: HITL Mapping Confirmation UI
# Generated via /generate-prompt --save --with-plan --tmux

**SP: 8 | Wave: 4 | Dependencies: Stories 2 + 3 complete**
**Design doc: `docs/architecture/multi-consultant-format-design.md` Section 5.2 (HITL trigger), Section 7 Story 6**

## Skills to Load

/planning-with-files — persistent markdown plan
/react-best-practices — React/Next.js component patterns
/sse-streaming — SSE for pause/resume extraction flow
/langgraph-human-in-the-loop — LangGraph interrupt() for HITL
/copilotkit — CopilotKit integration patterns
/test-driven-development — TDD for backend + frontend
/verification-before-completion — verify before claiming done

---

## Prerequisites

- Branch: `git checkout ACMV3`
- Story 2 complete (schema inference node with confidence scores)
- Story 3 complete (format profile registry with API endpoints)
- All services running (SurrealDB, API, Worker, Frontend)
- Pack 4 (Frontend UX) complete — SSE infrastructure fixed

---

## Glossary

| Term | Definition |
|------|-----------|
| HITL | Human-In-The-Loop — user confirmation step when schema inference confidence < 0.8 |
| Column mapping dialog | Frontend component showing PDF header → SF field mapping with confidence indicators |
| `interrupt()` | LangGraph function that pauses graph execution, sends state to frontend, waits for user response |
| PipelineEventBus | Pub/sub bus for SSE events — used to signal HITL pause/resume |
| Format profile | Saved mapping — on user approval, saved to `consultant_format_profile` for future cache hits |
| InferredSchema | Schema inference output — includes `confidence` score that triggers HITL |

---

## Key Files

**Read:**
- `docs/architecture/multi-consultant-format-design.md` — Section 5.2 (step 5: HITL trigger)
- `open_notebook/extractors/schema_inference.py` — confidence score, InferredSchema
- `open_notebook/graphs/acm_extraction.py` — existing interrupt() usage (CRUD chat HITL)
- `open_notebook/extractors/pipeline_event_bus.py` — SSE event emission
- `api/routers/format_profiles.py` — Story 3 API endpoints
- `frontend/src/components/acm/HITLApprovalDialog.tsx` — existing HITL dialog pattern (CRUD chat)
- `frontend/src/lib/hooks/useV3SSE.ts` — SSE hook
- `frontend/src/lib/stores/streamingStore.ts` — Zustand SSE store

**Create:**
- `frontend/src/components/acm/ColumnMappingDialog.tsx` — mapping review UI
- `frontend/src/lib/hooks/useColumnMapping.ts` — hook for HITL mapping flow
- `tests/test_hitl_schema_inference.py` — backend interrupt/resume tests

**Modify:**
- `open_notebook/extractors/schema_inference.py` — add `interrupt()` call when confidence < 0.8
- `open_notebook/graphs/acm_extraction.py` — handle HITL resume with user-confirmed mapping
- `api/routers/v3_streaming.py` — SSE event type for schema mapping HITL
- `frontend/src/lib/types/v3-streaming.ts` — add HITL event type

---

## Plan

Create `docs/sprint-artifacts/mcs6-hitl-ui/task_plan.md`:
- [ ] Design ColumnMappingDialog UI (table: PDF Header | SF Field | Confidence | Action)
- [ ] Implement backend: `interrupt()` in schema inference node when confidence < 0.8
- [ ] Implement SSE event: `schema_mapping_review` event type with InferredSchema payload
- [ ] Implement frontend: `useColumnMapping` hook — listen for SSE event, show dialog
- [ ] Implement ColumnMappingDialog — show mappings, allow modify/approve/reject per row
- [ ] Implement approve action: POST to format profile registry, resume extraction
- [ ] Implement reject action: fall back to COLUMN_ALIASES fuzzy matching
- [ ] Implement modify action: user edits mapping → approve with modified mapping
- [ ] Add confidence color coding: green (≥0.9), yellow (0.7-0.9), red (<0.7)
- [ ] Wire SSE: pause extraction → show dialog → resume on user action
- [ ] Write backend tests: interrupt() triggered at confidence 0.75, not at 0.85
- [ ] Write frontend tests: dialog renders with mock mapping data
- [ ] Run full test suite + lint + frontend build

---

## Agent Team Strategy: TMUX ( Opus + Claude Agent Teams - Not Subagents)

```
Pane 0 (left-top):    Backend — schema_inference.py interrupt(), SSE event
Pane 1 (left-bottom): Frontend — ColumnMappingDialog.tsx, useColumnMapping.ts
Pane 2 (right-top):   Test runner — pytest + npm run build
Pane 3 (right-bottom): Browser — verify dialog renders (agent-browser or chrome-devtools)
```

---

## Context7 Directives

1. resolve-library-id for "langgraph" → query-docs for "interrupt human-in-the-loop checkpoint resume"
2. resolve-library-id for "react" → query-docs for "useEffect useState dialog modal form"
3. resolve-library-id for "zustand" → query-docs for "store subscribe actions selectors"

---

## Verification Checklist

- [ ] Schema inference with confidence 0.75 triggers HITL interrupt
- [ ] Schema inference with confidence 0.85 does NOT trigger HITL
- [ ] SSE `schema_mapping_review` event emitted with InferredSchema payload
- [ ] ColumnMappingDialog renders with mapping table
- [ ] Each row shows: PDF header, mapped SF field, confidence badge (color-coded)
- [ ] User can modify SF field selection via dropdown
- [ ] Approve → saves to format profile registry → resumes extraction
- [ ] Reject → falls back to COLUMN_ALIASES → resumes extraction
- [ ] `cd frontend && npm run build` — build passes
- [ ] `uv run pytest tests/test_hitl_schema_inference.py -v` — all pass
- [ ] `uv run pytest tests/ -x` — full suite passes
- [ ] `uv run ruff check .` — lint clean

---

## Commit Template

```
feat(ux): add HITL column mapping confirmation UI for low-confidence schema inference

- Add interrupt() to schema inference node when confidence < 0.8
- Create ColumnMappingDialog with per-row approve/modify/reject
- SSE schema_mapping_review event for pause/resume flow
- On approve: save to format profile registry for future cache hits
- Color-coded confidence badges (green/yellow/red)
- Multi-Consultant Story 6 of 7

Co-Authored-By: Claude <noreply@anthropic.com>
```
