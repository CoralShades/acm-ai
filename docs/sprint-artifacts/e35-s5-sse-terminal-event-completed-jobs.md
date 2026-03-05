# E35-S5: SSE Terminal Event for Completed Jobs

## Story

**ID**: E35-S5 | **Epic**: E35 | **Sprint**: V3-8 | **Points**: 2 SP | **Risk**: LOW | **Type**: frontend

## Summary

When a user navigates to an extraction progress page for an already-completed job, both SSE endpoints currently block forever waiting for events that will never arrive. The `extraction_events.py` polling loop waits 300 seconds for a DB row to change, and the `agui_extraction.py` loop polls indefinitely for new `agui_events` rows. Neither endpoint checks whether the job is already in a terminal state before entering its polling loop. The result is a hung EventSource on the client, console errors when it eventually times out, and stale UI state.

This story fixes both the backend SSE endpoint (`/api/acm/extraction-progress/{command_id}/stream`) and the frontend `useExtractionProgress` hook so that:

1. The backend detects an already-completed or failed job on the **first poll** and immediately emits a terminal event, then closes the stream.
2. The frontend hook detects the terminal event type emitted by the backend and closes the EventSource cleanly without transitioning through a spurious error state.

The V3 streaming endpoints (`v3_streaming.py`) are **not** in scope — they use a separate in-memory `PipelineEventBus` which is ephemeral and unrelated to the DB-persisted `extraction_progress` table.

---

## Background and Context

### How the existing legacy SSE endpoints work

**Backend — `api/routers/extraction_events.py`** (the endpoint consumed by `useExtractionProgress`)

`/api/acm/extraction-progress/{command_id}/stream` polls the `extraction_progress` SurrealDB table once per second. On each tick it calls `_get_progress(command_id)`, checks whether `status` changed since last tick, and if the status is `"completed"` or `"failed"` it emits:

```
data: {"status": "completed", "state": {...}, "log_entries": [...]}

event: done
data: {"status": "completed"}
```

then returns, closing the stream.

The bug: there is no pre-flight check. If the job is already completed before the first client connection, the first poll sees `status == "completed"` and emits the terminal `event: done` correctly — **this path actually works** for the `extraction_events.py` endpoint. However, if the `extraction_progress` row does not exist yet (race condition between job submission and row creation), or if `command_id` is stale/wrong, the loop blocks for up to 300 seconds without emitting anything, leaving the EventSource open and causing the frontend's 3-second SSE timeout to fire, which triggers the polling fallback with `fallbackToPollingRef.current = true`.

The real bug manifests when `useExtractionProgress` is mounted **after** the job completes (e.g., user navigates away and back). In that case:
- `sessionStorage` still holds `phase: "extracting"` and a `commandId`.
- The hook re-opens an EventSource to `extraction-progress/stream`.
- If the `extraction_progress` DB row exists and is `"completed"`, the first poll tick does emit `event: done`. The `eventSource.addEventListener('done', ...)` handler fires in `use-agui-stream.ts` (which listens on the `/agui/extraction/` endpoint, not this one). The `useExtractionProgress` hook does NOT listen for the named `"done"` event — it only listens on `eventSource.onmessage` (unnamed data events). So the `event: done` payload is **not** received by `onmessage`.
- The hook never transitions out of `'extracting'` phase, and `fallbackToPollingRef.current` fires after 3 seconds.

**Backend — `api/routers/agui_extraction.py`**

`/api/agui/extraction/{command_id}/stream` polls the `agui_events` table. For a completed job the `agui_events` rows still exist (they are not deleted). The first poll at `after_seq=0` will return all rows, including the terminal `RunFinished` event. The loop emits those rows and then returns when it hits the `RunFinished` type. So this endpoint also already handles completed jobs correctly at the data level.

The bug here is identical: `use-agui-stream.ts` reconnects unconditionally when `commandId` changes. If the hook reconnects after job completion it will replay all events, which is benign for AGUI (idempotent state updates), but is wasteful.

### Root cause summary

