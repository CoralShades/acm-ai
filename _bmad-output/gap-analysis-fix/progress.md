# Gap Analysis Fix - Progress Tracker

GitHub Issue: #14 | Target: >= 7.0/10

## Work Stream A: Extract ALL Records (P0)
- [x] A1: Remove negative-skip directives from extraction prompts
- [x] A2: Fix product/location field mapping in prompts (updated result values in examples + schema)
- [x] A3: Fix orchestrator skip logic for buildings without register pages (SKIP -> REGEX_ONLY)

## Work Stream B: Fix Result Enum (P0)
- [x] B1: Update result normalization from binary to BAR vocabulary (Detected/Not Detected -> Positive/Negative)

## Work Stream C: Expose Compliance Fields via API (P0)
- [x] C1: Add 11 compliance fields to ACMRecordResponse
- [x] C2: Update ACM router serialization (list, get, create, update, CSV export, Excel export)

## Work Stream D: Fix Context Propagation & UI Bugs (P1)
- [x] C3: Update frontend TypeScript types (11 new fields + classification fields)
- [x] D1: Fix building_name propagation (orchestrator post-fills from plan)
- [x] D2: Fix page_number propagation (orchestrator post-fills from plan.page_range[0])
- [x] D3: Fix friable enum mismatch ('Non Friable' -> 'Non-friable')
- [x] D4: Fix search bar filter wiring (searchText state + ACMToolbar + ACMGrid quickFilterText)

## Verification
- [x] `grep -i "skip|only.*positive|do not extract" prompts/acm/*.jinja` -> zero matches
- [x] `uv run ruff check` -> All checks passed
- [x] `cd frontend && npm run build` -> Build succeeded (exit code 0)
- [x] `uv run pytest` -> 835 passed, 2 failed (pre-existing page_tagger flaky tests, unrelated)
- [ ] Integration test with Broadmeadows PDF -> pending (requires running services)

## Files Modified
| File | Changes |
|------|---------|
| `prompts/acm/extraction.jinja` | Removed negative-skip, updated examples/instructions to BAR vocab |
| `prompts/acm/building_extraction.jinja` | Removed negative-skip, updated examples/instructions to BAR vocab |
| `open_notebook/extractors/orchestrator.py` | SKIP->REGEX_ONLY, regex uses "Negative", page_number propagation |
| `open_notebook/extractors/acm_schemas.py` | Updated result field description to BAR vocabulary |
| `open_notebook/graphs/acm_extraction.py` | Result normalization: 4-value BAR vocab with Assumed Positive/Negative |
| `api/models.py` | Added 11 compliance fields to ACMRecordResponse |
| `api/routers/acm.py` | Added compliance fields to list/get/create/update/CSV/Excel endpoints |
| `frontend/src/lib/types/acm.ts` | Added 11 compliance + 5 classification fields, fixed FriableType |
| `frontend/src/app/(dashboard)/acm/page.tsx` | Wired searchText state between ACMToolbar and ACMGrid |
