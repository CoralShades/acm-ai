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
- [ ] Add `StageModelAssignment` and `ModelConfigSettings` Pydantic models to `open_notebook/domain/settings.py`
- [ ] Add `GET /api/settings/models` endpoint to `api/routers/settings.py` — reads from `open_notebook:default_models`
- [ ] Add `PUT /api/settings/models` endpoint to `api/routers/settings.py` — persists stage-to-model assignments

### Implementation — Frontend Types & API
- [ ] Add `ModelConfigSettings`, `StageModelAssignment` types to `frontend/src/lib/types/settings.ts`
- [ ] Extend `frontend/src/lib/api/settingsApi.ts` with `getModelConfig()`, `updateModelConfig()`

### Implementation — Frontend Page & Form
- [ ] Create `frontend/src/app/(dashboard)/settings/models/page.tsx` — route for model config
- [ ] Create `frontend/src/components/settings/ModelConfigForm.tsx` with:
  - [ ] Per-stage model selector dropdowns (6 stages: structure_analysis, building_inventory, acm_extraction, page_tagging, product_classification, corrective_validation)
  - [ ] Cost/speed tier badges (Fast/Balanced/Thorough) per model option
  - [ ] "Test" button per stage row — runs minimal extraction sample, shows latency/error inline
  - [ ] "Save Configuration" button with success/error toasts
  - [ ] "Reset to Defaults" button with confirmation dialog
  - [ ] Unsaved changes indicator

### Implementation — Sidebar
- [ ] Add "AI Models" nav item under CONFIGURE section in `frontend/src/components/layout/AppSidebar.tsx`

### Acceptance Criteria Verification
- [ ] AC: Settings page at `/settings/models` under CONFIGURE section
- [ ] AC: 6 extraction stages listed with model selectors
- [ ] AC: Dropdowns populated from `GET /api/models`
- [ ] AC: Current assignment loaded from `open_notebook:default_models`
- [ ] AC: Cost/speed tier badges on model options
- [ ] AC: Test button per stage with latency/error result
- [ ] AC: Save persists via PUT, Reset restores defaults
- [ ] AC: Loading skeleton, error state with retry, no-models warning banner

---

## Story 4: E12-S3 — Processing Options Configuration

### Implementation — Database Migration
- [ ] Create `migrations/XX_processing_config.surrealql` — `processing_config` table with seeded Balanced defaults

### Implementation — Backend
- [ ] Add `ProcessingConfig` Pydantic model to `open_notebook/domain/settings.py`
- [ ] Add `GET /api/settings/processing` endpoint to `api/routers/settings.py`
- [ ] Add `PUT /api/settings/processing` endpoint to `api/routers/settings.py`

### Implementation — Frontend Types & API
- [ ] Add `ProcessingConfig` type and `PROCESSING_PRESETS` constant to `frontend/src/lib/types/settings.ts`
- [ ] Extend `frontend/src/lib/api/settingsApi.ts` with `getProcessingConfig()`, `updateProcessingConfig()`

### Implementation — Frontend Page & Form
- [ ] Create `frontend/src/app/(dashboard)/settings/processing/page.tsx`
- [ ] Create `frontend/src/components/settings/ProcessingConfigForm.tsx` with:
  - [ ] Chunk Size number input (2000–8000, default 4000)
  - [ ] Confidence Threshold decimal input (0.0–1.0, step 0.05, default 0.7)
  - [ ] Max Correction Attempts integer input (1–5, default 3)
  - [ ] Batch Size integer input (1–10, default 3)
  - [ ] Per-Page Timeout integer input (10–120s, default 60)
  - [ ] Total Document Timeout integer input (1–30min, default 15)
  - [ ] Store Raw JSON toggle (default on)
  - [ ] Auto-Classify toggle (default on)
  - [ ] Auto-Normalize toggle (default on)
  - [ ] Three preset buttons: Fast, Balanced, Thorough
  - [ ] Active preset badge when values match a preset
  - [ ] Zod validation with inline error messages
  - [ ] Save / Reset to Defaults / unsaved changes indicator
  - [ ] Info banner: "Changes take effect on the next extraction run"

### Implementation — Sidebar
- [ ] Add "Processing" nav item under CONFIGURE section in `frontend/src/components/layout/AppSidebar.tsx`

### Acceptance Criteria Verification
- [ ] AC: Settings page at `/settings/processing` under CONFIGURE
- [ ] AC: All 6 processing parameters with correct ranges and defaults
- [ ] AC: All 2 timeout settings with correct ranges and defaults
- [ ] AC: All 3 output preference toggles with defaults
- [ ] AC: Three presets (Fast/Balanced/Thorough) populate fields without auto-save
- [ ] AC: Active preset badge shown when values match
- [ ] AC: Save/Reset/unsaved indicator work correctly
- [ ] AC: Loading skeleton, error state, inline validation errors
- [ ] AC: Info banner about next-run activation

---

## Story 5: E12-S4 — BAR Field Schema Config UI

### Implementation — Database Migration
- [ ] Create `migrations/XX_bar_schema_config.surrealql` — `bar_schema_config` table (singleton `bar_schema_config:active`)

### Implementation — Backend
- [ ] Add `FieldSchemaConfig` domain model to `open_notebook/domain/settings.py` (or extend from `field_config.py`)
- [ ] Add `GET /api/settings/field-schema` endpoint to `api/routers/settings.py`
- [ ] Add `PUT /api/settings/field-schema` endpoint to `api/routers/settings.py`