The real gap is in `useExtractionProgress`: after a page reload it restores `phase: "extracting"` from sessionStorage and reconnects the SSE. The SSE emits `event: done` (a named event), but `useExtractionProgress` only handles **unnamed** `message` events (`eventSource.onmessage`). The hook therefore never sees the terminal signal, never clears sessionStorage, and never transitions to `'completed'`. The 3-second timeout fires, the fallback polling path kicks in and queries `GET /api/commands/jobs/{id}` which does return `status: "completed"` — so the polling path does eventually resolve it correctly. But there is a 3-second delay and potential console noise.

The fix is in two places:

1. **`use-extraction-progress.ts`**: Add a `addEventListener('done', ...)` handler to the EventSource so the named `done` event closes the stream and triggers a final status check, bypassing the 3-second SSE timeout.
2. **`extraction_events.py`**: Add a pre-flight check at stream open time. If the job is already in a terminal state, emit the `data:` payload and the `event: done` immediately (without entering the polling loop), then close.

---

## Implementation Plan

### Change 1 — Backend pre-flight terminal check in `extraction_events.py`

Refactor `_sse_generator` to check the initial job status before entering the polling loop. If already terminal, emit the terminal payload and close immediately.

**File**: `api/routers/extraction_events.py`

Replace the `_sse_generator` async generator with the following logic:

```python
async def _sse_generator(command_id: str):
    """Generate SSE events by polling extraction_progress table.

    E35-S5: Pre-flight check — if the job is already in a terminal state on
    first connection, emit the terminal event immediately and close the stream.
    """
    last_updated = None
    heartbeat_counter = 0
    polls_per_heartbeat = int(_HEARTBEAT_INTERVAL_S / _POLL_INTERVAL_S)

    while True:
        progress = await _get_progress(command_id)

        if progress:
            current_updated = str(progress.get("updated_at", ""))
            if current_updated != last_updated:
                last_updated = current_updated
                data = {
                    "status": progress.get("status", "running"),
                    "state": json.loads(progress["state_json"])
                    if progress.get("state_json")
                    else None,
                    "log_entries": progress.get("log_entries", []),
                }
                yield f"data: {json.dumps(data)}\n\n"

                if progress.get("status") in _TERMINAL_STATUSES:
                    yield f"event: done\ndata: {json.dumps({'status': progress['status']})}\n\n"
                    return

        # Heartbeat to keep connection alive
        if heartbeat_counter >= polls_per_heartbeat:
            yield ": heartbeat\n\n"
            heartbeat_counter = 0

        heartbeat_counter += 1
        await asyncio.sleep(_POLL_INTERVAL_S)
```

**Important**: The existing code already emits the correct sequence (data event then `event: done`) when it detects a terminal status. The logic change here is minimal — the current `updated_at` guard (`if current_updated != last_updated`) means the very first poll always satisfies the condition (`last_updated` is `None`), so the terminal data event IS emitted on the first tick. The backend is actually already correct in this regard.

The meaningful backend change is adding a **timeout guard** so that if `_get_progress` returns `None` (no DB row found — job not yet recorded or stale `command_id`), instead of polling forever, the generator fails fast after a configurable number of attempts:

```python
_MAX_EMPTY_POLLS = 10  # 10 seconds at 1s interval before giving up

async def _sse_generator(command_id: str):
    last_updated = None
    heartbeat_counter = 0
    polls_per_heartbeat = int(_HEARTBEAT_INTERVAL_S / _POLL_INTERVAL_S)
    empty_poll_count = 0

    while True:
        progress = await _get_progress(command_id)

        if progress:
            empty_poll_count = 0  # reset on first found row
            current_updated = str(progress.get("updated_at", ""))
            if current_updated != last_updated:
                last_updated = current_updated
                data = {
                    "status": progress.get("status", "running"),
                    "state": json.loads(progress["state_json"])
                    if progress.get("state_json")
                    else None,
                    "log_entries": progress.get("log_entries", []),
                }
                yield f"data: {json.dumps(data)}\n\n"

                if progress.get("status") in _TERMINAL_STATUSES:
                    yield f"event: done\ndata: {json.dumps({'status': progress['status']})}\n\n"
                    return
        else:
            empty_poll_count += 1
            if empty_poll_count >= _MAX_EMPTY_POLLS:
                # No progress row found after 10 seconds — emit error and close
                yield (
                    f"event: error\n"
                    f"data: {json.dumps({'status': 'not_found', 'command_id': command_id})}\n\n"
                )
                return

        if heartbeat_counter >= polls_per_heartbeat:
            yield ": heartbeat\n\n"
            heartbeat_counter = 0

        heartbeat_counter += 1
        await asyncio.sleep(_POLL_INTERVAL_S)
```

