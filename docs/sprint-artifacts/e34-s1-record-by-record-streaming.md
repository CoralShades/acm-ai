# E34-S1: Record-by-Record Streaming — Tech Spec

## Overview

This story wires the existing V3 SSE infrastructure (E31-S7) into the Building Register UI (E33-S2) to deliver real-time incremental updates: building status badges animate through Extracting → Validating → Complete as each building finishes, and the AG Grid gains records building-by-building without a full-page reload. It also adds a progress bar with estimated time remaining.

The backend work is minimal — the `PipelineEventBus` and SSE endpoints already exist. The main work is:
1. Emit `ai.building_extracted` and `ai.items_extracted` events from the orchestrator (missing wire-up).
2. Consume those events in `BuildingSidebar` to update per-building status badges in real time.
3. Trigger React Query invalidation for a specific building's items query when its extraction completes.
4. Add progress percentage + ETA to the top bar of `/source/[id]`.

---

## Background / Context

### What Already Exists

| Component | Location | Status |
|-----------|----------|--------|
| `PipelineEventBus` | `open_notebook/extractors/pipeline_event_bus.py` | Done (E31-S7) |
| SSE endpoints | `api/routers/acm.py` | Done (E31-S7) |
| `useV3SSE` hook | `frontend/src/lib/hooks/useV3SSE.ts` | Done (E31-S7) |
| `useStreamingStore` (Zustand) | `frontend/src/lib/stores/streamingStore.ts` | Done (E31-S7) |
| `BuildingSidebar` | `frontend/src/components/acm/BuildingSidebar.tsx` | Done (E33-S2), no streaming |
| `ItemGrid` | `frontend/src/components/acm/ItemGrid.tsx` | Done (E33-S2), no streaming |
| `/source/[id]` page | `frontend/src/app/(dashboard)/source/[id]/page.tsx` | Done (E33-S2) |
| `useBuildings` | `frontend/src/lib/hooks/useBuildings.ts` | Done (E33-S2) |
| `useACMItems` | `frontend/src/lib/hooks/useACMItems.ts` | Done (E33-S2) |

### Critical Gap: Events Are Not Being Published

`PipelineEventBus.publish()` is **not called anywhere** in the orchestrator or command handlers. The bus infrastructure is complete but producers have never been wired up. This story must add the `publish()` calls in the extraction orchestrator.

### Relevant Event Types (already defined in pipeline_event_bus.py)

- `ai.building_extracted` — data: `{ building_id, building_name, records_extracted, model_used, duration_ms }`
- `ai.items_extracted` — data: `{ building_id, items_count, items_rejected }`
- `ai.validation_complete` — terminal event, data: `{ records_valid, records_corrected, records_rejected, validation_duration_ms }`

### How `operation_id` Maps to the UI

The `operation_id` in pipeline events maps to `command_id`. On the `/source/[id]` page, the command_id is retrievable from `sessionStorage` under key `acm-extraction-progress-{sourceId}` (same key used by `useExtractionSSE` in E33-S1). The `/source/[id]` page must read this to know which SSE stream to subscribe to.

### Key Query Keys

```typescript
// useBuildings
['buildings', 'v3', sourceId]

// useACMItems per building
['acm', 'items', sourceId, buildingId]
```

---

## Implementation Plan

### Backend Changes

#### 1. Wire `publish()` calls in the orchestrator

File: `open_notebook/extractors/orchestrator.py`

The orchestrator processes buildings sequentially. After each building's extraction completes, publish `ai.building_extracted`. After item-level extraction resolves, publish `ai.items_extracted`. After the final validation pass, publish `ai.validation_complete`.

Add an optional `operation_id: str | None = None` parameter to the main orchestrator entry point. Inside the per-building loop, after a building result is assembled:

```python
from open_notebook.extractors.pipeline_event_bus import get_event_bus

if operation_id:
    bus = get_event_bus()
    await bus.publish({
        "type": "ai.building_extracted",
        "operation_id": operation_id,
        "data": {
            "building_id": building_id,
            "building_name": building_name,
            "records_extracted": len(records),
            "model_used": model_used or "unknown",
            "duration_ms": duration_ms,
        }
    })
```

Similarly for `ai.items_extracted` after items are stored, and `ai.validation_complete` after validation.

#### 2. Thread `operation_id` from the command handler

File: `commands/acm_commands.py`

Pass `operation_id=command_id` when calling the orchestrator entry point. This is a one-line change.

### Frontend Changes

#### 3. Add per-building streaming status to `buildingStore`

File: `frontend/src/lib/stores/buildingStore.ts`

Add a `buildingStatus` map to track real-time extraction status per building:

```typescript
export type BuildingStreamStatus = 'extracting' | 'validating' | 'complete' | 'error'

// Add to store state:
buildingStatus: Map<string, BuildingStreamStatus>
setBuildingStatus: (buildingId: string, status: BuildingStreamStatus) => void
clearBuildingStatuses: () => void
```

Use `internal_id` (e.g. `BLD#ABC_001`) as the key — this is what SSE events carry.

#### 4. Create `useV3BuildingStream` hook

File: `frontend/src/lib/hooks/useV3BuildingStream.ts` (new file)

Wraps `useV3SSE` with building-specific event handling:

```typescript
interface UseV3BuildingStreamOptions {
  sourceId: string
  operationId: string | null
  totalBuildings: number
}

export function useV3BuildingStream(options: UseV3BuildingStreamOptions): {
  isStreaming: boolean
  completedCount: number
  estimatedSecondsRemaining: number | null
}
```

