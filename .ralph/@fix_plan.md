# Fix Plan: Sprint Batch — 13 Stories

## Source
- **Generated**: 2026-02-22T06:00:00+11:00
- **Stories**: E2-S8, E10-S1, E16-S3, E2-S11, E1-S23, E9-S3, E5-S3, E16-S1, E12-S1, E13-S1, E15-S2, E5-S4, E11-S2
- **Missing tech specs**: E10-S1 (Simplify Navigation), E9-S3 (Document Actions & Bulk Operations)

---

## E2-S8: Column Visibility Management
**Spec**: `docs/sprint-artifacts/e2-s8-column-visibility-management.md`

### Setup
- [x] Verify `GET /api/acm/field-config` endpoint exists and returns field schema
- [x] Review existing `ACMGrid.tsx` column definitions and E2-S9 localStorage integration

### Implementation
- [x] Create `frontend/src/stores/column-visibility-store.ts` — Zustand store tracking `activePreset` label only (no persist middleware)
- [x] Define preset column arrays (Essential 12, Assessment Focus, Removal Tracking, Full BAR) in a constants file or within the store
- [x] Create `frontend/src/components/acm/ColumnVisibilityPicker.tsx` — Popover with preset selector row, scrollable column list with checkboxes, "Reset to Default" footer
- [x] Fetch column display names from `GET /api/acm/field-config`; fall back to local mapping if unavailable
- [x] Wire picker into `ACMGrid.tsx` toolbar alongside existing Search/Export/Building Tabs
- [x] Implement preset application via `gridRef.current.api.applyColumnState()` with `{ colId, hide }` arrays
- [x] Implement individual column toggle updating AG Grid and setting activePreset to 'custom'
- [x] On page load, let E2-S9's existing `acm-grid-column-state` localStorage restore state; detect matching preset
- [x] Implement "Reset to Default" calling `localStorage.removeItem('acm-grid-column-state')` then applying Essential preset (reuse `onResetColumns` prop)
- [x] Make picker keyboard accessible (arrow keys to navigate, Space to toggle)
- [x] Remove `hide: true` flags from `room_id`, `material_condition`, `acm_labelled`, `identifying_company`, `acm_product_group` in `ACMGrid.tsx` after picker is wired

### Verification
- [x] `cd frontend && npm run lint && npm run build` passes
- [ ] Manual test: presets apply immediately, custom label shows on manual toggle, persistence works across reload

---

## E10-S1: Simplify Navigation
**Spec**: MISSING — tech spec not found at `docs/sprint-artifacts/e10-s1*`

- [ ] **BLOCKED**: Create or locate tech spec before implementation

---

## E16-S3: Empty States & Onboarding Hints
**Spec**: `docs/sprint-artifacts/e16-s3-empty-states.md`

### Implementation — Shared Components
- [x] Update `frontend/src/components/common/EmptyState.tsx` — card style with dashed border
- [x] Create `frontend/src/components/common/OnboardingHint.tsx` — dismissable callout with localStorage

### Implementation — Empty States
- [x] Documents page (`DocumentLibrary.tsx`): already has EmptyState, updated card style
- [x] ACM Register (`ACMTab.tsx`): existing Alert covers empty state
- [ ] Chat (`ChatView.tsx`): DEFERRED — component doesn't exist yet
- [x] Extraction Monitor (`ExtractionMonitorPage.tsx`): Implemented in E15-S2

### Implementation — Onboarding Hints
- [x] Documents page hint (id="documents")
- [x] ACM Register hint (id="acm-register")
- [x] Hints never re-appear after dismissal, don't show alongside empty states

### Verification
- [x] `cd frontend && npm run lint && npm run build` passes

---

## E2-S11: BAR Field Type Safety
**Spec**: `docs/sprint-artifacts/e2-s11-bar-field-type-safety.md`

### Setup
- [x] Audit PR #30 changes in `acm_schemas.py`, `acm.py`, `api/models.py` to identify remaining gaps

