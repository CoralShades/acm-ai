# MCS11 Findings — Jobs vs Source Page Audit

## Audit Date: 2026-03-19

### Visual Audit (Screenshots)

| Page | Screenshot | Observations |
|------|-----------|-------------|
| `/jobs/source:ID` Overview | `audit-job-detail.png` | 6 tabs, stats cards, Re-Extract — no SSE, no live progress |
| `/jobs/source:ID` Buildings | `audit-job-buildings.png` | **BUG**: "No Rows To Show" despite 2 buildings (V3 API returns 0) → **FIXED** with `useJobBuildings` |
| `/jobs/source:ID` Buildings (fixed) | `audit-job-buildings-fixed.png` | 2 buildings now visible via legacy API fallback |
| `/jobs/source:ID` ACM Records | `audit-job-acm.png` | Records work, building filter tabs, but no bulk ops/search/validation |
| `/source/source:ID` | `audit-source-page.png` | "No buildings extracted yet" — V3 API has no data for this source |
| User D1.png | Production reference | Shows the ideal layout for jobs page |
| User view3.png | Production reference | Shows buildings grid with data |

### Two Buildings APIs (Root Cause of Buildings Bug)

1. **V3 endpoint**: `GET /api/acm/buildings?source_id=X`
   - Queries `building_record` table (E30-S2)
   - Only populated by V3 extraction pipeline
   - Returns 0 for sources extracted via old pipeline

2. **Legacy endpoint**: `GET /api/acm/jobs/{source_id}/buildings`
   - Derives buildings from `acm_record` data
   - Always works — joins acm_record GROUP BY building_id
   - Returns full building data for all extraction modes

**Fix applied**: Created `useJobBuildings` hook + `acmApi.listJobBuildings()` adapter that maps `BuildingResponse` → `BuildingRecord` shape. Jobs page tries V3 first, falls back to legacy.

### Feature Distribution Analysis

| Feature | `/jobs/[id]` | `/source/[id]` | Gap Priority |
|---------|:-----------:|:--------------:|:------------|
| SSE live streaming | No | Yes | **P0** — core UX |
| Building status badges | No | Yes | **P0** — progress visibility |
| Live progress bar + ETA | No | Yes | **P0** |
| Bulk edit/validate | No | Yes | **P1** — core workflow |
| Validation error counts | No | Yes | **P1** |
| Quick text search | No | Yes | **P2** |
| Group by Room | No | Yes | **P2** |
| Building selection persistence | useState | Zustand | **P3** |
| Save phase tracking | No | Yes (MCS10) | **P0** |
| CRUD Chat (CopilotKit) | Yes | No | Jobs-only |
| Content/Log/Raw Tables | Yes | No | Jobs-only |

### Hooks Usage Comparison

| Hook | `/jobs/[id]` | `/source/[id]` |
|------|:-----------:|:--------------:|
| `useV3BuildingStream` | No | Yes |
| `useV3SSE` | No | Yes (indirect) |
| `useBuildings` | Yes | Yes |
| `useJobBuildings` | Yes (MCS10 fix) | No |
| `useACMItems` | No (uses raw fetch) | Yes (per-building) |
| `useValidationSummary` | No | Yes |
| `useBulkFix` | No | Yes |
| `useBuildingStore` (Zustand) | No | Yes |
| `useACMStats` | Yes | No |
| `useSource` | Yes | No |

### State Management Gap

- `/jobs/[id]` uses `useState` for building selection → resets on tab navigation
- `/source/[id]` uses Zustand `useBuildingStore` → persists across navigation
- `/jobs/[id]` fetches ALL records upfront (500 limit) → inefficient
- `/source/[id]` fetches per-building on demand → efficient

### SSE Event Flow (for reference)

```
ai.building_extracted → building in DB, invalidate buildings query
ai.items_extracted    → items extracted (not saved), update status to "Validating"
ai.validation_complete → validation done, status to "Saving..."
ai.save_started       → save phase begins
ai.save_progress      → per-building save status
ai.save_complete      → items NOW in DB, invalidate items query, clear statuses
```

### Sub-pages Under /jobs/[id]/ (Discovery)

| Route | Purpose | Has SSE? |
|-------|---------|----------|
| `/jobs/[id]/extract` | Extraction monitoring | **YES** — richest SSE (dual category) |
| `/jobs/[id]/review/buildings` | Building review wizard | No |
| `/jobs/[id]/review/records` | Records review wizard | No |
| `/jobs/[id]/chat` | Standalone chat | No |

The `/jobs/[id]/extract` page has the MOST complete SSE experience (subscribes to both `extraction` and `ai` categories + AG-UI stream). This is separate from the main jobs detail page.

---

## MCS11 Implementation Results (2026-03-19)

