# Task Plan: Jobs Dashboard UI/UX Audit & Fix

## Status: COMPLETE (pending visual verification)

## Phase 1: Dashboard Cards Redesign
- [x] 1.1 Remove Buildings stat card from `jobs/page.tsx`
- [x] 1.2 Remove ACM Records stat card from `jobs/page.tsx`
- [x] 1.3 Change grid from `lg:grid-cols-6` to `lg:grid-cols-4`
- [x] 1.4 Remove `totalBuildings`/`totalRecords` from stats useMemo
- [x] 1.5 Loading skeleton grid already `lg:grid-cols-4` — no change needed

## Phase 2: Filter Redesign
- [x] 2.1 Remove `building_review` from `JobFilter` type union
- [x] 2.2 Remove `building_review` from `FILTER_OPTIONS` array
- [x] 2.3 Labels: All, Extracting, Pending, Records, Published ✓
- [x] 2.4 Filter logic folds `building_review` → `pending_review`

## Phase 3: Job Card UI Bug Fixes
- [x] 3.1 Fix title overflow — `overflow-hidden` on Card + title container
- [x] 3.2 Add `break-words` for long unbroken filenames
- [x] 3.3 Three-dot menu: `flex-shrink-0` already present — unaffected by overflow fix
- [x] 3.4 Add metadata icon row (page count via FileText, file size via HardDrive)
- [x] 3.5 Import FileText + HardDrive from lucide-react + `formatFileSize` helper
- [x] 3.6 Consolidated uploaded date + building/record counts into single compact row

## Phase 4: Backend Wiring
- [x] 4.1 Research: `total_pages` in `source_intelligence` table (migration 41); `file_size` not stored
- [x] 4.2 Added `page_count` subquery (LEFT JOIN on `source_intelligence`) to both SurrealQL queries
- [x] 4.3 Added `file_size` derivation from `asset.file_path` via `Path.stat().st_size`
- [x] 4.4 Added `page_count` + `file_size` to `SourceListResponse` model (api/models.py)
- [x] 4.5 Updated `SourceListResponse` type in `frontend/src/lib/types/api.ts`

## Phase 5: Verification & QA
- [x] 5.1 `npm run build` — PASS (0 errors)
- [x] 5.2 `npm run lint` — PASS (only pre-existing warnings)
- [x] 5.3 `ruff check .` — PASS (0 errors)
- [x] 5.4 `pytest tests/ -x` — PASS (2175 passed, 0 failures)
- [ ] 5.5 Visual: 4 stat cards, 5 filter pills, no overflow, metadata icons
- [ ] 5.6 Responsive check at multiple viewports
- [ ] 5.7 Extraction progress bar still works
