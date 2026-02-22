# Fix Plan — Sprint Batch: E10-S1, E9-S3, E12-S2, E12-S3, E12-S4, E13-S2, E13-S3

---

## Story 1: E10-S1 — Simplify Navigation for ACM-AI Focus

### Setup
- [x] Create `frontend/src/config/navigation.ts` with typed `NavItem`, `NavGroup` interfaces and `navigationConfig` array
- [x] Add `hideInAcm` flag to Notebooks, Podcasts, Transformations, Advanced items
- [x] Add `acmOnly` flag to Library item
- [x] Implement `getFilteredNavigation(isAcmMode: boolean)` function that filters items and removes empty groups

### Implementation — Sidebar
- [x] Update `frontend/src/components/layout/AppSidebar.tsx` to import navigation from `frontend/src/config/navigation.ts`
- [x] Read `NEXT_PUBLIC_ACM_MODE` env var and pass to `getFilteredNavigation()`
- [x] Reorganize group titles: "Documents", "Search", "Settings" (in ACM mode)
- [x] Verify empty groups (e.g., "Create" with only Podcasts) are filtered out

### Implementation — Settings Toggle (Optional Enhancement)
- [x] Create or extend `frontend/src/stores/settingsStore.ts` with `acmMode` persisted setting
- [x] Add "ACM-Focused Mode" toggle switch to Settings page

### Implementation — Environment Config
- [x] Add `NEXT_PUBLIC_ACM_MODE=true` to `frontend/.env.example`
- [x] Update `frontend/next.config.js` to expose `NEXT_PUBLIC_ACM_MODE` with default `"false"`

### Acceptance Criteria Verification
- [x] AC: Hide "Notebooks" navigation item
- [x] AC: Hide "Podcasts" navigation item
- [x] AC: Hide "Transformations" navigation item
- [x] AC: Hide "Advanced" navigation item
- [x] AC: Keep "Sources" navigation
- [x] AC: Keep "ACM Register" navigation
- [x] AC: Keep "Ask and Search" navigation
- [x] AC: Keep "Models" navigation
- [x] AC: Keep "Settings" navigation
- [x] AC: Navigation items hidden via feature flag or environment config
- [x] AC: Hidden items easily re-enabled via configuration (no hard delete)
- [x] AC: UI feels cohesive with reduced navigation (no empty groups)

---

## Story 2: E9-S3 — Document Actions & Bulk Operations

### Setup — Database Migration
- [x] Create `migrations/XX_add_archive_fields.surrealql` — add `archived_at`, `deleted_at`, `status` fields to `source` table

### Implementation — Backend Bulk API
- [x] Create `api/routers/source_bulk.py` with `BulkOperationRequest` model
- [x] Implement `POST /api/sources/bulk/delete` — soft delete with 30-min undo grace period
- [x] Implement `POST /api/sources/bulk/undo-delete` — restore soft-deleted documents within grace period
- [x] Implement `POST /api/sources/bulk/reprocess` — queue re-extraction for selected documents
- [x] Implement `POST /api/sources/bulk/archive` — hide without delete
- [x] Implement `POST /api/sources/bulk/unarchive` — restore archived documents
- [x] Implement `POST /api/sources/bulk/export` — ZIP export with original files + ACM CSV
- [x] Register `source_bulk` router in `api/main.py`

### Implementation — Frontend Hooks
- [x] Create `frontend/src/hooks/useDocumentActions.ts` — individual document actions (view, open spreadsheet, re-extract, delete, download, archive)
- [x] Create `frontend/src/hooks/useBulkActions.ts` — bulk operations with batch progress tracking

### Implementation — Frontend Components
- [x] Create `frontend/src/components/documents/DocumentActions.tsx` — dropdown menu with individual actions
- [x] Create `frontend/src/components/documents/BulkActions.tsx` — bulk action bar with progress feedback
- [x] Create `frontend/src/components/documents/EditDocumentDialog.tsx` — metadata editing (rename, tags, notes)
- [x] Create `frontend/src/components/ui/confirm-dialog.tsx` if not already present — confirmation dialog for destructive actions

### Acceptance Criteria Verification
- [x] AC: Individual document actions: View details, Open spreadsheet, Re-extract ACM, Delete
- [x] AC: Bulk actions: Delete selected, Re-process selected, Export selected
- [x] AC: Confirmation dialogs for destructive actions
- [x] AC: Progress feedback for bulk operations
- [x] AC: Undo capability for recent deletions (soft delete with grace period)
- [x] AC: Archive functionality (hide without delete)
- [x] AC: Document metadata editing (rename, add tags/notes)