Event handling:
- `ai.building_extracted`: set `buildingStatus(event.data.building_id, 'extracting')`, increment completed count, invalidate `['acm', 'items', sourceId]` (broad — Option A for simplicity)
- `ai.items_extracted`: set `buildingStatus(event.data.building_id, 'validating')`
- `ai.validation_complete`: call `clearBuildingStatuses()`, invalidate `['buildings', 'v3', sourceId]`

ETA: rolling average of `duration_ms` values × remaining buildings.

#### 5. Modify `BuildingSidebar` for streaming status badges

File: `frontend/src/components/acm/BuildingSidebar.tsx`

- Read `buildingStatus` from `useBuildingStore`
- When a building has a streaming status, replace the static validation badge with a streaming badge:

| Status | Label | Style |
|--------|-------|-------|
| `extracting` | Extracting... | blue |
| `validating` | Validating... | yellow |
| `complete` | Complete | green |
| `error` | Error | red |

- Fall back to existing `deriveValidationStatus` badge when no streaming status.

#### 6. Modify `/source/[id]` page for progress bar

File: `frontend/src/app/(dashboard)/source/[id]/page.tsx`

- Read `commandId` from `sessionStorage` on mount (key: `acm-extraction-progress-{sourceId}`)
- Call `useV3BuildingStream({ sourceId, operationId: commandId, totalBuildings: buildings.length })`
- Render progress bar when `isStreaming`:

```tsx
{isStreaming && (
  <div className="w-full px-4 py-1 bg-muted/50 border-b shrink-0">
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full bg-primary transition-all duration-500"
          style={{ width: `${Math.round((completedCount / buildings.length) * 100)}%` }}
        />
      </div>
      <span className="text-xs text-muted-foreground shrink-0">
        {completedCount}/{buildings.length} buildings
        {estimatedSecondsRemaining !== null && ` · ~${estimatedSecondsRemaining}s remaining`}
      </span>
    </div>
  </div>
)}
```

---

## File Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `open_notebook/extractors/orchestrator.py` | modify | Add `operation_id` param; publish `ai.building_extracted`, `ai.items_extracted`, `ai.validation_complete` events |
| `commands/acm_commands.py` | modify | Pass `operation_id=command_id` to orchestrator entry point |
| `frontend/src/lib/stores/buildingStore.ts` | modify | Add `buildingStatus` map, `setBuildingStatus`, `clearBuildingStatuses`; export `BuildingStreamStatus` type |
| `frontend/src/lib/hooks/useV3BuildingStream.ts` | create | New hook: wraps `useV3SSE`, handles building events, tracks progress + ETA |
| `frontend/src/components/acm/BuildingSidebar.tsx` | modify | Read `buildingStatus` from store; render streaming badge when active |
| `frontend/src/app/(dashboard)/source/[id]/page.tsx` | modify | Read commandId from sessionStorage; call `useV3BuildingStream`; render progress bar |

---

## Acceptance Criteria Mapping

| AC | Implementation |
|----|----------------|
| AC1: Records appear incrementally | `useV3BuildingStream` invalidates `['acm', 'items', sourceId]` on each `ai.building_extracted`; `ItemGrid` refetches and renders new records |
| AC2: Sidebar status updates in real-time | `BuildingSidebar` reads `buildingStatus`; streaming badge cycles Extracting → Validating → Complete |
| AC3: SSE events trigger React Query refetch | `handleEvent` calls `queryClient.invalidateQueries` on `ai.building_extracted` and `ai.validation_complete` |
| AC4: Officers can edit while others process | No blocking — each building's `ItemGrid` is independently queryable; `RecordWizard` always enabled |
| AC5: Progress percentage | `completedCount / totalBuildings`; rendered in progress bar on `/source/[id]` |
| AC6: ETA | Rolling avg of `duration_ms` from `ai.building_extracted` events × remaining buildings |

---

## Test Plan

### Backend

1. **Unit test — orchestrator publishes events**: Mock `get_event_bus()`, run orchestrator with `operation_id="test-op"`. Assert `ai.building_extracted` published with correct fields and `ai.validation_complete` published at end.
2. **Thread operation_id**: Unit test that `acm_commands.py` passes `operation_id=command_id` to orchestrator.
3. **No regression**: Existing extraction tests still pass.

### Frontend

1. **`buildingStore` new actions**: Test `setBuildingStatus`, `clearBuildingStatuses`. Verify Map immutability.
2. **`useV3BuildingStream` hook**: Mock `useV3SSE` firing event sequence. Assert `completedCount` increments, `buildingStatus` entries set, `queryClient.invalidateQueries` called.
3. **`BuildingSidebar` streaming badge**: Render with mock `buildingStatus`. Assert streaming badge shown instead of static badge.
4. **Build passes**: `cd frontend && npm run build` — no TypeScript errors.

---

## Notes / Risks

- **Risk 1 (LOW)**: Orchestrator must be async for `await bus.publish()`. FastAPI/LangGraph context is already async — not an issue.
- **Risk 2 (LOW)**: building_id mismatch (internal_id vs SurrealDB id) — resolved by broad query invalidation (Option A).
- **Risk 3 (LOW)**: commandId availability — if user navigates directly to `/source/:id` without wizard session, streaming is disabled gracefully; page works normally.
- **Risk 4 (LOW)**: No late-subscriber replay on event bus — already-completed buildings show static validation badges (acceptable for 2 SP).