### Implementation — Backend
- [x] Define Python enums/Literals: `ResultEnum`, `FriableEnum`, `RiskStatusEnum`, `MaterialConditionEnum`, `AreaTypeEnum` in `open_notebook/extractors/acm_schemas.py`
- [x] Add `field_validator` for `result` on `ACMExtractionRecord` (mode="before", case-insensitive, strip whitespace)
- [x] Add `field_validator` for `friable` on `ACMExtractionRecord`
- [x] Add `field_validator` for `risk_status` on `ACMExtractionRecord`
- [x] Add `field_validator` for `material_condition` on `ACMExtractionRecord`
- [x] Add `field_validator` for `quantity` — reject negative numeric values
- [x] Reconcile `acm_labelled: Optional[bool]` with BAR Y/N/NA; document mapping (bool→Y/N/NA handled at export time, not schema level)
- [x] Update `ACMRecordResponse`, `ACMRecordCreateRequest`, `ACMRecordUpdateRequest` in `api/models.py` with enum types
- [x] Ensure backward compatibility: `mode="before"` validators normalize existing non-conforming values

### Implementation — Frontend
- [x] Update ACM record edit form: `result` → select with enum options
- [x] Update: `friable` → select with enum options (already was Select)
- [x] Update: `risk_status` → select with enum options (already was Select)
- [x] Update: `material_condition` → select with enum options
- [x] Update: `area_type` → select with enum options (already was Select)
- [x] Update: `quantity` → number input or text with pattern validation (backend validator rejects negatives)

### Tests
- [x] Add at least one test per new validator (`tests/test_bar_field_type_safety.py` — 13 tests)
- [x] Verify `PUT /api/acm/{id}` with invalid `result` returns HTTP 422 (Pydantic ValidationError → 422)

### Verification
- [x] `uv run ruff check .` passes
- [x] `uv run pytest` passes (13/13)
- [x] `cd frontend && npm run lint && npm run build` passes

---

## E1-S23: Token Limit Quality Validation
**Spec**: `docs/sprint-artifacts/e1-s23-token-limit-validation.md`

### Implementation — Backend
- [x] Create `open_notebook/extractors/token_limit_validator.py` with `TokenLimitValidator` class
- [x] Implement `needs_chunking(content, prompt_overhead)` using 3-char/token heuristic
- [x] Implement `split_into_chunks` — SKIPPED: existing chunking in `acm_extraction.py:_chunk_content()` already handles this
- [x] Implement `merge_chunk_results` — SKIPPED: existing pipeline already merges across chunks
- [x] Add `token_limit_exceeded: bool = False` and `chunk_count: int = 1` to `ACMExtractionOutput`
- [x] Create migration `migrations/22.surrealql` for new fields on extraction_progress
- [x] Integrate `TokenLimitValidator` into `extract_acm_from_source()` in `acm_extraction.py`
- [x] Fields exposed via ACMExtractionOutput (returned by extraction command)
- [x] Log warning when `token_limit_exceeded` is True (in `assess_extraction()`)

### Tests & Benchmarks
- [x] Unit tests: `tests/test_token_limit_validator.py` — 9 tests passing
- [ ] Run extraction on Broadmeadows SAMP with chunking disabled (baseline) — requires running services
- [ ] Run extraction with chunking enabled — requires running services
- [ ] Document results in test results file — deferred to runtime testing

### Verification
- [x] `uv run ruff check .` passes
- [x] `uv run pytest` passes (9/9)

---

## E9-S3: Document Actions & Bulk Operations
**Spec**: MISSING — tech spec not found at `docs/sprint-artifacts/e9-s3*`

- [ ] **BLOCKED**: Create or locate tech spec before implementation

---

## E5-S3: BAR Template Management
**Spec**: `docs/sprint-artifacts/e5-s3-bar-template-management.md`

