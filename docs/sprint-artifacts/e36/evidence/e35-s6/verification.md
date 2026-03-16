# V6: E35-S6 — Building Backfill (AC7)

## Verification Date: 2026-03-05

## Code Check: Backfill Endpoint

**File**: `api/routers/acm.py:1234-1269`

**Result**: PASS

- `POST /backfill-buildings` endpoint exists (line 1234)
- Imports `backfill_all` and `backfill_source` from `scripts/v3_building_backfill.py`
- Handles both all-sources and single-source backfill
- Returns `BackfillBuildingsResponse` with `buildings_created`, `buildings_skipped`, `records_linked`
- Idempotent: skips buildings that already exist, never overwrites non-NULL FK values

## API Test: Buildings Endpoint

**GET /api/acm/buildings?source_id=source:2kjfxd6goehaj0njkam3**

```json
{
  "total": 0,
  "building_count": 0
}
```

Returns empty array (not error) for source with no buildings. This is correct — the endpoint returns `total: 0` gracefully.

## Code Check: Buildings List Endpoint

**File**: `api/routers/acm.py:2638-2669`

- `GET /buildings` returns `BuildingRecordListResponse` with `buildings` array and `total` count
- When `buildings` is empty, returns `{"buildings": [], "total": 0}` — no 404 or crash

## Verdict: PASS
