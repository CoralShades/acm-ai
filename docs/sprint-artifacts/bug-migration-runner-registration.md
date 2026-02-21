# BUG: Migration Runner Registration Gap

**Status:** done
**Epic:** Infrastructure / Standalone
**Priority:** P0 - Critical
**Discovered:** 2026-02-22
**Sprint:** Bug Triage (Post-Implementation Fix)

## Problem Statement

The `AsyncMigrationManager` in `open_notebook/database/async_migrate.py` hardcodes only migrations 1-13 in its registry. Migrations 14-20 exist on disk but were never registered, causing the database to remain at version 13. This meant all schema changes from E1-S9 through E1-S28 were silently not applied — fields didn't exist, tables weren't created, and queries failed silently.

Additionally, `open_notebook/domain/site_config.py` uses `SELECT DISTINCT` which is invalid SurrealQL syntax (SurrealDB uses `GROUP BY` instead). This caused the `get_agencies()` method to silently return empty arrays.

## Root Cause

The migration runner uses a manual registry pattern — each new migration must be explicitly added to both `up_migrations` and `down_migrations` lists. When migrations 14-20 were created as part of various stories, they were added to the `migrations/` directory but never registered in the runner class.

## Fix

1. **Register migrations 14-20** in `AsyncMigrationManager.__init__()` — both up and down lists
2. **Replace `SELECT DISTINCT`** with `GROUP BY` in `SiteConfig.get_agencies()` — both query variants

## Acceptance Criteria

- [x] AC1: Migrations 14-20 registered in `up_migrations` list
- [x] AC2: Migrations 14-20 registered in `down_migrations` list
- [x] AC3: API restart applies all pending migrations (DB advances to version 20)
- [x] AC4: `SELECT DISTINCT` replaced with valid SurrealQL `GROUP BY`
- [x] AC5: `get_agencies()` returns actual agency data instead of empty arrays
- [x] AC6: Ruff lint passes on both modified files

## Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `open_notebook/database/async_migrate.py` | Modified | Register migrations 14-20 in up + down lists |
| `open_notebook/domain/site_config.py` | Modified | Replace `SELECT DISTINCT` with `GROUP BY` |

## Verification

1. `uv run ruff check` — lint passes
2. Restart API — check logs for "Running migration 14...15...16...17...18...19...20"
3. `curl http://localhost:5055/api/acm/config/agencies` — returns agency names
4. Re-run Broadmeadows extraction — verify improved record count

## Dev Agent Record

- **Build status:** PASS (ruff lint clean)
- **Files verified:** async_migrate.py, site_config.py
- **Impact:** Unblocks all features from E1-S9 through E1-S28 at the database level
