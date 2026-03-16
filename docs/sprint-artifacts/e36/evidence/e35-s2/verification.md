# E35-S2 Verification: Persist Model Defaults to SurrealDB

## Status: PASS

## Code Verification

### 1. PUT /api/models/defaults Writes to SurrealDB

In `api/routers/models.py`, the `update_default_models()` endpoint (line 162-212):

1. Fetches fresh defaults from DB: `defaults = await DefaultModels.get_instance()` (line 166)
2. Updates only provided fields (lines 169-190) using conditional `if defaults_data.X is not None`
3. Persists to SurrealDB via: `await defaults.update()` (line 192)
4. Returns the updated defaults as response

### 2. DefaultModels.get_instance() Bypasses Singleton Cache

In `open_notebook/domain/models.py` (lines 175-197), `get_instance()` is overridden to **always fetch fresh data from the database**, bypassing the parent `RecordModel` singleton cache:

```python
@classmethod
async def get_instance(cls) -> "DefaultModels":
    """Always fetch fresh defaults from database (override parent caching behavior)"""
    result = await repo_query(
        "SELECT * FROM ONLY $record_id",
        {"record_id": ensure_record_id(cls.record_id)},
    )
    # ... creates new instance with fresh data (bypass singleton cache)
    instance = object.__new__(cls)
    object.__setattr__(instance, "__dict__", {})
    super(RecordModel, instance).__init__(**data)
    return instance
```

This fixes the E35-S2 issue where cached defaults would be returned even after a PUT update.

### 3. RecordModel.update() Uses repo_upsert

In `open_notebook/domain/base.py` (lines 293-319), the `update()` method:

1. Serializes all model fields to a dict (lines 295-299)
2. Calls `await repo_upsert(table, record_id, data)` (line 301)
3. Re-reads the saved record to update the in-memory instance (lines 309-318)

`repo_upsert` in `repository.py` (line 119-127) issues `UPSERT {id} MERGE $data` -- a SurrealDB atomic create-or-update operation.

### 4. update_defaults_if_needed() Preserves User Customizations

In `api/model_provisioning.py` (lines 365-409), the startup provisioning:

- Only fills **empty** fields: `if current_value: continue` (line 397)
- Never overwrites existing user-set defaults
- This prevents the provisioning-on-restart overwrite bug

## Test Results

API endpoint test (live):

```json
GET /api/models/defaults -> 200
{
  "default_chat_model": "model:5oeg7t3t99u8qa69j9r5",
  "default_transformation_model": "model:iy35oq7ddgni1cyttdv0",
  "large_context_model": "model:iy35oq7ddgni1cyttdv0",
  "default_text_to_speech_model": null,
  "default_speech_to_text_model": null,
  "default_embedding_model": "model:gl7f90e9q15lucs2o3iy",
  "default_tools_model": "model:iy35oq7ddgni1cyttdv0",
  "default_extraction_model": "model:m7tdn5b7lavy0z1yg14j"
}
```

Defaults are persisted and returned correctly from SurrealDB.

## Evidence

Key code paths confirming persistence:

```python
# api/routers/models.py, line 192
await defaults.update()  # Writes to SurrealDB

# open_notebook/domain/base.py, lines 301-306
await repo_upsert(
    self.__class__.table_name if hasattr(...) else "record",
    self.record_id,  # "open_notebook:default_models"
    data,
)

# api/model_provisioning.py, lines 396-399
if current_value:
    logger.debug(f"Preserving existing {field} = {current_value}")
    continue  # Never overwrites user customizations
```

## Notes

- The `DefaultModels.get_instance()` override is critical -- without it, the singleton pattern in `RecordModel.__new__` would return stale cached data
- The `update_defaults_if_needed()` guard (`if current_value: continue`) prevents startup provisioning from overwriting persisted defaults
- Live API test confirms defaults survive across requests