### Commits
| Commit | Change |
|--------|--------|
| `b06c5788` | Phases 1-3: SSE streaming, bulk ops, search/filter + FK event bus wiring |
| `c254974f` | JobStatusPill SSE override (Extracting during active stream) |
| `545d6c41` | Query invalidation timing (MCS10 final + MCS11 buildings fix) |
| `f2941789` | API FK fields: building_record_id + parent_table_id in ACMRecordResponse |
| `658d21bb` | Test: RecordID conversion test for FK fields |

### MCS11 Phase Status After Commits
| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 1: SSE Streaming | 1.1-1.5 | DONE — useV3BuildingStream, progress bar, JobStatusPill override |
| Phase 2: Bulk Ops | 2.1-2.4 | DONE — BulkOperationsBar wired, Fix All button |
| Phase 3: Search/Filter | 3.1-3.2 | DONE — quick text search, Group by Room toggle |
| Phase 3: Search/Filter | 3.3-3.4 | REMAINING — per-building data source, BuildingTabStrip upgrade |
| Phase 4: Job Card Status | 4.1-4.3 | DEFERRED — not started |
| Phase 5: Validation | 5.1 | DONE — useValidationSummary wired |
| Phase 5: Validation | 5.2-5.3 | REMAINING — error row highlighting, overview card |
| Phase 6: Verification | 6.1 | DONE — E2E smoke (29/29 tests pass, all tabs render) |
| Phase 6: Verification | 6.2-6.6 | REMAINING — SSE test, bulk test, cross-page, mobile, screenshots |
| Gap4: FK exposure | All | DONE — building_record_id + parent_table_id exposed via API |

---

## MCS13 Bugs Found During E2E Testing (2026-03-19)

Three bugs surfaced while verifying FK linkage after MCS11 E2E testing with 2 PDF uploads.

### Bug 1: UNIQUE Index Collision (building_record table)
**Symptom**: Second upload of same PDF hijacked building_record rows from first upload.
**Root cause**: `internal_id` derived from `source.title[:8]` only → `BLD#CLUTCH_B_001` identical for both sources.
**Fix**: Appended first 6 chars of source record ID: `BLD#{title_short}_{source_suffix}_{seq:03d}`.
**Commit**: `5819d5e4`
**Files**: `open_notebook/domain/acm.py`, `open_notebook/graphs/acm_extraction.py`

### Bug 2: FK Schema Type Mismatch (building_record_id)
**Symptom**: `building_record_id` stored as `option<string>` but pipeline sends `RecordID` objects.
**Root cause**: Migration 40's `IF NOT EXISTS` was silently skipped — an earlier schema inference had already created the field as `string` type. Field never got the correct `record<building_record>` type.
**Fix**: Migration 55 forces `DEFINE FIELD building_record_id ON acm_record TYPE option<record<building_record>>`.
**Commit**: `45372518`
**Files**: `migrations/55.surrealql`, `migrations/55_down.surrealql`, `open_notebook/graphs/acm_extraction.py`

### Bug 3: LangGraph MemorySaver Crash (checkpointer serialization)
**Symptom**: Extraction crashed with `Type is not msgpack serializable: RecordID` when MemorySaver tried to checkpoint graph state.
**Root cause**: Graph state contains `RecordID` objects (from MCS8 ghost-save fix). LangGraph's MemorySaver uses msgpack which can't serialize custom Python objects.
**Fix**: Disabled MemorySaver (`checkpointer=None`) until a custom serializer converting RecordIDs to strings is implemented.
**Commit**: `45372518`
**Note**: This reverts MCS8's re-enablement of MemorySaver. Net state: checkpointer disabled (same as MCS7 state).

### E2E Result After All 3 Fixes
- 2 PDF uploads, same PDF, different sources
- 14 buildings total (7 per upload), 0 UNIQUE index collisions
- 101 records saved with 90% FK population rate (building_record_id populated)
- 10% FK gap = records saved before building_record committed to DB (race condition in save ordering)

---

## Known Bugs Still Open (As of 2026-03-19)

Bugs discovered during MCS11/MCS13 E2E testing but NOT yet fixed:

| Bug | Severity | Description |
|-----|----------|-------------|
| Quick Upload dialog stuck after upload | P1 | Dialog doesn't close / navigate after PDF upload completes |
| SSE streaming fails on fresh navigation | P1 | operationId not reliably picked up from sessionStorage on direct navigation |
| `/api/acm/field-config` returns 500 | P1 | field-schema endpoint error (config_json NULL on some records) |
| ProvenanceViewer crashes on some records | P1 | parent_table_id null causes crash in provenance fetch |
| Product validation too strict | P2 | Rejects valid product values not in exact SF enum (e.g. compound values) |
| Ollama timeout on large documents | P2 | STRUCTURE stage 148-208s for 27+ page docs (from BugFix12 N8) |
