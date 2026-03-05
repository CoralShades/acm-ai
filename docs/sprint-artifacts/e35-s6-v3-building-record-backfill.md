# E35-S6: V3 Building Record Backfill

## Story

**ID**: E35-S6 | **Epic**: E35 | **Sprint**: V3-8 | **Points**: 3 SP | **Risk**: MEDIUM | **Type**: backend

## Summary

Pre-V3 sources have ACM records with `building_id` strings (e.g. `"B01"`) but no corresponding rows in the `building_record` table and no `building_record_id` FK populated. This means `GET /api/acm/buildings?source_id=X` returns an empty list for any source extracted before the V3 pipeline was deployed, breaking the Building Grid view and SF-aligned export for legacy data.

This story creates a focused backfill script and a matching API endpoint that:

1. Creates `building_record` rows from distinct `(source_id, building_id)` pairs in `acm_record`.
2. Populates the `building_record_id` FK on every `acm_record` that lacks one.
3. Includes a rollback script to reverse the operation.
4. Leaves V3-extracted sources (which already have proper `building_record` rows) untouched.

---

## Background and Context

### How V3 handles buildings

The V3 extraction pipeline (`open_notebook/graphs/acm_extraction.py`) creates `BuildingRecord` objects during extraction via `extract_building_node` and links `acm_record.building_record_id` to them in `extract_items_node`. Any source processed by V3 already has correct building_record rows and FKs.

### How pre-V3 data looks

Pre-V3 sources have:
- `acm_record.building_id` = a string like `"B01"`, `"Main Building"`, etc.
- `acm_record.building_record_id` = `NULL` / `NONE`
- Zero rows in `building_record` for that source

### Existing migration script

`scripts/v3_data_migration.py` (from E30-S5) already implements the exact building backfill algorithm with idempotency, schema verification, and dry-run support. It also includes vocabulary migration (`"Good"` -> `"Stable"`) which is out of scope for this story. The new script will reuse the proven core logic but strip out the vocabulary migration and add rollback capability.

### Existing backfill API pattern

`POST /api/acm/backfill-parents` in `api/routers/acm.py` provides the template for the API endpoint: it accepts an optional `source_id` filter, runs the backfill, and returns a count + message.

---

## Implementation Plan

### Change 1 — Core backfill module: `scripts/v3_building_backfill.py`

Create a new script that extracts the building-backfill logic from `v3_data_migration.py` into a standalone, importable module. This script focuses solely on building record creation and FK linking (no vocabulary migration).

**File**: `scripts/v3_building_backfill.py` (NEW)

The module exposes three async functions for use by both the CLI and the API endpoint:

```python
async def backfill_source(source_id: str, dry_run: bool = False, verbose: bool = False) -> BackfillResult
async def backfill_all(dry_run: bool = False, verbose: bool = False) -> BackfillResult
async def verify_schema() -> bool
```

**`BackfillResult`** is a TypedDict (or dataclass) returned by both functions:

```python
@dataclass
class BackfillResult:
    sources_processed: int = 0
    buildings_created: int = 0
    buildings_skipped: int = 0
    records_linked: int = 0
    records_already_linked: int = 0
```

#### Algorithm (mirrors `v3_data_migration.py`)

1. **Schema check** — Verify `building_record` table exists via `SELECT * FROM building_record LIMIT 1`. Abort with guidance if missing.
2. **Fetch records** — `SELECT * FROM acm_record WHERE source_id = $src ORDER BY building_id` (or all sources if no filter).
3. **Group** — Group by `(source_id, building_id)` using `_group_records_by_building()`.
4. **Per group**:
   - **Idempotency check** — `SELECT id FROM building_record WHERE source_id = $src AND building_code = $code LIMIT 1`. If exists, use the existing ID and skip creation (count as `buildings_skipped`).
   - **Create** — Extract building-level fields via `_extract_building_fields()`, generate `internal_id` via `BuildingRecord.generate_internal_id()`, instantiate `BuildingRecord`, call `save()`.
   - **Link** — `UPDATE acm_record SET building_record_id = $bld_rec_id WHERE id = $record_id AND (building_record_id = NONE OR building_record_id IS NULL)` for each record in the group. Only updates records with NULL FK (idempotent).
5. **Return** `BackfillResult` with counts.

#### V3 Safety (AC5)

V3 sources already have `building_record` rows. The idempotency check in step 4 will find the existing `building_record` for each `(source_id, building_code)` pair and skip creation (`buildings_skipped` counter increments). The FK update uses `WHERE building_record_id IS NULL`, so records that already have a valid FK are never touched.

#### CLI interface

```
uv run python scripts/v3_building_backfill.py [--dry-run] [--source-id SOURCE_ID] [--verbose]
```

Same flags as `v3_data_migration.py`. Prints a formatted summary table on completion.

### Change 2 — Rollback script: `scripts/v3_building_rollback.py`

Create a rollback script that reverses the backfill operation for AC4.

**File**: `scripts/v3_building_rollback.py` (NEW)

The module exposes:

```python
async def rollback_source(source_id: str, dry_run: bool = False, verbose: bool = False) -> RollbackResult
async def rollback_all(dry_run: bool = False, verbose: bool = False) -> RollbackResult
```

**`RollbackResult`** dataclass:

```python
@dataclass
class RollbackResult:
    sources_processed: int = 0
    buildings_deleted: int = 0
    records_unlinked: int = 0
```

#### Algorithm

1. **Fetch building records** — `SELECT * FROM building_record WHERE source_id = $src` (or all building_records if no filter).
2. **Per building record**:
   - **Unlink FKs** — `UPDATE acm_record SET building_record_id = NONE WHERE building_record_id = $bld_id` (NULLs the FK on all linked acm_records).
   - **Delete building record** — `DELETE building_record WHERE id = $bld_id`.
3. **Return** `RollbackResult` with counts.

#### V3 Safety

The rollback script requires an explicit `--source-id` flag or `--all` confirmation flag when running without a source filter, to prevent accidental rollback of V3 data. When called from the API endpoint, `source_id` is always required.

#### CLI interface

```
uv run python scripts/v3_building_rollback.py --source-id SOURCE_ID [--dry-run] [--verbose]
uv run python scripts/v3_building_rollback.py --all [--dry-run] [--verbose]
```

### Change 3 — API endpoint: `POST /api/acm/backfill-buildings`

Add a new endpoint to `api/routers/acm.py` following the existing `POST /api/acm/backfill-parents` pattern.

**File**: `api/routers/acm.py` (MODIFIED)

```python
@router.post("/backfill-buildings", response_model=BackfillBuildingsResponse)
async def backfill_building_records(
    request: BackfillBuildingsRequest = BackfillBuildingsRequest(),
):
    """
    Backfill building_record rows for pre-V3 sources (E35-S6).

    Creates building_record from distinct acm_record.building_id strings
    and populates building_record_id FK. Idempotent — safe to run multiple times.
    Optionally filter by source_id.
    """
    try:
        from scripts.v3_building_backfill import backfill_all, backfill_source

        if request.source_id:
            result = await backfill_source(request.source_id)
        else:
            result = await backfill_all()

        return BackfillBuildingsResponse(
            buildings_created=result.buildings_created,
            buildings_skipped=result.buildings_skipped,
            records_linked=result.records_linked,
            message=(
                f"Created {result.buildings_created} building records, "
                f"linked {result.records_linked} ACM records"
                f" ({result.buildings_skipped} buildings already existed)"
            ),
        )

    except Exception as e:
        logger.error(f"Error backfilling building records: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Change 4 — Request/Response models: `api/models.py`

Add new Pydantic models following the `BackfillParentsRequest`/`BackfillParentsResponse` pattern.

**File**: `api/models.py` (MODIFIED)

```python
class BackfillBuildingsRequest(BaseModel):
    """Request to backfill building_record rows for pre-V3 sources (E35-S6)."""

    source_id: Optional[str] = Field(None, description="Optional source ID filter")


class BackfillBuildingsResponse(BaseModel):
    """Response from building record backfill operation."""

    buildings_created: int = Field(..., description="Number of building records created")
    buildings_skipped: int = Field(..., description="Number of buildings that already existed")
    records_linked: int = Field(..., description="Number of ACM records linked to buildings")
    message: str = Field(..., description="Status message")
```

### Change 5 — Unit tests: `tests/test_building_backfill.py`

Create unit tests that verify the backfill logic using mocked SurrealDB calls.

**File**: `tests/test_building_backfill.py` (NEW)

Test cases:

| Test | Description | AC |
|------|-------------|-----|
| `test_backfill_creates_building_records` | Mock 3 acm_records with 2 distinct building_ids. Verify 2 BuildingRecords created, 3 FK updates issued. | AC1, AC2 |
| `test_backfill_idempotent_skips_existing` | Mock `_find_existing_building` returning an ID. Verify buildings_skipped=1 and no new BuildingRecord created. FK update still runs for NULL FKs. | AC1 |
| `test_backfill_skips_v3_sources` | Mock acm_records where all have `building_record_id` already set. Verify buildings_skipped=N, records_already_linked=N, buildings_created=0. | AC5 |
| `test_backfill_dry_run` | Run with `dry_run=True`. Verify no `save()` or `repo_query(UPDATE ...)` calls. Counts still returned. | AC1 |
| `test_backfill_api_endpoint` | Use `TestClient` to POST `/api/acm/backfill-buildings`. Verify 200 response with correct JSON shape. | AC3 |
| `test_rollback_deletes_and_unlinks` | Mock building_records for a source. Run rollback. Verify DELETE and UPDATE (NULL FK) queries issued. | AC4 |

#### Test fixture pattern

```python
def _make_acm_record_dict(**overrides) -> dict:
    """Minimal acm_record dict for backfill tests."""
    defaults = {
        "id": "acm_record:test001",
        "source_id": "source:abc123",
        "building_id": "B01",
        "building_name": "Main Building",
        "building_record_id": None,
        "building_year": 1990,
        "building_construction": "Brick",
        "building_address": "123 Test St",
        "suburb": "Testville",
        "postcode": "2000",
        "building_type": "School",
    }
    defaults.update(overrides)
    return defaults
