# E35-S2: Persist Model Defaults to SurrealDB

## Story
**ID**: E35-S2
**Epic**: E35
**Sprint**: V3-8
**Points**: 2 SP
**Risk**: LOW
**Type**: backend

## Summary

Model defaults already persist to SurrealDB via `DefaultModels(RecordModel)` and `repo_upsert`, but `update_defaults_if_needed()` in `api/model_provisioning.py` overwrites user-customized defaults on every API restart. Fix the startup provisioning to only fill empty fields, add schema migration, and write tests.

## Acceptance Criteria

- AC1: PUT /api/models/defaults writes to SurrealDB settings record (**already works**)
- AC2: GET /api/models/defaults reads from SurrealDB, falls back to in-memory (**already works**)
- AC3: Defaults survive API restart (**bug fix needed** — provisioning overwrites user choices)
- AC4: Migration creates settings table (**add DEFINE FIELD declarations**)
- AC5: Unit test verifies persistence

## Root Cause Analysis

In `api/model_provisioning.py:update_defaults_if_needed()` (line 386-415):

```python
current_value = getattr(defaults, field, None)
if current_value == model_id:
    continue
# This OVERWRITES user-customized defaults!
setattr(defaults, field, model_id)
```

If user sets `default_chat_model = "model:xyz"` via PUT, and env says `ollama/qwen3:latest` resolving to `model:abc`, the provisioner sees `xyz != abc` and **overwrites** the user's choice.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `api/model_provisioning.py` | MODIFY | Fix `update_defaults_if_needed()` to only set None/empty fields |
| `migrations/45.surrealql` | CREATE | DEFINE FIELD declarations for default model fields on open_notebook table |
| `tests/test_model_defaults_persistence.py` | CREATE | Unit tests for GET/PUT persistence and restart survival |

## Implementation Details

### 1. Fix `update_defaults_if_needed()` (model_provisioning.py)

Change the skip logic from "skip if same" to "skip if already set (non-empty)":

```python
current_value = getattr(defaults, field, None)
# Only set defaults for empty fields — never overwrite user customizations
if current_value:
    logger.debug(f"Preserving existing {field} = {current_value}")
    continue
```

This ensures:
- First boot: all fields are None → env vars populate them ✅
- User changes via PUT: preserved on restart ✅
- User clears a field: env var repopulates on next restart ✅

### 2. Migration 45.surrealql

```sql
-- E35-S2: Define fields on open_notebook table for model defaults
-- Table already exists (seeded in migration 1), adding explicit field defs
DEFINE FIELD IF NOT EXISTS default_chat_model ON TABLE open_notebook TYPE option<string>;
DEFINE FIELD IF NOT EXISTS default_transformation_model ON TABLE open_notebook TYPE option<string>;
DEFINE FIELD IF NOT EXISTS large_context_model ON TABLE open_notebook TYPE option<string>;
DEFINE FIELD IF NOT EXISTS default_text_to_speech_model ON TABLE open_notebook TYPE option<string>;
DEFINE FIELD IF NOT EXISTS default_speech_to_text_model ON TABLE open_notebook TYPE option<string>;
DEFINE FIELD IF NOT EXISTS default_embedding_model ON TABLE open_notebook TYPE option<string>;
DEFINE FIELD IF NOT EXISTS default_tools_model ON TABLE open_notebook TYPE option<string>;
DEFINE FIELD IF NOT EXISTS default_extraction_model ON TABLE open_notebook TYPE option<string>;
```

### 3. Unit Tests (test_model_defaults_persistence.py)

Tests:
1. `test_put_defaults_persists_to_db` — PUT sets values, GET returns them
2. `test_defaults_survive_fresh_get_instance` — After PUT, a new `get_instance()` returns saved values
3. `test_provisioning_preserves_user_defaults` — After PUT, `update_defaults_if_needed()` does NOT overwrite
4. `test_provisioning_fills_empty_fields` — If field is None, provisioning populates it
5. `test_put_partial_update` — PUT with partial fields doesn't clear others

## Testing

```bash
uv run pytest tests/test_model_defaults_persistence.py -v
uv run ruff check api/model_provisioning.py
```

## Risk Assessment

LOW — the fix is a 3-line change in the skip condition. Migration is additive (DEFINE FIELD IF NOT EXISTS). No breaking changes.