### Implementation — Frontend Components
- [ ] Create `frontend/src/app/(dashboard)/settings/field-schema/page.tsx` — settings page
- [ ] Create `frontend/src/components/settings/FieldSchemaEditor.tsx` — drag-reorder list of 47 fields with sort_order, display name, type, required badge, active toggle
- [ ] Create `frontend/src/components/settings/FieldEditModal.tsx` — per-field edit dialog (display name, required, active, read-only key/column)
- [ ] Create `frontend/src/components/settings/PicklistEditor.tsx` — enum value add/remove/rename for fields with controlled enums
- [ ] Create `frontend/src/components/settings/BusinessRulesList.tsx` — rule toggle list (view + toggle only, no custom rule creation)

### Implementation — Import/Export
- [ ] Add "Export as JSON" button — downloads current field schema config
- [ ] Add "Import from BAR Excel" button — file upload `.xlsm/.xlsx`, sends to `POST /api/settings/field-schema/import`
- [ ] Add diff preview before confirming import
- [ ] Add "Reset to Defaults" — restores from `register_row.schema.json` + `register_enums.json`

### Implementation — Sidebar
- [ ] Add "Field Schema" nav item under CONFIGURE section in `frontend/src/components/layout/AppSidebar.tsx`

### Acceptance Criteria Verification
- [ ] AC: Page at `/settings/field-schema` accessible from sidebar
- [ ] AC: 47 BAR fields displayed in drag-reorder list
- [ ] AC: Each row shows BAR column letter, key, display name, type, required badge, active toggle
- [ ] AC: Drag reorder changes sort_order
- [ ] AC: Per-field edit modal with display name, required, active toggles
- [ ] AC: Picklist editor for enum fields (add/remove/rename values)
- [ ] AC: Business rules list with toggle on/off
- [ ] AC: Export JSON, Import BAR Excel with diff preview, Reset to Defaults
- [ ] AC: Changes reflected in extraction, AG Grid columns, and export
- [ ] AC: Unsaved changes indicator

---

## Story 6: E13-S2 — Knowledge Graph API & Data Service

### Implementation — Backend Repository
- [ ] Create `open_notebook/database/graph_repository.py` — SurrealDB graph traversal queries using `->` and `<-` operators

### Implementation — Backend Service
- [ ] Create `api/graph_service.py` — graph data service with dagre layout calculation, risk aggregation

### Implementation — Backend Router
- [ ] Create `api/routers/graph.py` with endpoints:
  - [ ] `GET /api/graph/source/{source_id}` — full graph for a source
  - [ ] `GET /api/graph/school/{school_id}` — school-centric graph
  - [ ] `GET /api/graph/building/{building_id}` — building-centric graph
  - [ ] `GET /api/graph/stats/{source_id}` — graph statistics
- [ ] Register graph router in `api/main.py`

### Implementation — Response Format
- [ ] Return React Flow compatible `{ nodes: ReactFlowNode[], edges: ReactFlowEdge[] }` JSON
- [ ] Implement auto-layout calculation (hierarchical top-down via dagre)
- [ ] Implement risk summary aggregation per node
- [ ] Implement filter options: by risk level, by building, by ACM status

### Acceptance Criteria Verification
- [ ] AC: All 4 API endpoints return correct graph data
- [ ] AC: Response format is React Flow compatible nodes and edges JSON
- [ ] AC: Auto-layout via dagre algorithm
- [ ] AC: Risk summary aggregation per node
- [ ] AC: Filter options work correctly

---

## Story 7: E13-S3 — React Flow Knowledge Graph Visualization

### Setup — Dependencies
- [ ] Install `@xyflow/react` and `dagre` npm packages in `frontend/`

### Implementation — Custom Node Components
- [ ] Create `frontend/src/components/acm/graph-nodes/SchoolNode.tsx` — name, code, address
- [ ] Create `frontend/src/components/acm/graph-nodes/BuildingNode.tsx` — name, year, construction, risk summary badge
- [ ] Create `frontend/src/components/acm/graph-nodes/RoomNode.tsx` — name, area, ACM count
- [ ] Create `frontend/src/components/acm/graph-nodes/ACMNode.tsx` — product, risk color (red/yellow/green), friability icon
- [ ] Create `frontend/src/components/acm/graph-nodes/index.ts` — node type registry

### Implementation — Main Graph Component
- [ ] Create `frontend/src/components/acm/KnowledgeGraph.tsx` — React Flow canvas with:
  - [ ] Custom node types registered
  - [ ] `useQuery` to fetch graph data from E13-S2 API
  - [ ] Click-for-details interaction
  - [ ] Zoom/pan controls
  - [ ] Expand/collapse groups
  - [ ] Risk level filter
  - [ ] Minimap
  - [ ] Export graph as PNG/SVG

### Implementation — Integration
- [ ] Modify `frontend/src/app/sources/[id]/page.tsx` — add Knowledge Graph tab alongside spreadsheet
- [ ] Add toggle between graph view and spreadsheet view

### Acceptance Criteria Verification
- [ ] AC: Knowledge Graph tab in source detail view
- [ ] AC: React Flow canvas renders custom nodes (School, Building, Room, ACM)
- [ ] AC: Interactive features: click, zoom/pan, expand/collapse, filter, minimap
- [ ] AC: Performance: 200+ nodes render smoothly
- [ ] AC: Export as PNG/SVG
- [ ] AC: Toggle between graph and spreadsheet views

---

## Verification — All Stories

### Lint
- [ ] `uv run ruff check .` passes (backend)
- [ ] `cd frontend && npm run lint` passes (frontend)

### Test
- [ ] `uv run pytest tests/ -x` passes (backend)
- [ ] `cd frontend && npm run build` passes (frontend build)

### File Existence
- [ ] All files listed in File Changes tables verified to exist via `Glob`