### Change 2 — Frontend: handle named `done` event in `useExtractionProgress`

**File**: `frontend/src/lib/hooks/use-extraction-progress.ts`

The EventSource created in the `useEffect` block only attaches `eventSource.onmessage` and `eventSource.onerror`. It does not listen for the named `done` event that the backend emits at the end of the stream. Add a `done` event listener that:

1. Cancels the SSE timeout (prevents spurious fallback-to-polling).
2. Reads the payload to determine terminal status.
3. Calls the existing completion/failure handler logic.
4. Closes the EventSource.

```typescript
// Inside the useEffect, after attaching eventSource.onmessage and before the return:

// E35-S5: Handle the named 'done' event emitted by the backend on terminal status.
// Without this, a completed job's terminal event is silently ignored because
// eventSource.onmessage only fires for unnamed (no "event:" prefix) SSE messages.
eventSource.addEventListener('done', (e: MessageEvent) => {
  // Cancel SSE timeout — we got a signal, no need to fall back to polling
  if (sseTimeoutRef.current) {
    clearTimeout(sseTimeoutRef.current)
    sseTimeoutRef.current = null
  }

  try {
    const payload: { status: string } = JSON.parse(e.data)
    const terminalStatus = payload.status

    if (terminalStatus === 'completed') {
      // Re-read pipelineState from the last onmessage update (already in state)
      // recordsCreated may be available from pipelineState already set by data event
      setPhase('completed')
      sessionStorage.removeItem(sessionKey)
      eventSource.close()

      queryClient.invalidateQueries({ queryKey: ['acm', 'records', sourceId] })
      queryClient.invalidateQueries({ queryKey: ACM_QUERY_KEYS.stats(sourceId) })
    } else if (terminalStatus === 'failed') {
      setPhase('failed')
      setErrorMessage('Extraction failed')
      sessionStorage.removeItem(sessionKey)
      eventSource.close()
    } else if (terminalStatus === 'not_found') {
      // Backend timed out waiting for a DB row — fall back to REST polling
      fallbackToPollingRef.current = true
      eventSource.close()
    }
  } catch {
    // Malformed done payload — close cleanly
    eventSource.close()
  }
})

// E35-S5: Handle named 'error' event from backend (not the onerror callback)
eventSource.addEventListener('error', (e: Event) => {
  const msgEvent = e as MessageEvent
  // Only treat as server-sent error when connection is OPEN
  if (eventSource.readyState === EventSource.OPEN) {
    console.warn('[ExtractionProgress] SSE server error event:', msgEvent.data)
    fallbackToPollingRef.current = true
    eventSource.close()
  }
})
```

**Note**: The `onmessage` handler already sets `phase: 'completed'` and clears sessionStorage when it sees `data.state.status === 'completed'` in the data payload. The `done` event handler is a safety net for cases where the `done` event fires but the preceding `data:` event was not received (e.g., the EventSource reconnected mid-stream after the data event but before the done event).

### Change 3 — Unit test for SSE endpoint with completed job

**File**: `tests/test_sse_terminal_event.py` (new file)

