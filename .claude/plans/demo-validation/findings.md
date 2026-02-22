# ACM-AI Demo Validation — Findings

## Session: 2026-02-22

### Environment
- SurrealDB: Running on port 8000 (confirmed via health check)
- FastAPI: Starting (user confirmed start-all.bat)
- Frontend: Starting (user confirmed start-all.bat)
- Test PDF: `tests/e2e/fixtures/samps/broadmeadows-police-station-samp.pdf` — confirmed exists
- Ground truth: `tests/e2e/fixtures/samps/broadmeadows-expected-results.json` — 31 records

### Failures Discovered
1. **FAIL-001 (P0-Critical)**: All dashboard routes 500 due to corrupted `.next` cache
   - Affects: /documents, /acm, /notebooks, /login, /settings/* — everything except landing page
   - Root cause: `_buildManifest.js.tmp` and `app-build-manifest.json` ENOENT errors
   - Known WSL2/Windows fragility (documented in project technical debt)
   - Fix: Delete `.next` dir and restart dev server

### Key Observations
- Existing data in DB: 2 Broadmeadows sources already uploaded, ACM records present
- API backend fully functional (sources API, ACM records API, config endpoint all work)
- Landing page renders correctly with full feature card layout
- Source IDs available: `source:o3xxk28rimze8w7704vq` (Broadmeadows 14), `source:vrgglsx5ru5ngfeo0023` (Broadmeadows 13)