```

Mocking strategy follows the existing pattern in `tests/test_building_record.py`:
- Patch `open_notebook.database.repository.repo_query` for DB calls
- Patch `BuildingRecord.save` for creation verification
- Patch `BuildingRecord.generate_internal_id` to return deterministic IDs

---

## File Changes Table

| File | Action | Description |
|------|--------|-------------|
| `scripts/v3_building_backfill.py` | CREATE | Core backfill module: `backfill_source()`, `backfill_all()`, `verify_schema()`, CLI entry point |
| `scripts/v3_building_rollback.py` | CREATE | Rollback module: `rollback_source()`, `rollback_all()`, CLI entry point |
| `api/routers/acm.py` | MODIFY | Add `POST /api/acm/backfill-buildings` endpoint |
| `api/models.py` | MODIFY | Add `BackfillBuildingsRequest`, `BackfillBuildingsResponse` models |
| `tests/test_building_backfill.py` | CREATE | Unit tests for backfill and rollback logic |

---

## Acceptance Criteria Mapping

| AC | Requirement | Satisfied By |
|----|-------------|--------------|
| AC1 | Script creates building_record from distinct acm_record.building_id strings | `backfill_source()` in `scripts/v3_building_backfill.py` groups by `(source_id, building_id)`, creates one `BuildingRecord` per unique pair with fields extracted from the first record in each group |
| AC2 | acm_record.building_id updated to FK reference | `backfill_source()` runs `UPDATE acm_record SET building_record_id = $bld_rec_id WHERE id = $record_id AND (building_record_id = NONE OR building_record_id IS NULL)` for each record |
| AC3 | GET /api/acm/buildings returns buildings for pre-V3 sources | After backfill runs, `BuildingRecord.get_by_source(source_id)` returns the newly created rows. Verified by `test_backfill_api_endpoint` calling the existing `GET /api/acm/buildings` endpoint after backfill. The new `POST /api/acm/backfill-buildings` endpoint provides an API trigger. |
| AC4 | Rollback script included | `scripts/v3_building_rollback.py` NULLs `building_record_id` FKs and DELETEs the created `building_record` rows. Verified by `test_rollback_deletes_and_unlinks`. |
| AC5 | V3 sources unaffected | Idempotency check: `_find_existing_building()` finds existing building_records for V3 sources and skips creation. FK update uses `WHERE building_record_id IS NULL` so already-linked records are never modified. Verified by `test_backfill_skips_v3_sources`. |
| AC6 | Unit test verifies backfill | `tests/test_building_backfill.py` with 6 test cases covering creation, idempotency, V3 safety, dry-run, API endpoint, and rollback |

---

## Key Design Decisions

### 1. Separate script vs. extending `v3_data_migration.py`

The existing `v3_data_migration.py` combines building backfill with vocabulary migration (`"Good"` -> `"Stable"`). Rather than adding flags to the existing script, we create a focused script that does only building backfill. This follows the single-responsibility principle and avoids risk of accidentally re-running vocabulary migration.

### 2. Importable module pattern

Both `v3_building_backfill.py` and `v3_building_rollback.py` are designed as importable modules (like `v3_data_migration.py`), with a `main()` CLI entry point and exported async functions. This allows:
- The API endpoint to call `backfill_source()` / `backfill_all()` directly
- Unit tests to call the functions with mocked DB calls
- CLI usage for manual data ops

### 3. Rollback scope

The rollback script operates per-source when `--source-id` is provided. Without a source filter, it requires explicit `--all` to prevent accidental rollback of V3 data. The API does not expose rollback (admin/CLI operation only).

### 4. Idempotency

Running the backfill multiple times is safe:
- Building creation checks for existing `(source_id, building_code)` pairs before creating
- FK updates use `WHERE building_record_id IS NULL` to avoid overwriting valid FKs
- Summary reports `buildings_skipped` and `records_already_linked` counts for visibility

---

## Dependencies

None. This story has no blocking dependencies. The `building_record` table and `building_record_id` field already exist (migration v40+, deployed as part of E30-S2).

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Backfill corrupts V3 data | Idempotency checks prevent creating duplicate building_records; FK update only touches NULL values (AC5) |
| Large dataset performance | Script processes one source at a time; FK updates are per-record with `WHERE id = $record_id` (indexed). No bulk UPDATE that could lock the table. |
| Rollback accidentally removes V3 buildings | Rollback requires explicit `--source-id` or `--all` flag; API does not expose rollback |
| Schema not ready | `verify_schema()` checks `building_record` table existence before proceeding; aborts with clear guidance if missing |

---

## Out of Scope

- Vocabulary migration (`"Good"` -> `"Stable"`) -- already handled by `v3_data_migration.py`
- Frontend changes -- the Building Grid already works once `GET /api/acm/buildings` returns data
- Automatic trigger on source upload -- backfill is a manual/on-demand operation
- Rollback API endpoint -- rollback is admin-only via CLI
