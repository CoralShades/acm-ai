# E30-S5: Data Migration Script — Tech Spec

## Story Summary

| Field | Value |
|-------|-------|
| Story ID | E30-S5 |
| Title | Data Migration Script |
| Epic | E30 — SF Schema Foundation |
| Sprint | V3-2 |
| Story Points | 3 |
| Risk | MEDIUM |
| Type | backend |
| Dependencies | E30-S2 (BuildingRecord model), E30-S3 (ACMRecord SF alignment) |

## Objective

Create a data migration script that extracts building-level fields from existing `acm_record` rows into new `building_record` entries, links them via the `building_record_id` FK, and applies the "Good → Stable" condition vocabulary migration to all existing records.

## Acceptance Criteria

- **AC1**: Migration script extracts building-level fields from existing acm_record rows into new building_record entries
- **AC2**: Groups records by building_id (legacy string) and creates one building_record per unique building
- **AC3**: Populates `acm_record.building_record_id` FK with the new `building_record` SurrealDB record ID (legacy `building_id` string preserved unchanged)
- **AC4**: Preserves `building_id` string on acm_record for rollback reference
- **AC5**: "Good → Stable" condition vocabulary migration applied to all existing records
- **AC6**: Rollback script provided
- **AC7**: Dry-run mode: reports what would change without modifying data
- **AC8**: Tested against Broadmeadows (31 records) and Alexander (43 records) benchmark data
- **AC9**: Idempotent: safe to run multiple times

## Design Decisions

### AC3 Clarification

The existing `building_id` field on `acm_record` remains a plain string (no schema change). The new `building_record_id` field (added by migration 40 in E30-S2) is populated with a `record<building_record>` reference. This is additive — no data loss, no breaking change.

### Grouping Strategy

Group by `(source_id, building_id)` — one `building_record` per unique combination. Building-level data (name, year, construction, address, suburb, postcode, type) is extracted from the first `acm_record` in each group.

### Type Conversions

- `ACMRecord.building_year` is `Optional[int]` → `BuildingRecord.building_year` is `Optional[str]` (SF picklist). Cast: `str(value) if value else None`.

### Migration Runner Pre-Condition

Migrations 37–40 exist on disk but `async_migrate.py` only registers up to 36. The migration script must verify the DB is at schema version ≥ 40 before running (i.e., `building_record` table and `building_record_id` column exist). If not, it should abort with guidance to run pending migrations first.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `scripts/v3_data_migration.py` | CREATE | Main migration script |
| `scripts/v3_data_migration_rollback.py` | CREATE | Rollback script |
| `tests/test_v3_data_migration.py` | CREATE | Unit tests |
| `migrations/async_migrate.py` | MODIFY | Register migrations 37–40 |

## Implementation Details

### 1. `scripts/v3_data_migration.py`

```python
"""
V3 Data Migration Script (E30-S5)

Extracts building-level fields from acm_record into building_record table,
populates building_record_id FK, and applies vocabulary migration.

Usage:
    uv run python scripts/v3_data_migration.py [--dry-run] [--source-id SOURCE_ID]
"""
```

**CLI Arguments:**
- `--dry-run`: Report changes without executing (AC7)
- `--source-id`: Migrate a single source (optional, for testing)
- `--verbose`: Detailed per-record logging

**Algorithm:**

```
1. Connect to SurrealDB via db_connection()
2. Verify schema version >= 40 (SELECT * FROM building_record LIMIT 1)
3. Fetch all acm_records: SELECT * FROM acm_record
4. Group by (source_id, building_id)
5. For each group:
   a. Check if building_record already exists for this (source_id, building_id)
      → If yes, skip creation (idempotent)
   b. Extract building-level fields from first record in group
   c. Generate internal_id via BuildingRecord.generate_internal_id(source_id)
   d. Create BuildingRecord and save
   e. Update all acm_records in group: SET building_record_id = new_building_record_id
      → Only if building_record_id is NULL (idempotent)
6. Vocabulary migration: UPDATE acm_record SET material_condition = 'Stable' WHERE material_condition = 'Good'
7. Report summary: buildings created, records updated, vocab changes
```