```python
"""Tests for E35-S5: SSE Terminal Event for Completed Jobs.

Verifies that the extraction_events SSE generator emits an immediate terminal
event when the job is already completed, and closes the stream without blocking.
"""
import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest


class TestSSETerminalEventCompleted:
    """Verify _sse_generator emits terminal event for already-completed jobs."""

    @pytest.mark.asyncio
    async def test_completed_job_emits_done_immediately(self):
        """A completed job emits data + event: done on the first poll tick."""
        from api.routers.extraction_events import _sse_generator

        progress_row = {
            "status": "completed",
            "state_json": json.dumps({"status": "completed", "total_records": 42}),
            "log_entries": ["Done"],
            "updated_at": "2026-03-05T10:00:00Z",
        }

        with patch(
            "api.routers.extraction_events._get_progress",
            new_callable=AsyncMock,
            return_value=progress_row,
        ):
            chunks = []
            async for chunk in _sse_generator("cmd:completed_job"):
                chunks.append(chunk)

        # Should emit exactly: data event + event:done — then close
        assert len(chunks) == 2
        assert chunks[0].startswith("data: ")
        data_payload = json.loads(chunks[0].removeprefix("data: ").strip())
        assert data_payload["status"] == "completed"

        assert "event: done" in chunks[1]
        done_payload = json.loads(chunks[1].split("data: ", 1)[1].strip())
        assert done_payload["status"] == "completed"

    @pytest.mark.asyncio
    async def test_failed_job_emits_done_immediately(self):
        """A failed job emits data + event: done on the first poll tick."""
        from api.routers.extraction_events import _sse_generator

        progress_row = {
            "status": "failed",
            "state_json": None,
            "log_entries": ["Error: extraction failed"],
            "updated_at": "2026-03-05T10:00:00Z",
        }

        with patch(
            "api.routers.extraction_events._get_progress",
            new_callable=AsyncMock,
            return_value=progress_row,
        ):
            chunks = []
            async for chunk in _sse_generator("cmd:failed_job"):
                chunks.append(chunk)

        assert len(chunks) == 2
        assert "event: done" in chunks[1]
        done_payload = json.loads(chunks[1].split("data: ", 1)[1].strip())
        assert done_payload["status"] == "failed"

    @pytest.mark.asyncio
    async def test_not_found_job_emits_error_after_max_polls(self):
        """When no DB row exists, generator emits error after _MAX_EMPTY_POLLS."""
        from api.routers.extraction_events import _sse_generator

        with patch(
            "api.routers.extraction_events._get_progress",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "api.routers.extraction_events.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            chunks = []
            async for chunk in _sse_generator("cmd:missing_job"):
                chunks.append(chunk)

        # Should emit exactly one error event after _MAX_EMPTY_POLLS ticks
        error_chunks = [c for c in chunks if "event: error" in c]
        assert len(error_chunks) == 1
        err_payload = json.loads(error_chunks[0].split("data: ", 1)[1].strip())
        assert err_payload["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_running_job_does_not_close_stream_early(self):
        """A running job does NOT emit event: done — stream remains open."""
        from api.routers.extraction_events import _sse_generator

        # Simulate 2 running ticks then cancel
        call_count = 0

        async def mock_get_progress(command_id: str):
            nonlocal call_count
            call_count += 1
            if call_count > 2:
                raise asyncio.CancelledError()
            return {
                "status": "running",
                "state_json": json.dumps({"status": "running"}),
                "log_entries": [],
                "updated_at": f"2026-03-05T10:00:0{call_count}Z",
            }

        with patch(
            "api.routers.extraction_events._get_progress",
            side_effect=mock_get_progress,
        ), patch(
            "api.routers.extraction_events.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            chunks = []
            try:
                async for chunk in _sse_generator("cmd:running_job"):
                    chunks.append(chunk)
            except asyncio.CancelledError:
                pass

        # No done events for a running job
        done_chunks = [c for c in chunks if "event: done" in c]
        assert len(done_chunks) == 0
        # But data events were emitted for the running ticks
        data_chunks = [c for c in chunks if c.startswith("data: ")]
        assert len(data_chunks) >= 1
```

---

## File Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `api/routers/extraction_events.py` | MODIFY | Add `_MAX_EMPTY_POLLS = 10` constant; refactor `_sse_generator` to track empty poll count and emit `event: error` + return after 10 consecutive empty polls (fast-fail for stale/missing `command_id`) |
| `frontend/src/lib/hooks/use-extraction-progress.ts` | MODIFY | Add `eventSource.addEventListener('done', ...)` handler that cancels SSE timeout, transitions phase to `'completed'`/`'failed'`, clears sessionStorage, invalidates queries, and closes EventSource; add `eventSource.addEventListener('error', ...)` handler for named server-sent error events |
| `tests/test_sse_terminal_event.py` | CREATE | Unit tests for `_sse_generator`: completed job emits terminal immediately, failed job emits terminal immediately, missing job emits error after max polls, running job does not emit done |

