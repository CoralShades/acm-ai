# E31-S7 Tech Spec: PipelineEventBus + SSE Infrastructure

**Story ID**: E31-S7
**Epic**: E31 — Dual-Provider Extraction Pipeline
**Sprint**: V3-4
**Story Points**: 3
**Risk**: MEDIUM
**Type**: Full-stack (Backend + Frontend)
**Dependencies**: E31-S5 (done — dual-provider sequential extraction with page-level consensus)
**Author**: SM / Tech Lead
**Date**: 2026-03-04

---

## 1. Overview

This story introduces an in-process **PipelineEventBus** (asyncio.Queue-based pub/sub) and a new **V3 SSE router** that streams real-time pipeline events to the frontend without polling SurrealDB. It also adds a **Zustand V3StreamingState store** and a **useV3SSE hook** with auto-reconnect.

The implementation extends — and does not replace — the existing E27 SSE infrastructure (`extraction_events.py`, `agui_extraction.py`). Both legacy endpoints remain fully operational. The V3 event bus is an in-process transport layer for lower-latency real-time feedback during dual-provider extractions (E31-S5 consensus runs, building-level AI processing, bulk batch operations).

---

## 2. Background / Context

### Existing SSE Infrastructure (E27, must not break)

| File | Endpoint | Transport |
|------|----------|-----------|
| `api/routers/extraction_events.py` | `GET /api/acm/extraction-progress/{id}/stream` | DB poll (1 s interval) |
| `api/routers/agui_extraction.py` | `GET /api/agui/extraction/{id}/stream` | DB poll (0.5 s interval) |
| `frontend/src/lib/hooks/use-extraction-progress.ts` | Consumes first endpoint | EventSource + polling fallback |

### What E31-S5 Introduced

E31-S5 added sequential dual-provider extraction (`docling` → `mineru`) with page-level consensus. It produces structured intermediate results (provider-level completions, consensus deltas) that are not yet surfaced in real time. The existing DB-poll SSE endpoints only report overall pipeline state snapshots, not the finer-grained provider-complete and consensus-complete milestones.

### Why a New Event Bus

- DB polling at 0.5–1 s adds unnecessary latency for in-process events that are available immediately.
- The `agui_events` SurrealDB table is scoped to AG-UI protocol events; V3 events have a different schema and different consumer targets.
- An asyncio.Queue-based in-memory bus can dispatch events in microseconds with zero DB round-trips.
- The bus is scoped per `operation_id`, which maps to `command_id` for extractions and a generated UUID for bulk batch operations.

---

## 3. Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC1 | `PipelineEventBus` exists in `open_notebook/extractors/pipeline_event_bus.py` as an asyncio.Queue-based singleton with `publish(event)` and `subscribe(operation_id)` that returns an AsyncGenerator. |
| AC2 | Three SSE endpoint categories registered under `/api/v3/stream/`: extraction pipeline, AI processing, and bulk operations. |
| AC3 | The following V3 event types are defined and serializable: `extraction.started`, `extraction.provider_complete`, `extraction.consensus_complete`, `ai.building_extracted`, `ai.items_extracted`, `ai.validation_complete`, `bulk.progress`, `bulk.complete`. |
| AC4 | `frontend/src/lib/stores/streamingStore.ts` exports a Zustand store with `V3StreamingState` shape containing `activeStreams: Map<string, StreamState>` and `isConnected: boolean`. |
| AC5 | `useV3SSE` hook fires `queryClient.invalidateQueries` on terminal events (`extraction.consensus_complete`, `ai.validation_complete`, `bulk.complete`). |
| AC6 | `useV3SSE` implements exponential-backoff auto-reconnect (max 5 retries, starting at 1 s, capped at 30 s). |
| AC7 | SSE endpoints accept `?operation_id=X` query param for event filtering; the endpoint path already encodes `operation_id` so query param acts as an additional assertion/filter for shared-stream scenarios. |
| AC8 | All existing E27 SSE endpoints remain unmodified and pass their existing tests. |
| AC9 | `tests/test_pipeline_event_bus.py` provides unit tests for pub/sub mechanics and SSE event serialization. |

---

## 4. File Changes