**Building Field Extraction Mapping:**

From `acm_record` → `building_record`:
| acm_record field | building_record field | Notes |
|-----|-----|-----|
| `building_id` | `building_code` | Was the grouping key string |
| `building_name` | `building_name` | Direct copy |
| `building_year` | `building_year` | `str(int_value)` cast |
| `building_construction` | `building_construction` | Direct copy |
| `building_address` | `building_address` | Direct copy |
| `suburb` | `suburb` | Direct copy |
| `postcode` | `postcode` | Direct copy |
| `building_type` | `building_type` | Direct copy |
| `source_id` | `source_id` | Direct copy |

Fields NOT on acm_record (new SF-only building fields like `building_category`, `roof_type`, etc.) are left as NULL — they will be populated by future AI extraction (E32-S1).

**Idempotency Strategy (AC9):**

1. Before creating a BuildingRecord, query: `SELECT * FROM building_record WHERE source_id = $src AND building_code = $code`
2. Before updating acm_record FK, check: `WHERE building_record_id = NONE OR building_record_id IS NULL`
3. Vocabulary update is naturally idempotent (no "Good" values after first run)

### 2. `scripts/v3_data_migration_rollback.py`

```
1. Delete all building_record rows (or filtered by source_id)
2. Set building_record_id = NULL on all acm_record rows
3. Optionally revert Stable → Good (with --revert-vocab flag)
4. Report summary
```

**Note:** Rollback does NOT delete acm_records — only removes building_records and clears the FK.

### 3. `migrations/async_migrate.py` — Register Migrations 37–40

Add registration entries for migrations 37, 38, 39, 40 in the migration runner's registry. These `.surrealql` files already exist on disk.

### 4. `tests/test_v3_data_migration.py`

**Test Cases:**

1. **test_groups_by_building_id** — Given 5 acm_records with 2 unique building_ids, creates 2 building_records
2. **test_building_field_extraction** — Verifies building_name, building_year (int→str), building_construction, address, suburb, postcode, type copied correctly
3. **test_building_record_id_fk_set** — After migration, all acm_records have non-null building_record_id pointing to correct building_record
4. **test_vocabulary_migration** — Records with `material_condition = "Good"` become `"Stable"`
5. **test_idempotent_rerun** — Running migration twice produces same result, no duplicate building_records
6. **test_dry_run_no_changes** — With --dry-run, no DB changes made
7. **test_rollback** — After rollback, building_records deleted, FKs nulled
8. **test_broadmeadows_benchmark** — Seed 31 Broadmeadows-like records, verify 1 building_record created with correct data
9. **test_alexander_benchmark** — Seed 43 Alexander-like records across 5 buildings, verify 5 building_records created

**Testing Strategy:**

Tests use SurrealDB test fixtures — create temporary acm_records via `repo_query()`, run migration functions, assert results, then clean up. The migration logic should be importable as functions (not just CLI entry point) to enable unit testing.

## Execution Plan

1. Update `async_migrate.py` to register migrations 37–40
2. Implement `scripts/v3_data_migration.py` with importable functions + CLI
3. Implement `scripts/v3_data_migration_rollback.py`
4. Write `tests/test_v3_data_migration.py`
5. Run `uv run ruff check .` and `uv run pytest tests/test_v3_data_migration.py`
6. Verify with `--dry-run` against any existing data

## Risk Mitigation

- **Data safety**: `--dry-run` default for first execution; rollback script provided
- **Schema dependency**: Pre-flight check ensures building_record table exists
- **Idempotency**: Multiple runs produce identical results
- **Type mismatch**: Explicit building_year int→str cast with null handling