---

## Acceptance Criteria Verification

| AC | Verification Step |
|----|------------------|
| AC1: SSE endpoint returns immediate `{type: complete}` for completed jobs | Run `pytest tests/test_sse_terminal_event.py::TestSSETerminalEventCompleted::test_completed_job_emits_done_immediately`. Confirm 2 chunks emitted, second contains `event: done` with `status: completed`. |
| AC2: Frontend SSE hook closes cleanly after terminal event | Manual: open browser devtools Network tab on `/source/[id]` page for a completed job. Confirm the SSE connection to `/api/acm/extraction-progress/{id}/stream` closes within ~1s (not after 3s timeout). Confirm no `[ExtractionProgress] SSE connection error` console log. |
| AC3: No console errors on completed extraction page | Manual: open browser console on `/source/[id]` for a completed job. Confirm no `EventSource` errors, no `[ExtractionProgress] SSE connection error` messages. Phase should transition to `'completed'` without the 3-second SSE timeout firing. |
| AC4: Unit test for SSE endpoint with completed job | Run `pytest tests/test_sse_terminal_event.py -v`. All 4 tests pass. |

---

## Test Plan

### Backend tests

```bash
uv run pytest tests/test_sse_terminal_event.py -v
uv run ruff check api/routers/extraction_events.py tests/test_sse_terminal_event.py
```

Expected: 4 tests pass, 0 lint errors.

### Frontend lint + build

```bash
cd frontend && npm run lint && npm run build
```

Expected: 0 lint errors, successful build.

### Manual browser verification

1. Start all services: `start-all.bat`
2. Upload a document and complete an extraction (or use a source with an existing completed extraction).
3. Note the `source_id` and the `command_id` stored in sessionStorage (`acm-extraction-progress-{sourceId}`).
4. Hard-reload the `/source/{id}` page.
5. Open DevTools > Network tab, filter by `stream`.
6. Observe: the SSE connection to `extraction-progress/{commandId}/stream` opens, receives 2 events (data + done), and closes within ~1 second.
7. Observe: DevTools > Console shows no `SSE connection error` or `SSE timeout` messages.
8. Observe: The UI transitions to showing the extraction results (not a loading/extracting state).

### Regression check — running job still works

1. Trigger a new extraction on a fresh document.
2. Verify the SSE stream stays open for the duration of the extraction.
3. Verify that the 3-second timeout does NOT fire (no fallback-to-polling log message in console) during a normally running extraction.

---

## Dev Agent Notes

- The `useExtractionProgress` hook uses `fallbackToPollingRef.current` (a mutable ref, not state) to gate the polling path. When the `done` event closes the EventSource cleanly, `fallbackToPollingRef.current` must remain `false` so the React Query polling path (for the `/api/commands/jobs/{id}` endpoint) is not enabled. The `done` handler closes the EventSource and transitions phase directly without setting `fallbackToPollingRef.current = true`.
- The `use-agui-stream.ts` hook (`useAGUIStream`) is a separate EventSource connection to `/api/agui/extraction/{commandId}/stream`. It already handles the `done` named event correctly (line 117-120 in `use-agui-stream.ts`). No changes are needed to that hook.
- The V3 streaming endpoints (`/api/v3/stream/...`) use the in-memory `PipelineEventBus` and are completely separate from the DB-polled legacy SSE endpoints. They are not affected by this story.
- The `_MAX_EMPTY_POLLS = 10` constant (10 seconds) gives sufficient time for a newly submitted job to create its `extraction_progress` row in SurrealDB before the stream gives up. The job submission path writes the DB row within ~1 second of the command starting.
- When adding the `eventSource.addEventListener('error', ...)` handler in the frontend hook, be careful to distinguish it from the native `onerror` callback (`eventSource.onerror`). The native `onerror` fires on network-level errors (when `readyState === CLOSED`). The named `error` event listener fires when the server explicitly sends `event: error\n` (when `readyState === OPEN`). Both need different handling.