| File | Action | Description |
|------|--------|-------------|
| `open_notebook/extractors/pipeline_event_bus.py` | CREATE | asyncio.Queue singleton event bus — V3PipelineEvent models, publish/subscribe interface |
| `api/routers/v3_streaming.py` | CREATE | FastAPI router with 3 SSE endpoint categories under `/v3/stream/` prefix |
| `api/main.py` | MODIFY | Register `v3_streaming` router with prefix `/api` and tag `v3-streaming` |
| `frontend/src/lib/stores/streamingStore.ts` | CREATE | Zustand V3StreamingState store — activeStreams Map, isConnected flag, actions |
| `frontend/src/lib/hooks/useV3SSE.ts` | CREATE | SSE subscription hook with auto-reconnect, React Query invalidation on terminal events |
| `tests/test_pipeline_event_bus.py` | CREATE | Unit tests for pub/sub, event filtering, SSE serialization, multiple subscribers |

---

## 5. Implementation Details

### 5.1 `open_notebook/extractors/pipeline_event_bus.py`

#### Responsibility

Singleton in-memory pub/sub bus. Producers (extraction nodes, consensus engine, bulk command handler) call `await bus.publish(event)`. Consumers (SSE generators in `v3_streaming.py`) call `bus.subscribe(operation_id)` which yields events as an AsyncGenerator until a terminal event or timeout.

#### Key Design Decisions

- **Singleton**: A module-level `_bus` instance created at import time. Import the singleton via `from open_notebook.extractors.pipeline_event_bus import get_event_bus`.
- **Per-subscriber queues**: Each call to `subscribe()` creates a new `asyncio.Queue`. The bus holds `Dict[str, List[asyncio.Queue]]` keyed by `operation_id`. On `publish()`, the event is put into every queue registered for that `operation_id`.
- **No persistence**: Events are not stored. Late subscribers miss past events. This is by design — the event bus is for real-time display only. Authoritative state is still in SurrealDB.
- **Timeout / cleanup**: `subscribe()` accepts a `timeout_seconds` parameter (default 300). If no event arrives within that window the generator raises `asyncio.TimeoutError` and the SSE generator sends a heartbeat or terminates gracefully. On subscriber cleanup (generator close), its queue is removed from the registry.
- **Thread safety**: All asyncio.Queue operations happen inside the async event loop. The singleton is not process-shared (each API worker process has its own bus). This is acceptable for the current single-worker deployment model.

#### Pydantic Event Models

All V3 events share a base envelope:

```python
class V3PipelineEvent(BaseModel):
    type: str                  # e.g. "extraction.started"
    operation_id: str          # command_id or bulk batch UUID
    timestamp: str             # ISO 8601 UTC — use now_iso() from pipeline_events.py
    data: Dict[str, Any]       # event-specific payload (see AC3 schema in section 6)
```

Typed subclasses are defined for each event type (AC3) using a `Literal` discriminator on `type`. The `data` dict is typed via a separate `*Data` Pydantic model for each variant. Both the envelope and the data model are exported so tests and SSE generators can import them directly.

#### Singleton accessor

```python
_bus: Optional["PipelineEventBus"] = None

def get_event_bus() -> "PipelineEventBus":
    global _bus
    if _bus is None:
        _bus = PipelineEventBus()
    return _bus
```

#### `subscribe` signature

```python
async def subscribe(
    self,
    operation_id: str,
    timeout_seconds: float = 300.0,
) -> AsyncGenerator[V3PipelineEvent, None]:
    ...
```

The generator cleans up its queue on normal exit, `GeneratorExit`, and `asyncio.TimeoutError`.

#### `publish` signature

```python
async def publish(self, event: V3PipelineEvent) -> int:
    """Dispatch event to all subscribers for the event's operation_id.
    Returns the number of subscriber queues the event was delivered to."""
```

---

### 5.2 `api/routers/v3_streaming.py`

#### Responsibility

FastAPI router that exposes three SSE endpoint categories. Each endpoint instantiates a subscriber on the `PipelineEventBus` and streams events as `text/event-stream`.

#### SSE Wire Format

Each event is serialized as:

```
event: extraction.provider_complete
data: {"type":"extraction.provider_complete","operation_id":"cmd:abc123","timestamp":"2026-03-04T10:00:00Z","data":{...}}

```

(Named event + data line + blank line separator per SSE spec.)

Terminal events additionally send:

```
event: done
data: {"operation_id":"cmd:abc123","final_type":"extraction.consensus_complete"}

```

Then the generator returns, closing the stream.

#### Heartbeat

Every 15 seconds with no events, emit:

```
: heartbeat

```

(SSE comment — ignored by EventSource but keeps the TCP connection alive through proxies.)

#### Response headers (all three endpoints)

```python
{
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}
```

#### Endpoints

```
GET /api/v3/stream/extraction/{operation_id}
GET /api/v3/stream/ai/{operation_id}
GET /api/v3/stream/bulk/{operation_id}
```

