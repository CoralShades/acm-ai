# E36 Adversarial Review Synthesis — Chat & UI Bug Fix Sprint

## Overview
- Fixes reviewed: 4 (B1, B2, B3, B4)
- BLOCKERs: 1
- CONCERNs: 9
- NITPICKs: 3

## Blocker Summary

### B2 — Session-Switch Race Condition (chatSessionStore.ts)
The store's `loadMessages()` sets `messagesLoaded: true` globally, not per-session.
When a user switches sessions before the first fetch resolves, the second session's
history load is permanently skipped because `messagesLoaded` is already `true` when its
`useEffect` runs. The component-level `cancelled` guard only prevents stale data
injection; it does not reset the store flag. Result: switching sessions leaves an empty
chat that never loads its history. This is a correctness bug, intermittent, and
reproducible by switching sessions during a slow API call.

## Top Concerns (Ranked)

1. **B2 — Authorization gap in `/messages` endpoint** (unified_sessions.py lines 177–178):
   The `source_id` path parameter is accepted but unused. Any caller who knows a
   `session_id` can read its full message history regardless of source ownership. Must be
   addressed before multi-tenant use.

2. **B4 — `'idle'` phase triggers stale-status override on cold load** (page.tsx line
   161): Users who open a job page mid-extraction see "pending review" briefly while the
   SSE hook initializes. Removing `'idle'` from the override set is a one-word fix.

3. **B3 — Partial FK coverage silently drops record counts** (acm_tools.py lines 394–431):
   Buildings with unlinked records (no `building_record_id`) report zero records when any
   building in the dataset has a FK. The name-based fallback is gated incorrectly and
   never runs in mixed datasets.

4. **B2 — Checkpointer connection management** (unified_sessions.py line 187):
   `get_checkpointer()` is called per-request; if it opens a new handle each time,
   connection handles accumulate under concurrent load.

5. **B4 — `ExtractionStatusBanner` reads raw status, not effective status** (page.tsx
   lines 340–343): Banner and header can display contradictory extraction states.

6. **B1 — Unverifiable model IDs create silent runtime failures** (model_provisioning.py
   lines 140–147): Models are seeded into DB without any live API validation; a wrong ID
   fails silently at inference time with no error surfaced to the user.

7. **B2 — `messagesLoaded` not scoped per-session** (chatSessionStore.ts line 38, 63):
   Cross-session state contamination; navigating away and back may permanently suppress
   history reload.

8. **B3 — Dead `.replace()` call masks field assumption** (acm_tools.py line 385):
   The no-op `.replace("source_id", "source_id")` is misleading and should be removed.

9. **B2 — Position-based message IDs risk CopilotKit deduplication collisions**
   (UnifiedChatPanel.tsx lines 32–35).

## Recommendations (Prioritized)

1. **Fix the session-switch race** (BLOCKER): Scope `messagesLoaded` per session ID in
   the store, or move it to local component state entirely. The store should not own
   per-session fetch lifecycle flags.

2. **Add source ownership check to the messages endpoint**: Mirror the `refers_to` graph
   traversal used by `list_sessions` — verify the session belongs to the given source
   before returning checkpoint data.

3. **Remove `'idle'` from the B4 stale-status override condition**: This is a one-line
   change that eliminates the cold-load flash.

4. **Fix B3 fallback guard**: Remove `not stats_by_id` from the name-based fallback
   condition so mixed FK/non-FK datasets always get correct counts.

5. **Audit OpenRouter/Anthropic model IDs** (B1): Add source-of-truth comments or a
   startup validation call for newly added models.

6. **Align ExtractionStatusBanner with effectiveReviewStatus** (B4): Use
   `effectiveReviewStatus === 'extracting'` instead of raw status checks.
