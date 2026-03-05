# Bug: PUT /api/models/defaults Doesn't Persist to SurrealDB

> **GitHub Issue**: #92
> **Discovered**: 2026-03-05 (E30-S8 verification)
> **Story**: E35-S2 (Sprint V3-8)
> **Priority**: P1
> **Status**: Open

## Problem

`PUT /api/models/defaults` stores model defaults in-memory only. After API restart, defaults revert to hardcoded values.

## Root Cause

The models router stores default model configuration in a module-level Python dict. No SurrealDB persistence layer exists for settings/preferences.

## Impact

- Users must re-set default extraction model after every API restart
- During E30-S8 verification, the default was an OpenRouter model with no credits (402 error), but the user-set Ollama model was lost on restart

## Fix

1. Create a `settings` SurrealDB table (via migration)
2. `PUT /api/models/defaults` writes to SurrealDB
3. `GET /api/models/defaults` reads from SurrealDB, falls back to in-memory defaults

## Key Files

| File | Change |
|------|--------|
| `api/routers/models.py` | Persist to/read from SurrealDB |
| `open_notebook/database/repository.py` | Add settings CRUD |
| `migrations/` | New migration for settings table |

## Acceptance Criteria

1. PUT /api/models/defaults writes to SurrealDB `settings` record
2. GET /api/models/defaults reads from SurrealDB, falls back to in-memory
3. Defaults survive API restart
4. Migration creates settings table
5. Unit test verifies persistence