All three share the same generator logic (pull from event bus, filter by category prefix, serialize). They differ only in which event type prefixes they forward:

| Endpoint | Forwarded prefixes |
|----------|--------------------|
| `/extraction/{operation_id}` | `extraction.*` |
| `/ai/{operation_id}` | `ai.*` |
| `/bulk/{operation_id}` | `bulk.*` |

The `operation_id` path parameter is used as the subscription key. The optional `?operation_id=X` query parameter (AC7), if provided, must match the path parameter; if it does not match the request returns HTTP 400.

#### Terminal event detection

```python
_TERMINAL_EVENT_TYPES = {
    "extraction.consensus_complete",
    "ai.validation_complete",
    "bulk.complete",
}
```

When a terminal event is yielded, the generator emits the `done` sentinel and returns.

#### Error handling

If the event bus raises an exception or the generator times out, yield an `error` SSE event with a human-readable message and return. Never propagate exceptions to FastAPI's response layer (which would corrupt the SSE stream).

---

### 5.3 `api/main.py` (modification)

Add to the imports block (alongside `agui_extraction`):

```python
from api.routers import v3_streaming
```

Add to the router registration block (after `source_bulk.router`):

```python
app.include_router(v3_streaming.router, prefix="/api", tags=["v3-streaming"])
```

The router internally sets its prefix to `/v3/stream` so the full paths become `/api/v3/stream/...`.

---

### 5.4 `frontend/src/lib/stores/streamingStore.ts`

#### Zustand pattern

Uses `create` from `zustand` v5 (no default export, consistent with `buildingStore.ts`).

#### State shape

```typescript
interface StreamState {
  operationId: string
  category: 'extraction' | 'ai' | 'bulk'
  status: 'connecting' | 'connected' | 'reconnecting' | 'done' | 'error'
  lastEventType: string | null
  lastEventTimestamp: string | null
  retryCount: number
  eventCount: number
}

interface V3StreamingState {
  activeStreams: Map<string, StreamState>
  isConnected: boolean   // true if any stream is in 'connected' state

  // Actions
  registerStream: (operationId: string, category: StreamState['category']) => void
  updateStream: (operationId: string, patch: Partial<StreamState>) => void
  removeStream: (operationId: string) => void
  clearAll: () => void
}
```

#### Notes

- `Map` is used over a plain object for O(1) keyed access. Zustand handles Map mutations correctly when using `set()` with a new Map reference (spread pattern: `new Map(state.activeStreams).set(key, val)`).
- `isConnected` is a derived value recalculated inside `updateStream` by checking whether any entry has `status === 'connected'`.
- The store is not persisted to localStorage (stream state is ephemeral).

---

### 5.5 `frontend/src/lib/hooks/useV3SSE.ts`

#### Purpose

Encapsulates EventSource lifecycle, auto-reconnect, Zustand store updates, and React Query invalidation for a single V3 SSE stream.

#### Signature

```typescript
interface UseV3SSEOptions {
  operationId: string
  category: 'extraction' | 'ai' | 'bulk'
  enabled?: boolean          // default true — set false to skip connecting
  onEvent?: (event: V3EventEnvelope) => void  // optional raw event callback
  invalidateQueryKeys?: unknown[][]  // React Query keys to invalidate on terminal events
}

function useV3SSE(options: UseV3SSEOptions): {
  status: StreamState['status']
  lastEventType: string | null
  eventCount: number
  disconnect: () => void
}
```

#### Connection URL

```typescript
const url = `/api/v3/stream/${options.category}/${options.operationId}`
```

(Proxied by Next.js `/api/*` rewrite to FastAPI port 5055.)

#### Auto-reconnect logic

```
Retry 1: wait 1s
Retry 2: wait 2s
Retry 3: wait 4s
Retry 4: wait 8s
Retry 5: wait 16s (capped at 30s)
After 5 retries: set status = 'error', stop reconnecting
```

The reconnect timer is managed with `setTimeout` inside `onerror`. The current `EventSource` is closed before creating a new one. The retry counter resets to 0 on a successful connection (first message received).

#### React Query invalidation

On terminal events (`extraction.consensus_complete`, `ai.validation_complete`, `bulk.complete`), call:

```typescript
for (const queryKey of options.invalidateQueryKeys ?? []) {
  queryClient.invalidateQueries({ queryKey })
}
```

This allows the calling component to declare which React Query caches should be refreshed when the operation finishes (e.g., ACM records list, building stats).

#### Cleanup