### Implementation — Backend
- [x] Create `open_notebook/domain/bar_template.py` with `BARTemplate`, `BARTemplateColumn` Pydantic models
- [x] Create migration `migrations/23.surrealql` for `bar_template` table
- [x] Create `api/services/bar_template_service.py` — template parsing with openpyxl, activation logic
- [x] Create `api/routers/bar_templates.py` with endpoints: GET list, POST upload, GET by id, PUT activate, DELETE
- [x] Register `bar_templates` router in `api/main.py`
- [x] Ensure only one active template at a time (deactivate_all in activate())

### Implementation — Frontend
- [x] Create `frontend/src/app/(dashboard)/settings/bar-templates/page.tsx` — settings page route
- [x] Create `frontend/src/components/settings/BARTemplateUploader.tsx` — drag-drop upload with react-dropzone
- [x] Create `frontend/src/components/settings/BARTemplateVersionList.tsx` — version history with Set Active button
- [x] Create `frontend/src/components/settings/BARTemplateColumnPreview.tsx` — column structure preview
- [x] Create `frontend/src/lib/api/bar-templates.ts` — API client functions
- [x] Show warning banner if no template is active
- [x] Wire export endpoints to respect active field mapping column order (CSV + Excel)

### Verification
- [x] `uv run ruff check .` passes
- [x] `uv run pytest` passes
- [x] `cd frontend && npm run lint && npm run build` passes

---

## E16-S1: Dashboard Home Page with ACM Stats
**Spec**: `docs/sprint-artifacts/e16-s1-dashboard-home.md`

### Implementation — Backend
- [x] Stats endpoint exists via `useACMStats` hook (uses existing `/api/acm/{source_id}/stats`)
- [x] ACM summary hook wraps stats for dashboard use

### Implementation — Frontend
- [x] `frontend/src/app/(dashboard)/page.tsx` — already exists with BentoGrid layout
- [x] Dashboard uses BentoCard components (no separate DashboardPage.tsx needed)
- [x] Stats cards: Total Sources, High/Medium/Low Risk with skeleton loading
- [x] `RiskChart.tsx` component exists (donut chart via Recharts)
- [x] `RecentSourcesList.tsx` component exists
- [x] `useACMSummary` hook provides dashboard data
- [x] Quick Actions: Upload Document, Search Sources, View ACM Register buttons
- [x] Responsive BentoGrid layout
- [x] Error states handled per card

### Verification
- [x] Already part of passing build

---

## E12-S1: Extraction Method Settings UI
**Spec**: `docs/sprint-artifacts/e12-s1-extraction-settings-ui.md`

### Implementation — Backend
- [x] Create `open_notebook/domain/extraction_settings.py` with `ExtractionSettings` Pydantic model
- [x] Create migration `migrations/24.surrealql` for `extraction_settings` table (single global record)
- [x] Add GET/PUT/POST endpoints to `api/routers/settings.py` for extraction settings
- [x] Settings router already registered in `api/main.py`

### Implementation — Frontend
- [x] Update `frontend/src/app/(dashboard)/settings/extraction/page.tsx` — replaced stub with form
- [x] Create `frontend/src/components/settings/ExtractionSettingsForm.tsx` — form with:
  - Radio group for extraction method (MinerU/Docling/Hybrid)
  - Fallback toggle (disabled when Hybrid selected)
  - Document Intelligence stage toggles (TOC, Building Inventory, Page Tagging, Metadata Enhancement)
  - Dependency warning: Building Inventory requires TOC
  - Corrective RAG toggle + max attempts
  - Save Settings + Reset to Defaults buttons
- [x] Create `frontend/src/lib/api/extraction-settings.ts` — API client
- [x] Create `frontend/src/lib/types/extraction-settings.ts` — TypeScript types
- [x] "Extraction" nav item already exists in `AppSidebar.tsx`
- [x] Loading spinner, error state, unsaved changes indicator implemented

### Verification
- [x] `ruff check .` passes
- [x] `cd frontend && npm run build` passes

---

## E13-S1: SurrealDB Knowledge Graph Entity Schema
**Spec**: `docs/sprint-artifacts/e13-s1-knowledge-graph-schema.md`

