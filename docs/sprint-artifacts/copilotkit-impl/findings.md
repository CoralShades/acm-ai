# Findings: CopilotKit HITL & Generative UI Implementation

Date: 2026-03-16
Status: IMPLEMENTATION COMPLETE

## Prior Audit Reference
See `docs/sprint-artifacts/copilotkit-audit/findings.md` for the complete audit.

## Architecture Decisions

### 1. LangGraph interrupt() for HITL (not copilotkit_interrupt)
Use LangGraph's native `interrupt()` from `langgraph.types`. CopilotKit's
`useLangGraphInterrupt` works with LangGraph's native interrupt protocol.

### 2. Separate check_write_approval node
`interrupt()` can only be called from a graph node, not from within a tool.
Graph flow: `agent → tools → check_approval → agent`

### 3. JSON string handling for resolve()
Backend parses both dict and JSON string from `interrupt()` return value
for robustness across CopilotKit versions.

### 4. confirm_write kept as legacy fallback
Delegates to `execute_pending_write()`. HITL flow bypasses this tool entirely.

### 5. copilotkit_emit_state guarded import
Non-fatal — app works without copilotkit SDK.

## Package Impact
- copilotkit 0.1.78 installed (NEW)
- fastapi downgraded 0.123.0→0.115.14 (copilotkit upper bound, within our >=0.104.0 req)
- starlette downgraded 0.50.0→0.46.2 (fastapi dep)

## CopilotKit Hooks Now Used
| Hook | File | Purpose |
|------|------|---------|
| useLangGraphInterrupt | CrudToolRenderers.tsx | HITL write approval |
| useRenderToolCall | ToolResultRenderers, CrudToolRenderers | Tool result rendering |
| useDefaultTool | ToolResultRenderers.tsx | Fallback for unregistered tools |
| useCoAgentStateRender | SmartChatPanel.tsx | Supervisor progress |
| useCopilotReadable | SmartChatPanel.tsx | Page context for LLM |
| useCopilotChatSuggestions | SmartChatPanel.tsx | Domain-aware suggestions |

## Follow-Up
1. Runtime verification with live services
2. useAgent v2 migration (separate story)
3. Bulk CRUD operations
4. E2E Playwright tests
5. Thread persistence (SqliteSaver for production)
