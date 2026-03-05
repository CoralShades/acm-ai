# Bug: Sync Upload Returns 500 — asyncio.run() in Event Loop

> **GitHub Issue**: #91
> **Discovered**: 2026-03-05 (E30-S8 verification)
> **Story**: E35-S1 (Sprint V3-8)
> **Priority**: P1
> **Status**: Open

## Problem

`POST /api/sources` with `async_processing=false` raises:

```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

## Root Cause

`commands/source_commands.py` uses `asyncio.run()` for synchronous processing, but FastAPI's request handler already runs inside an async event loop. `asyncio.run()` tries to create a new event loop, which fails when one is already running.

## Impact

- Sync upload path completely broken (500 error)
- Async upload path works fine (uses background worker)
- Affects users who need immediate processing without waiting for worker queue

## Fix

Replace `asyncio.run(process_source(...))` with `await process_source(...)` in the sync upload path.

## Key Files

| File | Change |
|------|--------|
| `commands/source_commands.py` | Replace `asyncio.run()` with `await` |
| `api/routers/sources.py` | Ensure sync endpoint is `async def` |

## Acceptance Criteria

1. Sync upload path uses `await` instead of `asyncio.run()` — no RuntimeError
2. `POST /api/sources` with `async_processing=false` returns 200
3. Async upload path unchanged
4. Unit test covers both sync and async paths