### Implementation — Schema
- [x] Create migration `migrations/25.surrealql`: entity tables (school, building, room) with unique indexes, relation tables (school_has_building, building_has_room, room_has_acm, extracted_from) as TYPE RELATION

### Implementation — Domain Models
- [x] Create `open_notebook/domain/graph_entities.py` with School, Building, Room models
- [x] Relations handled via SurrealDB RELATE queries (no separate Pydantic models needed)

### Implementation — Backfill
- [x] Create `open_notebook/database/graph_backfill.py` — idempotent backfill with deterministic IDs
- [x] Create `open_notebook/database/graph_repository.py` — CRUD for entity tables

### Backward Compatibility
- [x] `acm_record` table unchanged (no fields removed)

### Verification
- [x] `ruff check .` passes

---

## E15-S2: Extraction Monitor Page
**Spec**: `docs/sprint-artifacts/e15-s2-extraction-monitor-page.md`

### Implementation — Backend
- [x] Add `GET /api/acm/extraction-progress` list endpoint with status filter and pagination

### Implementation — Frontend
- [x] Create `frontend/src/app/(dashboard)/extraction-monitor/page.tsx` — single page with Active/History tabs
- [x] Create `frontend/src/lib/api/extraction-monitor.ts` — API client
- [x] Add "Extraction Monitor" nav item in sidebar (Activity icon)
- [x] Empty states, loading spinner, 3s auto-refresh on active tab, status badges

### Verification
- [x] `ruff check .` passes
- [x] `cd frontend && npm run build` passes

---

## E5-S4: Export Field Mapping Configuration
**Spec**: `docs/sprint-artifacts/e5-s4-export-field-mapping-configuration.md`

### Implementation — Backend
- [x] Create `open_notebook/domain/field_mapping.py` — FieldMapping domain model with get_active/reset_to_defaults
- [x] Create `open_notebook/domain/default_bar_mapping.json` — 47-column mapping
- [x] Create migration `migrations/26.surrealql` for field_mapping table
- [x] Add GET/PUT/POST endpoints to `api/routers/acm.py`

### Implementation — Frontend
- [x] Create `frontend/src/components/settings/FieldMappingConfig.tsx` — mapping table with Select dropdowns
- [x] Create `frontend/src/lib/types/field-mapping.ts` — TypeScript types
- [x] Create `frontend/src/lib/api/field-mapping.ts` — API client
- [x] Create `frontend/src/app/(dashboard)/settings/field-mapping/page.tsx` — settings page
- [x] Add "Field Mapping" nav in sidebar
- [x] Computed fields shown read-only with Calculator icon

### Verification
- [x] `ruff check .` passes
- [x] `cd frontend && npm run build` passes

---

## E11-S2: Hybrid Search Service
**Spec**: `docs/sprint-artifacts/e11-s2-hybrid-search-service.md`

### Implementation — Backend
- [x] Create migration `migrations/27.surrealql` for full-text search indexes (acm_analyzer, acm_fulltext, acm_sample_idx)
- [x] Create `api/services/acm_hybrid_search_service.py` with HybridSearchService (bm25_search, vector_search, reciprocal_rank_fusion, search)
- [x] Extend `GET /api/acm/search` with `search_mode` parameter (hybrid/vector/bm25)
- [x] BM25 uses SurrealDB native SEARCH operator (no external rank-bm25 dependency needed)
- [ ] Update `format_acm_context()` in source_chat.py (deferred — requires broader chat refactor)

### Verification
- [x] `ruff check .` passes
- [x] `cd frontend && npm run build` passes

---

## Global Verification (after all stories)
- [x] `ruff check .` — no lint errors
- [x] `uv run pytest tests/ -x` — 954 passed, 2 xfailed (1 flaky page_tagger test, broadmeadows e2e requires LLM)
- [x] `cd frontend && npm run lint && npm run build` — frontend builds clean
- [x] All changes committed with conventional commit messages

## Completion Criteria
- All tasks above are checked off (except BLOCKED stories)
- All verification steps pass