The `useEffect` cleanup function closes the EventSource and cancels any pending reconnect timer. It also calls `streamingStore.removeStream(operationId)`.

#### TypeScript types

Define a `V3EventEnvelope` interface in `frontend/src/lib/types/v3-streaming.ts` (new file, minimal surface):

```typescript
export interface V3EventEnvelope {
  type: string
  operation_id: string
  timestamp: string
  data: Record<string, unknown>
}

export type V3EventCategory = 'extraction' | 'ai' | 'bulk'
```

Import this in both `streamingStore.ts` and `useV3SSE.ts`.

---

### 5.6 `tests/test_pipeline_event_bus.py`

Unit tests use `pytest-asyncio` (already in dev dependencies). All tests are `async def` with `@pytest.mark.asyncio`.

Test coverage targets are detailed in the Test Plan (section 7).

---

## 6. API Schema

### 6.1 V3 Event Types (AC3)

#### `extraction.started`

Emitted when a dual-provider extraction begins.

```json
{
  "type": "extraction.started",
  "operation_id": "cmd:abc123",
  "timestamp": "2026-03-04T10:00:00.000000+00:00",
  "data": {
    "source_id": "source:xyz",
    "provider_sequence": ["docling", "mineru"],
    "total_pages": 42
  }
}
```

#### `extraction.provider_complete`

Emitted when one provider finishes its extraction pass.

```json
{
  "type": "extraction.provider_complete",
  "operation_id": "cmd:abc123",
  "timestamp": "2026-03-04T10:00:15.000000+00:00",
  "data": {
    "provider": "docling",
    "records_extracted": 87,
    "duration_ms": 14823,
    "pages_processed": 42
  }
}
```

#### `extraction.consensus_complete` (terminal for extraction category)

Emitted when consensus merging finishes.

```json
{
  "type": "extraction.consensus_complete",
  "operation_id": "cmd:abc123",
  "timestamp": "2026-03-04T10:00:28.000000+00:00",
  "data": {
    "records_final": 91,
    "records_docling_only": 3,
    "records_mineru_only": 7,
    "records_agreed": 81,
    "consensus_duration_ms": 420
  }
}
```

#### `ai.building_extracted`

Emitted when the LLM extraction pass completes for one building block.

```json
{
  "type": "ai.building_extracted",
  "operation_id": "cmd:abc123",
  "timestamp": "2026-03-04T10:00:20.000000+00:00",
  "data": {
    "building_id": "BLD-01",
    "building_name": "Main Building",
    "records_extracted": 12,
    "model_used": "openai/gpt-4o",
    "duration_ms": 3210
  }
}
```

#### `ai.items_extracted`

Emitted when item-level extraction completes for a building section.

```json
{
  "type": "ai.items_extracted",
  "operation_id": "cmd:abc123",
  "timestamp": "2026-03-04T10:00:21.000000+00:00",
  "data": {
    "building_id": "BLD-01",
    "items_count": 12,
    "items_rejected": 1
  }
}
```

#### `ai.validation_complete` (terminal for ai category)

Emitted when the final validation pass finishes.

```json
{
  "type": "ai.validation_complete",
  "operation_id": "cmd:abc123",
  "timestamp": "2026-03-04T10:00:35.000000+00:00",
  "data": {
    "records_valid": 90,
    "records_corrected": 4,
    "records_rejected": 1,
    "validation_duration_ms": 810
  }
}
```

#### `bulk.progress`

Emitted periodically during bulk batch operations (e.g., bulk re-extraction).

```json
{
  "type": "bulk.progress",
  "operation_id": "bulk:batch-20260304-001",
  "timestamp": "2026-03-04T10:01:00.000000+00:00",
  "data": {
    "total": 15,
    "completed": 7,
    "failed": 0,
    "percent": 46.7
  }
}
```

#### `bulk.complete` (terminal for bulk category)

```json
{
  "type": "bulk.complete",
  "operation_id": "bulk:batch-20260304-001",
  "timestamp": "2026-03-04T10:03:45.000000+00:00",
  "data": {
    "total": 15,
    "completed": 14,
    "failed": 1,
    "duration_ms": 164000
  }
}
```

### 6.2 SSE Wire Format (named event + data)

```
event: extraction.provider_complete
data: {"type":"extraction.provider_complete","operation_id":"cmd:abc123","timestamp":"2026-03-04T10:00:15.000000+00:00","data":{"provider":"docling","records_extracted":87,"duration_ms":14823,"pages_processed":42}}

event: done
data: {"operation_id":"cmd:abc123","final_type":"extraction.consensus_complete"}

```

