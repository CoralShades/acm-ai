# Findings: Critical Bug Investigation + E2E Test Design

## Created: 2026-02-09
## Last Updated: 2026-02-10

---

## NEW SESSION 2026-02-10: Service Status Check

**Verification Results:**
- SurrealDB: Command returned no output (container may be stopped)
- API (5055): Not responding to `/health` endpoint
- Frontend (8502): Returns HTTP 500 ✅ **Bug #1 confirmed**

**Implication:** API not running explains why frontend may be failing (API proxy dependency).

**API Startup Investigation:**
- Port 5055 is free (no conflicts)
- `run_api.py` starts uvicorn reloader successfully
- Import of `api.main:app` **hangs indefinitely** (timeout after 5s and 10s tests)
- Uvicorn logs: "Started reloader process" but worker process never starts

**ROOT CAUSE IDENTIFIED:**
- `open_notebook/database/async_migrate.py` line 96-127: `AsyncMigrationManager.__init__()`
- **Hardcoded to load migrations 1-13 only**
- **Actual migrations in repo: 1-18** (5 migrations missing!)
- Missing migrations: 14, 15, 16, 17, 18
- This causes import to fail/hang when initializing the migration manager

**Frontend Turbopack Investigation:**
- Frontend on port 8502 returns HTTP 500 - **RESOLVED: Stale frontend process**
- Fresh frontend started on port 3003 - **WORKING CORRECTLY**
- Root cause: Old crashed frontend on 8502, not a Turbopack bug
- Solution: Restart frontend, auto-assigned port 3003

---

## Bug #2: API Upload Asyncio Error - RESOLVED

**Root Cause:**
- `api/routers/sources.py` line 508: `execute_command_sync()` called from within async function
- `execute_command_sync` uses `asyncio.run()` internally
- `asyncio.run()` cannot be called when event loop already running (async context)

**Solution:**
- Wrapped sync call with `asyncio.to_thread()` to run in thread pool
- Prevents blocking the async event loop

**Files Modified:**
- `api/routers/sources.py` line 508-516: Added `await asyncio.to_thread()` wrapper

**Verification:**
- Upload test: `curl -X POST http://localhost:5055/api/sources` with PDF
- Result: ✅ SUCCESS - Source created with ID `source:mkds0x80ukfwyaabsjwr`

---

## Bug 1: Source Not Found - RESOLVED

**Symptom:** When opening or uploading a source, getting "Source Not Found" 500 error with `[Errno 2] No such file or directory`.

### Root Cause
The running API process had stale code and wasn't auto-reloading. Uvicorn's StatReload doesn't detect WSL file changes because `watchfiles` package isn't installed. The actual code in `api/routers/sources.py` was correct.

### Resolution
Killed all stale API processes and restarted. All source endpoints now return HTTP 200.

### Verification
- curl: All 3 test sources return HTTP 200
- Playwright: Source detail page loads with full content, ACM tabs, and chat panel

### Files Involved
- `api/routers/sources.py` (lines 649-706) - get_source endpoint (no changes needed)
- `run_api.py` - API startup with uvicorn reload

---

## Bug 2: AG Grid RowGroupingModule Error #200 - RESOLVED

**Symptom:** Console error #200: "Unable to use rowGroup as RowGroupingModule is not registered" when viewing ACM records.

### Root Cause
`ACMGrid.tsx` had `enableGrouping = true` as default prop, which activated enterprise-only `rowGroup` feature. Only `ag-grid-community` is installed (no enterprise module).

### Resolution
Changed default `enableGrouping` from `true` to `false` in ACMGrid.tsx. The column definitions already used the correct spread pattern `...(enableGrouping && { rowGroup: true })` to conditionally include the property, so with `enableGrouping = false`, the `rowGroup` property is completely omitted from column defs.

### Verification
- Playwright: ACM tab loads with 2 records, no AG Grid error #200
- Only remaining console items: 4 AG Grid deprecation warnings (non-critical) + 1 React Query warning (unrelated)

### Files Modified
- `frontend/src/components/acm/ACMGrid.tsx` line 114: `enableGrouping = true` -> `enableGrouping = false`
- Same change applied to lane-b worktree at `/mnt/d/ailocal/acm-ai-frontend/frontend/src/components/acm/ACMGrid.tsx`

---

## Bug 3: E2E PDF Extraction Test - PENDING

**Requirement:** True end-to-end PDF extraction test.

### Test Flow
1. Load real PDF from tests/fixtures/
2. Run MinerU extraction -> markdown
3. Run full LangGraph pipeline (metadata -> structure -> inventory -> tagging -> extraction -> validation)
4. Assert on actual extracted ACM records

### Status
Research completed, implementation not yet started.
