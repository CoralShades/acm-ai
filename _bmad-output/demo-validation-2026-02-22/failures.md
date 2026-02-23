# Demo Validation Failures — 2026-02-22

> **Report**: ACM-AI Feature-Complete Demo & Validation
> **Date**: 2026-02-22
> **Test Document**: Broadmeadows Police Station SAMP (31 ground truth records)
> **Known Baseline**: 87% extraction accuracy (27/31 records), last validated Feb 12

---

## Failures

### FAIL-001: Next.js Turbopack _buildManifest.js.tmp race condition
- **Phase**: 0 (Environment Setup) / affects ALL phases intermittently
- **Step**: 0.2 — Service verification
- **Expected**: Frontend dev server compiles all routes without errors
- **Actual**: Repeated ENOENT errors for `_buildManifest.js.tmp.*` and `app-build-manifest.json` files during hot-reload compilation. Occurs on /sources/[id], /extraction-monitor, /notebooks routes. Server does NOT fully crash but routes may fail intermittently.
- **Screenshot**: evidence/00-app-loaded.png (landing page works), evidence/01-sidebar-notebooks.png (notebooks loads OK), evidence/02-upload-dialog.png (upload dialog works)
- **Severity**: P2-Medium (intermittent, not blocking — dev server recovers)
- **Root Cause**: Next.js 15.5 Turbopack temp file race condition on Windows. Known WSL2/Windows fragility issue from project retrospective.
- **Workaround**: Stop frontend → delete `frontend/.next` → restart `npm run dev`. Or wait for recovery.
- **Note**: Environment issue, not a code defect. Previously documented as known technical debt.

### FAIL-002: Landing page "Upload Your First Document" links to /sources (→ /notebooks), not /documents
- **Phase**: 1 (Dashboard & Navigation)
- **Step**: 1.4 — Quick actions work
- **Expected**: "Upload Your First Document" CTA navigates to /documents page
- **Actual**: Links to `/sources` which redirects to `/notebooks` page
- **Screenshot**: evidence/01-sidebar-notebooks.png
- **Severity**: P3-Low (sidebar "Upload Document" button works correctly as alternative)
- **Workaround**: Use sidebar "Upload Document" button instead

### FAIL-003: Worker process not auto-detected — extraction commands queue but don't execute
- **Phase**: 3 (Extraction Pipeline)
- **Step**: 3.1 — Trigger ACM extraction
- **Expected**: Extraction command is picked up by worker within seconds
- **Actual**: Worker health shows "status: unknown, pid: null". Command `command:7307hhxff0zlzfxwi68v` submitted but extraction progress shows "No progress found". Zero records extracted after 60+ seconds.
- **Severity**: P0-Critical (BLOCKS extraction, grid, export, graph validation)
- **Root Cause**: Worker process (`uv run run_worker.py`) not started or died. `start-all.bat` may not have started it, or it crashed.
- **Workaround**: Manually start worker: `uv run run_worker.py --import-modules commands`

### FAIL-004: CSV/Excel export returns 404 when no records exist
- **Phase**: 8 (Export CSV & Excel)
- **Step**: 8.1/8.4 — Export buttons
- **Expected**: Export returns empty file or appropriate empty-state message (HTTP 200/204)
- **Actual**: Returns HTTP 404 (Not Found) for both `/api/acm/export` and `/api/acm/export/excel` when source has 0 records
- **Severity**: P3-Low (only affects empty-state UX, not real-world usage)
- **Workaround**: None needed — won't encounter this with real data