### 6.3 Heartbeat Format

```
: heartbeat

```

### 6.4 Error Event Format

```
event: error
data: {"message":"Event bus subscription timed out after 300s","operation_id":"cmd:abc123"}

```

---

## 7. Test Plan

### AC1 — PipelineEventBus pub/sub

| Test | Description |
|------|-------------|
| `test_publish_delivers_to_subscriber` | Publish one event; assert subscriber generator yields it. |
| `test_publish_delivers_to_multiple_subscribers` | Two subscribers for same operation_id both receive event. |
| `test_subscriber_filters_by_operation_id` | Publish event for op-A; subscriber on op-B receives nothing. |
| `test_subscriber_cleanup_on_close` | Close generator early; assert queue removed from registry. |
| `test_bus_singleton` | `get_event_bus()` returns same instance across two calls. |
| `test_publish_returns_subscriber_count` | `publish()` returns 2 when 2 subscribers are registered. |

### AC2/AC3 — Event types and SSE serialization

| Test | Description |
|------|-------------|
| `test_v3_event_serialization_extraction_started` | Create `V3PipelineEvent` with type `extraction.started`, call `.model_dump_json()`, assert JSON round-trips cleanly. |
| `test_v3_event_all_types_schema_valid` | Parameterized test over all 8 event types; assert Pydantic validation succeeds with minimal required fields. |
| `test_sse_format_named_event` | Given a `V3PipelineEvent`, assert the SSE serializer produces `event: <type>\ndata: <json>\n\n`. |
| `test_sse_terminal_event_sends_done_sentinel` | Assert consensus_complete, validation_complete, bulk.complete each produce a trailing `event: done\n...` line. |

### AC7 — Event filtering

| Test | Description |
|------|-------------|
| `test_extraction_endpoint_filters_ai_events` | Publish `ai.building_extracted` to bus; extraction endpoint generator does not yield it. |
| `test_bulk_endpoint_filters_extraction_events` | Publish `extraction.started`; bulk endpoint generator does not yield it. |

### AC8 — Non-breaking

| Test | Description |
|------|-------------|
| `test_existing_extraction_events_router_unmodified` | Import `extraction_events.router` and assert `len(router.routes) == 3` (existing 3 routes unchanged). |
| `test_existing_agui_extraction_router_unmodified` | Import `agui_extraction.router` and assert `len(router.routes) == 1` (existing 1 route unchanged). |

### AC9 — Full unit test coverage

All tests above are collected in `tests/test_pipeline_event_bus.py`. They must pass with:

```bash
uv run pytest tests/test_pipeline_event_bus.py -v
```

No running SurrealDB instance required (event bus is fully in-memory).

---

## 8. Definition of Done

- [ ] `open_notebook/extractors/pipeline_event_bus.py` exists, passes all unit tests.
- [ ] `api/routers/v3_streaming.py` exists with 3 SSE endpoint categories.
- [ ] `api/main.py` registers `v3_streaming.router`.
- [ ] `frontend/src/lib/stores/streamingStore.ts` exists with `V3StreamingState` Zustand store.
- [ ] `frontend/src/lib/hooks/useV3SSE.ts` exists with auto-reconnect (max 5 retries, exponential backoff).
- [ ] `frontend/src/lib/types/v3-streaming.ts` exists with `V3EventEnvelope` and `V3EventCategory` types.
- [ ] `tests/test_pipeline_event_bus.py` exists; all tests pass (`uv run pytest tests/test_pipeline_event_bus.py -v`).
- [ ] Backend lint passes: `uv run ruff check . --fix && uv run ruff format .`
- [ ] Frontend build passes: `cd frontend && npm run build`
- [ ] Existing E27 SSE tests remain green (no regressions).
- [ ] All 8 V3 event types defined in section 6.1 are implemented as Pydantic models.
- [ ] Sprint status YAML updated: E31-S7 status `done`.

---

## 9. Out of Scope (for this story)

- Wiring `publish()` calls into the actual orchestrator / consensus engine nodes — that is a follow-on integration story (E31-S8 or similar). The event bus and endpoints are infrastructure; producers are plumbed in separately.
- Persisting V3 events to SurrealDB for replay — events are ephemeral. SurrealDB persistence for audit is handled by the existing `extraction_progress` / `agui_events` tables.
- Frontend UI components that consume `useV3SSE` — components will be built as part of the stories that need real-time display (E33-S3 and beyond).
- Replacing `useExtractionProgress` hook — it remains in place for legacy consumers.
