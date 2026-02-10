# Findings: Critical Bug Investigation + E2E Test Design

## Created: 2026-02-09
## Last Updated: 2026-02-09

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
