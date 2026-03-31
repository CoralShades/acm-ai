# Chat System Debug & Fix — 5 Issues Resolved (2026-03-28)

**Branch**: fix/chat-v2 (merged via PRs #114, #115, #116)
**Date**: 2026-03-28
**Files changed**: 7
**Scope**: Backend tools, system prompt, and frontend chat renderers

---

## Summary

Five bugs identified in the UnifiedChatPanel (CopilotKit/AG-UI path) were investigated and fixed.
The issues spanned backend tool gaps, SurrealQL binding failures, tool name mismatches, and
frontend UX regressions from intermediate "thinking" messages rendering as full chat bubbles.

---

## Issues Fixed

### Issue #4: surreal_query tool failing (CRITICAL — fixed first)

**Root cause**: LLM-generated SurrealQL used variable names beyond the pre-bound `$sid`/`$val`
params (e.g. `$risk`, `$room`, `$material`). These unmatched params were passed to SurrealDB
unbound, causing query failures or zero results.

**Fix**: `open_notebook/graphs/crud_tools.py` — Auto-bind any unmatched `$param` references in
the LLM-generated query to `None` before execution. Unmatched params are detected by diffing
the set of `$xxx` tokens in the query string against the explicitly provided bindings.

**Files**: `open_notebook/graphs/crud_tools.py`

---

### Issue #3: Agent only queries acm_record table

**Root cause**: No tools existed for building-level summaries or source/document metadata.
The agent defaulted to ACM record search tools because they were the only available option.

**Fix**: Two new `@tool` functions added to `open_notebook/graphs/chat_tools/acm_tools.py`:

- `list_acm_buildings` — Returns all buildings for the current source with per-building ACM
  item counts and risk level breakdowns (friable / non-friable / assumed positive counts).
- `get_source_metadata` — Returns document-level metadata: source title, consultant name,
  site name, date of audit, extraction statistics (total items, buildings, extraction date).

Both tools were registered in `open_notebook/graphs/chat_tools/__init__.py` via `get_acm_tools()`
and added to the system prompt in `prompts/unified_agent.jinja` with usage guidance.

**Files**:
- `open_notebook/graphs/chat_tools/acm_tools.py`
- `open_notebook/graphs/chat_tools/__init__.py`
- `prompts/unified_agent.jinja`

---

### Issue #2: Tool name mismatch — frontend renderers not firing

**Root cause**: Frontend `useRenderToolCall` registrations in `UnifiedToolRenderers.tsx` used
stale tool names (`search_documents_vector`, `text_search_documents`) that did not match the
current backend tool names (`search_documents`, `semantic_search_acm`). The new tools added in
Issue #3 (`list_acm_buildings`, `get_source_metadata`) also had no renderers.

**Fix**:
- `semantic_search_acm` renderer added to `UnifiedToolRenderers.tsx`
- `get_source_metadata` renderer added (shows document metadata card)
- `list_acm_buildings` renderer added using new `BuildingSummaryCard` component
- Tool name strings corrected to match backend `@tool` decorated function names

Final alignment: 18 frontend renderers cover 17 LLM-facing tools + 1 internal tool.

**Files**: `frontend/src/components/chat/UnifiedToolRenderers.tsx`

---

### Issue #1: Thinking/processing messages show as full chat bubbles

**Root cause**: The AG-UI protocol emits `TEXT_MESSAGE_CONTENT` events for short intermediate
agent reasoning steps. CopilotKit rendered each as a full `AssistantMessage` bubble. Short
messages (under a threshold) that appeared between tool calls were processing thoughts, not
final answers.

**Fix**: `frontend/src/components/chat/ACMAssistantMessage.tsx` — Added `isThinkingContent()`
detector. Short messages (under 120 characters) containing thinking/processing keywords
("thinking", "let me", "checking", "searching", "looking", "analyzing", "found", "based on")
are rendered as a compact spinner + text indicator instead of a full message bubble.
Messages with empty content return `null` (no render).

**Files**: `frontend/src/components/chat/ACMAssistantMessage.tsx`

---

### Issue #5: Orphaned renderers — ItemDetailCard and BuildingSummaryCard unused

**Root cause**: `ItemDetailCard.tsx` and `BuildingSummaryCard.tsx` existed in the renderers
directory but were never imported by `UnifiedToolRenderers.tsx`. The `get_acm_record_detail`
tool was rendering via a generic single-row `ACMTableResult` instead of the richer card.

**Fix**:
- `get_acm_record_detail` renderer updated to use `ItemDetailCard` for rich record display
- `list_acm_buildings` renderer wired to use `BuildingSummaryCard`
- `get_source_metadata` and `list_acm_buildings` labels added to `ToolStepItem.tsx`

**Files**:
- `frontend/src/components/chat/UnifiedToolRenderers.tsx`
- `frontend/src/components/chat/renderers/ToolStepItem.tsx`

---

## Files Modified

| File | Change |
|------|--------|
| `open_notebook/graphs/chat_tools/acm_tools.py` | Added `list_acm_buildings` and `get_source_metadata` tools |
| `open_notebook/graphs/chat_tools/__init__.py` | Updated exports and `get_acm_tools()` to include new tools |
| `open_notebook/graphs/crud_tools.py` | Auto-bind unmatched `$param` references in LLM SurrealQL queries |
| `prompts/unified_agent.jinja` | Added new tools to system prompt and tool selection guide |
| `frontend/src/components/chat/UnifiedToolRenderers.tsx` | Added renderers for `semantic_search_acm`, `get_source_metadata`, `list_acm_buildings`; wired `ItemDetailCard` for `get_acm_record_detail` |
| `frontend/src/components/chat/ACMAssistantMessage.tsx` | Compact thinking indicator for short intermediate messages; null return for empty content |
| `frontend/src/components/chat/renderers/ToolStepItem.tsx` | Added labels for `get_source_metadata` and `list_acm_buildings` |

---

## Fix Priority Order Applied

Issues were fixed in dependency order:

1. **#4 (surreal_query binding)** — Foundation: queries must work before anything else
2. **#3 (new tools)** — Agent needs building and metadata tools to query multiple tables
3. **#2 (tool name alignment)** — Renderers must match backend tool names exactly
4. **#5 (orphaned renderers)** — Wire existing components now that tool results flow correctly
5. **#1 (thinking UX)** — UI-only fix applied after tool pipeline confirmed working

---

## Related History

- `unified-chat-phase1-backend-2026-03-22` — Original unified agent implementation
- `unified-chat-phase3-s2-legacy-chat-deprecation-2026-03-22` — Legacy chat deletion
- `fix-chat-pipeline-async-tools-2026-03-23` (PR #114) — Async tools + AsyncSqliteSaver
- PR #115 — Token streaming + CopilotKit suggestions + streaming cursor
- PR #116 — Active tab context + mobile fix + input polish
