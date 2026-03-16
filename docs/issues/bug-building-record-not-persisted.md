# Building Records Not Persisted to `building_record` Table

> **Discovered**: 2026-03-11 (Bug Fix 11 live extraction verification)
> **Source**: Clutch_Broadmeadows.pdf — 1 building in inventory, 0 in `building_record` table
> **Priority**: P1
> **Status**: Open
> **Blocks**: Source register view (`/source/:id`) shows 0 buildings

## Problem

After extraction completes, the `building_record` SurrealDB table is empty. The pipeline compiles a building inventory (with `BuildingMeta` objects) and uses them to orchestrate extraction, but never persists the building metadata to the database.

### Building name = building ID

Additionally, when the generic heuristic fallback generates buildings (Bug Fix 11), the building name is set to the building ID ("B001") instead of the actual site name ("Broadmeadows Police Station"). The `BuildingMeta.name` should be populated from `document_metadata.site_name` or the first building name found in the data.

## Evidence

From Bug Fix 11 live test:
- Building inventory creates: `B001` (name="Main Building", page_start=1, page_end=999)
- `building_record` table: **empty** (SELECT * returns 0 rows)
- Source register view (`/source/:id`): shows 0 buildings
- `GET /api/acm/buildings?source_id=X`: returns `{ buildings: [], total: 0 }`

## Impact

- Frontend building sidebar empty
- Two-view architecture (Building Grid + Item Grid) broken
- No building-level aggregation possible
- API endpoints return empty results

## Fix Approach

1. In `acm_extraction.py`, after building inventory compilation, persist each `BuildingMeta` to `building_record` table
2. Use `site_name` from `document_metadata` as building name for generic fallback buildings
3. Ensure `building_record` has `source_id` foreign key for querying
4. Update `store_results_node` or add a `store_buildings_node` to handle persistence

## Files to Modify

| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Add building persistence after inventory compilation |
| `open_notebook/extractors/building_inventory.py` | Use site_name for generic fallback building names |
| `open_notebook/database/` | Verify `building_record` table schema exists in migrations |
| `migrations/` | Add building_record CREATE if missing |

---

## Status: RESOLVED (2026-03-11)

Fixed across Bug Fix 11 Phases 3-5:
- Phase 3 (commit `b05c91ab`): Minimal BuildingRecord fallback when LLM extraction fails
- Phase 5 (commit `a757c141`): CRITICAL `ObjectModel.save()` return value fix — `save()` returns `None`, code was checking return value instead of `self.id`. Root cause of ALL building persistence failures.
- Result: 3/3 buildings now persist correctly