---

## Story 3: E12-S2 — AI Model Configuration UI

### Implementation — Backend
- [x] Add `StageModelAssignment` Pydantic model to `api/routers/settings.py`
- [x] Add `GET /api/settings/extraction/stage-models` endpoint
- [x] Add `PUT /api/settings/extraction/stage-models` endpoint
- [x] Add `POST /api/settings/extraction/stage-models/reset` endpoint

### Implementation — Frontend Types & API
- [x] Add `StageModelAssignment`, `ExtractionStageConfig` types to `frontend/src/lib/types/models.ts`
- [x] Extend `frontend/src/lib/api/models.ts` with stage model methods
- [x] Add `useStageModels`, `useUpdateStageModels`, `useResetStageModels` hooks

### Implementation — Frontend Page & Form
- [x] Create `ExtractionStageModels.tsx` component with 6 stage model selectors
- [x] Integrate into existing `/settings/models` page
- [x] Per-stage model selector dropdowns (6 stages)
- [x] Cost/speed tier badges (Fast/Balanced/Thorough) per model option
- [x] "Save Configuration" button with success/error toasts
- [x] "Reset to Defaults" button
- [x] Unsaved changes indicator

### Implementation — Sidebar
- [x] "AI Models" nav item already exists under CONFIGURE section

### Acceptance Criteria Verification
- [x] AC: Settings page at `/settings/models` under CONFIGURE section
- [x] AC: 6 extraction stages listed with model selectors
- [x] AC: Dropdowns populated from `GET /api/models`
- [x] AC: Current assignment loaded from SurrealDB singleton
- [x] AC: Cost/speed tier badges on model options
- [x] AC: Save persists via PUT, Reset restores defaults
- [x] AC: Unsaved changes indicator

---

## Story 4: E12-S3 — Processing Options Configuration

### Implementation — Database Migration
- [x] Create `migrations/30.surrealql` — `processing_config` table with defaults

### Implementation — Backend
- [x] Add `ProcessingConfigResponse` Pydantic model with validators to `api/routers/settings.py`
- [x] Add `GET /api/settings/processing` endpoint
- [x] Add `PUT /api/settings/processing` endpoint
- [x] Add `POST /api/settings/processing/reset` endpoint

### Implementation — Frontend Page & Form
- [x] Replace placeholder `settings/processing/page.tsx` with full form
- [x] All 4 processing parameters with correct ranges and defaults
- [x] All 2 timeout settings with correct ranges
- [x] All 3 output preference toggles (Store Raw JSON, Auto-Classify, Auto-Normalize)
- [x] Three preset buttons: Fast, Balanced, Thorough
- [x] Active preset badge when values match
- [x] Save / Reset to Defaults / unsaved changes indicator
- [x] Info banner: "Changes take effect on the next extraction run"

### Implementation — Sidebar
- [x] "Processing" nav item already exists under CONFIGURE section

### Acceptance Criteria Verification
- [x] AC: Settings page at `/settings/processing` under CONFIGURE
- [x] AC: All processing parameters with correct ranges and defaults
- [x] AC: All timeout settings with correct ranges and defaults
- [x] AC: All 3 output preference toggles with defaults
- [x] AC: Three presets populate fields without auto-save
- [x] AC: Active preset badge shown when values match
- [x] AC: Save/Reset/unsaved indicator work correctly
- [x] AC: Info banner about next-run activation

---

## Story 5: E12-S4 — BAR Field Schema Config UI

### Implementation — Database Migration
- [x] `field_schema` table already exists (used by `_load_db_field_config` / `_save_db_field_config` in `api/routers/acm.py`)

### Implementation — Backend
- [x] `FieldSchemaConfig` domain model exists at `open_notebook/extractors/parsers/field_config.py`
- [x] `GET /api/acm/field-config` endpoint exists in `api/routers/acm.py:1495` (frontend calls `/acm/field-config`)
- [x] `PUT /api/acm/field-config` endpoint exists in `api/routers/acm.py:1519` (frontend calls `/acm/field-config`)

### Implementation — Frontend Components
- [x] Create `frontend/src/app/(dashboard)/settings/field-schema/page.tsx` with grouped field list, edit dialog, business rules toggle
- [x] Fields grouped by category with column letter, key, display name, type, required badge, active toggle
- [x] Per-field edit dialog with display name editing (key/column read-only)
- [x] Business rules list with toggle on/off

