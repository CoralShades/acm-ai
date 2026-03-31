# Chat System Debug & Fix — Task Plan

> Generated: 2026-03-28
> Scope: 5+1 critical chat bugs in UnifiedChatPanel (CopilotKit/AG-UI path)

## Priority Order

- [x] **Issue #4**: surreal_query tool failing — Fixed unbound `$val` params
- [x] **Issue #3**: Agent only queries acm_record — Added `list_acm_buildings` + `get_source_metadata` backend tools
- [x] **Issue #2**: Tool name mismatch frontend/backend — Added `semantic_search_acm` + `get_source_metadata` renderers
- [x] **Issue #1**: Thinking messages as full chat bubbles — Compact thinking indicator for short intermediate messages
- [x] **Issue #5**: Orphaned renderers — Wired `ItemDetailCard` for record detail, `BuildingSummaryCard` for buildings
- [x] **ROOT CAUSE**: ACMAssistantMessage never rendered `message.generativeUI()` — ALL tool renders were silently dropped
- [x] **Verification**: Build, lint, test — TypeScript, Ruff, format all pass
- [x] **Documentation**: Sprint status, artifacts, progress.md
- [ ] **E2E Testing**: Live browser verification pending

## Root Cause Discovery (from LangSmith trace analysis)

The AG-UI SSE stream correctly emits `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END` events.
CopilotKit's `useRenderToolCall` hooks fire correctly and produce JSX.
CopilotKit attaches the rendered JSX to `message.generativeUI`.

**BUT**: Our custom `ACMAssistantMessage` component **never called `message.generativeUI()`**, so all tool renders were silently dropped. The default CopilotKit `AssistantMessage` renders it as a `subComponent`, but our custom component replaced it completely without this critical line.

**Fix**: Added `const toolUI = message?.generativeUI?.() ?? null` and rendered it in all code paths.

## Changes Made

### Backend (Python)
1. `open_notebook/graphs/chat_tools/acm_tools.py` — Added `list_acm_buildings` and `get_source_metadata` tools
2. `open_notebook/graphs/chat_tools/__init__.py` — Updated exports and `get_acm_tools()` list
3. `open_notebook/graphs/crud_tools.py` — Fixed `$val` binding: auto-bind unmatched params in LLM-generated SurrealQL
4. `prompts/unified_agent.jinja` — Added new tools to system prompt and tool selection guide

### Frontend (TypeScript/React)
5. `frontend/src/components/chat/UnifiedToolRenderers.tsx` — Added renderers for `semantic_search_acm`, `get_source_metadata`, `list_acm_buildings` (with BuildingSummaryCard), `get_acm_record_detail` (with ItemDetailCard)
6. `frontend/src/components/chat/ACMAssistantMessage.tsx` — **KEY FIX**: Added `message.generativeUI()` rendering + compact thinking indicator + null for empty content
7. `frontend/src/components/chat/renderers/ToolStepItem.tsx` — Added labels for `get_source_metadata` and `list_acm_buildings`

### Tool Alignment (18 renderers ↔ 17 LLM tools + 1 internal)
All tools now have matching frontend renderers. No orphaned renderers remain.
