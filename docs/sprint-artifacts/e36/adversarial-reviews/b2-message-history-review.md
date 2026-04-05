# Adversarial Review: B2 — Message History Endpoint + Auto-Restore

## Fix Summary
Three-part change:
1. `api/routers/unified_sessions.py` — new `GET /{source_id}/unified-sessions/{session_id}/messages`
   endpoint that reads the LangGraph checkpointer and returns serialized messages.
2. `frontend/src/lib/stores/chatSessionStore.ts` — `loadMessages()` action + auto-activate
   most-recent session with 10-minute recency threshold.
3. `frontend/src/components/chat/UnifiedChatPanel.tsx` — `useEffect` injects history into
   CopilotKit via `useCopilotChatInternal().setMessages()` on session activation.
4. `frontend/src/lib/types/chat-session.ts` — `ChatMessage` and `MessageHistoryResponse` types.

## Files Reviewed
- `api/routers/unified_sessions.py` (lines 166–239)
- `frontend/src/lib/stores/chatSessionStore.ts`
- `frontend/src/components/chat/UnifiedChatPanel.tsx` (lines 196–221)
- `frontend/src/lib/types/chat-session.ts`

## Findings

### [BLOCKER] Race: Session Switch Can Inject Stale History into Wrong Session
**What**: `UnifiedChatPanelContent` triggers history loading via `useEffect` keyed on
`[effectiveSessionId, sourceId, messagesLoaded]`. When the user switches sessions rapidly,
the `cancelled` ref correctly aborts the `then()` callback. However, `loadMessages()` in
the store sets `messagesLoaded: true` unconditionally before the component checks
`cancelled`. The sequence:

1. User clicks Session A → `messagesLoaded` = false → fetch starts for A
2. Before fetch resolves, user clicks Session B → `setActive()` sets `messagesLoaded`
   = false again → fetch for B starts
3. Fetch A resolves first → store's `loadMessages` sets `messagesLoaded: true`
4. Component's `cancelled` guard fires, so `setMessages` is skipped — good
5. But now `messagesLoaded = true` in store even though B's history was never loaded
6. The `useEffect` for B will not re-run because `messagesLoaded` is already `true`

Result: Session B opens with an empty chat and never loads its history.
**Why it matters**: User sees a blank chat where they expect their prior conversation.
Intermittent and hard to reproduce in testing (requires two rapid clicks).
**Evidence**: `chatSessionStore.ts` line 148: `set({ messagesLoaded: true })` runs
inside `loadMessages` regardless of which session the component is currently viewing.
The component-level `cancelled` flag (`UnifiedChatPanel.tsx` line 217) only guards
`setMessages`, not the store mutation.
**Recommendation**: The store should not own `messagesLoaded` as global state. It should
be a per-session flag keyed by `sessionId`, or `loadMessages` should accept and return
a session-scoped token that the component validates before updating state.

### [CONCERN] `source_id` Is Not Verified in the Messages Endpoint
**What**: `GET /{source_id}/unified-sessions/{session_id}/messages` accepts any
`source_id` path param but never checks that the session actually belongs to that source.
The implementation goes directly to `SELECT thread_id FROM $sid` using only the
`session_id`.
**Why it matters**: Any authenticated user who knows a `session_id` can read its message
history regardless of which source it belongs to, bypassing the source-scoping boundary.
This is an authorization gap, not just a validation gap.
**Evidence**: `unified_sessions.py` lines 177–178. The `source_id` parameter is accepted
but unused in the messages endpoint. The existing `list_sessions` endpoint correctly
validates ownership via the graph traversal `SELECT <-refers_to<-chat_session.*`.
**Recommendation**: Add an ownership check: verify the session has a `refers_to` edge
pointing to the given `source_id` before returning messages. Match the pattern used in
`list_sessions`.

### [CONCERN] Checkpointer Memory Leak — `get_checkpointer()` Called Per Request
**What**: `get_session_messages` calls `get_checkpointer()` on every request. Depending
on what `get_checkpointer()` returns, this may open a new SQLite connection (or
`AsyncSqliteSaver` handle) on each call without closing it.
**Why it matters**: Under concurrent session-history loads (e.g., multiple browser tabs
or a session list with auto-load), connection handles accumulate until GC collects them,
which SQLite aiofiles-based savers do not guarantee promptly.
**Evidence**: `unified_sessions.py` line 187. The checkpointer is not closed or released
after `aget_tuple()`.
**Recommendation**: Verify `get_checkpointer()` returns a singleton/shared instance. If
it creates a new connection each call, wrap usage in an async context manager or cache
the instance at module level.

### [CONCERN] `toCopilotMessage` Uses Position-Based IDs — Collision on Append
**What**: History messages get IDs like `history-0`, `history-1`, etc. When CopilotKit
appends new messages after injection, it uses its own ID scheme. If CopilotKit also
generates `history-0` for any reason (e.g., a conflict with an internal counter reset),
the message deduplication logic could drop either the injected history or the new
response.
**Why it matters**: Could silently drop a user message or assistant response from the
visible chat, making the conversation appear corrupted.
**Evidence**: `UnifiedChatPanel.tsx` lines 32–35. No UUID or content-hash fallback.
**Recommendation**: Use a stable content-addressable ID (e.g., hash of role+content) or
a namespaced UUID per message (`crypto.randomUUID()`) rather than positional indexes.

### [CONCERN] `messagesLoaded` Initializes to `false` at Store Level — Loads on Every Mount
**What**: `messagesLoaded` is initialized to `false` in the store definition (line 38 of
`chatSessionStore.ts`). On every page navigation to `/jobs/[id]` (client-side route
change), the component mounts fresh, reads `messagesLoaded: false`, and triggers a
history fetch — even for sessions the user has not switched to.
**Why it matters**: Every cold mount fires a history load for the auto-selected session.
For sessions with long histories, this is a non-trivial network call on every tab change.
**Evidence**: `chatSessionStore.ts` line 38. The store is a singleton (Zustand global),
so `messagesLoaded` persists across mounts — but only within the same page session. A
full route navigation resets React state, but Zustand persists. If the user navigates
away and back, `messagesLoaded` may still be `true` from the previous visit, meaning
history is never reloaded despite a potential server-side update.
**Recommendation**: Reset `messagesLoaded: false` in `fetchSessions()` when the
`sourceId` changes, or scope the flag per session ID.

### [NITPICK] Silent Swallow of `checkpointer.aget_tuple()` Errors
**What**: The outer `try/except Exception` in `get_session_messages` returns
`MessageHistoryResponse(messages=[], total=0)` on any error. This means a corrupt
checkpoint, a SQLite lock contention, or a schema mismatch silently returns empty
history with a 200 response and no error signal to the frontend.
**Why it matters**: Ops will not notice checkpoint corruption until users complain about
"missing history."
**Evidence**: `unified_sessions.py` lines 233–239. The `logger.error` call is present
but the HTTP response is 200 with empty data.
**Recommendation**: This is an intentional UX tradeoff (the comment says "graceful
degradation"). It is acceptable, but the log message should include enough context (thread
ID, session ID) to diagnose silently-dropped histories in production.

## Verdict: PASS WITH CONCERNS

The session-switch race condition (BLOCKER) is the primary risk. The authorization gap
(CONCERN) should be addressed before this endpoint is exposed to multi-tenant data.
The remaining concerns are defensible tradeoffs but should be tracked.
