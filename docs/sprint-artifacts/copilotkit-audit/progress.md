# Progress: CopilotKit Audit & Integration

Date: 2026-03-16

## Completed

### Pre-Session
- [x] Pre-session codebase audit (CopilotKit usage scan across 25+ files)
- [x] Frontend dependency inventory (3 CopilotKit packages at v1.51.4)
- [x] Gap matrix baseline (12 implemented, 16 missing features identified)
- [x] Prompt pack generated and saved to docs/sprint-artifacts/prompt-packs/

### Phase 1 — Research
- [x] Read all 8 CopilotKit skill reference docs (SKILL.md + 8 references)
- [x] Read AG-UI pipeline spec (docs/ag-ui-pipeline-spec.md)
- [x] CopilotKit docs research via Context7 MCP (v1 vs v2 APIs, all hooks, migration path)
- [x] LangGraph HITL docs research via Context7 MCP (interrupt, Command, streaming, subgraphs)
- [x] Deep codebase gap analysis (30+ file audit, comprehensive gap matrix)

### Phase A — Critical Bug Fixes
- [x] A1: Runtime routes rewritten with lazy singleton pattern (BUG-1, BUG-2)
- [x] A2: MemorySaver checkpointer added to CRUD graph (BUG-3)
- [x] A3: Error handling via isErrorResult() in all 11 tool renderers (BUG-4)
- [x] A4: CopilotProvider fixed: env-conditional showDevConsole + onError callback (BUG-5)
- [x] A5: @ag-ui/client added as explicit dependency v0.0.43 (was transitive only)

### Phase B — High-Priority Correctness Fixes
- [x] B1: ToolResultRenderers refactored: useCopilotAction → useRenderToolCall (9 renderers)
- [x] B2: CrudToolRenderers refactored: useCopilotAction → useRenderToolCall (2 renderers)
- [x] B3: useCopilotReadable added for source/notebook/page context in SmartChatPanel
- [x] B4: makeSystemMessage signature fixed in JobCrudChatPanel (contextString parameter)

### Phase C — Feature Additions
- [x] C1: useCopilotChatSuggestions added to SmartChatPanel (domain-aware suggestions)

### Verification
- [x] Frontend build passes: `cd frontend && npm run build`
- [x] Frontend lint passes: `cd frontend && npm run lint` (only pre-existing warnings)
- [x] Backend lint passes: `uv run ruff check` on modified files
- [x] ToolErrorCard component created for error state rendering

## Not Implemented (deferred)

- B5: useSmartChat state divergence fix — requires useAgent v2 migration
- C2: useCoAgentStateRender — needs backend emit_state wiring
- C3: useDefaultTool — low priority, no unknown tools emitted
- D1-D3: HITL interrupt() implementation — larger change, separate story recommended
- useAgent v2 migration — non-breaking, defer to separate story
- copilotkit Python SDK adoption — ag-ui-langgraph works fine

## Key Decisions

1. **Stay on v1 API** — v2 additive, no breaking changes needed now
2. **useRenderToolCall status types** — v1.51.4 types only include "inProgress" | "executing" | "complete" (no "failed"). Error handling via result inspection using isErrorResult().
3. **Lazy singleton pattern** for CopilotRuntime — dynamic imports required by serverExternalPackages, cached via module-level promise.
4. **HITL deferred** — requires CRUD graph redesign + new frontend hook wiring, better as separate sprint story.