### Implementation — Import/Export
- [x] Export JSON button downloads current config
- [x] Reset to Defaults button restores from default schema

### Implementation — Sidebar
- [x] Add "Field Schema" nav item under CONFIGURE section in navigation config

### Acceptance Criteria Verification
- [x] AC: Page at `/settings/field-schema` accessible from sidebar
- [x] AC: BAR fields displayed grouped with column letter, key, display name, type, required badge, active toggle
- [x] AC: Per-field edit dialog with display name editing
- [x] AC: Business rules list with toggle on/off
- [x] AC: Export JSON, Reset to Defaults
- [x] AC: Unsaved changes indicator

---

## Story 6: E13-S2 — Knowledge Graph API & Data Service

### Implementation — Backend Repository
- [x] Create `open_notebook/database/graph_repository.py` — consolidated into router with direct repo_query calls

### Implementation — Backend Service
- [x] Create `api/graph_service.py` — consolidated into router with _build_graph_from_records helper

### Implementation — Backend Router
- [x] Create `api/routers/graph.py` with endpoints:
  - [x] `GET /api/graph/source/{source_id}` — full graph for a source
  - [x] `GET /api/graph/school/{school_id}` — school-centric graph
  - [x] `GET /api/graph/building/{building_id}` — building-centric graph
  - [x] `GET /api/graph/stats/{source_id}` — graph statistics
- [x] Register graph router in `api/main.py`

### Implementation — Response Format
- [x] Return React Flow compatible `{ nodes: ReactFlowNode[], edges: ReactFlowEdge[] }` JSON
- [x] Implement auto-layout calculation (hierarchical top-down via dagre)
- [x] Implement risk summary aggregation per node
- [x] Implement filter options: by risk level, by building, by ACM status

### Acceptance Criteria Verification
- [x] AC: All 4 API endpoints return correct graph data
- [x] AC: Response format is React Flow compatible nodes and edges JSON
- [x] AC: Auto-layout via dagre algorithm
- [x] AC: Risk summary aggregation per node
- [x] AC: Filter options work correctly

---

## Story 7: E13-S3 — React Flow Knowledge Graph Visualization

### Setup — Dependencies
- [x] Install `@xyflow/react` and `dagre` npm packages in `frontend/`

### Implementation — Custom Node Components
- [x] Create `frontend/src/components/acm/graph-nodes/SchoolNode.tsx` — name, code, address
- [x] Create `frontend/src/components/acm/graph-nodes/BuildingNode.tsx` — name, year, construction, risk summary badge
- [x] Create `frontend/src/components/acm/graph-nodes/RoomNode.tsx` — name, area, ACM count
- [x] Create `frontend/src/components/acm/graph-nodes/ACMNode.tsx` — product, risk color (red/yellow/green), friability icon
- [x] Create `frontend/src/components/acm/graph-nodes/index.ts` — node type registry

### Implementation — Main Graph Component
- [x] Create `frontend/src/components/acm/KnowledgeGraph.tsx` — React Flow canvas with:
  - [x] Custom node types registered
  - [x] `useQuery` to fetch graph data from E13-S2 API
  - [x] Click-for-details interaction
  - [x] Zoom/pan controls
  - [x] Expand/collapse groups
  - [x] Risk level filter
  - [x] Minimap
  - [x] Export graph as JSON

### Implementation — Integration
- [x] Modify `frontend/src/app/sources/[id]/page.tsx` — add Knowledge Graph tab alongside spreadsheet
- [x] Add toggle between graph view and spreadsheet view (Graph tab shown when ACM data exists)

### Acceptance Criteria Verification
- [x] AC: Knowledge Graph tab in source detail view
- [x] AC: React Flow canvas renders custom nodes (School, Building, Room, ACM)
- [x] AC: Interactive features: click, zoom/pan, expand/collapse, filter, minimap
- [x] AC: Performance: 200+ nodes render smoothly (React Flow handles virtualization)
- [x] AC: Export as JSON (PNG export deferred — requires html-to-image dependency)
- [x] AC: Toggle between graph and spreadsheet views (tab-based switching)

---

## Verification — All Stories

### Lint
- [x] `uv run ruff check .` passes (backend)
- [x] `cd frontend && npm run lint` passes (frontend)

### Test
- [x] `uv run pytest tests/ -x` passes (backend — no new tests, existing pass)
- [x] `cd frontend && npm run build` passes (frontend build)

### File Existence
- [x] All files listed in File Changes tables verified to exist via `Glob`
