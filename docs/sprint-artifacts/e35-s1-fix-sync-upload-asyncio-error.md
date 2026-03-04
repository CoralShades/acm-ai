# E35-S1: Fix Sync Upload asyncio.run() Error

## Summary

The sync upload path in `POST /api/sources` calls `execute_command_sync()` from the
`surreal-commands` library, which internally uses `asyncio.run()`. Since FastAPI endpoints
are `async def`, they already run inside an event loop — calling `asyncio.run()` raises
`RuntimeError: asyncio.run() cannot be called from a running event loop`.

## Root Cause

`execute_command_sync` (surreal_commands/core/client.py:170) →
`wait_for_command_sync` → `asyncio.run(wait_for_command(...))`.

The async FastAPI endpoint already has a running event loop, so `asyncio.run()` fails.

## Fix

Replace `execute_command_sync()` with the async equivalents that already exist:
- `submit_command()` (sync — just writes to DB, no event loop needed)
- `await wait_for_command()` (async — polls DB, uses `asyncio.sleep`)

## File Changes

| File | Change |
|------|--------|
| `api/routers/sources.py` | Replace `execute_command_sync` with `submit_command` + `await wait_for_command` |
| `tests/test_sync_upload.py` | New: unit tests for both sync and async paths |

## Acceptance Criteria Mapping

- **AC1**: `await wait_for_command()` instead of `asyncio.run()` — no RuntimeError
- **AC2**: POST /api/sources with async_processing=false returns 200
- **AC3**: Async upload path unchanged (no modifications to that branch)
- **AC4**: Unit test covers both sync and async paths
